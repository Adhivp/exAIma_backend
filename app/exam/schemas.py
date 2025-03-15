from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class QuestionBase(BaseModel):
    question_text: str = Field(..., description="The text of the question")
    option_a: str = Field(..., description="Option A")
    option_b: str = Field(..., description="Option B")
    option_c: str = Field(..., description="Option C")
    option_d: str = Field(..., description="Option D")
    marks: int = Field(1, description="Marks assigned to this question")


class QuestionCreate(QuestionBase):
    correct_option: str = Field(..., pattern="^[A-D]$", description="The correct option (A, B, C, or D)")


class QuestionResponse(QuestionBase):
    id: str = Field(..., description="Unique question identifier")
    exam_id: str = Field(..., description="The exam this question belongs to")
    created_at: Optional[datetime] = Field(None, description="When the question was created")
    updated_at: Optional[datetime] = Field(None, description="When the question was last updated")


class QuestionForExam(BaseModel):
    id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., description="The text of the question")
    option_a: str = Field(..., description="Option A")
    option_b: str = Field(..., description="Option B")
    option_c: str = Field(..., description="Option C")
    option_d: str = Field(..., description="Option D")
    marks: int = Field(1, description="Marks assigned to this question")


class QuestionWithAnswer(QuestionForExam):
    correct_option: str = Field(..., description="The correct option (A, B, C, or D)")


class ExamBase(BaseModel):
    exam_name: str = Field(..., description="Name of the exam")
    description: str = Field(..., description="Description of the exam")
    duration_mins: int = Field(..., gt=0, description="Duration of the exam in minutes")
    is_mcq: bool = Field(True, description="Whether the exam consists of multiple choice questions")


class ExamCreate(ExamBase):
    pass


class ExamResponse(ExamBase):
    id: str = Field(..., description="Unique exam identifier")
    number_of_questions: int = Field(0, description="Number of questions in the exam")
    created_at: Optional[datetime] = Field(None, description="When the exam was created")
    updated_at: Optional[datetime] = Field(None, description="When the exam was last updated")


class ExamWithQuestions(ExamResponse):
    questions: List[QuestionForExam] = Field([], description="List of questions in the exam")


class UserAnswer(BaseModel):
    question_id: str = Field(..., description="The ID of the question")
    selected_option: str = Field(..., pattern="^[A-D]$", description="The option selected by the user (A, B, C, or D)")


class SubmitExamRequest(BaseModel):
    exam_id: str = Field(..., description="ID of the exam being submitted")
    answers: List[UserAnswer] = Field(..., description="List of answers provided by the user")


class QuestionResultResponse(BaseModel):
    question_id: str = Field(..., description="The ID of the question")
    question_text: str = Field(..., description="The text of the question")
    selected_option: str = Field(..., description="The option selected by the user")
    correct_option: str = Field(..., description="The correct option")
    is_correct: bool = Field(..., description="Whether the answer is correct")
    marks: int = Field(..., description="Marks assigned to this question")
    options: Dict[str, str] = Field(..., description="All options for this question")


class ExamResultResponse(BaseModel):
    id: str = Field(..., description="Unique result identifier")
    user_id: str = Field(..., description="ID of the user who took the exam")
    exam_id: str = Field(..., description="ID of the exam")
    exam_name: str = Field(..., description="Name of the exam")
    total_marks: int = Field(..., description="Total marks possible")
    obtained_marks: int = Field(..., description="Marks obtained by the user")
    correct_answers: int = Field(..., description="Number of correct answers")
    wrong_answers: int = Field(..., description="Number of wrong answers")
    percentage: float = Field(..., description="Percentage score")
    completed_at: datetime = Field(..., description="When the exam was completed")
    question_results: List[QuestionResultResponse] = Field(..., description="Detailed results for each question")