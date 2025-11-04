"""
Unit tests for Jeopardy API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from jeopardy.ai.oracle import NotAbleToDetermineAnswer


class TestGetRandomQuestion:
    """Tests for GET /question/ endpoint."""
    
    def test_get_random_question_success(self, client: TestClient, sample_questions):
        """Test successfully retrieving a random question."""
        response = client.get("/question/?round=Jeopardy!&value=$200")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["question_id"] == 1
        assert data["round"] == "Jeopardy!"
        assert data["category"] == "HISTORY"
        assert data["value"] == "$200"
        assert "Galileo" in data["question"]
    
    def test_get_random_question_different_round(self, client: TestClient, sample_questions):
        """Test retrieving a question from Double Jeopardy round."""
        response = client.get("/question/?round=Double Jeopardy!&value=$800")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["question_id"] == 3
        assert data["round"] == "Double Jeopardy!"
        assert data["value"] == "$800"
    
    def test_get_random_question_not_found(self, client: TestClient, sample_questions):
        """Test 404 when no question matches criteria."""
        response = client.get("/question/?round=Final Jeopardy!&value=$1000")
        
        assert response.status_code == 404
        assert "No question found" in response.json()["detail"]
    
    def test_get_random_question_invalid_value_format(self, client: TestClient, sample_questions):
        """Test 400 when value format is invalid."""
        response = client.get("/question/?round=Jeopardy!&value=invalid")
        
        assert response.status_code == 400
        assert "Invalid value format" in response.json()["detail"]
    
    def test_get_random_question_none_value(self, client: TestClient, test_db):
        """Test handling of None value (questions with no dollar value)."""
        from jeopardy.db.models import JeopardyQuestion
        from datetime import date
        
        # Add a question with None value
        question = JeopardyQuestion(
            id=99,
            show_number=1234,
            air_date=date(2020, 1, 1),
            round="Final Jeopardy!",
            category="TEST",
            value_in_dollars=None,
            question="Test question with no value",
            answer="Test answer"
        )
        test_db.add(question)
        test_db.commit()
        
        response = client.get("/question/?round=Final Jeopardy!&value=None")
        
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "None"


class TestVerifyAnswer:
    """Tests for POST /verify-answer/ endpoint."""
    
    def test_verify_answer_correct(self, client: TestClient, sample_questions, mock_oracle: Mock):
        """Test verifying a correct answer."""
        # Set up mock to return correct answer
        mock_response = Mock()
        mock_response.is_correct = True
        mock_response.reason = "Copernicus is the correct answer"
        mock_oracle.determine_correctness.return_value = mock_response
        
        response = client.post(
            "/verify-answer/",
            json={"question_id": 1, "user_answer": "Copernicus"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_correct"] is True
        assert "correct" in data["ai_response"].lower()
        
        # Verify the oracle was called correctly
        mock_oracle.determine_correctness.assert_called_once()
        call_args = mock_oracle.determine_correctness.call_args
        assert "Galileo" in call_args.kwargs["question"]
        assert call_args.kwargs["correct_answer"] == "Copernicus"
        assert call_args.kwargs["given_answer"] == "Copernicus"
    
    def test_verify_answer_incorrect(self, client: TestClient, sample_questions, mock_oracle: Mock):
        """Test verifying an incorrect answer."""
        # Set up mock to return incorrect answer
        mock_response = Mock()
        mock_response.is_correct = False
        mock_response.reason = "Newton is not the correct answer. The correct answer is Copernicus"
        mock_oracle.determine_correctness.return_value = mock_response
        
        response = client.post(
            "/verify-answer/",
            json={"question_id": 1, "user_answer": "Newton"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_correct"] is False
        assert "not" in data["ai_response"].lower() or "correct answer" in data["ai_response"].lower()
    
    def test_verify_answer_question_not_found(self, client: TestClient, sample_questions):
        """Test 404 when question doesn't exist."""
        response = client.post(
            "/verify-answer/",
            json={"question_id": 9999, "user_answer": "Test"}
        )
        
        assert response.status_code == 404
        assert "No question found" in response.json()["detail"]
    
    def test_verify_answer_oracle_error(self, client: TestClient, sample_questions, mock_oracle: Mock):
        """Test 500 when Oracle fails to determine correctness."""
        # Set up mock to raise exception
        mock_oracle.determine_correctness.side_effect = NotAbleToDetermineAnswer()
        
        response = client.post(
            "/verify-answer/",
            json={"question_id": 1, "user_answer": "Test"}
        )
        
        assert response.status_code == 500
        assert "Not able to determine" in response.json()["detail"]
    
    def test_verify_answer_missing_fields(self, client: TestClient, sample_questions):
        """Test 422 when required fields are missing."""
        response = client.post("/verify-answer/", json={"question_id": 1})
        
        assert response.status_code == 422  # Validation error


class TestAgentPlay:
    """Tests for POST /agent-play/ endpoint."""
    
    def test_agent_play_success(self, client: TestClient, sample_questions, mock_oracle: Mock):
        """Test successful agent play execution."""
        # Set up mocks
        mock_oracle.answer_question.return_value = "Copernicus"
        mock_response = Mock()
        mock_response.is_correct = True
        mock_response.reason = "Copernicus is correct"
        mock_oracle.determine_correctness.return_value = mock_response
        
        response = client.post("/agent-play/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["agent_name"] == "AI-Bot"
        assert "question_id" in data
        assert "round" in data
        assert "category" in data
        assert "value" in data
        assert "question" in data
        assert data["ai_answer"] == "Copernicus"
        assert data["is_correct"] is True
        assert data["verification_response"] == "Copernicus is correct"
        
        # Verify Oracle methods were called
        mock_oracle.answer_question.assert_called_once()
        mock_oracle.determine_correctness.assert_called_once()
    
    def test_agent_play_incorrect_answer(self, client: TestClient, sample_questions, mock_oracle: Mock):
        """Test agent play with incorrect answer."""
        # Set up mocks for incorrect answer
        mock_oracle.answer_question.return_value = "Wrong Answer"
        mock_response = Mock()
        mock_response.is_correct = False
        mock_response.reason = "Wrong Answer is incorrect"
        mock_oracle.determine_correctness.return_value = mock_response
        
        response = client.post("/agent-play/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ai_answer"] == "Wrong Answer"
        assert data["is_correct"] is False
    
    def test_agent_play_answer_generation_fails(self, client: TestClient, sample_questions, mock_oracle: Mock):
        """Test 500 when answer generation fails."""
        # Set up mock to raise exception
        mock_oracle.answer_question.side_effect = Exception("API Error")
        
        response = client.post("/agent-play/")
        
        assert response.status_code == 500
        assert "Failed to generate answer" in response.json()["detail"]
    
    def test_agent_play_no_questions_in_db(self, client: TestClient, mock_oracle: Mock):
        """Test 404 when no questions exist in database."""
        # Don't use sample_questions fixture, so DB is empty
        response = client.post("/agent-play/")
        
        assert response.status_code == 404
        assert "No question found" in response.json()["detail"]
    
    def test_agent_play_selects_random_question(self, client: TestClient, sample_questions, mock_oracle: Mock):
        """Test that agent_play selects from available questions."""
        # Set up mocks
        mock_oracle.answer_question.return_value = "Test Answer"
        mock_response = Mock()
        mock_response.is_correct = True
        mock_response.reason = "Correct"
        mock_oracle.determine_correctness.return_value = mock_response
        
        # Make multiple requests
        question_ids = set()
        for _ in range(5):
            response = client.post("/agent-play/")
            if response.status_code == 200:
                data = response.json()
                question_ids.add(data["question_id"])
        
        # At least one question should be selected
        assert len(question_ids) > 0
        # All selected questions should be from our sample
        assert all(qid in [1, 2, 3] for qid in question_ids)
