import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import pandas as pd

from nlp_engine import (
    extract_text_from_pdf, 
    extract_contact_info, 
    calculate_hybrid_score, 
    extract_skills,
    extract_candidate_name,
    evaluate_individual_resume
)

# Load configuration from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "contexthire_super_secret_production_key_9942")
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['EXPORTS_FOLDER'] = os.path.join(os.path.dirname(__file__), 'exports')
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['TEMPLATES_AUTO_RELOAD'] = True

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORTS_FOLDER'], exist_ok=True)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and indexes from schema.sql and runs safe migrations."""
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if tables exist in database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone()
    
    if not table_exists and os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        print("ContextHire SQLite database initialized from schema.sql.")
        
    # Safe migration: ensure account_type exists in users
    cursor.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in cursor.fetchall()]
    if cols and 'account_type' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN account_type VARCHAR(50) DEFAULT 'hiring_team'")
        conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

init_db()

@app.route('/')
def index():
    return render_template('landing.html')

# Role-Based Authentication
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        if session.get('account_type') == 'individual':
            return redirect(url_for('ats_checker'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        account_type = request.form.get('account_type', 'hiring_team').strip()
        
        conn = get_db_connection()
        try:
            hashed_pw = generate_password_hash(password)
            conn.execute('INSERT INTO users (username, email, password_hash, account_type) VALUES (?, ?, ?, ?)',
                         (username, email, hashed_pw, account_type))
            conn.commit()
            flash("Account registered successfully! Please log in to continue.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("An account with that email or username already exists.", "danger")
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('account_type') == 'individual':
            return redirect(url_for('ats_checker'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['account_type'] = user['account_type'] if 'account_type' in user.keys() and user['account_type'] else 'hiring_team'
            
            flash(f"Welcome back, {user['username']}!", "success")
            if session['account_type'] == 'individual':
                return redirect(url_for('ats_checker'))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please verify credentials.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Successfully signed out.", "info")
    return redirect(url_for('login'))

# Individual Resume ATS Checker
@app.route('/ats-checker', methods=['GET', 'POST'])
def ats_checker():
    analysis = None
    candidate_name = None
    job_desc = ""

    if request.method == 'POST':
        job_desc = request.form.get('job_description', '').strip()
        
        if 'resume' in request.files and request.files['resume'].filename != '':
            file = request.files['resume']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                raw_text = extract_text_from_pdf(file_path)
                candidate_name = extract_candidate_name(raw_text, filename)
                analysis = evaluate_individual_resume(raw_text, job_desc)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                if len(raw_text.strip()) < 20:
                    flash(f"Warning: No readable text detected in '{filename}'. PDF appears to be a scanned image or flattened graphic. ATS algorithms require selectable text.", "warning")
            else:
                flash("Please upload a standard PDF resume document.", "danger")
        else:
            flash("No resume attached. Please choose a PDF file to analyze.", "danger")

    # Sample demo request
    elif request.args.get('sample') == '1':
        sample_text = """
        Alex Rivera
        Email: alex.rivera@example.com | Phone: (555) 234-5678 | San Francisco, CA
        Summary: Full Stack Software Engineer with 4 years of experience building scalable web applications.
        Experience:
        Senior Software Engineer - TechCore Labs (2022 - Present)
        - Architected and deployed 6 microservices using Python, FastAPI, and PostgreSQL, cutting API latency by 38%.
        - Spearheaded migration to Docker and Kubernetes on AWS, achieving 99.99% system availability.
        - Automated CI/CD deployment pipeline via GitHub Actions, accelerating release cycles by 40%.
        Software Developer - AppPulse Inc (2020 - 2022)
        - Engineered responsive user interfaces using React, TypeScript, and Tailwind CSS for 85k monthly active users.
        - Optimized complex SQL queries and Redis caching, reducing slow queries by 45%.
        Education:
        B.S. in Computer Science - State University
        Skills:
        Python, JavaScript, TypeScript, React, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git, CI/CD, REST API, Agile
        Projects:
        Distributed Analytics Engine - Engineered streaming analytics platform handling 1.5M events/day.
        """
        candidate_name = "Alex Rivera"
        analysis = evaluate_individual_resume(sample_text, "Looking for a Full Stack Engineer with Python, React, Docker, and AWS experience.")

    return render_template('ats_checker.html', analysis=analysis, candidate_name=candidate_name, job_desc=job_desc)

# Hiring Team Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if session.get('account_type') == 'individual':
        flash("You are signed in as an Individual. Redirected to your ATS Resume Checker.", "info")
        return redirect(url_for('ats_checker'))
        
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs ORDER BY created_at DESC').fetchall()
    
    total_cand = conn.execute('SELECT COUNT(*) FROM candidates').fetchone()[0]
    shortlisted = conn.execute('SELECT COUNT(*) FROM candidates WHERE status = "Shortlisted"').fetchone()[0]
    rejected = conn.execute('SELECT COUNT(*) FROM candidates WHERE status = "Rejected"').fetchone()[0]
    avg_score = conn.execute('SELECT AVG(match_score) FROM candidates').fetchone()[0] or 0.0
    
    # Calculate score buckets for Chart.js
    cands = conn.execute('SELECT match_score FROM candidates').fetchall()
    
    # Recent candidates query
    recent_candidates = conn.execute('''
        SELECT c.*, j.title as job_title 
        FROM candidates c 
        JOIN jobs j ON c.job_id = j.id 
        ORDER BY c.uploaded_at DESC LIMIT 8
    ''').fetchall()
    conn.close()
    
    b1 = sum(1 for c in cands if c['match_score'] < 40)
    b2 = sum(1 for c in cands if 40 <= c['match_score'] < 70)
    b3 = sum(1 for c in cands if 70 <= c['match_score'] < 85)
    b4 = sum(1 for c in cands if c['match_score'] >= 85)
    distribution = [b1, b2, b3, b4]
    
    return render_template('dashboard.html', jobs=jobs, total_cand=total_cand,
                           shortlisted=shortlisted, rejected=rejected,
                           avg_score=round(avg_score, 1), score_distribution=distribution,
                           recent_candidates=recent_candidates)

# Job Position Management
@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if session.get('account_type') == 'individual':
        flash("You are signed in as an Individual. Redirected to your ATS Resume Checker.", "info")
        return redirect(url_for('ats_checker'))
        
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title'].strip()
        department = request.form.get('department', 'Engineering').strip()
        experience_level = request.form.get('experience_level', 'Mid-Level')
        description = request.form['description'].strip()
        manual_skills = request.form.get('manual_skills', '').strip()
        
        # Mine skills via NLP or combine with recruiter override
        if manual_skills:
            required_skills = ", ".join([s.strip().lower() for s in manual_skills.split(',') if s.strip()])
        else:
            auto_skills = extract_skills(description)
            required_skills = ", ".join(auto_skills)
            
        conn.execute('''
            INSERT INTO jobs (title, department, experience_level, description, required_skills)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, department, experience_level, description, required_skills))
        conn.commit()
        flash(f"Job profile '{title}' configured with competencies: {required_skills}", "success")
        return redirect(url_for('jobs'))
        
    jobs_list = conn.execute('SELECT * FROM jobs ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('job_profiles.html', jobs=jobs_list)

@app.route('/jobs/<int:job_id>/delete')
def delete_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM candidates WHERE job_id = ?', (job_id,))
    conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()
    flash("Job position and applicant records deleted.", "info")
    return redirect(url_for('jobs'))

# Candidates Screening & Ranking Roster
@app.route('/jobs/<int:job_id>/candidates', methods=['GET', 'POST'])
def candidates(job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    if not job:
        conn.close()
        flash("Job role not found.", "danger")
        return redirect(url_for('jobs'))
        
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash("No file attached in upload payload.", "danger")
            return redirect(request.url)
            
        file = request.files['resume']
        if file.filename == '':
            flash("No file selected.", "danger")
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # 1. Parse text from layout
            raw_text = extract_text_from_pdf(file_path)
            
            # 2. Extract Candidate Name & Contact Info
            candidate_name = extract_candidate_name(raw_text, filename)
            email, phone = extract_contact_info(raw_text)
            
            # 3. Calculate Hybrid Match Score (HMS)
            matching = calculate_hybrid_score(raw_text, job['description'], job['required_skills'])
            
            # 4. Persist to DB
            conn.execute('''
                INSERT INTO candidates (job_id, name, email, phone, match_score, matched_skills, missing_skills, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job_id, candidate_name, email, phone, matching['score'],
                  ", ".join(matching['matched_skills']), ", ".join(matching['missing_skills']), raw_text))
            conn.commit()
            
            # Clean up temporary upload
            if os.path.exists(file_path):
                os.remove(file_path)
                
            if len(raw_text.strip()) < 20:
                flash(f"Warning: No readable text detected in '{filename}'. PDF appears to be a scanned image or flattened graphic without selectable text. Real ATS engines require text-based PDFs (e.g., Export from Word/Google Docs). Match score is 0%.", "warning")
            else:
                flash(f"Resume for '{candidate_name}' evaluated. Hybrid Match Score: {matching['score']}%", "success")
            return redirect(url_for('candidates', job_id=job_id))
        else:
            flash("Invalid file format. Please upload standard PDF documents.", "danger")
            return redirect(request.url)

    candidates_list = conn.execute('''
        SELECT * FROM candidates WHERE job_id = ? ORDER BY match_score DESC
    ''', (job_id,)).fetchall()
    
    total_cand = len(candidates_list)
    shortlisted = sum(1 for c in candidates_list if c['status'] == 'Shortlisted')
    rejected = sum(1 for c in candidates_list if c['status'] == 'Rejected')
    avg_score = sum(c['match_score'] for c in candidates_list) / total_cand if total_cand > 0 else 0.0
    
    conn.close()
    return render_template('candidates.html', job=job, candidates=candidates_list,
                           total_cand=total_cand, shortlisted=shortlisted,
                           rejected=rejected, avg_score=round(avg_score, 1))

@app.route('/candidates/<int:candidate_id>/status/<string:new_status>')
def update_status(candidate_id, new_status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if new_status not in ['Shortlisted', 'Rejected', 'Pending']:
        flash("Invalid status flag.", "danger")
        return redirect(url_for('dashboard'))
        
    conn = get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    if candidate:
        conn.execute('UPDATE candidates SET status = ? WHERE id = ?', (new_status, candidate_id))
        conn.commit()
        job_id = candidate['job_id']
        conn.close()
        flash(f"Candidate '{candidate['name']}' transitioned to {new_status}.", "success")
        return redirect(url_for('candidates', job_id=job_id))
        
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/candidates/<int:candidate_id>/details')
def candidate_detail(candidate_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    candidate = conn.execute('''
        SELECT c.*, j.title as job_title, j.description as jd_text
        FROM candidates c JOIN jobs j ON c.job_id = j.id
        WHERE c.id = ?
    ''', (candidate_id,)).fetchone()
    conn.close()
    
    if not candidate:
        flash("Candidate record not found.", "danger")
        return redirect(url_for('dashboard'))
        
    matched_list = [s.strip() for s in (candidate['matched_skills'] or '').split(',') if s.strip()]
    missing_list = [s.strip() for s in (candidate['missing_skills'] or '').split(',') if s.strip()]
    
    return render_template('candidate_detail.html', candidate=candidate,
                           matched_skills=matched_list, missing_skills=missing_list)

@app.route('/jobs/<int:job_id>/export')
def export_csv(job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    job = conn.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()
    query = '''
        SELECT name as "Candidate Name", email as "Email", phone as "Phone", 
               match_score as "Hybrid Match Score (%)", status as "Recruiter Status",
               matched_skills as "Matched Skills", missing_skills as "Skill Gaps",
               uploaded_at as "Evaluated On"
        FROM candidates WHERE job_id = ? ORDER BY match_score DESC
    '''
    df = pd.read_sql_query(query, conn, params=(job_id,))
    conn.close()
    
    clean_title = "".join(c for c in (job['title'] if job else 'job') if c.isalnum() or c in (' ', '_')).rstrip()
    csv_filename = f"ContextHire_{clean_title.replace(' ', '_')}_Rankings.csv"
    csv_path = os.path.join(app.config['EXPORTS_FOLDER'], csv_filename)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    return send_file(csv_path, as_attachment=True, download_name=csv_filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
