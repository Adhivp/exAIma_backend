from fastapi import HTTPException, status
from app.config import supabase
from app.exam.models import Exam, Question, ExamResult
from app.auth.models import User
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime


class ExamService:
    """
    Service for handling exam operations
    """
    
    @staticmethod
    async def get_all_exams() -> List[Exam]:
        """
        Get all available exams with their question count
        """
        try:
            # Get all exams
            exams_result = supabase.table("exams").select("*").execute()
            
            if not exams_result.data:
                return []
            
            exams = []
            for exam_data in exams_result.data:
                # Count questions for each exam
                questions_count = supabase.table("questions").select("id", count="exact").eq("exam_id", exam_data["id"]).execute()
                
                # Create exam object with question count
                exam = Exam.from_dict(exam_data)
                # Create empty questions list with the correct length
                exam.questions = [None] * questions_count.count
                exams.append(exam)
            
            return exams
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching exams: {str(e)}"
            )
    
    @staticmethod
    async def get_exam_with_questions(exam_id: str) -> Exam:
        """
        Get a specific exam with all its questions (excluding correct answers)
        """
        try:
            # Get exam details
            exam_result = supabase.table("exams").select("*").eq("id", exam_id).execute()
            
            if not exam_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam with ID {exam_id} not found"
                )
            
            # Get questions for this exam (excluding correct_option)
            questions_result = supabase.table("questions").select(
                "id", "exam_id", "question_text", "option_a", "option_b", "option_c", "option_d", "marks"
            ).eq("exam_id", exam_id).execute()
            
            # Create question objects
            questions = []
            for q_data in questions_result.data:
                # Add a placeholder for correct_option since we're not returning it
                q_data["correct_option"] = ""
                questions.append(Question.from_dict(q_data))
            
            # Create and return exam with questions
            return Exam.from_dict(exam_result.data[0], questions=questions)
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching exam: {str(e)}"
            )
    
    @staticmethod
    async def evaluate_exam(user: User, exam_id: str, user_answers: List[Dict[str, str]]) -> ExamResult:
        """
        Evaluate an exam based on user answers and store the results
        """
        try:
            # Get exam details
            exam_result = supabase.table("exams").select("*").eq("id", exam_id).execute()
            
            if not exam_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam with ID {exam_id} not found"
                )
            
            exam_data = exam_result.data[0]
            
            # Get all questions with correct answers
            questions_result = supabase.table("questions").select("*").eq("exam_id", exam_id).execute()
            
            if not questions_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No questions found for exam with ID {exam_id}"
                )
            
            # Create a dictionary of questions by ID for easy lookup
            questions_by_id = {q["id"]: q for q in questions_result.data}
            
            # Convert user_answers to a dictionary for easy lookup
            user_answers_dict = {a["question_id"]: a["selected_option"] for a in user_answers}
            
            # Initialize evaluation variables
            total_marks = 0
            obtained_marks = 0
            correct_answers = 0
            wrong_answers = 0
            question_responses = []
            
            # Evaluate each question
            for q_id, question in questions_by_id.items():
                total_marks += question["marks"]
                
                # Check if user answered this question
                if q_id in user_answers_dict:
                    user_option = user_answers_dict[q_id]
                    is_correct = user_option == question["correct_option"]
                    
                    if is_correct:
                        obtained_marks += question["marks"]
                        correct_answers += 1
                    else:
                        wrong_answers += 1
                else:
                    # User didn't answer this question
                    user_option = None
                    is_correct = False
                    wrong_answers += 1
                
                # Prepare question response data
                question_response = {
                    "question_id": q_id,
                    "question_text": question["question_text"],
                    "selected_option": user_option,
                    "correct_option": question["correct_option"],
                    "is_correct": is_correct,
                    "marks": question["marks"],
                    "options": {
                        "A": question["option_a"],
                        "B": question["option_b"],
                        "C": question["option_c"],
                        "D": question["option_d"]
                    }
                }
                
                question_responses.append(question_response)
            
            # Create a result ID
            result_id = str(uuid.uuid4())
            
            # Prepare result data for database
            result_data = {
                "id": result_id,
                "user_id": user.id,
                "exam_id": exam_id,
                "total_marks": total_marks,
                "obtained_marks": obtained_marks,
                "correct_answers": correct_answers,
                "wrong_answers": wrong_answers,
                "completed_at": datetime.now().isoformat()
            }
            
            # Store result in database
            supabase.table("user_exam_results").insert(result_data).execute()
            
            # Store question responses in database
            for response in question_responses:
                response_data = {
                    "id": str(uuid.uuid4()),
                    "result_id": result_id,
                    "question_id": response["question_id"],
                    "selected_option": response["selected_option"],
                    "is_correct": response["is_correct"],
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("user_question_responses").insert(response_data).execute()
            
            # Create and return exam result with responses
            result = ExamResult.from_dict(result_data, question_responses=question_responses)
            result.exam_name = exam_data["exam_name"]  # Add exam name to the result
            
            return result
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error evaluating exam: {str(e)}"
            )
    
    @staticmethod
    async def get_user_exam_history(user_id: str) -> List[Dict[str, Any]]:
        """
        Get history of exams taken by a user
        """
        try:
            # Join user_exam_results with exams to get exam names
            results_query = """
                SELECT uer.*, e.exam_name
                FROM user_exam_results uer
                JOIN exams e ON uer.exam_id = e.id
                WHERE uer.user_id = ?
                ORDER BY uer.completed_at DESC
            """
            
            results = supabase.table("user_exam_results").select("*").eq("user_id", user_id).execute()
            
            if not results.data:
                return []
            
            exam_history = []
            for result_data in results.data:
                # Get exam name
                exam_result = supabase.table("exams").select("exam_name").eq("id", result_data["exam_id"]).execute()
                if exam_result.data:
                    result_data["exam_name"] = exam_result.data[0]["exam_name"]
                
                # Create result object without question responses
                result = ExamResult.from_dict(result_data)
                exam_history.append(result.to_dict())
            
            return exam_history
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching exam history: {str(e)}"
            )