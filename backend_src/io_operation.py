import os
import re
import sqlite3
from PIL import Image
import fitz 
import json
import PyPDF2
from extractous import Extractor
import re,json
import re
import json
import os
from database import populate_q_db
from logger_config import logging

class PDFProcessor:
    def __init__(self):
        self.outpath = 'generated_files'
        os.makedirs(self.outpath,exist_ok=True)
        
    def process_pdf(self,path,file_type=''):
        if file_type == 'Question':
            outpath = f"{self.outpath}/{path.split('/')[-1].split('.')[0]}_images"
            return outpath
        
        elif file_type == 'answer_sheet':
            txt = self.read_pdf(path)
            self.answer_sheet = self.format_answers(txt)
            s_id=self.answer_sheet["Student ID"]
            q_id=self.answer_sheet["Question Paper ID"]
            return self.answer_sheet,s_id,q_id
        else:
            txt = self.read_pdf(path)
            self.answer_key = self.format_answers(txt) 
            return self.answer_key
        
    def read_pdf(self,file_path):
        """
        Reads and extracts text from a PDF file.
        """
        text = ""
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text

    def extract_questions(self,path:str,out:str):

        # extractor = Extractor().set_ocr_config(TesseractOcrConfig().set_language("deu"))
        # result, _ = extractor.extract_file_to_string("QuestionPaper.pdf")

        extractor = Extractor()
        extractor.set_extract_string_max_length(10000)

        # Extract text from a file
        result, metadata = extractor.extract_file_to_string(path)

        question_paper_id_pattern = r"(?i)\bquestion[\s_-]*paper[\s_-]*id[:\s]*([\w\d]+)"
        question_paper_id_match = re.search(question_paper_id_pattern, result.lower())
        question_paper_id = question_paper_id_match.group(1) if question_paper_id_match else "Unknown"

        pattern = r"(\d+)\.\s(.*?)(?:A\))(.*?)B\)(.*?)C\)(.*?)D\)(.*?)(?=\d+\.|$)"

        matches = re.findall(pattern, result, re.DOTALL)
        
        data =[]
        for match in matches:
            q = match[1].strip()
            op = [match[2].strip(), match[3].strip(), match[4].strip(), match[5].strip()]
            options = {}
            c=1
            for i in op:
                    options[c]=i
                    c+=1
            question_no=match[0].strip()
            data.append({
                "Question no": int(question_no),
                "Question": q,
                "options": options
            })

        with open(out+question_paper_id+".json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        return data
    
    def merge_answers_with_questions(self,quest_paper):
        merged_json = []

        # Iterate through each question in quest_paper
        for question in quest_paper:
            question_no = str(question.get("Question no")).strip()

            # Find the corresponding answer in the answer key
            print(f"answer:{self.answer_key}")
            correct_option = None
            # for answer in self.answer_key:
            for ans in self.answer_key['answers']:
                    if str(ans.get("Question no")).strip() == question_no:
                        correct_option = ans.get("option")
                        break
            # Add the correct answer to the question
            if correct_option:
                question['Correct Answer'] = correct_option
            else:
                question['Correct Answer'] = "Not Available"

            merged_json.append(question)

            q_paper = self.answer_key['Question Paper ID']
            file_path = f"QA_{q_paper}.json"
            with open(f"{self.outpath}/{file_path}", 'w') as f:
                    json.dump(merged_json, f, indent=4)
            connection = sqlite3.connect("Database/Questions.db")
            cursor = connection.cursor()
            populate_q_db(question,q_paper,connection,cursor)
            connection.commit()
        logging.info(f"Question Paper data updated in DB")
        connection.close()
        return merged_json,q_paper

    
    def format_answers(self, answer_key_text: str):
        # Patterns for extracting Question Paper ID and Student ID
        question_paper_id_pattern = r"(?i)\bquestion[\s_-]*paper[\s_-]*id[:\s]*([\w\d]+)"
        student_id_pattern = r"(?i)\bstudent[\s_-]*id[:\s]*([\w\d]+)"

        # Extract IDs
        question_paper_id_match = re.search(question_paper_id_pattern, answer_key_text.lower())
        student_id_match = re.search(student_id_pattern, answer_key_text.lower())
        question_paper_id = question_paper_id_match.group(1) if question_paper_id_match else "Unknown"
        student_id = student_id_match.group(1) if student_id_match else "Unknown"

        # Split the answer key by subject headings (e.g., "Physics:")
        subject_split_pattern = r"(\w+):\s*\n"
        subjects = re.split(subject_split_pattern, answer_key_text)

        formatted_result = []
        option_mapping = {"A": 1, "B": 2, "C": 3, "D": 4, "UNATTEMPTED": "Unattempted"}

        # if len(subjects) > 1:  # More than one section
        #     for subject_text in subjects[1:]:  # Skip the first part as it's the unmatched text
        #         answer_pattern = r"(\d+)\.\s*([A-Da-d]|Unattempted)"
        #         answers = re.findall(answer_pattern, subject_text)
        #         print(answers)
        #         formatted_answers = [   
        #             {"Question no": int(question_no), "option": option_mapping[option.UPPER()]}
        #             for question_no, option in answers
        #         ]
        #         formatted_result.extend(formatted_answers)
        # else:  # No subject divisions, process entire text
        answer_pattern = r"(\d+)\.\s*([A-Da-d]|Unattempted)"
        answers = re.findall(answer_pattern, answer_key_text)
        formatted_result = [
                {"Question no": int(question_no), "option": option_mapping[option.upper()]}
                for question_no, option in answers
        ]
        print(formatted_result)
        # Define output file path
        if student_id != "Unknown":
            outfile_path = f"{self.outpath}/{student_id}"
            filename = f"response_sheet_{question_paper_id}.json"
        else:
            outfile_path = f"{self.outpath}/{question_paper_id}"
            filename = f"answer_key_{question_paper_id}.json"

        os.makedirs(outfile_path, exist_ok=True)

        # Create output dictionary
        outfile = {
            "Student ID": student_id if student_id != "Unknown" else None,
            "Question Paper ID": question_paper_id,
            "answers": formatted_result,
        }

        # Write to JSON file
        file_path = f"{outfile_path}/{filename}"
        with open(file_path, 'w') as f:
            json.dump(outfile, f, indent=4)

        logging.debug(f"File {filename} successfully saved to {outfile_path}")

        return outfile