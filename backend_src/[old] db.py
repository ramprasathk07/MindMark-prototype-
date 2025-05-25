from flask import Flask,  jsonify, make_response, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import json,os
from tqdm import tqdm 
from io_operation import PDFProcessor
# from gemini_services import extract_text_from_images
# from phi3_ocr import Phi3
from logger_config import logging 
# from explain_groq_v1 import Assistant
from explain_gem import Assistant
from evaluate_student import calculate_score_and_generate_report
import os
import tempfile
from werkzeug.utils import secure_filename
from utils.get_keys import load_config
import sys 
from pathlib import Path
from rag import start_RAG
import shutil
def remove_instance_folder():
    instance_folder = os.path.join(os.getcwd(), "instance")
    
    if os.path.exists(instance_folder):
        try:
            shutil.rmtree(instance_folder)
            print(f"'instance' folder removed successfully.")
        except Exception as e:
            print(f"Error removing 'instance' folder: {e}")
    else:
        print("'instance' folder does not exist.")

remove_instance_folder()

app = Flask(__name__)
db=SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///DB.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db.init_app(app)
objs = PDFProcessor()
# phi_ocr = Phi3()

def reset_db_instance():
    instance_path = Path("instance")
    db_path = instance_path / 'DB.db'

    try:
        if db_path.exists():
            shutil.rmtree(instance_path)  # Remove entire instance folder
        instance_path.mkdir(parents=True)  # Recreate instance folder
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///DB.db"
        db.init_app(app)  # Reinitialize the database
        logging.info("Database instance reset successfully.")
    except Exception as e:
        logging.error(f"An error occurred while resetting the database instance: {e}")

class Questionpaper(db.Model):
    Qno=db.Column(db.Integer,primary_key=True)
    Question=db.Column(db.String,nullable=False)
    op1=db.Column(db.String,nullable=False)
    op2=db.Column(db.String,nullable=False)
    op3=db.Column(db.String,nullable=False)
    op4=db.Column(db.String,nullable=False)
    correct_op=db.Column(db.String,nullable=False)

class LLM_output(db.Model):
    Qno=db.Column(db.Integer,db.ForeignKey('questionpaper.Qno'),primary_key=True)
    diff=db.Column(db.String,nullable=False)
    subject=db.Column(db.String,nullable=False)
    topic=db.Column(db.String,nullable=False)
    corr_expl=db.Column(db.String,nullable=False)
    wrng_1=db.Column(db.String,nullable=False)
    wrng_2=db.Column(db.String,nullable=False)
    wrng_3 = db.Column(db.String,nullable=False)
    Common_Student_Misconceptions = db.Column(db.String,default="NA")
    Question_Type = db.Column(db.String,default="NA")
    Taxonomy = db.Column(db.String,default="NA")
    Positive_Feedback = db.Column(db.String,default="NA")
    Negative_Feedback = db.Column(db.String,default="NA")

class Eval_report(db.Model):
    Qno=db.Column(db.Integer,db.ForeignKey('questionpaper.Qno'),primary_key=True)
    Question=db.Column(db.String,nullable=False)
    Score = db.Column(db.Integer,nullable=True)
    subject=db.Column(db.String,nullable=False)  
    topic=db.Column(db.String,nullable=False)
    diff=db.Column(db.Integer, default=0)
    Taxonomy = db.Column(db.String,default="NA")
    stud_op=db.Column(db.String, default="NA")
    Error_exp=db.Column(db.String,default="NA")
    Common_Student_Misconceptions = db.Column(db.String,nullable=False)
    Feedback = db.Column(db.String,default="NA")
    
def populate_report_db(questions:list):
    # with open("op.json", "r") as file:
        # for i in json.load(file):
        
    for i in questions:
        if "Total Score" in i.keys():
            break
        score = 0
        expl=""
        if isinstance(i.get("Explanation for the option chosen"), dict):
            expl=(list(i.get("Explanation for the option chosen").values())[0]+" "+list(i.get("Explanation for the option chosen").values())[1])
        else:
            expl=i.get("Explanation for the option chosen")
        feedback = i.get("Positive Feedback", i.get("Negative Feedback", "NA"))
        qp = Eval_report(
            Qno=int(i["Question Number"]),
            Question=i["Question"],
            Score=i["Score"],
            subject=i["Subject"],
            topic=i["Topic"],
            diff=int(i["Difficulty"]),
            Taxonomy=i.get("Taxonomy", "NA"),
            stud_op=i.get("Student Option", "NA"),
            Error_exp=expl,
            Common_Student_Misconceptions=i.get("Common Misconceptions", "NA"),
            Feedback=feedback
        )
        db.session.add(qp)
        db.session.commit()
    
    logging.info(f"Question Paper data updated in DB")
    return {}

def populate_q_db(questions:list):
    # with open("op.json", "r") as file:
        # for i in json.load(file):
    for i in questions:
        print(i)
        opts=i["options"]
        if opts=={}:
            opts={1:"NA",2:"NA",3:"NA",4:"NA"}
        qp=Questionpaper(Qno = int(i["Question no"]),
                         Question = i["Question"],
                         op1 = opts[1],
                         op2 = opts[2],
                         op3 = opts[3],
                         op4 = opts[4],
                         correct_op = i["Correct Answer"])
        
        db.session.add(qp)
        db.session.commit()
    
    logging.info(f"Question Paper data updated in DB")
    return {}

# Function to save the uploaded file as a PDF
def save_uploaded_file(file, file_type):
    # Ensure the file is saved with a .pdf extension
    temp_dir = tempfile.mkdtemp()  # Create a temporary directory
    temp_file_path = os.path.join(temp_dir, f"{file_type}.pdf")  # Save with a .pdf extension
    file.save(temp_file_path)  # Save the uploaded file
    return temp_file_path

global analysis_over
analysis_over=False
def populate_analysis_db(op):
    with open(op, "r",encoding='utf-8') as file:
        questions=json.load(file)
    print(questions)
    if not isinstance(questions, list):
        questions = list(questions.values())
    for i in range(len(questions)):
            if "error" in questions[i].keys():
                continue
            # for i in questions.keys():
            print(questions[i])
            print("\n\n")
            opts=questions[i]["Options"]
            print(opts)
            if opts=={}:
                opts={"1":"NA","2":"NA","3":"NA","4":"NA"}
            
            incorrect_analysis = list(questions[i]['Incorrect_Option_Analysis'].values())


            print(list(questions[i]['Incorrect_Option_Analysis'].values())[1]["Type_of_Error"]+" "+list(questions[i]['Incorrect_Option_Analysis'].values())[1]["Description"])
            qp=LLM_output(Qno=int(i),
                        diff=questions[i]["Difficulty"],
                        subject=questions[i]["Subject"],
                        topic=questions[i]["Topic"],
                        wrng_1 = (
                            incorrect_analysis[0]["Type_of_Error"] + " " + incorrect_analysis[0]["Description"]
                            if len(incorrect_analysis) > 0 else "NA"
                        ),

                        wrng_2 = (
                            incorrect_analysis[1]["Type_of_Error"] + " " + incorrect_analysis[1]["Description"]
                            if len(incorrect_analysis) > 1 else "NA"
                        ),

                        wrng_3 = (
                            incorrect_analysis[2]["Type_of_Error"] + " " + incorrect_analysis[2]["Description"]
                            if len(incorrect_analysis) > 2 else "NA"
                        ),
                        corr_expl=questions[i]['Correct_Answer_Explanation'],
                        Common_Student_Misconceptions = questions[i]['Common_Student_Misconceptions'],
                        Question_Type=questions[i]["Question_Type"],
                        Taxonomy=questions[i]["Taxonomy"],
                        Positive_Feedback=questions[i]["Positive_Feedback"],
                        Negative_Feedback=questions[i]["Negative_Feedback"],
                        )
            
            db.session.add(qp)
            db.session.commit()
            logging.info(f"Question Paper data updated in DB")

    return {}

@app.route("/post_db",methods=["POST"])
def post_db():
    
    global analysis_over
    current_dir = Path(__file__).parent.resolve()
    parent_dir = current_dir.parent
    sys.path.append(str(parent_dir))

    load_config('../configs/config.yaml')
    
    qp=request.files["question"]
    ans_key=request.files["anskey"]
    ans_sh=request.files["ans_sheet"]
    #Creating data directory

  # Save all files with appropriate names
    question_file_path = save_uploaded_file(qp, "question")
    ans_key_file_path = save_uploaded_file(ans_key, "ans_key")
    ans_sh_file_path = save_uploaded_file(ans_sh, "ans_sheet")

    student_answers = objs.process_pdf(file_type='answer_sheet',path=ans_sh_file_path)
    objs.process_pdf(file_type='',path=ans_key_file_path)
    
    # print(f"\nstudent_answers:{student_answers}\n")
    # return
    logging.info(f"Answer sheet and key extraction completed successfully. Output saved at: generated_files")

    # base = f"generated_files\{quest_path.split('\\')[-1].split('.')[0]}"
    # question_outpath = f"generated_files/{quest_path.split('\\')[-1].split('.')[0]}.json"
    # image_paths = [os.path.join(saved_path,i) for i in os.listdir(saved_path)]
    all_questions = objs.extract_questions(question_file_path,out = f"generated_files/question_paper.json")

    ## link question 
    print(all_questions)
    result = objs.merge_answers_with_questions(quest_paper=all_questions)
    print(result)

    #update db 
    populate_q_db(result)

    output_path = 'generated_files/analysis.json'
    
    # api_key=os.environ["GROQ_API"]
    # assistant_analysis = Assistant(question_data=result,api_key=api_key,output_path=output_path)
    outfile = Assistant(result,model_name  = "gemini-2.0-flash-exp",output_path=output_path)

    logging.info(f"Analysis Generation completed successfully. Output saved at: {output_path}")
    
    # print(f"\nassistant_analysis:{assistant_analysis}\n")
    populate_analysis_db(output_path)
    results = calculate_score_and_generate_report(analysis_file = output_path, student_answers = student_answers)

    output_path = 'generated_files/eval_report.json'
    with open(output_path, 'w',encoding='utf-8') as f:
        json.dump(results, f, indent=4)

    populate_report_db(results)
    analysis_over=True
    logging.info(f"Evaluation for student:{student_answers['Student ID']} completed successfully. Output saved at: {output_path}")
    logging.info(f"Starting RAG on Evaluation Report for student:{student_answers['Student ID']}")

    # FLAG = True
    # while FLAG:
    #     question = input("ENTER THE QUERY")
    #     if question == "/bye":
    #         FLAG = False
    #         print(f"SESSION ENDED!!!")
    #     else:
    #         ans = start_RAG(output_path,question=question)
    #         print(f"The answer is:{ans}")
    return {}

@app.route('/rag', methods=['POST'])
def rag():
    output_path = 'generated_files/eval_report.json'
    data = request.json
    question = data.get('question')
    if question:
        answer = start_RAG(output_path,question)
        print("ANSWER:",answer)
        return jsonify({'answer': answer})
    else:
        return jsonify({'error': 'No question provided'}), 400

@app.route("/json_file",methods=["GET"])
def json_file():
    file_path = os.path.join('generated_files', 'analysis.json')
    print(analysis_over)
    if analysis_over:
        return jsonify({"message":"done"})
    if os.path.exists(file_path):
        with open(file_path, 'r',encoding='utf-8') as file:
            data = json.load(file)
            d={}
            for i in data.keys():
                if "error" in data[i].keys():
                    continue
                d[i]=data[i]
        return jsonify(d)
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000, use_reloader=False)
