import json
import sqlite3

from database import populate_report_db

def load_json(file_path):
    """Loads JSON data from a file."""
    with open(file_path, 'r',encoding='utf-8') as f:
        return json.load(f)

# def calculate_score_and_generate_report(analysis_file, student_answers):
#     """Calculates the score and generates a report for students."""

#     explanation_data = load_json(analysis_file)
#     results = []
#     total_score = 0

#     # print(f"\nstudent_answers:{student_answers}\n")
#     print(f"\explanation_data:{explanation_data}\n")

#     for student_data in student_answers['answers']:
#         question_no = int(student_data.get("Question no",-1))  # Extract question number
#         student_option = f"Option{student_data['option']}" if student_data["option"] != "Unattempted" else "Unattempted"
#         explanation = explanation_data.get(question_no, {})
        
#         # Extract necessary details
#         question_text = explanation.get("Question", "No question available.")
#         subject = explanation.get("Subject", "Unknown")
#         topic = explanation.get("Topic", "Unknown")
#         difficulty = explanation.get("Difficulty", 2.5)
#         taxonomy = explanation.get("Taxonomy", "Unknown")
#         correct_option = 'Option'+str(explanation.get("correct_option", "Unattempted"))  # Assume Option3 is correct; adjust as needed

#         # Check if the student's choice is correct
#         if student_option != "Unattempted":
#             is_correct = student_option == correct_option
#             score = 4 if is_correct else -1
#         else:
#             is_correct = False
#             score = 0

#         total_score += score

#         # Generate explanation based on correctness
#         if is_correct:            
#             explanation_text = explanation.get("Correct_Answer_Explanation", "No explanation available.")
#             positive_highlights = explanation.get("Positive_Feedback", "No highlights available.")
#             Positive_Feedback =f"Great job! {positive_highlights} Keep up the good work!"

#             # Append results for correct answer
#             results.append({
#                 "Question Number": question_no,
#                 "Question": question_text,
#                 "Score": score,
#                 "Subject": subject,
#                 "Topic": topic,
#                 "Difficulty": difficulty,
#                 "Taxonomy": taxonomy,
#                 "Correct Option": correct_option,
#                 "Student Option": student_option,
#                 "Explanation for correct option": explanation_text,
#                 "Positive_Feedback": Positive_Feedback
#             })
#         else:
#             explanation_text = explanation.get("Incorrect_Option_Analysis", {}).get(
#                 student_option[-1] if student_option != "Unattempted" else "Unattempted",
#                 "No explanation available.")
            
#             misconceptions = explanation.get("Common_Student_Misconceptions", "No misconceptions available.")
#             Negative_Feedback = explanation.get("Negative_Feedback", "No misconceptions available.")
#             # Append results for incorrect answer

#             Negative_Feedback = f"Consider revisiting the key concepts related to this question. Your selected answer suggests a potential misunderstanding. {Negative_Feedback}"

#             results.append({
#                 "Question Number": question_no,
#                 "Question": question_text,
#                 "Score": score,
#                 "Subject": subject,
#                 "Topic": topic,
#                 "Difficulty": difficulty,
#                 "Taxonomy": taxonomy,
#                 "Correct Option": correct_option,
#                 "Student Option": student_option,
#                 "Explanation for the option choosed": explanation_text,
#                 "Common Misconceptions": misconceptions,
#                 "Negative_Feedback": Negative_Feedback,
#             })

#     # Append total score
#     results.append({"Total Score": total_score})

#     return results

def calculate_score_and_generate_report(qid,sid, student_answers):
    """Calculates the score and generates a report for students."""

    read_connection = sqlite3.connect(f"Database/Questions.db")
    read_connection.row_factory = sqlite3.Row 
    cursor = read_connection.cursor()
    write_conn=sqlite3.connect(f"Database/{sid}.db")
    write_cursor=write_conn.cursor()
    results = []
    total_score = 0
    query_LLM = f"SELECT * FROM {qid}_LLM WHERE Qno = ?"
    query_QP=f"SELECT * FROM {qid}_QP WHERE Qno = ?"
    # Iterate through student answers
    data={}
    for student_data in student_answers['answers']:
        question_no = int(student_data.get("Question no", -1))  # Extract question number
        student_option = f"Option{student_data['option']}" if student_data["option"] != "Unattempted" else "Unattempted"
        
        # Retrieve explanation data for the current question
        cursor.execute(query_LLM, (question_no,))
        exp = cursor.fetchone()
        if exp==None:
            continue
        explanation=dict(exp)
        cursor.execute(query_QP, (question_no,))
        exp = cursor.fetchone()
        explanation.update(dict(exp))
        print(explanation)

        # Extract necessary details
        question_text = explanation.get("Question", "No question available.")
        subject = explanation.get("subject", "Unknown")
        topic = explanation.get("topic", "Unknown")
        difficulty = explanation.get("Difficulty", 2.5)
        taxonomy = explanation.get("Taxonomy", "Unknown")
        correct_option = f"Option{explanation.get('correct_option', 'Unattempted')}"

        # Check if the student's choice is correct
        if student_option != "Unattempted":
            is_correct = student_option == correct_option
            score = 4 if is_correct else -1
        else:
            is_correct = False
            score = 0

        total_score += score

        # Generate explanation based on correctness
        if is_correct:            
            explanation_text = explanation.get("corr_expl", "No explanation available.")
            positive_highlights = explanation.get("Positive_Feedback", "No highlights available.")
            positive_feedback = f"Great job! {positive_highlights} Keep up the good work!"

            # Append results for correct answer
            data={
                "Question Number": question_no,
                "Question": question_text,
                "Score": score,
                "Subject": subject,
                "Topic": topic,
                "Difficulty": difficulty,
                "Taxonomy": taxonomy,
                "Correct Option": correct_option,
                "Student Option": student_option,
                "Explanation for correct option": explanation_text,
                "Positive Feedback": positive_feedback
            }
        else:
            explanation_text = explanation.get("Incorrect_Option_Analysis", {}).get(
                student_option[-1] if student_option != "Unattempted" else "Unattempted",
                "No explanation available.")
            
            misconceptions = explanation.get("Common_Student_Misconceptions", "No misconceptions available.")
            negative_feedback = explanation.get("Negative_Feedback", "No feedback available.")
            
            negative_feedback = f"Consider revisiting the key concepts related to this question. Your selected answer suggests a potential misunderstanding. {negative_feedback}"

            # Append results for incorrect answer
            data={
                "Question Number": question_no,
                "Question": question_text,
                "Score": score,
                "Subject": subject,
                "Topic": topic,
                "Difficulty": difficulty,
                "Taxonomy": taxonomy,
                "Correct Option": correct_option,
                "Student Option": student_option,
                "Explanation for the option chosen": explanation_text,
                "Common Misconceptions": misconceptions,
                "Negative Feedback": negative_feedback,
            }
        
        populate_report_db(write_conn,write_cursor,data,qid)
        write_conn.commit()
        results.append(data)

    # Append total score
    results.append({"Total Score": total_score})
    write_conn.commit()
    write_conn.close()
    read_connection.close()
    return results

def save_json(data, output_file):
    """Saves JSON data to a file."""
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

def main(explanation_file, student_answers_file, output_file):
    # Load data
    explanation_data = load_json(explanation_file)
    student_answers = load_json(student_answers_file)

    # Process data
    results = calculate_score_and_generate_report(explanation_data, student_answers)

    # Save results
    save_json(results, output_file)

    print(f"Insights and scores saved to {output_file}")

# Example usage
if __name__ == "__main__":
    explanation_file = f"generated_files/analysis.json"  # Path to the explanation file
    student_answers_file = f"generated_files\si_1/repsonse_sheet_qp_1.json"  # Path to the student answers file
    output_file = "results_.json"  # Output file path

    main(explanation_file, student_answers_file, output_file)
