# ContextHire: Context-Aware Candidate Screening & ATS Resume Compatibility Engine

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://contexthire.onrender.com)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0-black?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

**Live Application URL**: [https://contexthire.onrender.com](https://contexthire.onrender.com)

ContextHire is a full-stack recruitment intelligence and resume analysis platform built with Python (Flask), SQLite, and Natural Language Processing. The project addresses the limitations of traditional Applicant Tracking Systems (ATS) that rely solely on rigid keyword matching, often rejecting qualified candidates due to vocabulary mismatches or synonyms.

The system implements a **Hybrid Match Scoring (HMS)** algorithm combining lexical matching (TF-IDF), dense vector semantic embeddings (Sentence-BERT), and direct technical competency entity extraction. It caters to two distinct user journeys:
1. **Hiring Teams & Recruiters**: Job position configuration, bulk PDF resume parsing, candidate scoring/ranking, skill gap visualization, and CSV reporting.
2. **Individual Candidates & Students**: Self-service ATS resume audit, compatibility scoring (0–100), formatting checks, action verb analysis, and targeted keyword improvement suggestions.

---

## Motivation & Problem Statement

Most standard ATS parsers use basic boolean searches or token-based keyword counting. This leads to two common failure modes:
- **False Negatives**: A candidate who writes *"built distributed microservices in AWS"* might be filtered out if the job description specifically asks for *"cloud infrastructure experience"*, despite having the requisite skill set.
- **Keyword Stuffing**: Applicants can artificially inflate their match score by pasting white-font keywords or repetitive lists into their resume without demonstrating actual context or measurable impact.

ContextHire solves this by analyzing candidate resumes across multiple dimensions:
- **Lexical Overlap (25%)**: Measures exact terminology and n-gram overlap via TF-IDF cosine similarity.
- **Semantic Understanding (35%)**: Generates dense 384-dimensional vector embeddings using the `all-MiniLM-L6-v2` Sentence-BERT transformer model to capture contextual meaning and synonym relationships.
- **Competency Intersection (40%)**: Uses NLP pattern matching and regular expressions to extract concrete technical entities (languages, frameworks, tools) and calculate direct skill coverage.

---

## System Architecture

```
                                  [ Candidate Resume (PDF) ]
                                              │
                                              ▼
                                 [ Layout-Aware Text Parser ]
                                  (pdfplumber + Regex Filters)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
         [ 25% Lexical Engine ]     [ 35% Semantic Engine ]   [ 40% Competency Match ]
           TF-IDF Vectorizer         Sentence Transformers       Skill Entity Regex
           Cosine Similarity          (all-MiniLM-L6-v2)         Intersection & Gaps
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                                 [ Hybrid Match Score (HMS) ]
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
          [ Recruiter Dashboard ]                          [ Individual ATS Checker ]
           - Ranked Candidate Pool                          - Overall Score (0-100)
           - Score Distribution Chart                       - Formatting & Action Verbs
           - Skill Gap Radar & Details                      - Missing Keywords Feedback
           - Export Pipeline to CSV                         - Job Description Gap Check
```

---

## Core Features

### 1. Recruiter & Hiring Team Workspace
- **Role-Based Authentication**: Secure registration and login separating recruiters from individual candidates.
- **Job Position Management**: Define job title, department, seniority level, description, and required core skills.
- **Automated Resume Parsing**: Drag-and-drop PDF resume ingestion with automatic extraction of candidate name, email, phone number, and raw text.
- **Candidate Ranking Table**: Ranked list sorted by match score with status workflow (`Applied`, `Shortlisted`, `Rejected`).
- **Interactive Analytics**: Chart.js data visualizations showing candidate score distribution and a 3-axis radar chart (lexical, semantic, skill overlap).
- **Data Export**: Export candidate evaluation rosters directly to CSV for offline review.

### 2. Individual Candidate Resume Auditor
- **ATS Compatibility Score**: Calculates an objective 0–100 score categorized into *Excellent*, *Good*, *Needs Improvement*, or *Low*.
- **Multi-Factor Breakdown**:
  - *Formatting & Structure*: Detects presence of standard resume sections (Education, Experience, Skills, Projects) and contact details.
  - *Action Verb Density*: Identifies strong impact verbs (e.g., *Engineered*, *Optimized*, *Architected*) vs. passive phrases.
  - *Quantifiable Metrics*: Flags whether bullet points contain measurable business outcomes and numbers.
- **Actionable Feedback**: Side-by-side display of identified strengths and specific improvement recommendations.
- **Missing Keywords**: Highlights relevant industry competencies missing from the resume.

---

## Tech Stack

- **Backend**: Python 3.10+, Flask 3.0
- **Database**: SQLite3 (relational schema with users, jobs, candidates tables)
- **Natural Language Processing**:
  - `sentence-transformers` (`all-MiniLM-L6-v2` lightweight embedding model)
  - `scikit-learn` (`TfidfVectorizer`, cosine similarity)
  - `nltk` (tokenization, stopword filtering)
- **PDF Extraction**: `pdfplumber` (layout-preserving text extraction)
- **Frontend**: Semantic HTML5, Vanilla CSS3 (custom design system with CSS custom properties), JavaScript (ES6)
- **Data Visualization**: Chart.js 4.x
- **Icons & Typography**: Remix Icon, Inter font family

---

## Project Structure

```
ContextHire/
├── app.py                  # Main Flask application, routing, auth, database migrations
├── nlp_engine.py           # NLP pipelines: TF-IDF, SBERT embeddings, entity extraction
├── evaluate.py             # Evaluation benchmark script (Precision, Recall, F1, MRR)
├── schema.sql              # Database schema definition
├── database.db             # Local SQLite database (created on first run)
├── requirements.txt        # Python package dependencies
├── .env                    # Environment variables (secret key, configs)
├── .gitignore              # Ignored files (virtual environment, cache, uploads)
├── ContextHire.png         # Project logo asset
├── static/
│   ├── css/
│   │   ├── style.css       # Core design system tokens, dashboard, tables, auth styling
│   │   └── landing.css     # Homepage styles
│   ├── js/
│   │   └── charts.js       # Chart.js initialization (bar distribution, radar breakdown)
│   └── img/
│       ├── ContextHire.png # Cropped branding asset
│       └── ContextHire.svg # Vector icon
└── templates/
    ├── base.html           # Master layout with sidebar, universal nav, and flash alerts
    ├── landing.html        # Public homepage
    ├── login.html          # Login portal
    ├── register.html       # Role-selection registration
    ├── dashboard.html      # Recruiter analytics dashboard
    ├── job_profiles.html   # Job opening configuration
    ├── candidates.html     # Candidate pipeline & resume uploader
    ├── candidate_detail.html # Individual candidate dossier & radar chart
    └── ats_checker.html    # Individual ATS resume evaluation tool
```

---

## Getting Started

### Prerequisites
- Python 3.10 or higher installed
- `pip` package manager
- `git`

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SANGRAMADHIKARYsrc/ContextHire.git
   cd ContextHire
   ```

2. **Create and activate a virtual environment**:
   - Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - macOS / Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the root directory (or use default configuration):
   ```env
   SECRET_KEY=your_development_secret_key_here
   FLASK_ENV=development
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```
   *Note: On first run, the system will download the `all-MiniLM-L6-v2` model weights (~90MB) and automatically initialize the SQLite database schema.*

6. **Open in browser**:
   Navigate to `http://127.0.0.1:5000`

---

## Running the Benchmark Evaluation

An offline benchmark suite is provided in `evaluate.py` to test the matching engine against ground-truth relevance annotations:

```bash
python evaluate.py
```

This runs test resumes against a reference machine learning job description and outputs:
- Predicted Hybrid Match Score (HMS) per candidate
- Ranking order comparison against ground truth
- Classification metrics: **Precision**, **Recall**, **F1-Score** at 50% cutoff threshold
- Ranking metric: **Mean Reciprocal Rank (MRR)**

---

## Database Schema Overview

The database uses SQLite with three relational tables:
- **`users`**: Stores user authentication credentials (`id`, `username`, `email`, `password_hash`, `account_type`, `created_at`). `account_type` differentiates `hiring_team` from `individual`.
- **`jobs`**: Stores configured job postings (`id`, `title`, `description`, `required_skills`, `experience_level`, `department`, `created_at`).
- **`candidates`**: Stores parsed resume records associated with a job profile (`id`, `job_id`, `name`, `email`, `phone`, `match_score`, `matched_skills`, `missing_skills`, `status`, `raw_text`, `uploaded_at`).

---

## Security & Design Considerations

- **Password Hashing**: Passwords stored using PBKDF2 with SHA-256 via Werkzeug security utilities.
- **Route Authorization**: Route guards protect recruiter dashboards and job management endpoints from unauthenticated or individual accounts.
- **File Sanitization**: Resumes must be valid `.pdf` files. Filenames are secured and processed using temporary storage paths.
- **Fail-Safe Semantic Scoring**: If Hugging Face Hub is unreachable or dense embedding models cannot load, the system gracefully falls back to normalized lexical TF-IDF matching to prevent downtime.

---

## Future Improvements

- Support for additional document formats (`.docx`, `.txt`).
- Fine-tuning custom domain-specific embeddings for medical and legal recruitment.
- Multi-user team collaboration with interview feedback scoring.
- Automated email notifications to candidates upon status change.
