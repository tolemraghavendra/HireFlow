# HireFlow — Agentic AI Recruitment & Interview Intelligence Platform

**From Resume Screening to Evidence-Based Interviews.**

HireFlow does not rank candidates with a single AI score. Instead, it runs an **agentic workflow**
that finds gaps in resume evidence and asks the candidate targeted questions to resolve them:

```
Job Description → Requirement Extraction → Resume Analysis → Evidence Mapping
     → Uncertainty Detection → Targeted Interview Question → Candidate Answer
     → Evidence Update → Human Review
```

Every AI action is logged to an audit trail. Final hiring decisions always stay with the human
recruiter — HireFlow never auto-rejects a candidate or infers protected characteristics.

---

## 1. Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env if you have an OpenAI key (optional, see below)
```

### Frontend

```bash
cd frontend
npm install
```

---

## 2. Configuration (`.env`)

Copy `backend/.env.example` to `backend/.env`:

```
DEMO_MODE=false
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///./hireflow.db
```

- **With an `OPENAI_API_KEY` set:** every agent calls the real OpenAI API.
- **With no key, or `DEMO_MODE=true`:** HireFlow automatically runs in **Demo Mode** — a fully
  deterministic, keyword/heuristic pipeline that produces sensible, explainable results with zero
  external calls. This means the app **always works**, even with no internet access or API
  credits, which is exactly what you want for a live hackathon demo. Every AI response and every
  audit log entry is tagged with whether it came from Demo Mode or a live model call.

Never expose `OPENAI_API_KEY` to the frontend — it is only ever read on the backend.

---

## 3. Database setup

The database (SQLite, `backend/hireflow.db`) is created automatically the first time you start the
backend — no manual migration step needed.

To pre-load the demo role and three fictional candidates (recommended before a live demo):

```bash
cd backend
python seed_demo_data.py
```

This creates the **Python Backend Developer** role with 5 requirements, and three candidates
(Rahul Sharma, Priya Nair, Aditya Rao) with different evidence states already mapped, so you can
jump straight to the Interview Intelligence step without waiting on uploads.

---

## 4. Running the app

**Backend** (from `backend/`):

```bash
uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`. Interactive API docs: `http://localhost:8000/docs`.

**Frontend** (from `frontend/`, in a second terminal):

```bash
npm run dev
```

Runs on `http://localhost:5173` and proxies `/api` requests to the backend automatically (see
`vite.config.js`).

---

## 5. Demo script (~3 minutes)

1. Open `http://localhost:5173`. If you ran `seed_demo_data.py`, the dashboard already shows the
   **Python Backend Developer** role — click into it. Otherwise, click **Create Job**, paste a job
   description (or click "Use sample JD"), and click **Analyze Job Description**. The **JD Analyzer
   Agent** extracts requirements (Python, REST API, SQL, Git, FastAPI) into a table.
2. On the job page, upload Rahul's resume (or open the seeded **Rahul Sharma** candidate directly)
   under **Analyze Candidate**.
3. The **Resume Analyzer Agent** and **Evidence Mapping Agent** run automatically. You land on the
   **Candidate Intelligence** page with the evidence table:
   - Python ✓ EXPLICIT
   - SQL ✓ EXPLICIT
   - Git ✓ EXPLICIT
   - REST API ⚠ UNCLEAR
   - FastAPI ✗ NOT FOUND
4. Click **Validate** next to REST API. The **Validation Agent** explains *why* the evidence is
   unclear and generates a targeted interview question (not a generic one).
5. Type a candidate answer, e.g.:
   > "I built an inventory REST API using Flask with GET, POST, PUT and DELETE endpoints."
6. Click **Analyze Answer**. The **Interview Agent** evaluates the answer and updates
   REST API from **UNCLEAR → EXPLICIT** in real time.
7. Go to **Audit Trail** in the sidebar. Every agent action — JD extraction, resume parsing,
   evidence mapping, question generation, answer analysis — is listed with a timestamp, in order.

---

## 6. Project structure

```
hireflow/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, router wiring
│   │   ├── database/db.py          # SQLAlchemy engine/session
│   │   ├── models/models.py        # ORM tables
│   │   ├── schemas/schemas.py      # Pydantic request/response models
│   │   ├── api/                    # roles, candidates, interviews, audit, dashboard routers
│   │   ├── agents/                 # the 5 agents (see below)
│   │   ├── services/               # llm_client (demo-mode fallback), audit logger, skill KB
│   │   ├── prompts/prompts.py      # system prompts for live-LLM mode
│   │   └── utils/text_extraction.py
│   ├── uploads/                    # uploaded resumes land here
│   ├── seed_demo_data.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Dashboard, CreateJob, JobDetail, CandidateIntelligence,
│   │   │                           # InterviewIntelligence, AuditTrail
│   │   ├── components/             # Layout, StatusBadge, Card, AgentActivityItem, etc.
│   │   ├── services/api.js         # Axios client
│   │   ├── App.jsx / main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 7. The agent architecture

| # | Agent | File | Input | Output |
|---|-------|------|-------|--------|
| 1 | **JD Analyzer** | `agents/jd_agent.py` | Job title + description | Structured requirements (skill, type, priority, description, evidence needed) |
| 2 | **Resume Analyzer** | `agents/resume_agent.py` | Resume text | Factual, page-sourced claims — never invented, never inferring protected attributes |
| 3 | **Evidence Mapper** | `agents/evidence_agent.py` | One requirement + resume text | `EXPLICIT` / `UNCLEAR` / `NOT_FOUND` verdict, evidence snippet, source page, confidence |
| 4 | **Validation Agent** | `agents/validation_agent.py` | Requirement + evidence status | A specific, targeted interview question (never generic) |
| 5 | **Interview Agent** | `agents/interview_agent.py` | Requirement + question + candidate answer | Updated status, evidence, confidence, whether follow-up is still required |

Each agent call is written through `services/llm_client.py`, which calls a real OpenAI model when
`OPENAI_API_KEY` is configured, and **automatically falls back to deterministic Demo Mode** logic
(`services/skill_knowledge.py` + rule-based heuristics inside each agent) if no key is present or
the live call fails for any reason. This is why the "Demo Mode" banner note appears in the audit
trail even when you *do* have a key configured, if a call happens to fail — the app never crashes
mid-demo.

Every agent call writes a row to `audit_logs` via `services/audit.py`, which is what powers both
the Dashboard's "AI Activity" feed and the dedicated Audit Trail page.

---

## 8. How this demonstrates agentic AI (not just "an AI feature")

- **Multi-step, stateful pipeline**: each agent's output becomes the next agent's input
  (JD → resume → evidence → question → answer → updated evidence), and that state is persisted in
  SQLite, not just held in a single prompt.
- **The system takes an action based on uncertainty it detects itself**: when Evidence Mapping
  returns `UNCLEAR` or `NOT_FOUND`, the Validation Agent is invoked *automatically* by the
  workflow logic to close that specific gap — the human only decides whether to send the resulting
  question to the candidate.
- **Evidence updates propagate**: the Interview Agent's verdict overwrites the corresponding
  `candidate_evidence` row, so the same requirement visibly changes status (UNCLEAR → EXPLICIT) as
  a direct, auditable result of an agent action.
- **Full observability**: the Audit Trail is not a log for developers — it's a first-class page a
  recruiter can open to see exactly what each agent did, on what input, with what result.
- **Guardrails are structural, not just prompted**: agents are restricted to three allowed
  statuses, source attribution is required, and the UI can never display a single numeric
  candidate score or an auto-reject action — the architecture enforces "evidence and interview
  intelligence, not a hiring decision."

---

## 9. Safety & scope

HireFlow's agents are instructed, in both live-LLM prompts and demo-mode logic, to:
- Never invent experience the candidate didn't state.
- Never infer gender, age, race, religion, health, disability, or political views.
- Never produce a single ranking score or automatically reject/accept a candidate.

The UI always states: *"HireFlow provides evidence and interview intelligence. Final hiring
decisions remain with the human recruiter."*
