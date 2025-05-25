import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import json,os
from io_operation import PDFProcessor
from logger_config import logging 
from evaluate_student import calculate_score_and_generate_report
import tempfile
from utils.get_keys import load_config
import sys 
from pathlib import Path
from gemi_rag import start_RAG
from explain_gem import Assistant

app = Flask(__name__)
CORS(app)
objs = PDFProcessor()

global analysis_over
analysis_over=False

# Function to save the uploaded file as a PDF
def save_uploaded_file(file, file_type):
    # Ensure the file is saved with a .pdf extension
    temp_dir = tempfile.mkdtemp()  # Create a temporary directory
    temp_file_path = os.path.join(temp_dir, f"{file_type}.pdf")  # Save with a .pdf extension
    file.save(temp_file_path)  # Save the uploaded file
    return temp_file_path

@app.route("/post_db",methods=["POST"])
def post_db():
    global analysis_over
    analysis_over=False
    current_dir = Path(__file__).parent.resolve()
    parent_dir = current_dir.parent
    sys.path.append(str(parent_dir))

    load_config('../configs/config.yaml')
    
    qp=request.files["question"]
    ans_key=request.files["anskey"]
    ans_sh=request.files["ans_sheet"]
    question_file_path = save_uploaded_file(qp, "question")
    ans_key_file_path = save_uploaded_file(ans_key, "ans_key")
    ans_sh_file_path = save_uploaded_file(ans_sh, "ans_sheet")

    student_answers,sid,qid = objs.process_pdf(file_type='answer_sheet',path=ans_sh_file_path)
    objs.process_pdf(file_type='',path=ans_key_file_path)
    
    logging.info(f"Answer sheet and key extraction completed successfully. Output saved at: generated_files")

    #Populating Question paper DB
    result,id = objs.merge_answers_with_questions(quest_paper=objs.extract_questions(question_file_path,out = f"generated_files/Question_paper_"))

    #Populating Analysis LLM Output DB
    output_path = 'generated_files/analysis.json'
    Assistant(result,id, model_name  = "gemini-2.0-flash-exp",output_path=output_path)

    logging.info(f"Analysis Generation completed successfully. Output saved at: {output_path}")
    
    results = calculate_score_and_generate_report(qid,sid,student_answers = student_answers)


    output_path = 'generated_files/eval_report.json'
    with open(output_path, 'w',encoding='utf-8') as f:
        json.dump(results, f, indent=4)

    analysis_over=True
    logging.info(f"Evaluation for student:{student_answers['Student ID']} completed successfully. Output saved in DB")
    logging.info(f"Starting RAG on Evaluation Report for student:{student_answers['Student ID']}")
    return {}

@app.route('/rag', methods=['POST'])
def rag():
    output_path = 'generated_files/eval_report.json'
    data = request.json
    question = data.get('question')
    if question:
        answer = start_RAG(output_path,question)
        return jsonify({'answer': answer})
    else:
        return jsonify({'error': 'No question provided'}), 400

@app.route("/json_file",methods=["GET"])
def json_file():
    file_path = os.path.join('generated_files', 'analysis.json')
    if analysis_over:
        return jsonify({"message":"done"})
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r',encoding='utf-8') as file:
                data = json.load(file)
                d={}
                for i in data.keys():
                    if "error" in data[i].keys():
                        continue
                    d[i]=data[i]
            return jsonify(d)
    except:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"error": "File not found"}), 404

# @app.route("/test",methods=["GET"])
# def test():
    
#     # Prepare and execute the query
#     query = f"SELECT * FROM qp_1 WHERE Qno = ?"
#     cursor.execute(query, (1,))
    
#     # Fetch the row
#     row = cursor.fetchone()
    
    
#     print(dict(row))
#     return {}

if __name__ == "__main__":
    directory_path = "Database"
    os.makedirs(directory_path, exist_ok=True)
    app.run(debug=True, port=5000, use_reloader=False)
