"""
Seed HireFlow with a demo job role and three fictional candidates so the
hackathon demo works instantly, with no uploads required.

Usage (from backend/):
    python seed_demo_data.py
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.database.db import Base, engine, SessionLocal
from app.models.models import Role, Requirement, Candidate, CandidateEvidence, AuditLog

Base.metadata.create_all(bind=engine)
db = SessionLocal()

JOB_DESCRIPTION = (
    "We are looking for a Python Backend Developer to join our engineering team. "
    "You will design and build REST APIs, work with relational databases, and "
    "collaborate using Git-based workflows. Required: Python, REST API design, SQL. "
    "Preferred: FastAPI, Git, Docker. 2+ years of experience preferred."
)

if db.query(Role).filter(Role.title == "Python Backend Developer").first():
    print("Demo data already exists. Skipping seed.")
    db.close()
    sys.exit(0)

role = Role(title="Python Backend Developer", description=JOB_DESCRIPTION)
db.add(role)
db.commit()
db.refresh(role)

req_specs = [
    ("Python", "Required", "High", "Strong hands-on Python programming ability.", "Evidence of building real Python applications."),
    ("REST API", "Required", "High", "Ability to design and build RESTful APIs.", "A described REST API project with endpoints/methods."),
    ("SQL", "Required", "Medium", "Comfort working with relational databases.", "Evidence of querying/designing SQL databases."),
    ("Git", "Preferred", "Medium", "Version control using Git-based workflows.", "GitHub/GitLab project links or explicit Git mention."),
    ("FastAPI", "Preferred", "Medium", "Experience with the FastAPI framework specifically.", "Explicit mention of FastAPI in projects."),
]
requirements = {}
for skill, type_, priority, desc, evid in req_specs:
    r = Requirement(role_id=role.id, skill=skill, type=type_, priority=priority,
                     description=desc, evidence_needed=evid)
    db.add(r)
    db.commit()
    db.refresh(r)
    requirements[skill] = r

db.add(AuditLog(agent="JD Analyzer", action="Extracted 5 requirements (Demo Mode)",
                 role_id=role.id, output_text=str(list(requirements.keys()))))
db.commit()


def add_candidate(name, email, evidence_map, note_offset_minutes):
    c = Candidate(role_id=role.id, name=name, email=email, resume_path="",
                  resume_text=f"[Demo candidate: {name}]",
                  created_at=datetime.utcnow() - timedelta(minutes=note_offset_minutes))
    db.add(c)
    db.commit()
    db.refresh(c)

    for skill, (status, evidence_text, source, confidence) in evidence_map.items():
        db.add(CandidateEvidence(
            candidate_id=c.id, requirement_id=requirements[skill].id,
            status=status, evidence_text=evidence_text, source_page=source, confidence=confidence,
        ))
    db.commit()

    flagged = [s for s, v in evidence_map.items() if v[0] != "EXPLICIT"]
    db.add(AuditLog(agent="Resume Analyzer", action="Parsed candidate resume (Demo Mode)",
                     candidate_id=c.id, role_id=role.id))
    db.add(AuditLog(
        agent="Evidence Mapper",
        action=f"Mapped 5 requirements" + (f" \u2014 needs validation: {', '.join(flagged)}" if flagged else " \u2014 all explicit"),
        candidate_id=c.id, role_id=role.id, status="WARNING" if flagged else "SUCCESS",
    ))
    db.commit()
    return c


# Candidate 1: Rahul Sharma (the flagship demo candidate)
add_candidate(
    "Rahul Sharma", "rahul.sharma@example.com",
    {
        "Python": ("EXPLICIT", "Developed backend applications using Python for 2 years.", "Resume page 2", 0.93),
        "SQL": ("EXPLICIT", "Used MySQL to design and query relational databases in a course project.", "Resume page 2", 0.9),
        "Git": ("EXPLICIT", "Maintains multiple projects on GitHub with regular commits.", "Resume page 3", 0.88),
        "REST API": ("UNCLEAR", "Developed backend applications using Flask.", "Resume page 2", 0.6),
        "FastAPI": ("NOT_FOUND", "No supporting evidence found in the resume.", "\u2014", 0.1),
    },
    note_offset_minutes=40,
)

# Candidate 2: Priya Nair (strong all-around, one gap)
add_candidate(
    "Priya Nair", "priya.nair@example.com",
    {
        "Python": ("EXPLICIT", "Built data pipelines and internal tools in Python.", "Resume page 1", 0.91),
        "REST API": ("EXPLICIT", "Designed and shipped a REST API with GET/POST/PUT endpoints using Django REST Framework.", "Resume page 1", 0.95),
        "SQL": ("EXPLICIT", "Wrote complex SQL queries against a PostgreSQL warehouse.", "Resume page 2", 0.9),
        "Git": ("EXPLICIT", "Uses Git and GitHub for all team projects.", "Resume page 2", 0.85),
        "FastAPI": ("NOT_FOUND", "No supporting evidence found in the resume.", "\u2014", 0.15),
    },
    note_offset_minutes=25,
)

# Candidate 3: Aditya Rao (earlier-career, several gaps)
add_candidate(
    "Aditya Rao", "aditya.rao@example.com",
    {
        "Python": ("EXPLICIT", "Completed academic projects using Python and Pandas.", "Resume page 1", 0.8),
        "REST API": ("NOT_FOUND", "No supporting evidence found in the resume.", "\u2014", 0.1),
        "SQL": ("UNCLEAR", "Resume mentions 'database' coursework without specifying SQL.", "Resume page 1", 0.5),
        "Git": ("UNCLEAR", "Resume mentions version control coursework but not Git specifically.", "Resume page 1", 0.45),
        "FastAPI": ("NOT_FOUND", "No supporting evidence found in the resume.", "\u2014", 0.1),
    },
    note_offset_minutes=10,
)

print("Demo data seeded successfully:")
print(f"  Role: {role.title} (id={role.id})")
print("  Candidates: Rahul Sharma, Priya Nair, Aditya Rao")
db.close()
