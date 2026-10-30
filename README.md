
# AI Interview Coach

An AI-powered web application built with **Flask** and **Google Gemini AI** (`google-generativeai`) designed to conduct simulated technical and behavioral interviews, evaluate responses, and provide real-time actionable feedback.

## Tech Stack
- **Backend Framework:** Flask 3.0.3
- **AI Integration:** Google Gemini API (`google-generativeai`)
- **Authentication & Communication:** Flask-Mail, Werkzeug, `python-dotenv`
- **Database:** SQLite / SQLAlchemy (`models.py`)
- **Frontend:** Jinja2 HTML Templates & Custom CSS/JS (`templates/`, `static/`)

## Application Structure
- `app.py`: Main Flask application routes, authentication handlers, and Gemini AI interview integration.
- `models.py`: Database models for user profiles, interview setup parameters, and evaluation results.
- `config.py`: Application environment configurations.
- `templates/`: UI pages (`login.html`, `dashboard.html`, `interview_setup.html`, `interview.html`, `results.html`, `otp_verify.html`, `admin.html`).
- `static/`: Custom CSS styling (`style.css`) and client-side JavaScript (`main.js`).

## Local Setup & Installation

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/bhxrxth100/ai-interview-coach.git](https://github.com/bhxrxth100/ai-interview-coach.git)
   cd ai-interview-coach

```

2. **Set Up Virtual Environment & Dependencies:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

```


3. **Configure Environment Variables:**
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_google_gemini_api_key
SECRET_KEY=your_flask_secret_key
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password

```


4. **Run the Application:**
```bash
python app.py

```


Open `http://127.0.0.1:5000` in your web browser.
