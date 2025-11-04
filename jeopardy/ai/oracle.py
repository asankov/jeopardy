from openai.types.responses.response_output_message import ResponseOutputMessage
from pydantic import BaseModel
from openai import OpenAI
import json

class Response(BaseModel):
    is_correct: bool
    reason: str

class NotAbleToDetermineAnswer(Exception):
    pass

class Oracle:
    def __init__(self, api_key: str | None = None) -> None:
        self._client = OpenAI(api_key=api_key)

    def determine_correctness(self, question: str, correct_answer: str, given_answer: str) -> Response:
        completion = self._client.responses.create(
            model="gpt-5",
            input=[
                {
                    "role": "system",
                    "content": """
    You are an expert trivia answer checker.

    You will be given two parameters - a question, an answer to a question and the correct answer of that question.
    Your job is to determine whether the given answer is correct and to provide reasoning for why that is so.
    The wording of the answer might be different that the exact wording of the correct answer, but the answer might still be correct.

    ## Examples:
    ### Example One
    #### Input
    question: "30 steals for the Birmingham Barons; 2,306 steals for the Bulls"
    correct_answer: "Michael Jordan"
    given_answer: "Michael Jordan"

    #### Output
    {"is_correct": true, "reason": {Michael Jordan is the correct answer to this question."}

    ### Example Two
    #### Input
    question: "30 steals for the Birmingham Barons; 2,306 steals for the Bulls"
    correct_answer: "Michael Jordan"
    given_answer: "it's Michael Jordan"

    #### Output
    {"is_correct": true, "reason": {Michael Jordan is the correct answer to this question."}

    ### Example Three
    #### Input
    question: "30 steals for the Birmingham Barons; 2,306 steals for the Bulls"
    correct_answer: "Michael Jordan"
    given_answer: "Kobe Bryant"

    #### Output
    {"is_correct": false, "reason": "Kobe Bryant is the correct answer to this question."}
"""
                },
                {
                    "role": "user",
                    "content": f"""question: {question}
    correct_answer: {correct_answer}
    given_answer: {given_answer}"""
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "Response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "is_correct": {"type": "boolean"},
                            "reason": {"type": "string"}
                        },
                        "required": ["is_correct", "reason"],
                        "additionalProperties": False
                    },
                }
            }
        )

        for output in completion.output:
            if isinstance(output, ResponseOutputMessage):
                return Response(**json.loads(output.content[0].text))

        raise NotAbleToDetermineAnswer()
