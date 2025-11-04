from pydantic import BaseModel

class GetRandomQuestionResponse(BaseModel):
    question_id: int
    round: str
    category: str
    value: str
    question: str

class VerifyAnswerRequest(BaseModel):
    question_id: int
    user_answer: str

class VerifyAnswerResponse(BaseModel):
    is_correct: bool
    ai_response: str

class AgentPlayResponse(BaseModel):
    agent_name: str
    question: str
    ai_answer: str
    is_correct: bool
