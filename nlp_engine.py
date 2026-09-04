import os
import re
import pdfplumber
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize sentence-transformers if available
TRANSFORMERS_AVAILABLE = False
semantic_model = None
try:
    from sentence_transformers import SentenceTransformer
    semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    TRANSFORMERS_AVAILABLE = True
except Exception as e:
    print(f"Notice: Running with high-performance Lexical fallback ({e})")

# Download NLTK stopwords safely to private path
nltk_dir = os.path.expanduser('~/nltk_data')
os.makedirs(nltk_dir, exist_ok=True)
if nltk_dir not in nltk.data.path:
    nltk.data.path.insert(0, nltk_dir)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('stopwords', download_dir=nltk_dir, quiet=True)
    except Exception:
        pass

# Expanded Industry-Grade Skill Corpus (150+ competencies)
SKILLS_DB = [
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "golang", "rust", "ruby", "php", 
    "swift", "kotlin", "scala", "dart", "shell", "bash", "powershell", "r", "matlab",
    
    # Web & Frameworks
    "react", "react.js", "next.js", "vue", "vue.js", "angular", "node.js", "express", "express.js",
    "flask", "django", "fastapi", "spring", "spring boot", "asp.net", "laravel", "rails", "svelte",
    "html", "html5", "css", "css3", "tailwind css", "bootstrap", "sass", "graphql", "rest api", "grpc",
    
    # AI / Machine Learning / Data Science
    "machine learning", "deep learning", "nlp", "natural language processing", "computer vision", 
    "llm", "large language models", "rag", "langchain", "llamaindex", "transformers", "hugging face",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", "scipy", "opencv",
    "data science", "data analysis", "prompt engineering", "fine-tuning", "bert", "gpt",
    
    # Cloud, DevOps & Containers
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", "terraform", "ansible",
    "ci/cd", "jenkins", "github actions", "gitlab ci", "helm", "linux", "nginx", "prometheus", "grafana",
    "microservices", "serverless", "lambda", "cloudformation",
    
    # Databases & Caching
    "sql", "mysql", "postgresql", "postgres", "sqlite", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "neo4j", "oracle", "mariadb", "snowflake", "bigquery",
    
    # Tools, Methodologies & Testing
    "git", "github", "gitlab", "jira", "agile", "scrum", "kanban", "unit testing", "pytest", 
    "selenium", "cypress", "playwright", "tdd", "system design", "data structures", "algorithms"
]

# Sort skills by length descending to match multi-word phrases first
SKILLS_DB_SORTED = sorted(SKILLS_DB, key=len, reverse=True)

def extract_text_from_pdf(pdf_path):
    """
    Extracts structured text from a resume PDF using multi-tier fallback:
    1. pdfplumber layout engine
    2. pdfplumber raw text stream
    3. pypdf extraction
    """
    extracted_text = ""
    # Tier 1: pdfplumber layout engine
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = None
                try:
                    text = page.extract_text(layout=True)
                except Exception:
                    pass
                if not text or not text.strip():
                    try:
                        text = page.extract_text()
                    except Exception:
                        pass
                if text:
                    extracted_text += text + "\n"
    except Exception as e:
        print(f"pdfplumber extraction notice: {e}")

    # Tier 2: pypdf fallback if empty
    if not extracted_text.strip():
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        except Exception as e:
            print(f"pypdf extraction notice: {e}")

    return extracted_text.strip()

def clean_text(text):
    """
    Normalize text: lowercases, cleans noise, removes stopwords.
    Preserves key tokens like c++, c#, .net.
    """
    if not text:
        return ""
    text = text.lower()
    # Normalize common abbreviations
    text = re.sub(r'\bnode(?:\.js)?\b', 'node.js', text)
    text = re.sub(r'\breact(?:\.js)?\b', 'react', text)
    text = re.sub(r'\bvue(?:\.js)?\b', 'vue', text)
    
    # Preserve technical chars +, #, .
    text = re.sub(r'[^a-z0-9\s\.\-\+#]', ' ', text)
    words = text.split()
    
    try:
        stop_words = set(stopwords.words('english'))
        cleaned = [w for w in words if w not in stop_words and len(w) > 1]
    except Exception:
        cleaned = [w for w in words if len(w) > 1]
        
    return " ".join(cleaned)

def extract_skills(text):
    """
    Scans candidate/JD text and isolates recognized technical competencies.
    Longer tokens matched first to prevent sub-phrase cannibalization.
    """
    found_skills = set()
    cleaned = f" {text.lower()} "
    
    for skill in SKILLS_DB_SORTED:
        pattern = r'(?<![a-z0-9])' + re.escape(skill) + r'(?![a-z0-9])'
        if re.search(pattern, cleaned):
            found_skills.add(skill)
            # Remove matched to avoid overlapping sub-tokens
            cleaned = re.sub(pattern, ' ', cleaned)
            
    return sorted(list(found_skills))

def extract_candidate_name(text, filename=""):
    """
    Heuristic to extract candidate name.
    1. Checks the first few non-empty lines for 2-3 word capitalized sequence.
    2. Falls back to sanitized filename.
    """
    if text:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:5]:
            # Disregard lines containing emails or phone numbers
            if '@' in line or re.search(r'\d{3}', line) or 'resume' in line.lower() or 'curriculum' in line.lower():
                continue
            words = line.split()
            if 1 < len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
                return " ".join(words)
                
    if filename:
        clean = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        clean = re.sub(r'(?i)resume|cv|final|v\d+', '', clean).strip()
        if clean:
            return clean.title()
            
    return "Applicant"

def extract_contact_info(text):
    """
    Parses email, phone, and optional LinkedIn/GitHub handles.
    """
    email = "Not Found"
    phone = "Not Found"
    
    if not text:
        return email, phone
        
    # Email regex
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        email = email_match.group(0)
        
    # International & national phone regex
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        phone = phone_match.group(0)
        
    return email, phone

def calculate_hybrid_score(resume_text, jd_text, jd_required_skills=""):
    """
    Hybrid Match Score (HMS):
    25% TF-IDF Cosine Similarity
    35% Dense Vector Semantic Embeddings (Sentence Transformers or Lexical Fallback)
    40% Direct Skill Overlap
    """
    cleaned_resume = clean_text(resume_text)
    cleaned_jd = clean_text(jd_text)
    
    if not cleaned_resume:
        return {"score": 0.0, "matched_skills": [], "missing_skills": []}
        
    # 1. Lexical Similarity (TF-IDF + Cosine)
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        tfidf_mat = vectorizer.fit_transform([cleaned_resume, cleaned_jd])
        lexical_score = float(cosine_similarity(tfidf_mat[0], tfidf_mat[1])[0][0])
    except Exception:
        lexical_score = 0.0

    # 2. Semantic Embedding Similarity
    if TRANSFORMERS_AVAILABLE and semantic_model:
        try:
            embeddings = semantic_model.encode([resume_text, jd_text], show_progress_bar=False)
            semantic_score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
            semantic_score = max(0.0, min(semantic_score, 1.0))
        except Exception as e:
            semantic_score = lexical_score
    else:
        semantic_score = lexical_score

    # 3. Skill Overlap & Gap Analysis
    resume_skills = set(extract_skills(resume_text))
    
    if isinstance(jd_required_skills, str):
        required_skills = {s.strip().lower() for s in jd_required_skills.split(',') if s.strip()}
    else:
        required_skills = {s.strip().lower() for s in jd_required_skills if s}
        
    if not required_skills:
        required_skills = set(extract_skills(jd_text))

    if required_skills:
        matched = resume_skills.intersection(required_skills)
        missing = required_skills - resume_skills
        skill_score = len(matched) / len(required_skills)
    else:
        matched = resume_skills
        missing = set()
        skill_score = 1.0

    # Weighted Composite Score
    composite = (0.25 * lexical_score) + (0.35 * semantic_score) + (0.40 * skill_score)
    final_score = round(min(100.0, max(0.0, composite * 100)), 1)

    return {
        "score": final_score,
        "matched_skills": sorted(list(matched)),
        "missing_skills": sorted(list(missing)),
        "all_extracted_skills": sorted(list(resume_skills)),
        "breakdown": {
            "lexical": round(lexical_score * 100, 1),
            "semantic": round(semantic_score * 100, 1),
            "skills": round(skill_score * 100, 1)
        }
    }

def evaluate_individual_resume(raw_text, job_description=""):
    """
    Evaluates an individual's resume for ATS compatibility:
    - Formatting & structure
    - Technical and domain skills
    - Action verbs and readability
    - Measurable impact metrics
    - Optional comparison with a job description
    """
    if not raw_text:
        return None

    lower_text = raw_text.lower()
    words = raw_text.split()
    word_count = len(words)

    # 1. Formatting checks
    contact_email, contact_phone = extract_contact_info(raw_text)
    has_contact = bool(contact_email or contact_phone)
    
    sections = ['experience', 'education', 'skills', 'projects', 'summary']
    detected_sections = [s for s in sections if s in lower_text]
    section_score = (len(detected_sections) / len(sections)) * 100
    
    # Word count penalty if too brief or too excessively verbose
    if 350 <= word_count <= 1100:
        length_score = 100
    elif 200 <= word_count < 350 or 1100 < word_count <= 1600:
        length_score = 75
    else:
        length_score = 50

    format_score = round(0.4 * (100 if has_contact else 40) + 0.4 * section_score + 0.2 * length_score, 1)

    # 2. Skills Analysis
    extracted_skills = extract_skills(raw_text)
    skill_count = len(extracted_skills)
    if skill_count >= 10:
        skills_score = 95.0
    elif skill_count >= 6:
        skills_score = 82.0
    elif skill_count >= 3:
        skills_score = 65.0
    else:
        skills_score = 45.0

    # 3. Impact & Action Verbs
    action_verbs = [
        "architected", "engineered", "spearheaded", "developed", "designed",
        "implemented", "optimized", "built", "launched", "scaled", "led",
        "managed", "accelerated", "slashed", "increased", "decreased", "automated"
    ]
    matched_verbs = [v for v in action_verbs if re.search(r'\b' + v + r'\b', lower_text)]
    metrics_matches = re.findall(r'\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?[kmb]?|\b\d+\+?\s*(?:users|clients|teams|projects|services)\b', lower_text)
    
    readability_score = round(min(100.0, len(matched_verbs) * 12 + len(metrics_matches) * 10 + 35), 1)

    # 4. Keywords score
    keywords_score = round(min(100.0, skill_count * 7 + (85 if len(extracted_skills) > 4 else 45)), 1)

    # 5. Strengths and Opportunities
    strengths = []
    opportunities = []

    if has_contact:
        strengths.append(f"Clear contact information provided ({contact_email or 'Email detected'})")
    else:
        opportunities.append("Add clear direct contact information (Email and Phone) in header")

    if len(detected_sections) >= 4:
        strengths.append(f"Well-structured standard section hierarchy ({', '.join(detected_sections[:3]).title()})")
    else:
        opportunities.append("Ensure distinct standard section headings: Experience, Education, Skills, and Projects")

    if len(extracted_skills) >= 6:
        strengths.append(f"Identified {len(extracted_skills)} recognized competencies including: {', '.join(extracted_skills[:4])}")
    else:
        opportunities.append("Expand dedicated skills section with specific technical tools and frameworks")

    if len(metrics_matches) >= 2:
        strengths.append("Contains quantified impact statements (percentages, metrics, or financial indicators)")
    else:
        opportunities.append("Add measurable outcomes to bullet points (e.g. 'improved speed by 25%' or 'served 10k users')")

    if len(matched_verbs) >= 3:
        strengths.append(f"Strong action-driven language utilized ({', '.join(matched_verbs[:3])})")
    else:
        opportunities.append("Replace passive phrases ('responsible for', 'worked on') with strong action verbs (Engineered, Led, Optimized)")

    # 6. Job Description matching if supplied
    job_match = None
    missing_keywords = []
    if job_description.strip():
        matching = calculate_hybrid_score(raw_text, job_description)
        job_match = matching['score']
        missing_keywords = matching['missing_skills'][:8]
    else:
        # Suggest complementary industry keywords not yet present
        standard_suggestions = ["git", "ci/cd", "rest api", "unit testing", "agile", "docker", "python", "sql"]
        missing_keywords = [s for s in standard_suggestions if s not in extracted_skills][:5]

    # Overall ContextHire Resume Compatibility Score
    overall_score = round(0.25 * format_score + 0.35 * skills_score + 0.25 * readability_score + 0.15 * keywords_score, 1)

    if overall_score >= 80:
        category = "Excellent"
    elif overall_score >= 60:
        category = "Good"
    elif overall_score >= 40:
        category = "Needs Improvement"
    else:
        category = "Low"

    return {
        "score": overall_score,
        "category": category,
        "word_count": word_count,
        "formatting_score": format_score,
        "keywords_score": keywords_score,
        "skills_score": skills_score,
        "readability_score": readability_score,
        "extracted_skills": extracted_skills,
        "missing_keywords": missing_keywords,
        "strengths": strengths,
        "opportunities": opportunities,
        "job_match": job_match
    }
