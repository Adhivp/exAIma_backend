from fastapi import APIRouter, HTTPException, Depends, Security, status
from app.auth.dependencies import get_current_user
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