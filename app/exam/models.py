from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class Question:
    """
    Question model that maps to the questions table in Supabase
    """
    def __init__(
        self,
        id: Union[str, int],
        exam_id: Union[str, int],
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_option: str,
        marks: int = 1,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.id = str(id) if id is not None else None
        self.exam_id = str(exam_id) if exam_id is not None else None
        self.question_text = question_text
        self.option_a = option_a
        self.option_b = option_b
        self.option_c = option_c
        self.option_d = option_d
        self.correct_option = correct_option
        self.marks = marks
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        """
        Create a Question instance from a dictionary
        """
        return cls(
            id=data.get("id"),
            exam_id=data.get("exam_id"),
            question_text=data.get("question_text"),
            option_a=data.get("option_a"),
            option_b=data.get("option_b"),
            option_c=data.get("option_c"),
            option_d=data.get("option_d"),
            correct_option=data.get("correct_option"),
            marks=data.get("marks", 1),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Question instance to dictionary
        """
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "question_text": self.question_text,
            "option_a": self.option_a,
            "option_b": self.option_b,
            "option_c": self.option_c,
            "option_d": self.option_d,
            "correct_option": self.correct_option,
            "marks": self.marks,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Exam:
    """
    Exam model that maps to the exams table in Supabase
    """
    def __init__(
        self,
        id: Union[str, int],
        exam_name: str,
        description: str,
        duration_mins: int,
        is_mcq: bool = True,
        questions: List[Question] = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.id = str(id) if id is not None else None
        self.exam_name = exam_name
        self.description = description
        self.duration_mins = duration_mins
        self.is_mcq = is_mcq
        self.questions = questions or []
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], questions: List[Question] = None) -> "Exam":
        """
        Create an Exam instance from a dictionary
        """
        return cls(
            id=data.get("id"),
            exam_name=data.get("exam_name"),
            description=data.get("description"),
            duration_mins=data.get("duration_mins"),
            is_mcq=data.get("is_mcq", True),
            questions=questions,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def to_dict(self, include_questions: bool = False) -> Dict[str, Any]:
        """
        Convert Exam instance to dictionary
        """
        result = {
            "id": self.id,
            "exam_name": self.exam_name,
            "description": self.description,
            "duration_mins": self.duration_mins,
            "is_mcq": self.is_mcq,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "number_of_questions": len(self.questions) if self.questions else 0
        }
        
        if include_questions and self.questions:
            result["questions"] = [q.to_dict() for q in self.questions]
            
        return result


class ExamResult:
    """
    Exam Result model that maps to the user_exam_results table in Supabase
    """
    def __init__(
        self,
        id: Union[str, int],
        user_id: Union[str, int],
        exam_id: Union[str, int],
        total_marks: int,
        obtained_marks: int,
        correct_answers: int,
        wrong_answers: int,
        question_responses: List[Dict[str, Any]] = None,
        completed_at: datetime = None
    ):
        self.id = str(id) if id is not None else None
        self.user_id = str(user_id) if user_id is not None else None
        self.exam_id = str(exam_id) if exam_id is not None else None
        self.total_marks = total_marks
        self.obtained_marks = obtained_marks
        self.correct_answers = correct_answers
        self.wrong_answers = wrong_answers
        self.question_responses = question_responses or []
        self.completed_at = completed_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], question_responses: List[Dict[str, Any]] = None) -> "ExamResult":
        """
        Create an ExamResult instance from a dictionary
        """
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            exam_id=data.get("exam_id"),
            total_marks=data.get("total_marks"),
            obtained_marks=data.get("obtained_marks"),
            correct_answers=data.get("correct_answers"),
            wrong_answers=data.get("wrong_answers"),
            question_responses=question_responses,
            completed_at=data.get("completed_at")
        )
    
    def to_dict(self, include_responses: bool = False) -> Dict[str, Any]:
        """
        Convert ExamResult instance to dictionary
        """
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "exam_id": self.exam_id,
            "total_marks": self.total_marks,
            "obtained_marks": self.obtained_marks,
            "correct_answers": self.correct_answers,
            "wrong_answers": self.wrong_answers,
            "percentage": round((self.obtained_marks / self.total_marks) * 100, 2) if self.total_marks > 0 else 0,
            "completed_at": self.completed_at
        }
        
        if include_responses and self.question_responses:
            result["question_responses"] = self.question_responses
            
        return result