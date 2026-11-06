# PlagiaGuard AI 🔍
### AI-Driven Plagiarism Intelligence for Assignments
**IBM Cloud Internship — Problem Statement #10**

---

## Overview
PlagiaGuard AI is an adaptive academic integrity platform that detects plagiarism and AI-generated content using **IBM Granite LLM** via **IBM watsonx.ai**. The system learns from instructor feedback to improve accuracy over time.

---

## Features
| Feature | Description |
|---|---|
| 📝 Student Submission | Submit assignment text for instant analysis |
| 🤖 IBM Granite Analysis | LLM-based AI-generation detection & contextual review |
| 🧠 Semantic Similarity | Neural embeddings vs historical submission corpus |
| 📊 Dashboard | Analytics, score distribution charts, submission history |
| 🚩 Smart Flagging | Risk tiers: LOW / MEDIUM / HIGH |
| 👨‍🏫 Instructor Panel | Review, feedback, and model learning loop |
| 📄 Full Report | Printable report with gauges and similarity breakdown |

---

## Technology Stack
- **IBM Granite** (`ibm/granite-13b-instruct-v2`) via **IBM watsonx.ai**
- **IBM Cloud Lite** services
- Flask 3 (Python backend)
- Sentence Transformers (`all-MiniLM-L6-v2`) for semantic similarity
- Vanilla HTML/CSS/JS frontend (no external frameworks)
- SQLite (local corpus store)

---

## Project Structure
```
plagiarism-ai/
├── app.py                  # Flask app & API routes
├── plagiarism_engine.py    # IBM Granite + similarity engine
├── db.py                   # SQLite schema & helpers
├── seed.py                 # Demo data seeder
├── requirements.txt
├── .env.example
├── static/
│   └── style.css
└── templates/
    ├── index.html          # Landing page
    ├── submit.html         # Student submission
    ├── dashboard.html      # Analytics dashboard
    ├── instructor.html     # Instructor review panel
    └── report.html         # Full submission report
```

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure IBM watsonx.ai
```bash
cp .env.example .env
# Edit .env and add your IBM_WATSONX_API_KEY and IBM_WATSONX_PROJECT_ID
```
Get your API key from: https://cloud.ibm.com/iam/apikeys  
Get your Project ID from: https://dataplatform.cloud.ibm.com

### 3. Seed demo data (optional)
```bash
python seed.py
```

### 4. Run the server
```bash
python app.py
```

Open http://localhost:5000

---

## Pages
| Route | Page |
|---|---|
| `/` | Home / Landing Page |
| `/submit` | Student Assignment Submission |
| `/dashboard` | Analytics Dashboard |
| `/instructor` | Instructor Review Panel |
| `/report/<id>` | Full Submission Report |

---

## API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/submit` | Analyze and save a new submission |
| GET | `/api/submissions` | List all submissions |
| GET | `/api/submission/<id>` | Get full details of one submission |
| POST | `/api/feedback/<id>` | Submit instructor feedback |
| GET | `/api/stats` | Aggregate statistics |
| GET | `/api/courses` | List all courses |

---

## How It Works
1. Student submits assignment text via the web form
2. **Semantic similarity** engine compares against all prior submissions in the same course using neural embeddings
3. **IBM Granite LLM** analyzes the text for AI-generation signatures and contextual anomalies
4. Combined scores produce a **Risk Level** (LOW / MEDIUM / HIGH)
5. Instructors review flagged submissions and submit feedback
6. Feedback is stored in the learning corpus to improve future detection

---

*Built with IBM Granite AI — Problem Statement #10*
