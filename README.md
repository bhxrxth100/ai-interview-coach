# AI Interview Coach

An AI-powered web application built with **Flask** and **Google Gemini AI** (`google-generativeai`) designed to conduct simulated technical and behavioral interviews, evaluate responses, and provide real-time actionable feedback with resilient fallback safeguards.

## Features
- **Simulated Mock Interviews:** Generates role-tailored technical, behavioral, HR, and situational questions.
- **Gemini AI Integration with Offline Fallbacks:** Automatically handles rate limits (HTTP 429), timeouts, and network interruptions by seamlessly switching to verified question sets and algorithmic scoring without crashing.
- **Real-Time Timed Sessions:** Responsive countdown timer and user answer tracking.
- **Detailed Evaluation Scorecards:** Comprehensive breakdown of technical proficiency, communication skills, confidence, strengths, improvement areas, and study topics.
- **User Authentication & OTP Verification:** Secure signup, login, password hashing, and OTP email verification.
- **Admin Management Panel:** User management, session tracking, and candidate progress overview.

## Tech Stack
- **Backend:** Flask 3.0.3, Werkzeug 3.0.3
- **AI & LLM Integration:** Google Gemini API (`google-generativeai`) with `google.api_core` error handling
- **Database:** SQLite 3 (`models.py`)
- **Email & Auth:** Flask-Mail, python-dotenv
- **Testing & CI:** Pytest, GitHub Actions
- **Frontend:** Jinja2 HTML Templates, Bootstrap 5, Chart.js, Custom CSS

## Application Structure
- `app.py`: Flask application routes, session management, Gemini AI integration, and fallback handling.
- `models.py`: Database models and operations for users, OTP tokens, interviews, Q&A, and evaluation results.
- `config.py`: Environment configuration and validation.
- `tests/`: Automated unit and integration test suite (`test_app.py`).
- `templates/`: Jinja2 templates (`base.html`, `index.html`, `login.html`, `register.html`, `dashboard.html`, `interview_setup.html`, `interview.html`, `results.html`, `admin.html`).
- `static/`: Custom CSS styling and client-side JavaScript.

## Local Setup & Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/bhxrxth100/ai-interview-coach.git
   cd ai-interview-coach
   ```

2. **Set Up Virtual Environment & Dependencies:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_flask_secret_key_here
   GEMINI_API_KEY=your_google_gemini_api_key_here
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_email_app_password
   ```
   *Note: If `GEMINI_API_KEY` is not provided or quota limits are exceeded, the application automatically runs in demo mode with verified offline question banks and algorithmic scoring.*

4. **Run Automated Tests:**
   ```bash
   pytest -v
   ```

5. **Start the Application:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your web browser. Default admin credentials: `admin@example.com` / `admin123`.
