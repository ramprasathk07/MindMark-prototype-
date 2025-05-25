import os
import json
from pathlib import Path as p
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.chains import ConversationalRetrievalChain
from langchain_core.runnables import RunnablePassthrough
import logging


logging.basicConfig(level=logging.INFO)

from utils.get_keys import load_config

class Ask_Gemini():
    def __init__(self,json_file):

        load_config('configs\config.yaml')
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY is not set in environment variables.")
        
        self.instance_folder = 'backend_src\instance'

        self.model = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    google_api_key=api_key,
                    temperature=0.0,
                    convert_system_message_to_human=True,
                    timeout=500
                )

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            documents = [
                Document(
                    page_content=(
                        f"Question: {item.get('Question', 'NA')}\n"
                        f"Score: {item.get('Score', 'NA')}\n"
                        f"Explanation for correct option: {item.get('Explanation for correct option', 'NA')}\n"
                        f"Positive Feedback: {item.get('Positive Feedback', 'NA')}\n"
                        f"Negative Feedback: {item.get('Negative Feedback', 'NA')}\n"
                        f"Common Misconceptions: {item.get('Common Misconceptions', 'NA')}"
                    ),
                    metadata={
                        "Question Number": item.get("Question Number", "NA"),
                        "Subject": item.get("Subject", "NA"),
                        "Topic": item.get("Topic", "NA"),
                        "Taxonomy": item.get("Taxonomy", "NA"),
                        "Difficulty": item.get("Difficulty", "NA"),
                        "Correct Option": item.get("Correct Option", "NA"),
                        "Student Option": item.get("Student Option", "NA")
                    }
                )
                for item in data
            ]
           
        except Exception as e:
            logging.error(f"Error in start_RAG: {e}")
            return None

        self.embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=api_key
                )

        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, 
                                                            chunk_overlap=100)

        self.QUERY_PROMPT = PromptTemplate(
            input_variables=["question"],
            template="""You are an AI assistant specialized in analyzing and providing insights about a student's performance in exams, assessments, and studies. 
            Your goal is to assist students by answering their questions and providing detailed analysis based on their performance data. 
            Address the following aspects as applicable to the student's query:

            - Identify strengths and weaknesses in specific subjects or topics.
            - Offer actionable recommendations for improvement.
            - Suggest effective study strategies and time management techniques.
            - Provide insights into common mistakes and how to avoid them.
            - Highlight areas of consistent performance and growth opportunities.

            Student data: {question}

            Respond with clear, concise, and actionable insights tailored to the student's needs.
            """
        )
        self.vector_db_path = os.path.join(self.instance_folder, "vector_db")
        self.chunks = self.text_splitter.split_documents(documents)
        self.vector_db = Chroma.from_documents(documents=self.chunks, embedding=self.embeddings, collection_name="local-rag",
                                               persist_directory=self.vector_db_path)
        self.vector_db.persist() 
        logging.info(f"Vector database saved to {self.vector_db_path}")

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            chat_memory=ChatMessageHistory(),
            return_messages=True
        )

    def __call__(self,question):
      
        self.retriever = MultiQueryRetriever.from_llm(self.vector_db.as_retriever(search_kwargs={"k": 45}),
                                                      llm=self.model, 
                                                      prompt=self.QUERY_PROMPT)
        response_prompt = ChatPromptTemplate.from_template("Answer the question based ONLY on the following context:\n{context}\nQuestion: {question}")
        chain = {"context": self.retriever, "question": RunnablePassthrough()} | response_prompt | self.model | StrOutputParser()
        
        # chain = ConversationalRetrievalChain.from_llm(
        #     self.model,
        #     chain_type="stuff",
        #     retriever=self.retriever,
        #     memory=self.memory,
        #     return_source_documents=True
        # )

        results = chain.invoke(question)
        logging.info("RAG setup completed successfully.")
        return results

if __name__ == '__main__':
    gemini = Ask_Gemini('generated_files_1/eval_report.json')
    # import time 
    # time.sleep(5)
    print(gemini(question='Explain weak areas in Chemistry ?'))
    print("===================")
    print(gemini(question='so what the strong ponts then?'))

    # if __name__ == '__main__':
    # answer = start_RAG(json_file='generated_files/eval_report.json', question='Explain weak areas in Chemistry.')
    # print("Answer:", answer if answer else "Failed to generate an answer.")

