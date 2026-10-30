import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ai-interview-coach-secret-key-2024')

    # SQLite database path
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interview_coach.db')

    # Gemini API Key - set this in your .env file or replace directly
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')

    # Email configuration (Gmail SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_app_password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')

    # OTP expiry in minutes
    OTP_EXPIRY_MINUTES = 5

    # Admin credentials
    ADMIN_EMAIL = 'admin@example.com'
    ADMIN_PASSWORD = 'admin123'
