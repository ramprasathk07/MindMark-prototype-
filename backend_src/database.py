#Quesation paper creation
import json
import sqlite3

from logger_config import logging


def populate_q_db(question:list,id:str,connection,cursor):
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {id}_QP (
    Qno INTEGER PRIMARY KEY,
    Question TEXT NOT NULL,
    op1 TEXT NOT NULL,
    op2 TEXT NOT NULL,
    op3 TEXT NOT NULL,
    op4 TEXT NOT NULL,
    correct_op TEXT NOT NULL
    );''')
    connection.commit()
    opts=question["options"]
    if opts=={}:
        opts={1:"NA",2:"NA",3:"NA",4:"NA"}
    data = (
        int(question["Question no"]),
        question["Question"],
        opts[1],           
        opts[2],      
        opts[3],    
        opts[4],
        question["Correct Answer"]
    )
    cursor.execute(f'''
    INSERT OR IGNORE INTO {id}_QP (Qno, Question, op1, op2, op3, op4, correct_op)
    VALUES (?, ?, ?, ?, ?, ?, ?)''', data)


# #LLM Output Database
def populate_analysis_db(connection,cursor, question,qno, id):
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {id}_LLM (
            Qno INTEGER PRIMARY KEY,
            diff TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            corr_expl TEXT NOT NULL,
            wrng_1 TEXT NOT NULL,
            wrng_2 TEXT NOT NULL,
            wrng_3 TEXT NOT NULL,
            Common_Student_Misconceptions TEXT DEFAULT "NA",
            Question_Type TEXT DEFAULT "NA",
            Taxonomy TEXT DEFAULT "NA",
            Positive_Feedback TEXT DEFAULT "NA",
            Negative_Feedback TEXT DEFAULT "NA",
            FOREIGN KEY (Qno) REFERENCES {id}_QP(Qno)
    );''') 
    connection.commit()
    if "error" in question.keys():
        return
    opts = question["Options"]
    if opts == {}:
        opts = {"1": "NA", "2": "NA", "3": "NA", "4": "NA"}
    print(question['Incorrect_Option_Analysis'].values())
    wrng_1 = (list(question['Incorrect_Option_Analysis'].values())[0]["Type_of_Error"] +
                " " + list(question['Incorrect_Option_Analysis'].values())[0]["Description"])
    wrng_2 = (list(question['Incorrect_Option_Analysis'].values())[1]["Type_of_Error"] +
                " " + list(question['Incorrect_Option_Analysis'].values())[1]["Description"])
    try:
        wrng_3 = (list(question['Incorrect_Option_Analysis'].values())[2]["Type_of_Error"] +
                " " + list(question['Incorrect_Option_Analysis'].values())[2]["Description"])
    except:
        wrng_3="NA"
    data = (
        qno,
        question["Difficulty"],
        question["Subject"],
        question["Topic"],
        wrng_1,
        wrng_2,
        wrng_3,
        question['Correct_Answer_Explanation'],
        question.get('Common_Student_Misconceptions', "NA"),
        question.get("Question_Type", "NA"),
        question.get("Taxonomy", "NA"),
        question.get("Positive_Feedback", "NA"),
        question.get("Negative_Feedback", "NA")
    )
    print(data)
    cursor.execute(f'''
    INSERT OR IGNORE INTO {id}_LLM (Qno, diff, subject, topic, wrng_1, wrng_2, wrng_3, corr_expl,
                            Common_Student_Misconceptions, Question_Type, Taxonomy,
                            Positive_Feedback, Negative_Feedback)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
    connection.commit()
    return {}

#evaluation report of students
def populate_report_db(connection,cursor,question: list,qp_id:str):
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {qp_id} (
            Qno INTEGER PRIMARY KEY,
            Question TEXT NOT NULL,
            Score INTEGER,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            diff INTEGER DEFAULT 0,
            Taxonomy TEXT DEFAULT "NA",
            stud_op TEXT DEFAULT "NA",
            Error_exp TEXT DEFAULT "NA",
            Common_Student_Misconceptions TEXT NOT NULL,
            Feedback TEXT DEFAULT "NA"
        )''')
    connection.commit()

    if "Total Score" in question.keys():
        return 
    expl = ""
    if isinstance(question.get("Explanation for the option chosen"), dict):
        expl = (
            list(question.get("Explanation for the option chosen").values())[0] + " " +
            list(question.get("Explanation for the option chosen").values())[1]
        )
    else:
        expl = question.get("Explanation for the option chosen", "NA")
    feedback = question.get("Positive Feedback", question.get("Negative Feedback", "NA"))
    data=(
        int(question["Question Number"]),
        question["Question"],
        question.get("Score", None),
        question["Subject"],
        question["Topic"],
        int(question["Difficulty"]),
        question.get("Taxonomy", "NA"),
        question.get("Student Option", "NA"),
        expl,
        question.get("Common Misconceptions", "NA"),
        feedback
    )
    cursor.execute(f'''
        INSERT OR IGNORE INTO {qp_id} (
            Qno, Question, Score, subject, topic, diff, Taxonomy, 
            stud_op, Error_exp, Common_Student_Misconceptions, Feedback
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    connection.commit()
    logging.info("Question Paper data updated in DB")
    return {}


