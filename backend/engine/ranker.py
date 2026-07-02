import os
import sys
import json
import re
import math
import time
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.stdout.reconfigure(encoding='utf-8')

PURE_SERVICES_COMPANIES = {
    'tcs', 'tata consultancy services', 'infosys', 'wipro', 'accenture',
    'cognizant', 'capgemini', 'hcltech', 'hcl technologies', 'tech mahindra', 'ltti', 'l&t technology services'
}

DISQUALIFIED_TITLES = [
    r'\bmarketing manager\b', r'\bcontent writer\b', r'\bgraphic designer\b',
    r'\bhr manager\b', r'\bhuman resources\b', r'\boperations manager\b',
    r'\bsales executive\b', r'\baccount executive\b', r'\bcopywriter\b',
    r'\bmechanical engineer\b', r'\bbrand manager\b', r'\bseo specialist\b'
]

CORE_TECH_KEYWORDS = [
    'embeddings', 'vector search', 'vector database', 'pinecone', 'weaviate',
    'qdrant', 'milvus', 'opensearch', 'elasticsearch', 'faiss', 'sentence-transformers',
    'rag', 'retrieval', 'ranking', 'recommender', 'ndcg', 'mrr', 'map', 'evaluations',
    'python', 'pytorch', 'tensorflow', 'xgboost', 'fastapi', 'learning to rank'
]

def is_honeypot(candidate):
    profile = candidate.get('profile', {})
    yoe = profile.get('years_of_experience', 0)
    
    if yoe > 45 or yoe < 0:
        return True
        
    skills = candidate.get('skills', [])
    expert_zero_duration = sum(1 for s in skills if s.get('proficiency') == 'expert' and s.get('duration_months', 0) == 0)
    if expert_zero_duration >= 3:
        return True
        
    career = candidate.get('career_history', [])
    total_months_claimed = sum(c.get('duration_months', 0) for c in career)
    if yoe > 0 and (total_months_claimed / 12.0) > (yoe * 2.5 + 5):
        return True

    return False

def check_services_only(candidate):
    career = candidate.get('career_history', [])
    if not career:
        return False
    
    services_count = 0
    for job in career:
        comp = str(job.get('company', '')).lower()
        ind = str(job.get('industry', '')).lower()
        if any(sc in comp for sc in PURE_SERVICES_COMPANIES) or 'it services' in ind or 'consulting' in ind:
            services_count += 1
            
    return services_count == len(career)

def evaluate_candidate(candidate, jd_vectorizer, jd_tfidf_vector):
    cid = candidate.get('candidate_id')
    profile = candidate.get('profile', {})
    headline = str(profile.get('headline', '')).lower()
    current_title = str(profile.get('current_title', '')).lower()
    summary = str(profile.get('summary', ''))
    yoe = float(profile.get('years_of_experience', 0.0))
    current_comp = profile.get('current_company', 'Product Tech Co')
    location = profile.get('location', 'India')
    
    for pat in DISQUALIFIED_TITLES:
        if re.search(pat, current_title) or re.search(pat, headline):
            return 0.0, None, None

    if check_services_only(candidate):
        return 0.0, None, None
        
    career_texts = []
    product_company_months = 0
    recent_coding_signal = False
    
    career = candidate.get('career_history', [])
    for idx, job in enumerate(career):
        title = job.get('title', '')
        desc = job.get('description', '')
        comp = job.get('company', '')
        ind = str(job.get('industry', '')).lower()
        dur = job.get('duration_months', 0)
        
        career_texts.append(f"{title} at {comp}: {desc}")
        if 'software' in ind or 'internet' in ind or 'saas' in ind or 'product' in ind or 'technology' in ind:
            product_company_months += dur
            
        if idx == 0 and job.get('is_current'):
            if any(k in title.lower() for k in ['engineer', 'developer', 'scientist', 'applied', 'researcher']):
                recent_coding_signal = True

    skills = candidate.get('skills', [])
    skill_names = [s.get('name', '') for s in skills]
    skill_text = ", ".join(skill_names)
    
    full_text = f"{headline} {summary} {' '.join(career_texts)} Skills: {skill_text}"
    
    # 1. Semantic TF-IDF Fit (35%)
    cand_vec = jd_vectorizer.transform([full_text])
    sem_sim = float(cosine_similarity(cand_vec, jd_tfidf_vector)[0][0])
    
    # 2. Technical Skill Depth (30%)
    tech_matches = []
    full_text_lower = full_text.lower()
    for kw in CORE_TECH_KEYWORDS:
        if kw in full_text_lower:
            tech_matches.append(kw)
            
    skill_score = min(1.0, len(tech_matches) / 8.0)
    
    # 3. Trajectory & Experience Fit (20%)
    if 5.0 <= yoe <= 9.0:
        yoe_score = 1.0
    elif 4.0 <= yoe < 5.0 or 9.0 < yoe <= 11.0:
        yoe_score = 0.85
    elif 3.0 <= yoe < 4.0 or 11.0 < yoe <= 14.0:
        yoe_score = 0.6
    else:
        yoe_score = 0.3
        
    prod_score = min(1.0, product_company_months / 48.0)
    coding_score = 1.0 if recent_coding_signal else 0.7
    
    traj_score = (yoe_score * 0.4) + (prod_score * 0.4) + (coding_score * 0.2)
    
    # 4. Redrob Behavioral Signals (15%)
    signals = candidate.get('redrob_signals', {})
    resp_rate = float(signals.get('recruiter_response_rate', 0.0))
    gh_score = float(signals.get('github_activity_score', 0.0))
    gh_norm = min(1.0, max(0.0, gh_score / 100.0)) if gh_score > 0 else 0.5
    completeness = float(signals.get('profile_completeness_score', 50.0)) / 100.0
    
    beh_score = (resp_rate * 0.5) + (gh_norm * 0.3) + (completeness * 0.2)
    
    # Combined Composite Score
    final_score = (sem_sim * 0.35) + (skill_score * 0.30) + (traj_score * 0.20) + (beh_score * 0.15)
    
    top_skills_str = ", ".join([s.title() for s in tech_matches[:4]]) if tech_matches else "ML & Search skills"
    current_role = profile.get('current_title', 'ML Engineer')
    comp_name = career[0].get('company', current_comp) if career else current_comp
    
    reasoning = (
        f"{current_role} at {comp_name} with {yoe:.1f} yrs exp; "
        f"hands-on in {top_skills_str}; "
        f"recruiter response rate {resp_rate:.2f}."
    )
    
    # Detailed score breakdown dictionary
    details = {
        'candidate_id': cid,
        'current_role': current_role,
        'current_company': comp_name,
        'years_of_experience': yoe,
        'location': location,
        'recruiter_response_rate': resp_rate,
        'github_activity_score': gh_score,
        'score_breakdown': {
            'semantic_fit_pct': round(sem_sim * 100, 1),
            'skill_depth_pct': round(skill_score * 100, 1),
            'trajectory_pct': round(traj_score * 100, 1),
            'behavioral_pct': round(beh_score * 100, 1)
        },
        'matched_skills': [s.title() for s in tech_matches],
        'interview_questions': [
            f"Can you walk us through how you handled embedding drift and index updates for vector retrieval at {comp_name}?",
            f"What evaluation metrics (e.g. NDCG, MAP) did you rely on when testing search ranking offline vs. online?",
            f"How do you decide between fine-tuning an open embedding model vs. using a vector DB like Pinecone/FAISS?"
        ]
    }
    
    return final_score, reasoning, details

def rank_candidates(jsonl_path, jd_text, top_k=100):
    print(f"Loading and vectorizing Job Description...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
    jd_vec = vectorizer.fit_transform([jd_text])
    
    scored_candidates = []
    total_processed = 0
    honeypots_detected = 0
    
    t0 = time.time()
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            total_processed += 1
            line_str = line.strip()
            if not line_str:
                continue
                
            candidate = json.loads(line_str)
            
            if is_honeypot(candidate):
                honeypots_detected += 1
                continue
                
            score, reasoning, details = evaluate_candidate(candidate, vectorizer, jd_vec)
            if score > 0.15:
                scored_candidates.append({
                    'candidate_id': candidate.get('candidate_id'),
                    'score': round(score, 4),
                    'reasoning': reasoning,
                    'details': details
                })
                
    scored_candidates.sort(key=lambda x: (-x['score'], x['candidate_id']))
    top_candidates = scored_candidates[:top_k]
    
    submission_rows = []
    json_export_list = []
    
    for rank_idx, cand in enumerate(top_candidates, start=1):
        submission_rows.append({
            'candidate_id': cand['candidate_id'],
            'rank': rank_idx,
            'score': f"{cand['score']:.4f}",
            'reasoning': cand['reasoning']
        })
        
        # Enriched JSON entry
        item = {
            'rank': rank_idx,
            'candidate_id': cand['candidate_id'],
            'score': cand['score'],
            'reasoning': cand['reasoning'],
            **cand['details']
        }
        json_export_list.append(item)
        
    # Save enriched JSON
    json_path = r'C:\Users\Shubhaan Banerjee\.gemini\antigravity\scratch\talent-rank-ai\ranked_candidates.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_export_list, f, indent=2)
        
    return pd.DataFrame(submission_rows)

if __name__ == '__main__':
    dataset_dir = r'C:\Users\Shubhaan Banerjee\.gemini\antigravity\scratch\talent-rank-ai\dataset\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge'
    jsonl_path = os.path.join(dataset_dir, 'candidates.jsonl')
    
    import docx
    doc = docx.Document(os.path.join(dataset_dir, 'job_description.docx'))
    jd_text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
    
    out_df = rank_candidates(jsonl_path, jd_text, top_k=100)
    
    out_csv = r'C:\Users\Shubhaan Banerjee\.gemini\antigravity\scratch\talent-rank-ai\ranked_candidates.csv'
    out_xlsx = r'C:\Users\Shubhaan Banerjee\.gemini\antigravity\scratch\talent-rank-ai\ranked_candidates.xlsx'
    out_df.to_csv(out_csv, index=False, encoding='utf-8')
    out_df.to_excel(out_xlsx, index=False)
    print(f"Successfully exported enriched CSV, XLSX, and JSON files.")
