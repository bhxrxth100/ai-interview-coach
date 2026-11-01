import json
import random
import string
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import (
    create_interview,
    create_user,
    delete_otp,
    delete_user,
    get_all_interviews,
    get_all_results,
    get_all_users,
    get_interview_by_id,
    get_interviews_by_user,
    get_qa_by_interview,
    get_result_by_interview,
    get_user_by_email,
    get_user_by_id,
    get_user_stats,
    get_user_top_area,
    init_db,
    save_otp,
    save_qa,
    save_result,
    update_interview_status,
    update_user_password,
    verify_otp,
    verify_user_email,
)

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)

# ─────────────────────────────────────────────
# Gemini AI Setup
# ─────────────────────────────────────────────
try:
    import google.generativeai as genai
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    GEMINI_AVAILABLE = True
except Exception as e:
    print(f"Gemini not available: {e}")
    GEMINI_AVAILABLE = False

# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email, otp, purpose='verification'):
    try:
        subject = 'AI Interview Coach - Email Verification OTP' if purpose == 'verification' else 'AI Interview Coach - Password Reset OTP'
        body = f'''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1a73e8, #0d47a1); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0;">AI Interview Coach</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h2 style="color: #333;">Your OTP Code</h2>
                <p style="color: #666;">Use the following OTP to {"verify your email" if purpose == "verification" else "reset your password"}:</p>
                <div style="background: white; border: 2px solid #1a73e8; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #1a73e8; font-size: 36px; letter-spacing: 8px; margin: 0;">{otp}</h1>
                </div>
                <p style="color: #999; font-size: 14px;">This OTP expires in <strong>5 minutes</strong>. Do not share it with anyone.</p>
            </div>
        </body>
        </html>
        '''
        msg = Message(subject=subject, recipients=[email], html=body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def gemini_generate(prompt):
    """Call Gemini API with fallback to demo data."""
    if GEMINI_AVAILABLE and Config.GEMINI_API_KEY != 'YOUR_GEMINI_API_KEY_HERE':
        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
    # Fallback - return None to use demo data
    return None

# ─────────────────────────────────────────────
# Landing Page
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# ─────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if len(name) < 2:
            flash('Name must be at least 2 characters.', 'danger')
            return render_template('register.html')
        if '@' not in email:
            flash('Invalid email address.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # Check if email exists
        existing = get_user_by_email(email)
        if existing:
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        # Hash password & create user (unverified)
        hashed_pw = generate_password_hash(password)
        result = create_user(name, email, hashed_pw)
        if not result:
            flash('Registration failed. Try again.', 'danger')
            return render_template('register.html')

        # Generate & send OTP
        otp = generate_otp()
        save_otp(email, otp, 'verification')
        email_sent = send_otp_email(email, otp, 'verification')

        session['pending_email'] = email
        session['pending_purpose'] = 'verification'
        # Always store OTP in session so it shows on screen (dev mode)
        session['dev_otp'] = otp
        session['email_sent'] = email_sent

        print(f"\n{'='*40}\n  YOUR OTP IS: {otp}\n{'='*40}\n")

        return redirect(url_for('otp_verify'))

    return render_template('register.html')

# ─────────────────────────────────────────────
# OTP Verification
# ─────────────────────────────────────────────

@app.route('/otp-verify', methods=['GET', 'POST'])
def otp_verify():
    email = session.get('pending_email')
    purpose = session.get('pending_purpose', 'verification')

    if not email:
        return redirect(url_for('register'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()

        if verify_otp(email, entered_otp, purpose):
            delete_otp(email, purpose)

            if purpose == 'verification':
                verify_user_email(email)
                session.pop('pending_email', None)
                session.pop('pending_purpose', None)
                flash('Email verified successfully! Please login.', 'success')
                return redirect(url_for('login'))
            elif purpose == 'reset':
                session['reset_verified'] = True
                flash('OTP verified. Set your new password.', 'success')
                return redirect(url_for('reset_password'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')

    dev_otp = session.get('dev_otp', '')
    email_sent = session.get('email_sent', False)
    return render_template('otp_verify.html', email=email, purpose=purpose, dev_otp=dev_otp, email_sent=email_sent)

@app.route('/resend-otp')
def resend_otp():
    email = session.get('pending_email')
    purpose = session.get('pending_purpose', 'verification')
    if not email:
        return redirect(url_for('register'))
    otp = generate_otp()
    save_otp(email, otp, purpose)
    email_sent = send_otp_email(email, otp, purpose)
    session['dev_otp'] = otp
    session['email_sent'] = email_sent
    print(f"\n{'='*40}\n  YOUR NEW OTP IS: {otp}\n{'='*40}\n")
    return redirect(url_for('otp_verify'))

# ─────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Admin login
        if email == Config.ADMIN_EMAIL and password == Config.ADMIN_PASSWORD:
            session['is_admin'] = True
            session['admin_email'] = email
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin_panel'))

        # User login
        user = get_user_by_email(email)
        if not user:
            flash('No account found with this email.', 'danger')
            return render_template('login.html')

        if not check_password_hash(user['password'], password):
            flash('Incorrect password.', 'danger')
            return render_template('login.html')

        if not user['is_verified']:
            otp = generate_otp()
            save_otp(email, otp, 'verification')
            send_otp_email(email, otp, 'verification')
            session['pending_email'] = email
            session['pending_purpose'] = 'verification'
            session['dev_otp'] = otp
            session['email_sent'] = False
            print(f"\n{'='*40}\n  YOUR OTP IS: {otp}\n{'='*40}\n")
            return redirect(url_for('otp_verify'))

        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# ─────────────────────────────────────────────
# Forgot Password
# ─────────────────────────────────────────────

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = get_user_by_email(email)
        if not user:
            flash('No account found with this email.', 'danger')
            return render_template('forgot_password.html')
        otp = generate_otp()
        save_otp(email, otp, 'reset')
        email_sent = send_otp_email(email, otp, 'reset')
        session['pending_email'] = email
        session['pending_purpose'] = 'reset'
        session['dev_otp'] = otp
        session['email_sent'] = email_sent
        print(f"\n{'='*40}\n  PASSWORD RESET OTP: {otp}\n{'='*40}\n")
        return redirect(url_for('otp_verify'))
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_verified'):
        return redirect(url_for('forgot_password'))
    email = session.get('pending_email')

    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('reset_password.html')
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html')
        hashed_pw = generate_password_hash(new_password)
        update_user_password(email, hashed_pw)
        session.pop('pending_email', None)
        session.pop('pending_purpose', None)
        session.pop('reset_verified', None)
        flash('Password reset successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

# ─────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    stats = get_user_stats(user_id)
    strongest, weakest = get_user_top_area(user_id)
    interviews = get_interviews_by_user(user_id, limit=5)

    avg_score = round(stats['avg_score'] or 0, 1)
    total = stats['total_interviews'] or 0

    return render_template('dashboard.html',
                           user=user,
                           total_interviews=total,
                           avg_score=avg_score,
                           strongest_area=strongest,
                           weakest_area=weakest,
                           interviews=interviews)

# ─────────────────────────────────────────────
# Start Interview
# ─────────────────────────────────────────────

@app.route('/interview/new', methods=['GET', 'POST'])
@login_required
def new_interview():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        job_role = request.form.get('job_role', '').strip()
        job_description = request.form.get('job_description', '').strip()
        resume_text = request.form.get('resume_text', '').strip()

        if not company_name or not job_role:
            flash('Company name and job role are required.', 'danger')
            return render_template('interview_setup.html')

        interview_id = create_interview(
            session['user_id'], company_name, job_role,
            job_description, resume_text
        )

        # Generate questions with Gemini
        questions = generate_interview_questions(job_role, job_description, resume_text)
        session['interview_id'] = interview_id
        session['questions'] = questions
        session['current_q'] = 0
        session['answers'] = []

        return redirect(url_for('interview_session'))

    return render_template('interview_setup.html')

def generate_interview_questions(job_role, job_description, resume_text):
    """Generate interview questions using Gemini AI."""
    prompt = f"""
You are an expert technical interviewer. Generate exactly 10 interview questions for the following role.

Job Role: {job_role}
Job Description: {job_description[:500] if job_description else 'Not provided'}
Resume Summary: {resume_text[:500] if resume_text else 'Not provided'}

Generate exactly these question types:
1. Technical Question 1
2. Technical Question 2
3. Technical Question 3
4. HR Question 1
5. HR Question 2
6. Behavioral Question 1
7. Behavioral Question 2
8. Situational Question 1
9. Situational Question 2
10. Project/Experience Question 1

Return ONLY a JSON array in this exact format, no markdown, no explanation:
[
  {{"type": "Technical", "question": "..."}},
  {{"type": "Technical", "question": "..."}},
  {{"type": "Technical", "question": "..."}},
  {{"type": "HR", "question": "..."}},
  {{"type": "HR", "question": "..."}},
  {{"type": "Behavioral", "question": "..."}},
  {{"type": "Behavioral", "question": "..."}},
  {{"type": "Situational", "question": "..."}},
  {{"type": "Situational", "question": "..."}},
  {{"type": "Project", "question": "..."}}
]
"""
    response = gemini_generate(prompt)

    if response:
        try:
            # Strip markdown code fences if present
            clean = response.strip()
            if clean.startswith('```'):
                clean = clean.split('```')[1]
                if clean.startswith('json'):
                    clean = clean[4:]
            questions = json.loads(clean.strip())
            if isinstance(questions, list) and len(questions) > 0:
                return questions
        except Exception as e:
            print(f"Question parse error: {e}")

    # Fallback demo questions
    return [
        {"type": "Technical", "question": f"Explain the core technical concepts required for a {job_role} role."},
        {"type": "Technical", "question": f"How would you approach debugging a critical production issue as a {job_role}?"},
        {"type": "Technical", "question": "Describe the architecture of a scalable system you have worked on or would design."},
        {"type": "HR", "question": "Tell me about yourself and your professional journey so far."},
        {"type": "HR", "question": "Why are you interested in this role and what are your long-term career goals?"},
        {"type": "Behavioral", "question": "Describe a time when you had to work under tight deadlines. How did you manage it?"},
        {"type": "Behavioral", "question": "Tell me about a conflict you had with a team member and how you resolved it."},
        {"type": "Situational", "question": "If a major feature you built caused a production outage, what steps would you take?"},
        {"type": "Situational", "question": "How would you handle it if you disagreed with your manager's technical decision?"},
        {"type": "Project", "question": "Walk me through the most challenging project you have worked on and your specific contributions."},
    ]

# ─────────────────────────────────────────────
# Interview Session
# ─────────────────────────────────────────────

@app.route('/interview/session')
@login_required
def interview_session():
    if 'interview_id' not in session or 'questions' not in session:
        flash('No active interview session.', 'warning')
        return redirect(url_for('new_interview'))

    questions = session.get('questions', [])
    current_q = session.get('current_q', 0)
    total_q = len(questions)

    if current_q >= total_q:
        return redirect(url_for('submit_interview'))

    current_question = questions[current_q]
    return render_template('interview.html',
                           question=current_question,
                           question_num=current_q + 1,
                           total_questions=total_q,
                           interview_id=session['interview_id'])

@app.route('/interview/answer', methods=['POST'])
@login_required
def submit_answer():
    if 'interview_id' not in session:
        return redirect(url_for('dashboard'))

    answer = request.form.get('answer', '').strip()
    questions = session.get('questions', [])
    current_q = session.get('current_q', 0)

    if current_q < len(questions):
        q = questions[current_q]
        answers = session.get('answers', [])
        answers.append({
            'question_number': current_q + 1,
            'type': q['type'],
            'question': q['question'],
            'answer': answer
        })
        session['answers'] = answers
        session['current_q'] = current_q + 1

    if session['current_q'] >= len(questions):
        return redirect(url_for('submit_interview'))

    return redirect(url_for('interview_session'))

@app.route('/interview/submit')
@login_required
def submit_interview():
    if 'interview_id' not in session:
        return redirect(url_for('dashboard'))

    interview_id = session['interview_id']
    answers = session.get('answers', [])
    questions = session.get('questions', [])

    # Save all Q&A
    for ans in answers:
        save_qa(interview_id, ans['question_number'], ans['type'],
                ans['question'], ans['answer'])

    # Fill unanswered questions
    answered_nums = {a['question_number'] for a in answers}
    for i, q in enumerate(questions, 1):
        if i not in answered_nums:
            save_qa(interview_id, i, q['type'], q['question'], '')

    # Evaluate with AI
    interview = get_interview_by_id(interview_id)
    evaluation = evaluate_interview(interview, answers)

    # Save results
    save_result(
        interview_id,
        evaluation['technical_score'],
        evaluation['communication_score'],
        evaluation['confidence_score'],
        evaluation['overall_score'],
        evaluation['strongest_area'],
        evaluation['weakest_area'],
        evaluation['feedback'],
        evaluation['improvement_suggestions'],
        evaluation['recommended_topics'],
        evaluation['communication_tips']
    )

    update_interview_status(interview_id, 'completed')

    # Clear session interview data
    session.pop('interview_id', None)
    session.pop('questions', None)
    session.pop('current_q', None)
    session.pop('answers', None)

    flash('Interview completed! Here are your results.', 'success')
    return redirect(url_for('results', interview_id=interview_id))

def evaluate_interview(interview, answers):
    """Evaluate answers using Gemini AI."""
    qa_text = ""
    for ans in answers:
        qa_text += f"\nQ{ans['question_number']} ({ans['type']}): {ans['question']}\nAnswer: {ans['answer']}\n"

    prompt = f"""
You are an expert interview evaluator. Evaluate the following interview responses for a {interview['job_role']} position at {interview['company_name']}.

Interview Q&A:
{qa_text}

Evaluate and return ONLY a JSON object (no markdown, no explanation) with these exact keys:
{{
  "technical_score": <number 0-100>,
  "communication_score": <number 0-100>,
  "confidence_score": <number 0-100>,
  "overall_score": <number 0-100>,
  "strongest_area": "<one of: Technical, Communication, Behavioral, HR, Situational, Project>",
  "weakest_area": "<one of: Technical, Communication, Behavioral, HR, Situational, Project>",
  "feedback": "<2-3 sentence overall feedback>",
  "improvement_suggestions": "<3-4 specific improvement points, separated by |>",
  "recommended_topics": "<3-4 topics to study, separated by |>",
  "communication_tips": "<3-4 communication improvement tips, separated by |>"
}}

Be fair but realistic. If answers are blank/poor, give low scores. Be specific in feedback.
"""
    response = gemini_generate(prompt)

    if response:
        try:
            clean = response.strip()
            if clean.startswith('```'):
                clean = clean.split('```')[1]
                if clean.startswith('json'):
                    clean = clean[4:]
            result = json.loads(clean.strip())
            # Ensure all required keys exist
            required_keys = ['technical_score', 'communication_score', 'confidence_score',
                             'overall_score', 'strongest_area', 'weakest_area', 'feedback',
                             'improvement_suggestions', 'recommended_topics', 'communication_tips']
            if all(k in result for k in required_keys):
                return result
        except Exception as e:
            print(f"Evaluation parse error: {e}")

    # Fallback evaluation based on answer length
    def score_from_answers(answer_list, q_type):
        relevant = [a for a in answer_list if a.get('type') == q_type]
        if not relevant:
            return random.randint(40, 60)
        avg_len = sum(len(a.get('answer', '')) for a in relevant) / len(relevant)
        if avg_len > 200:
            return random.randint(72, 88)
        elif avg_len > 80:
            return random.randint(55, 72)
        else:
            return random.randint(30, 55)

    tech = score_from_answers(answers, 'Technical')
    comm = score_from_answers(answers, 'Behavioral') + random.randint(-5, 10)
    comm = max(0, min(100, comm))
    conf = random.randint(55, 85)
    overall = round((tech + comm + conf) / 3, 1)

    areas = {'Technical': tech, 'Communication': comm, 'Confidence': conf}
    strongest = max(areas, key=areas.get)
    weakest = min(areas, key=areas.get)

    return {
        'technical_score': tech,
        'communication_score': comm,
        'confidence_score': conf,
        'overall_score': overall,
        'strongest_area': strongest,
        'weakest_area': weakest,
        'feedback': f'You showed decent understanding of the {interview["job_role"]} role. Focus on providing structured, detailed answers with real examples.',
        'improvement_suggestions': 'Use STAR method for behavioral questions|Practice explaining technical concepts simply|Add quantifiable achievements|Prepare 2-3 strong project examples',
        'recommended_topics': f'{interview["job_role"]} fundamentals|System design basics|Data structures & algorithms|Latest industry trends',
        'communication_tips': 'Speak clearly and at a moderate pace|Structure answers with introduction, body, conclusion|Listen carefully before answering|Avoid filler words like "um" and "uh"'
    }

# ─────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────

@app.route('/results/<int:interview_id>')
@login_required
def results(interview_id):
    interview = get_interview_by_id(interview_id)
    if not interview or interview['user_id'] != session['user_id']:
        flash('Interview not found.', 'danger')
        return redirect(url_for('dashboard'))

    result = get_result_by_interview(interview_id)
    if not result:
        flash('Results not available yet.', 'warning')
        return redirect(url_for('dashboard'))

    qa_list = get_qa_by_interview(interview_id)

    improvement_suggestions = (result['improvement_suggestions'] or '').split('|')
    recommended_topics = (result['recommended_topics'] or '').split('|')
    communication_tips = (result['communication_tips'] or '').split('|')

    return render_template('results.html',
                           interview=interview,
                           result=result,
                           qa_list=qa_list,
                           improvement_suggestions=[s.strip() for s in improvement_suggestions if s.strip()],
                           recommended_topics=[t.strip() for t in recommended_topics if t.strip()],
                           communication_tips=[c.strip() for c in communication_tips if c.strip()])

# ─────────────────────────────────────────────
# Admin Panel
# ─────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_panel():
    users = get_all_users()
    interviews = get_all_interviews()
    all_results = get_all_results()
    return render_template('admin.html',
                           users=users,
                           interviews=interviews,
                           all_results=all_results,
                           total_users=len(users),
                           total_interviews=len(interviews))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    delete_user(user_id)
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out.', 'success')
    return redirect(url_for('login'))

# ─────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────

@app.route('/profile')
@login_required
def profile():
    user = get_user_by_id(session['user_id'])
    stats = get_user_stats(session['user_id'])
    strongest, weakest = get_user_top_area(session['user_id'])
    return render_template('profile.html', user=user, stats=stats,
                           strongest=strongest, weakest=weakest)

# ─────────────────────────────────────────────
# API endpoint for interview progress
# ─────────────────────────────────────────────

@app.route('/api/interview/progress')
@login_required
def interview_progress():
    return jsonify({
        'current': session.get('current_q', 0),
        'total': len(session.get('questions', [])),
        'interview_id': session.get('interview_id')
    })

# ─────────────────────────────────────────────
# App Entry Point
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  AI Interview Coach - Starting...")
    print("  URL: http://127.0.0.1:5000")
    print("  Admin: admin@example.com / admin123")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
