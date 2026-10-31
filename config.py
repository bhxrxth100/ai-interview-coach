import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ai-interview-coach-secret-key-2024')

    # SQLite database path
    DATABASE = os.environ.get(
        'DATABASE_PATH',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interview_coach.db')
    )

    # Gemini API Key
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')

    # Email configuration (Gmail SMTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    try:
        MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    except (ValueError, TypeError):
        MAIL_PORT = 587

    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_app_password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # OTP expiry in minutes
    try:
        OTP_EXPIRY_MINUTES = int(os.environ.get('OTP_EXPIRY_MINUTES', 5))
    except (ValueError, TypeError):
        OTP_EXPIRY_MINUTES = 5

    # Admin credentials
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
