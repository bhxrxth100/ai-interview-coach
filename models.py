import sqlite3

from config import Config


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # OTP table for email verification and password reset
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            purpose TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    ''')

    # Interview table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            job_description TEXT,
            resume_text TEXT,
            interview_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER NOT NULL,
            technical_score REAL DEFAULT 0,
            communication_score REAL DEFAULT 0,
            confidence_score REAL DEFAULT 0,
            overall_score REAL DEFAULT 0,
            strongest_area TEXT,
            weakest_area TEXT,
            feedback TEXT,
            improvement_suggestions TEXT,
            recommended_topics TEXT,
            communication_tips TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (interview_id) REFERENCES interviews(id)
        )
    ''')

    # QA table for storing questions and answers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_qa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER NOT NULL,
            question_number INTEGER,
            question_type TEXT,
            question TEXT,
            answer TEXT,
            FOREIGN KEY (interview_id) REFERENCES interviews(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# ─────────────────────────────────────────────
# User functions
# ─────────────────────────────────────────────

def create_user(name, email, password_hash):
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
            (name, email, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def verify_user_email(email):
    conn = get_db()
    conn.execute('UPDATE users SET is_verified = 1 WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def update_user_password(email, new_password_hash):
    conn = get_db()
    conn.execute('UPDATE users SET password = ? WHERE email = ?', (new_password_hash, email))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY created_date DESC').fetchall()
    conn.close()
    return users

def delete_user(user_id):
    conn = get_db()
    conn.execute('DELETE FROM interview_qa WHERE interview_id IN (SELECT id FROM interviews WHERE user_id = ?)', (user_id,))
    conn.execute('DELETE FROM results WHERE interview_id IN (SELECT id FROM interviews WHERE user_id = ?)', (user_id,))
    conn.execute('DELETE FROM interviews WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# OTP functions
# ─────────────────────────────────────────────

def save_otp(email, otp, purpose):
    from datetime import datetime, timedelta
    conn = get_db()
    expires_at = datetime.now() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
    # Delete old OTPs for this email/purpose
    conn.execute('DELETE FROM otp_tokens WHERE email = ? AND purpose = ?', (email, purpose))
    conn.execute(
        'INSERT INTO otp_tokens (email, otp, purpose, expires_at) VALUES (?, ?, ?, ?)',
        (email, otp, purpose, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

def verify_otp(email, otp, purpose):
    from datetime import datetime
    conn = get_db()
    record = conn.execute(
        'SELECT * FROM otp_tokens WHERE email = ? AND otp = ? AND purpose = ?',
        (email, otp, purpose)
    ).fetchone()
    conn.close()
    if not record:
        return False
    expires_at = record['expires_at']
    if isinstance(expires_at, str):
        from datetime import datetime
        expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
    if datetime.now() > expires_at:
        return False
    return True

def delete_otp(email, purpose):
    conn = get_db()
    conn.execute('DELETE FROM otp_tokens WHERE email = ? AND purpose = ?', (email, purpose))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# Interview functions
# ─────────────────────────────────────────────

def create_interview(user_id, company_name, job_role, job_description, resume_text):
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO interviews (user_id, company_name, job_role, job_description, resume_text) VALUES (?, ?, ?, ?, ?)',
        (user_id, company_name, job_role, job_description, resume_text)
    )
    interview_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return interview_id

def get_interview_by_id(interview_id):
    conn = get_db()
    interview = conn.execute('SELECT * FROM interviews WHERE id = ?', (interview_id,)).fetchone()
    conn.close()
    return interview

def get_interviews_by_user(user_id, limit=10):
    conn = get_db()
    interviews = conn.execute(
        '''SELECT i.*, r.overall_score, r.strongest_area, r.weakest_area
           FROM interviews i
           LEFT JOIN results r ON i.id = r.interview_id
           WHERE i.user_id = ?
           ORDER BY i.interview_date DESC
           LIMIT ?''',
        (user_id, limit)
    ).fetchall()
    conn.close()
    return interviews

def get_all_interviews():
    conn = get_db()
    interviews = conn.execute(
        '''SELECT i.*, u.name as user_name, u.email as user_email, r.overall_score
           FROM interviews i
           JOIN users u ON i.user_id = u.id
           LEFT JOIN results r ON i.id = r.interview_id
           ORDER BY i.interview_date DESC'''
    ).fetchall()
    conn.close()
    return interviews

def update_interview_status(interview_id, status):
    conn = get_db()
    conn.execute('UPDATE interviews SET status = ? WHERE id = ?', (status, interview_id))
    conn.commit()
    conn.close()

def save_qa(interview_id, question_number, question_type, question, answer):
    conn = get_db()
    conn.execute(
        'INSERT INTO interview_qa (interview_id, question_number, question_type, question, answer) VALUES (?, ?, ?, ?, ?)',
        (interview_id, question_number, question_type, question, answer)
    )
    conn.commit()
    conn.close()

def get_qa_by_interview(interview_id):
    conn = get_db()
    qa = conn.execute(
        'SELECT * FROM interview_qa WHERE interview_id = ? ORDER BY question_number',
        (interview_id,)
    ).fetchall()
    conn.close()
    return qa

# ─────────────────────────────────────────────
# Results functions
# ─────────────────────────────────────────────

def save_result(interview_id, technical_score, communication_score, confidence_score,
                overall_score, strongest_area, weakest_area, feedback,
                improvement_suggestions, recommended_topics, communication_tips):
    conn = get_db()
    conn.execute(
        '''INSERT INTO results
           (interview_id, technical_score, communication_score, confidence_score,
            overall_score, strongest_area, weakest_area, feedback,
            improvement_suggestions, recommended_topics, communication_tips)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (interview_id, technical_score, communication_score, confidence_score,
         overall_score, strongest_area, weakest_area, feedback,
         improvement_suggestions, recommended_topics, communication_tips)
    )
    conn.commit()
    conn.close()

def get_result_by_interview(interview_id):
    conn = get_db()
    result = conn.execute('SELECT * FROM results WHERE interview_id = ?', (interview_id,)).fetchone()
    conn.close()
    return result

def get_all_results():
    conn = get_db()
    results = conn.execute(
        '''SELECT r.*, i.company_name, i.job_role, u.name as user_name
           FROM results r
           JOIN interviews i ON r.interview_id = i.id
           JOIN users u ON i.user_id = u.id
           ORDER BY r.created_at DESC'''
    ).fetchall()
    conn.close()
    return results

def get_user_stats(user_id):
    conn = get_db()
    stats = conn.execute(
        '''SELECT
               COUNT(i.id) as total_interviews,
               AVG(r.overall_score) as avg_score,
               MAX(r.overall_score) as best_score
           FROM interviews i
           LEFT JOIN results r ON i.id = r.interview_id
           WHERE i.user_id = ?''',
        (user_id,)
    ).fetchone()
    conn.close()
    return stats

def get_user_top_area(user_id):
    conn = get_db()
    strongest = conn.execute(
        '''SELECT strongest_area, COUNT(*) as cnt
           FROM results r JOIN interviews i ON r.interview_id = i.id
           WHERE i.user_id = ? AND strongest_area IS NOT NULL
           GROUP BY strongest_area ORDER BY cnt DESC LIMIT 1''',
        (user_id,)
    ).fetchone()
    weakest = conn.execute(
        '''SELECT weakest_area, COUNT(*) as cnt
           FROM results r JOIN interviews i ON r.interview_id = i.id
           WHERE i.user_id = ? AND weakest_area IS NOT NULL
           GROUP BY weakest_area ORDER BY cnt DESC LIMIT 1''',
        (user_id,)
    ).fetchone()
    conn.close()
    return (
        strongest['strongest_area'] if strongest else 'N/A',
        weakest['weakest_area'] if weakest else 'N/A'
    )
