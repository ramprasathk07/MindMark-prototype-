import json
import os
import sqlite3
import sys
import time
import logging
from typing import Any, Dict, List, Union
from database import populate_analysis_db
from utils.get_keys import load_config
import sys
import google.generativeai as genai
from google.api_core import exceptions as genai_exceptions
from langchain_core.pydantic_v1 import BaseModel, Field

load_config("../configs/config.yaml")

class Explain(BaseModel):
    Question: str = Field(description="Question")
    Subject: str = Field(description="Subject name")
    Topic: str = Field(description="Topic name")
    sub_topic: str = Field(description="sub_topic name")
    Difficulty: float = Field(description="Difficulty level of question on scale of 0 to 5")
    Correct_Answer_Explanation: str = Field(description="Detailed explanation of the correct answer.")
    Incorrect_Option_Analysis: dict = Field(description="Detailed explanations for only the incorrect options.")
    Common_Student_Misconceptions: str = Field(description="List common misconceptions.")
    Question_Type: str = Field(description="Question_Type")
    Taxonomy: str = Field(description="Taxonomy")
    Positive_Feedback: str = Field(description="Positive_Feedback")
    Negative_Feedback: str = Field(description="Negative_Feedback")
    correct_option: str = Field(description="correct_option")
    Options: dict = Field(description="Options")

class APIKeyManager:
    def __init__(self, api_keys: List[str]):
        if not api_keys:
            logging.error("No API keys provided.")
            sys.exit(1)
        self.api_keys = api_keys
        self.total_keys = len(api_keys)
        self.current_index = 0

    def get_current_key(self) -> str:
        return self.api_keys[self.current_index]

    def switch_key(self) -> bool:
        """
        Switch to the next API key.
        Returns True if switched successfully, False if all keys have been tried.
        """
        self.current_index += 1
        if self.current_index >= self.total_keys:
            self.current_index = 0
            return False  # All keys have been cycled through
        return True

class AIModelEvaluator:
    def __init__(self, api_key_manager: APIKeyManager, model_type="gemini", temperature=0.7):
        self.model_type = model_type
        self.temperature = temperature
        self.api_key_manager = api_key_manager
        self.configure_current_key()

        self.generation_config = {
            "temperature": self.temperature,
            "top_p": 0.9,                # Adjusted for diversity
            "top_k": 30,                 # Reduced to limit the number of tokens considered
            "max_output_tokens": 7500,   # Reduced to prevent excessive length
            "response_mime_type": "application/json",  # Expecting JSON response
        }

        self.client = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=self.generation_config,
        )

    def configure_current_key(self):
        current_key = self.api_key_manager.get_current_key()
        genai.configure(api_key=current_key)
        logging.info(f"Using API Key {self.api_key_manager.current_index + 1} of {self.api_key_manager.total_keys}")

    def generate_explanations(self, question: str, options: Dict[str, str], correct_option: str) -> Union[Explain, Dict[str, Any]]:
        prompt = f"""
        You are an AI Evaluation Assistant designed to analyze and evaluate questions, providing structured and comprehensive feedback.

        Question: {question}           # <-- Ensure this is included explicitly
        Options: {json.dumps(options, indent=4)}
        Correct Answer: {correct_option}

        Provide explanations in the following JSON format:
        {{
            "Question: {question},
            "Options: {json.dumps(options, indent=4)},
            "correct_option": {correct_option},
            "Subject": "Subject name",
            "Topic": "Topic name",
            "sub_topic": "Sub_topic name according to subject and topic",
            "Taxonomy": "Cognitive level (e.g., Knowledge, Application, Analysis).",
            "Question_Type": "Type of question (e.g., Calculative, Conceptual, Application-Based).",
            "Correct_Answer_Explanation": "Detailed explanation of the correct answer.",
            "Incorrect_Option_Analysis": {{
                "Option_Number": {{
                    "Type_of_Error": "Specify the type of error (e.g., Conceptual Error, Calculative Error, etc.)",
                    "Description": "Explain why this option is incorrect and contrast it with the correct answer."
                }}
            }},
            "Common_Student_Misconceptions": "List common misconceptions that students might have while answering this question.",
            "Difficulty": "Rate the difficulty on a scale of 0 to 5.",
            "Positive_Feedback": "Provide detailed feedback, focusing on the student's strengths in understanding the key concepts and the topic of the question. Highlight their ability to apply these concepts effectively in 2-3 sentences.",
            "Negative_Feedback": "Provide negative feedback but detailed feedback, focusing on the student's misunderstanding of the key concepts and the topic. Identify the exact areas where they need improvement and offer a clear review in 2-3 sentences."
        }}
        """
        while True:
            try:
                chat_session = self.client.start_chat(history=[])
                response = chat_session.send_message(prompt).text
                print(f"\nResponse:{response}\n")
                logging.info("Received response from Generative AI.")

                # Attempt to parse the response directly as JSON
                explanation_report = json.loads(response)
                explanation_report = Explain(**explanation_report)
                return explanation_report.dict()

            except genai_exceptions.ResourceExhausted as e:
                logging.error(f"API quota exceeded: {e}")
                # Attempt to switch API key
                if not self.api_key_manager.switch_key():
                    logging.warning("All API keys have been exhausted. Waiting for 60 seconds before retrying...")
                    time.sleep(60)
                else:
                    self.configure_current_key()
                    logging.info("Switched to the next API key and retrying...")
            
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                logging.debug(f"Raw response: {response}")
                return {"error": "Invalid JSON response received from the model."}
            
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                return {"error": "An unexpected error occurred during explanation generation."}

    def generate_explanations_single_file(self,id, question_data: Union[List[Dict[str, Any]], Dict[str, Any]],outfile_path = 'generated_files/analysis.json' ) -> str:
        if os.path.exists(outfile_path):
            with open(outfile_path, 'r', encoding='utf-8') as file:
                try:
                    existing_data = json.load(file)
                except json.JSONDecodeError:
                    existing_data = {}
        else:
            existing_data = {}
        questions = question_data if isinstance(question_data, list) else [question_data]

        connection = sqlite3.connect("Database/Questions.db")
        cursor = connection.cursor()
        for question_entry in questions:
            question_no = question_entry.get("Question no", "N/A")
            question = question_entry.get("Question", "")
            options = question_entry.get("options", {})
            correct_option = question_entry.get("Correct Answer", "Unattempted")
            try:
                q=f"SELECT * FROM {id}_LLM WHERE Qno=?"
                cursor.execute(q,(question_no,))
                if cursor.fetchone()!=None:
                    continue
            except:
                pass
            explanation = self.generate_explanations(question, options, correct_option)
            existing_data[question_no] = explanation
            populate_analysis_db(connection,cursor,explanation,question_no,id)
            try:
                with open(outfile_path, 'w', encoding='utf-8') as file:
                    json.dump(existing_data, file, indent=4, ensure_ascii=False)
                logging.info(f"Successfully saved explanation for Question {question_no} to {outfile_path}")
            except Exception as e:
                logging.error(f"Failed to save explanation for Question {question_no}: {e}")
                
        connection.commit()
        connection.close()

        return outfile_path

def Assistant(question_data, id, model_name:str="Gemini 1.5 Pro",output_path='generated_files/analysis.json') -> str:
    api_keys = [
        os.environ.get('GEMINI_API_KEY')
    ]

    api_key_manager = APIKeyManager(api_keys=api_keys)
    evaluator = AIModelEvaluator(
        api_key_manager=api_key_manager,
        model_type=model_name,
        temperature=0.5
    )

    outfile = evaluator.generate_explanations_single_file(id,question_data,output_path)

if __name__ == "__main__":
    single_file_path = "generated_files\question_paper_qp_1.json" # Replace with the path to your input JSON file
    with open(single_file_path,'r') as f:
        ques = json.load(f)
    outfile = Assistant(ques,model_name  = "gemini-2.0-flash-exp")
    print(f"Generated output saved to: {outfile}")