import os
import sys
import unittest
from datetime import datetime

# Ensure repository root is on Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, evaluate_interview, generate_interview_questions  # noqa: E402
from models import (  # noqa: E402
    create_interview,
    create_user,
    delete_otp,
    delete_user,
    get_db,
    get_interview_by_id,
    get_interviews_by_user,
    get_qa_by_interview,
    get_result_by_interview,
    get_user_by_email,
    init_db,
    save_otp,
    save_qa,
    save_result,
    update_interview_status,
    update_user_password,
    verify_otp,
    verify_user_email,
)


class TestAIInterviewCoach(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret-key-123"
        self.client = app.test_client()
        init_db()

        # Clean test records
        conn = get_db()
        conn.execute('DELETE FROM users WHERE email LIKE "unittest_%"')
        conn.execute('DELETE FROM otp_tokens WHERE email LIKE "unittest_%"')
        conn.commit()
        conn.close()

    def test_database_models_user_lifecycle(self):
        email = f"unittest_candidate_{datetime.now().timestamp()}@example.com"
        created = create_user("Test Candidate", email, "hashed_test_password")
        self.assertTrue(created)

        user = get_user_by_email(email)
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "Test Candidate")
        self.assertEqual(user["is_verified"], 0)

        verify_user_email(email)
        verified_user = get_user_by_email(email)
        self.assertEqual(verified_user["is_verified"], 1)

        update_user_password(email, "new_hashed_password")
        updated_user = get_user_by_email(email)
        self.assertEqual(updated_user["password"], "new_hashed_password")

        delete_user(user["id"])
        self.assertIsNone(get_user_by_email(email))

    def test_otp_token_lifecycle(self):
        email = f"unittest_otp_{datetime.now().timestamp()}@example.com"
        save_otp(email, "123456", "verification")
        self.assertTrue(verify_otp(email, "123456", "verification"))
        self.assertFalse(verify_otp(email, "654321", "verification"))
        delete_otp(email, "verification")
        self.assertFalse(verify_otp(email, "123456", "verification"))

    def test_interview_creation_and_qa_storage(self):
        user_id = 999
        interview_id = create_interview(
            user_id, "Test Company", "Python Engineer", "Flask and cloud pipelines", "Resume highlights"
        )
        self.assertIsNotNone(interview_id)

        interview = get_interview_by_id(interview_id)
        self.assertEqual(interview["company_name"], "Test Company")
        self.assertEqual(interview["job_role"], "Python Engineer")

        save_qa(interview_id, 1, "Technical", "What is WSGI?", "Web Server Gateway Interface")
        qa_list = get_qa_by_interview(interview_id)
        self.assertEqual(len(qa_list), 1)
        self.assertEqual(qa_list[0]["answer"], "Web Server Gateway Interface")

        update_interview_status(interview_id, "completed")
        updated = get_interview_by_id(interview_id)
        self.assertEqual(updated["status"], "completed")

        interviews = get_interviews_by_user(user_id)
        self.assertTrue(any(i["id"] == interview_id for i in interviews))

    def test_result_storage(self):
        interview_id = 888
        save_result(
            interview_id=interview_id,
            technical_score=90,
            communication_score=80,
            confidence_score=85,
            overall_score=85,
            strongest_area="System Design",
            weakest_area="Behavioral framing",
            feedback="Excellent performance across all technical questions.",
            improvement_suggestions="Structure responses with STAR format.",
            recommended_topics="Distributed systems, caching",
            communication_tips="Speak clearly and pause for emphasis.",
        )
        result = get_result_by_interview(interview_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["overall_score"], 85)
        self.assertEqual(result["technical_score"], 90)

    def test_public_routes(self):
        # Landing page
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

        # Login page
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)

        # Register page
        res = self.client.get("/register")
        self.assertEqual(res.status_code, 200)

        # Forgot password page
        res = self.client.get("/forgot-password")
        self.assertEqual(res.status_code, 200)

    def test_generate_interview_questions_fallback(self):
        # With default/missing API key, fallback questions are generated
        questions = generate_interview_questions("Frontend Engineer", "", "")
        self.assertEqual(len(questions), 10)
        self.assertEqual(questions[0]["type"], "Technical")
        self.assertIn("question", questions[0])

    def test_evaluation_fallback_scores(self):
        interview = {"job_role": "DevOps Engineer", "company_name": "CloudCorp"}
        answers = [
            {
                "question_number": 1,
                "type": "Technical",
                "question": "Q1",
                "answer": "Detailed answer about Kubernetes deployment." * 5,
            },
            {
                "question_number": 2,
                "type": "Behavioral",
                "question": "Q2",
                "answer": "Detailed answer using STAR method." * 5,
            },
        ]
        result = evaluate_interview(interview, answers)
        self.assertIn("overall_score", result)
        self.assertIn("technical_score", result)
        self.assertIn("feedback", result)
        self.assertTrue(0 <= result["overall_score"] <= 100)


if __name__ == "__main__":
    unittest.main()
