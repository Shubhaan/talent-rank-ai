# TalentRank AI — Context-Aware Candidate Discovery & Ranking Engine

> **Redrob Hackathon — Intelligent Candidate Discovery & Ranking Challenge**  
> **Repository:** [https://github.com/shubhaan/talent-rank-ai](https://github.com/shubhaan/talent-rank-ai)  
> **Hosted Sandbox:** [https://huggingface.co/spaces/shubhaan/talent-rank-ai](https://huggingface.co/spaces/shubhaan/talent-rank-ai)

---

## 📌 Executive Overview
Recruiters review hundreds of profiles but frequently miss high-potential talent because traditional keyword filters match superficial word occurrences rather than true role fit.

**TalentRank AI** is an intelligent candidate evaluation engine that reads job descriptions and evaluates candidate profiles across **four core dimensions**:
1. **Context-Aware Semantic Search**: Vector & TF-IDF similarity parsing candidate career trajectories against production search, retrieval, and vector database requirements.
2. **Technical Skill Depth & Recency**: Quantifying hands-on expertise in embeddings, vector databases (Pinecone, FAISS, Milvus, Qdrant), evaluation metrics (NDCG, MAP), and production Python code.
3. **Career Trajectory & Company Quality**: Filtering out pure IT consulting/services firms and non-technical titles (Marketing Managers, Content Writers, HR Managers), while prioritizing product company experience and active coding in the last 18 months.
4. **Redrob Behavioral Signals**: Factoring in recruiter response rate, profile completeness, and GitHub activity score to prioritize active, reachable talent.

---

## 🏆 Benchmark Performance Results

| Metric | Measured Result | Challenge Constraint / Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Dataset Pool** | 100,000 Candidates | 100,000 Candidates (`candidates.jsonl`) | Completed |
| **Execution Runtime** | **85.2 Seconds** | < 5 Minutes (CPU Only) | **PASSED** |
| **Honeypot Trap Rate** | **0.0%** in Top 100 | < 10% Disqualification Threshold | **PASSED** |
| **Output Data Rows** | **Exactly 100 Rows** | Exactly 100 Data Rows | **PASSED** |
| **Format Validation** | `Submission is valid.` | `validate_submission.py` Pass | **PASSED** |

---

## 🛠️ Quickstart & Reproduction Command

### Prerequisites
- Python 3.11+
- 16 GB RAM (CPU Execution)

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/shubhaan/talent-rank-ai.git
cd talent-rank-ai

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Single Command Submission Reproduction
To reproduce `ranked_candidates.csv` directly from the dataset:
```bash
python backend/engine/ranker.py
```

### 3. Validate Submission Output
```bash
python dataset/[PUB]\ India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py ranked_candidates.csv
```

### 4. Generate Presentation Deck PDF
```bash
python backend/engine/deck_generator.py
```

---

## 📁 Repository Directory Structure

```
talent-rank-ai/
├── backend/
│   └── engine/
│       ├── ranker.py            # Core candidate ranking & multi-stage scoring engine
│       ├── deck_generator.py    # ReportLab presentation PDF generator (approach_deck.pdf)
│       └── jd_parser.py        # Job description context parser
├── frontend/
│   └── index.html               # Interactive recruiter web dashboard
├── dataset/                     # Extracted challenge dataset directory
├── ranked_candidates.csv        # Primary submission file (100 rows, 100% valid)
├── ranked_candidates.json       # JSON export of top candidate recommendations
├── approach_deck.pdf            # Slide deck presentation converted to PDF
├── submission_metadata.yaml     # Official submission metadata declaration
└── requirements.txt             # Project dependencies
```

---

## 🎯 Submission Deliverables Summary
1. **GitHub Repository Code**: Clean, modular, fully reproducible codebase.
2. **Approach Deck PDF**: `approach_deck.pdf` detailing problem statement, architectural pipeline, scoring formula, and benchmark results.
3. **Ranked Candidate CSV**: `ranked_candidates.csv` formatted and verified per challenge specification.
