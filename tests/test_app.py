import os
import sys

# Ensure repository root is on Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app import app, gemini_generate, generate_interview_questions, evaluate_interview
from models import (
    init_db, get_db, create_user, get_user_by_email, get_user_by_id,
    verify_user_email, update_user_password, save_otp, verify_otp, delete_otp,
    create_interview, get_interview_by_id, save_qa, get_qa_by_interview,
    save_result, get_result_by_interview
)
from config import Config
from google.api_core import exceptions as google_exceptions

class TestInterviewCoach(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key-123'
        self.client = app.test_client()
        init_db()

        # Clean test records
        conn = get_db()
        conn.execute('DELETE FROM users WHERE email LIKE "unittest_%"')
        conn.execute('DELETE FROM otp_tokens WHERE email LIKE "unittest_%"')
        conn.commit()
        conn.close()

    def test_database_models_user_lifecycle(self):
        email = f'unittest_candidate_{datetime.now().timestamp()}@example.com'
        created = create_user('Test Candidate', email, 'hashed_test_password')
        self.assertTrue(created)

        user = get_user_by_email(email)
        self.assertIsNotNone(user)
        self.assertEqual(user['name'], 'Test Candidate')
        self.assertEqual(user['is_verified'], 0)

        verify_user_email(email)
        verified_user = get_user_by_email(email)
        self.assertEqual(verified_user['is_verified'], 1)

    def test_otp_token_lifecycle(self):
        email = f'unittest_otp_{datetime.now().timestamp()}@example.com'
        save_otp(email, '123456', 'verification')
        self.assertTrue(verify_otp(email, '123456', 'verification'))
        self.assertFalse(verify_otp(email, '654321', 'verification'))
        delete_otp(email, 'verification')
        self.assertFalse(verify_otp(email, '123456', 'verification'))

    def test_interview_creation_and_qa_storage(self):
        user_id = 999
        interview_id = create_interview(
            user_id, 'Test Company', 'Python Engineer',
            'Flask and cloud pipelines', 'Resume highlights'
        )
        self.assertIsNotNone(interview_id)

        interview = get_interview_by_id(interview_id)
        self.assertEqual(interview['company_name'], 'Test Company')
        self.assertEqual(interview['job_role'], 'Python Engineer')

        save_qa(interview_id, 1, 'Technical', 'What is WSGI?', 'Web Server Gateway Interface')
        qa_list = get_qa_by_interview(interview_id)
        self.assertEqual(len(qa_list), 1)
        self.assertEqual(qa_list[0]['answer'], 'Web Server Gateway Interface')

    @patch('app.gemini_model')
    @patch('app.GEMINI_AVAILABLE', True)
    def test_gemini_resource_exhausted_fallback(self, mock_model):
        # Simulate 429 ResourceExhausted rate limit error
        mock_model.generate_content.side_effect = google_exceptions.ResourceExhausted("429 Quota Exceeded")
        text, error_msg = gemini_generate("Test prompt")
        self.assertIsNone(text)
        self.assertIn("rate limit", error_msg.lower())

    @patch('app.gemini_model')
    @patch('app.GEMINI_AVAILABLE', True)
    def test_gemini_deadline_exceeded_fallback(self, mock_model):
        # Simulate timeout error
        mock_model.generate_content.side_effect = google_exceptions.DeadlineExceeded("504 Timeout")
        text, error_msg = gemini_generate("Test prompt")
        self.assertIsNone(text)
        self.assertIn("timed out", error_msg.lower())

    @patch('app.gemini_model')
    @patch('app.GEMINI_AVAILABLE', True)
    def test_gemini_google_api_error_fallback(self, mock_model):
        # Simulate general GoogleAPIError
        mock_model.generate_content.side_effect = google_exceptions.GoogleAPIError("API down")
        text, error_msg = gemini_generate("Test prompt")
        self.assertIsNone(text)
        self.assertIn("gemini api error", error_msg.lower())

    @patch('app.gemini_generate')
    def test_generate_interview_questions_fallback(self, mock_generate):
        mock_generate.return_value = (None, "Simulated rate limit error")
        questions, warning_msg = generate_interview_questions("Frontend Engineer", "", "")
        self.assertEqual(len(questions), 10)
        self.assertIsNotNone(warning_msg)
        self.assertEqual(questions[0]['type'], 'Technical')

    def test_interview_ui_shows_warning_banner(self):
        email = f'unittest_ui_{datetime.now().timestamp()}@example.com'
        create_user('UI User', email, 'hash')
        verify_user_email(email)

        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['interview_id'] = 1
            sess['questions'] = [{'type': 'Technical', 'question': 'Sample Question'}]
            sess['current_q'] = 0
            sess['answers'] = []
            sess['ai_warning'] = 'Gemini API rate limit or quota exceeded. Using verified offline interview questions.'

        res = self.client.get('/interview/session')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Gemini API rate limit or quota exceeded', res.data)
        self.assertIn(b'Notice:', res.data)

    def test_evaluation_fallback_scores(self):
        interview = {'job_role': 'DevOps Engineer', 'company_name': 'CloudCorp'}
        answers = [
            {'question_number': 1, 'type': 'Technical', 'question': 'Q1', 'answer': 'Detailed answer about Kubernetes deployment.' * 5},
            {'question_number': 2, 'type': 'Behavioral', 'question': 'Q2', 'answer': 'Detailed answer using STAR method.' * 5}
        ]
        result = evaluate_interview(interview, answers)
        self.assertIn('overall_score', result)
        self.assertIn('technical_score', result)
        self.assertIn('feedback', result)
        self.assertTrue(0 <= result['overall_score'] <= 100)

if __name__ == '__main__':
    unittest.main()
