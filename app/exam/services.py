from fastapi import HTTPException, status
from app.config import supabase
from app.exam.models import Exam, Question, ExamResult
from app.auth.models import User
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from google import genai
import os
from typing import Dict, Any, List, Optional
import json
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

def load_env_files():
    # Try app directory first
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        return
        
    # Try project root next
    root_env_file = Path(__file__).parent.parent / ".env"
    if root_env_file.exists():
        load_dotenv(root_env_file)
        return

# Load environment variables at import time
load_env_files()

class StrengthLevel(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    POOR = "Poor"

class TopicAnalysis(BaseModel):
    topic: str
    strength: StrengthLevel
    correct_questions: int
    total_questions: int
    percentage: float
    improvement_tips: List[str]

class ScoreSummary(BaseModel):
    total_marks: int
    obtained_marks: int
    percentage: float
    correct_answers: int
    wrong_answers: int
    grade: Optional[str] = None

class StudyPlanItem(BaseModel):
    topic: str
    priority: str
    activities: List[str]
    resources: Optional[List[str]] = None
    duration: Optional[str] = None

class ExamAnalysisReport(BaseModel):
    overall_performance: str
    score_summary: ScoreSummary
    topic_analysis: List[TopicAnalysis]
    general_improvement_tips: List[str]
    study_plan: List[StudyPlanItem]
    time_management_tips: List[str]
    exam_strategy_tips: List[str]


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

    @staticmethod
    async def generate_exam_analysis(result_id: str) -> Dict[str, Any]:
        """
        Generate a detailed analysis report for a specific exam result using Gemini API
        
        Args:
            result_id: ID of the exam result to analyze
            
        Returns:
            Dictionary containing the structured analysis report
        """
        try:
            # Initialize Gemini client with API key from settings
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Gemini API key not configured"
                )
            
            genai_client = genai.Client(api_key=api_key)
            
            # Get the exam result details from database
            result_data = supabase.table("user_exam_results").select("*").eq("id", result_id).execute()
            
            if not result_data.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam result with ID {result_id} not found"
                )
            
            result = result_data.data[0]
            
            # Get the exam details
            exam_id = result["exam_id"]
            exam_data = supabase.table("exams").select("*").eq("id", exam_id).execute()
            
            if not exam_data.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam with ID {exam_id} not found"
                )
            
            exam = exam_data.data[0]
            
            # Get all questions for this exam
            questions_data = supabase.table("questions").select("*").eq("exam_id", exam_id).execute()
            
            if not questions_data.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No questions found for exam with ID {exam_id}"
                )
            
            questions = questions_data.data
            
            # Get user's answers for this exam
            user_answers_data = supabase.table("user_question_responses").select("*").eq("result_id", result_id).execute()
            
            if not user_answers_data.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No responses found for result with ID {result_id}"
                )
            
            user_answers = {str(ans["question_id"]): ans for ans in user_answers_data.data}
            
            # Format questions with user answers for analysis
            question_data_for_analysis = []
            for q in questions:
                question_id = str(q["id"])
                user_answer = user_answers.get(question_id, {})
                
                question_info = {
                    "question_id": question_id,
                    "question_text": q.get("question_text", ""),
                    "options": {
                        "A": q.get("option_a", ""),
                        "B": q.get("option_b", ""),
                        "C": q.get("option_c", ""),
                        "D": q.get("option_d", "")
                    },
                    "correct_option": q.get("correct_option", ""),
                    "selected_option": user_answer.get("selected_option", None),
                    "is_correct": user_answer.get("is_correct", False),
                    "marks": q.get("marks", 1),
                    "topic": q.get("topic", "General") or "General"  # Use "General" if topic is None or empty
                }
                question_data_for_analysis.append(question_info)
            
            # Prepare data for Gemini API
            analysis_context = {
                "exam_name": exam.get("exam_name", ""),
                "exam_description": exam.get("description", ""),
                "total_marks": result.get("total_marks", 0),
                "obtained_marks": result.get("obtained_marks", 0),
                "correct_answers": result.get("correct_answers", 0),
                "wrong_answers": result.get("wrong_answers", 0),
                "percentage": round((result.get("obtained_marks", 0) / result.get("total_marks", 1)) * 100, 2),
                "questions": question_data_for_analysis
            }
            
            # Create prompt for Gemini
            prompt = f"""
            As an intelligent exam analysis system, analyze the following exam result and provide detailed feedback:
            
            {json.dumps(analysis_context, indent=2)}
            
            Based on this data, generate a comprehensive analysis including:
            1. Overall performance assessment (a paragraph summarizing performance)
            2. Score summary (including total marks, obtained marks, percentage, correct answers, wrong answers, and a letter grade)
            3. Topic-wise analysis showing strengths and weaknesses (include topic name, strength level, correct vs total questions, percentage, and specific improvement tips)
            4. General improvement tips (list of tips applicable to all topics)
            5. A recommended study plan (with topic, priority level, recommended activities, resources, and suggested duration)
            6. Time management tips (specific to this type of exam)
            7. Exam strategy recommendations (techniques to improve performance)
            
            Structure your response according to the specified schema.
            """
            
            # Call Gemini API with improved schema definition
            response = genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': {
                        "type": "object",
                        "properties": {
                            "overall_performance": {"type": "string"},
                            "score_summary": {
                                "type": "object",
                                "properties": {
                                    "total_marks": {"type": "integer"},
                                    "obtained_marks": {"type": "integer"},
                                    "percentage": {"type": "number"},
                                    "correct_answers": {"type": "integer"},
                                    "wrong_answers": {"type": "integer"},
                                    "grade": {"type": "string"}
                                },
                                "required": ["total_marks", "obtained_marks", "percentage", "correct_answers", "wrong_answers"]
                            },
                            "topic_analysis": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {"type": "string"},
                                        "strength": {"type": "string", "enum": ["Excellent", "Good", "Average", "Needs Improvement", "Poor"]},
                                        "correct_questions": {"type": "integer"},
                                        "total_questions": {"type": "integer"},
                                        "percentage": {"type": "number"},
                                        "improvement_tips": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "required": ["topic", "strength", "correct_questions", "total_questions", "percentage", "improvement_tips"]
                                }
                            },
                            "general_improvement_tips": {"type": "array", "items": {"type": "string"}},
                            "study_plan": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {"type": "string"},
                                        "priority": {"type": "string"},
                                        "activities": {"type": "array", "items": {"type": "string"}},
                                        "resources": {"type": "array", "items": {"type": "string"}},
                                        "duration": {"type": "string"}
                                    },
                                    "required": ["topic", "priority", "activities"]
                                }
                            },
                            "time_management_tips": {"type": "array", "items": {"type": "string"}},
                            "exam_strategy_tips": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["overall_performance", "score_summary", "topic_analysis", "general_improvement_tips", "study_plan", "time_management_tips", "exam_strategy_tips"]
                    }
                }
            )
            
            # Parse and return the structured response
            if not response or not response.text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate analysis from Gemini API"
                )
            
            # Try to parse the response as JSON
            try:
                analysis_report = json.loads(response.text)
                return analysis_report
            except json.JSONDecodeError:
                # If parsing fails, return the raw text
                return {
                    "error": "Failed to parse structured response",
                    "raw_response": response.text
                }
                
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating exam analysis: {str(e)}"
            )