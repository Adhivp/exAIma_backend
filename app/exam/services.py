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
    async def evaluate_exam(user: User, exam_id: str, user_answers: List[Dict[str, Any]]) -> ExamResult:
        """
        Evaluate an exam based on user answers and store the results
        """
        try:
            # Convert exam_id to integer for database query
            exam_id_int = int(exam_id)
            
            # Get exam details
            exam_result = supabase.table("exams").select("*").eq("id", exam_id_int).execute()
            
            if not exam_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam with ID {exam_id} not found"
                )
            
            exam_data = exam_result.data[0]
            
            # Get all questions with correct answers
            questions_result = supabase.table("questions").select("*").eq("exam_id", exam_id_int).execute()
            
            if not questions_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No questions found for exam with ID {exam_id}"
                )
            
            # Create a dictionary of questions by ID for easy lookup
            # Use integer IDs as keys
            questions_by_id = {q["id"]: q for q in questions_result.data}
            
            # Convert user_answers question_ids to integers for lookup
            user_answers_dict = {}
            for answer in user_answers:
                try:
                    # Convert question_id to integer
                    question_id_int = int(answer.get("question_id"))
                    user_answers_dict[question_id_int] = answer.get("selected_option")
                except ValueError:
                    # Skip invalid question IDs
                    continue
            
            # Initialize evaluation variables
            total_marks = 0
            obtained_marks = 0
            correct_answers = 0
            wrong_answers = 0
            question_responses = []
            
            # Evaluate each question
            for q_id, question in questions_by_id.items():
                marks = question.get("marks", 1) or 1
                total_marks += marks
                
                # Check if user answered this question
                if q_id in user_answers_dict:
                    user_option = user_answers_dict[q_id]
                    is_correct = user_option == question["correct_option"]
                    
                    if is_correct:
                        obtained_marks += marks
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
                    "question_id": q_id,  # Keep as integer for database
                    "question_text": question["question_text"],
                    "selected_option": user_option,
                    "correct_option": question["correct_option"],
                    "is_correct": is_correct,
                    "marks": marks,
                    "options": {
                        "A": question["option_a"],
                        "B": question["option_b"],
                        "C": question["option_c"],
                        "D": question["option_d"]
                    }
                }
                
                question_responses.append(question_response)
            
            # Insert result with auto-incrementing ID
            # Note: Let the database assign the ID automatically for integer columns
            result_data = {
                # Omit the 'id' field to let the database assign it automatically
                "user_id": user.id,  # This is a UUID, matches the user_id column type
                "exam_id": exam_id_int,  # Integer for the exam_id column
                "total_marks": total_marks,
                "obtained_marks": obtained_marks,
                "correct_answers": correct_answers,
                "wrong_answers": wrong_answers,
                "completed_at": datetime.now().isoformat()
            }
            
            # Store result in database and get the generated ID
            result_insert = supabase.table("user_exam_results").insert(result_data).execute()
            
            # Get the auto-generated result ID
            if not result_insert.data or len(result_insert.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to insert exam result"
                )
            
            result_id = result_insert.data[0]["id"]  # Get the auto-generated integer ID
            
            # Store question responses in database
            for response in question_responses:
                response_data = {
                    # Omit the 'id' field to let the database assign it automatically
                    "result_id": result_id,  # Integer ID from the result
                    "question_id": response["question_id"],  # Integer question ID
                    "selected_option": response["selected_option"],
                    "is_correct": response["is_correct"],
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("user_question_responses").insert(response_data).execute()
            
            # Add the ID to the result data after insertion
            result_data["id"] = result_id
            
            # Create and return exam result with responses
            result = ExamResult.from_dict(result_data, question_responses=question_responses)
            result.exam_name = exam_data.get("exam_name", "Unknown Exam")
            
            return result
            
        except ValueError as ve:
            # Handle conversion errors (e.g., non-integer IDs)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ID format. IDs must be integers: {str(ve)}"
            )
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