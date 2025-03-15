from fastapi import APIRouter, HTTPException, Depends, Security, status
from app.auth.dependencies import get_current_user, verify_exam_access
from app.auth.models import User
from app.exam.services import ExamService
from app.exam.schemas import (
    ExamResponse, 
    ExamWithQuestions, 
    SubmitExamRequest, 
    ExamResultResponse,
    QuestionResultResponse
)
from typing import List, Dict, Any

router = APIRouter(prefix="/exams", tags=["Exams"])

@router.get("/", response_model=List[ExamResponse])
async def get_all_exams(current_user: User = Security(get_current_user)):
    """
    Get all available exams with their basic information
    """
    exams = await ExamService.get_all_exams()
    return [exam.to_dict() for exam in exams]

@router.get("/{exam_id}", response_model=ExamWithQuestions)
async def get_exam_with_questions(
    exam_id: str,
    current_user: User = Security(get_current_user)
):
    """
    Get a specific exam with all its questions (for taking the exam)
    """
    exam = await ExamService.get_exam_with_questions(exam_id)
    return exam.to_dict(include_questions=True)

@router.post("/submit", response_model=ExamResultResponse)
async def submit_exam(
    request: SubmitExamRequest,
    current_user: User = Security(get_current_user)
):
    """
    Submit an exam for evaluation and get results
    """
    result = await ExamService.evaluate_exam(
        user=current_user,
        exam_id=request.exam_id,
        user_answers=[answer.dict() for answer in request.answers]
    )
    
    # Format the response according to the schema
    response = {
        "id": result.id,
        "user_id": result.user_id,
        "exam_id": result.exam_id,
        "exam_name": result.exam_name,
        "total_marks": result.total_marks,
        "obtained_marks": result.obtained_marks,
        "correct_answers": result.correct_answers,
        "wrong_answers": result.wrong_answers,
        "percentage": round((result.obtained_marks / result.total_marks) * 100, 2) if result.total_marks > 0 else 0,
        "completed_at": result.completed_at,
        "question_results": []
    }
    
    # Add question results
    for q_response in result.question_responses:
        question_result = {
            "question_id": q_response["question_id"],
            "question_text": q_response["question_text"],
            "selected_option": q_response["selected_option"] or "",
            "correct_option": q_response["correct_option"],
            "is_correct": q_response["is_correct"],
            "marks": q_response["marks"],
            "options": q_response["options"]
        }
        response["question_results"].append(question_result)
    
    return response

@router.get("/history/me", response_model=List[Dict[str, Any]])
async def get_my_exam_history(current_user: User = Security(get_current_user)):
    """
    Get the exam history for the current user
    """
    return await ExamService.get_user_exam_history(current_user.id)

@router.get("/history/{exam_id}", response_model=Dict[str, Any])
async def get_exam_history(
    exam_id: str,
    current_user: User = Security(get_current_user)
):
    """
    Get detailed history of a specific exam attempt including:
    - All questions
    - User's answers
    - Correct answers
    - Score breakdown
    - Time taken
    
    Args:
        exam_id: ID of the exam to retrieve history for
        
    Returns:
        Dictionary containing complete exam history details
    """
    try:
        # Ensure exam_id is a string
        exam_id = str(exam_id)
        
        # Get exam details from user_exam_results table
        try:
            # Check if user_exam_results table exists and contains records for this user and exam
            exam_result = supabase.table("user_exam_results").select("*").eq("exam_id", exam_id).eq("user_id", current_user.id).execute()
            
            if not exam_result.data:
                return {
                    "status": "not_found",
                    "message": "You haven't taken this exam yet",
                    "exam_id": exam_id
                }
                
            exam_data = exam_result.data[0]
            
            # Get the exam information
            exam_info = supabase.table("exams").select("*").eq("id", exam_id).execute()
            
            if not exam_info.data:
                return {
                    "status": "error",
                    "message": "Exam not found",
                    "exam_id": exam_id
                }
                
            exam_title = exam_info.data[0].get("exam_name", "Unknown Exam")
            
            # Get all questions for this exam
            questions_result = supabase.table("questions").select("*").eq("exam_id", exam_id).execute()
            
            # Get user's answers for this exam - ensure result_id is string
            result_id = str(exam_data["id"])
            user_answers_result = supabase.table("user_question_responses").select("*").eq("result_id", result_id).execute()
            
            # Process the results to create a comprehensive history
            questions = questions_result.data if questions_result.data else []
            user_answers = {}
            
            if user_answers_result.data:
                # Convert all question_ids to strings to ensure matching
                user_answers = {str(ans["question_id"]): ans for ans in user_answers_result.data}
            
            # Format questions with user answers and correctness
            formatted_questions = []
            for q in questions:
                question_id = str(q["id"])
                user_answer = user_answers.get(question_id, {})
                
                formatted_questions.append({
                    "question_id": question_id,
                    "question_text": q.get("question_text", ""),
                    "options": {
                        "A": q.get("option_a", ""),
                        "B": q.get("option_b", ""),
                        "C": q.get("option_c", ""),
                        "D": q.get("option_d", "")
                    },
                    "correct_answer": q.get("correct_option", ""),
                    "user_answer": user_answer.get("selected_option", None),
                    "is_correct": user_answer.get("is_correct", False),
                    "explanation": q.get("explanation", "")
                })
            
            # Compile final response with default values to prevent errors
            total_marks = exam_data.get("total_marks", 0) or 0  # Handle None values
            obtained_marks = exam_data.get("obtained_marks", 0) or 0
            
            # Calculate percentage safely
            percentage = 0
            if total_marks > 0:
                percentage = round((obtained_marks / total_marks) * 100, 2)
            
            return {
                "status": "success",
                "exam_id": exam_id,
                "title": exam_title,
                "date_taken": exam_data.get("completed_at", ""),
                "score": obtained_marks,
                "total_marks": total_marks,
                "total_questions": len(questions),
                "correct_answers": exam_data.get("correct_answers", 0) or 0,
                "wrong_answers": exam_data.get("wrong_answers", 0) or 0,
                "percentage": percentage,
                "questions": formatted_questions
            }
            
        except Exception as e:
            # Handle specific known errors
            if hasattr(e, 'code') and e.code == '42P01':  # PostgreSQL code for relation not found
                return {
                    "status": "not_available",
                    "message": "Exam history feature is not available yet",
                    "exam_id": exam_id
                }
            # Check for other relation does not exist error formats
            elif isinstance(e, str) and "relation" in str(e) and "does not exist" in str(e):
                return {
                    "status": "not_available",
                    "message": "Exam history feature is not available yet",
                    "exam_id": exam_id
                }
            # For postgREST API errors
            elif hasattr(e, 'message') and "relation" in str(e.message) and "does not exist" in str(e.message):
                return {
                    "status": "not_available",
                    "message": "Exam history feature is not available yet",
                    "exam_id": exam_id
                }
            raise e
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        # Return a more informative error response
        return {
            "status": "error",
            "message": f"Error retrieving exam history: {str(e)}",
            "exam_id": exam_id
        }