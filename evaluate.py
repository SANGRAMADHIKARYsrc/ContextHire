import numpy as np
from nlp_engine import calculate_hybrid_score

EVAL_JD_TEXT = """
We are seeking an experienced Senior Machine Learning Engineer to design, train, 
and deploy predictive models and scalable LLM/NLP pipelines. 
Key requirements: Strong Python development, hands-on PyTorch or TensorFlow, 
Docker containerization, AWS cloud architecture, CI/CD, and REST APIs.
"""
EVAL_REQUIRED = "python, pytorch, tensorflow, docker, aws, nlp, rest api"

EVAL_RESUMES = [
    {
        "id": 1,
        "name": "Dr. Sarah Chen (Ideal Senior ML Specialist)",
        "text": """
        Senior Machine Learning Engineer with 6 years building production NLP and deep learning systems.
        Proficient in Python, PyTorch, Hugging Face transformers, and scikit-learn.
        Architected cloud inference services on AWS (ECS, Lambda, S3) using Docker containers.
        Implemented automated CI/CD pipelines and high-throughput REST APIs with FastAPI.
        """,
        "ground_truth_relevance": 1
    },
    {
        "id": 2,
        "name": "Marcus Vance (Data Analyst / Junior ML)",
        "text": """
        Data Analyst with 3 years querying relational data using SQL and Python.
        Built basic exploratory data science models using scikit-learn and pandas.
        Familiar with Git and basic Linux scripting. Lacks cloud and container experience.
        """,
        "ground_truth_relevance": 0
    },
    {
        "id": 3,
        "name": "David Ross (Frontend React Developer)",
        "text": """
        Frontend Software Engineer specializing in React, Next.js, TypeScript, and CSS3.
        Built responsive single page applications and state management with Redux.
        Integrated GraphQL and REST APIs. No machine learning or model deployment background.
        """,
        "ground_truth_relevance": 0
    },
    {
        "id": 4,
        "name": "Elena Rostova (Synonym & Dense Vector Match)",
        "text": """
        AI Research Practitioner specialized in neural architectures and natural language understanding.
        Programming expertise in Python. Developed deep learning models and distributed them across
        Amazon Web Services cloud environments inside containerized microservices.
        """,
        "ground_truth_relevance": 1
    }
]

def run_evaluation_suite():
    print("=" * 65)
    print("CONTEXTHIRE HYBRID NLP ENGINE - BENCHMARK REPORT")
    print("=" * 65)
    
    scored_candidates = []
    for cand in EVAL_RESUMES:
        res = calculate_hybrid_score(cand["text"], EVAL_JD_TEXT, EVAL_REQUIRED)
        score = res["score"]
        scored_candidates.append({
            "name": cand["name"],
            "score": score,
            "y_true": cand["ground_truth_relevance"],
            "matched": res["matched_skills"],
            "missing": res["missing_skills"]
        })
        print(f"Candidate: {cand['name']:<42} | Predicted HMS: {score:>5}% | Relevant: {cand['ground_truth_relevance']}")
        print(f"   -> Matched: {', '.join(res['matched_skills']) or 'None'}")
        print(f"   -> Gaps:    {', '.join(res['missing_skills']) or 'None'}")
        print("-" * 65)
        
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    print("\n" + "=" * 65)
    print("SYSTEM RANKING ORDER (PREDICTED)")
    print("=" * 65)
    for rank, cand in enumerate(scored_candidates, 1):
        print(f"#{rank} | {cand['name']:<42} | HMS: {cand['score']}%")
        
    # Classification Metrics (Threshold = 50.0%)
    THRESHOLD = 50.0
    y_pred = [1 if c["score"] >= THRESHOLD else 0 for c in scored_candidates]
    y_true = [c["y_true"] for c in scored_candidates]
    
    tp = sum(1 for p, t in zip(y_pred, y_true) if p == 1 and t == 1)
    fp = sum(1 for p, t in zip(y_pred, y_true) if p == 1 and t == 0)
    fn = sum(1 for p, t in zip(y_pred, y_true) if p == 0 and t == 1)
    tn = sum(1 for p, t in zip(y_pred, y_true) if p == 0 and t == 0)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # Mean Reciprocal Rank (MRR)
    first_rel_rank = next((idx + 1 for idx, c in enumerate(scored_candidates) if c["y_true"] == 1), 0)
    mrr = 1.0 / first_rel_rank if first_rel_rank > 0 else 0.0
    
    print("\n" + "=" * 65)
    print("SCIENTIFIC EVALUATION METRICS")
    print("=" * 65)
    print(f"Precision @ 50% Threshold: {precision * 100:.1f}%  (Prevents recruiter false positives)")
    print(f"Recall @ 50% Threshold:    {recall * 100:.1f}%  (Captures all relevant candidates)")
    print(f"F1-Score:                  {f1 * 100:.1f}%  (Harmonic mean of precision & recall)")
    print(f"Mean Reciprocal Rank (MRR):{mrr:.3f}   (1.000 = Top relevant candidate placed at Rank #1)")
    print("=" * 65)

if __name__ == "__main__":
    run_evaluation_suite()
