import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
from plagiarism_engine import PlagiarismEngine
from db import init_db, get_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
CORS(app)

# Initialize DB and engine on startup
init_db()
engine = PlagiarismEngine()


# ─────────────────────────── PAGES ────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit")
def submit_page():
    return render_template("submit.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/instructor")
def instructor_page():
    return render_template("instructor.html")

@app.route("/report/<int:submission_id>")
def report_page(submission_id):
    return render_template("report.html", submission_id=submission_id)


# ─────────────────────────── API ──────────────────────────────

@app.route("/api/submit", methods=["POST"])
def api_submit():
    """Student submits an assignment."""
    data = request.get_json()
    student_name = data.get("student_name", "").strip()
    course = data.get("course", "").strip()
    assignment_title = data.get("assignment_title", "").strip()
    text = data.get("text", "").strip()

    if not all([student_name, course, assignment_title, text]):
        return jsonify({"error": "All fields are required."}), 400
    if len(text) < 50:
        return jsonify({"error": "Assignment text must be at least 50 characters."}), 400

    # Run plagiarism analysis
    result = engine.analyze(text, course, assignment_title)

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO submissions
            (student_name, course, assignment_title, text, plagiarism_score,
             ai_generated_score, similarity_matches, granite_analysis, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_name, course, assignment_title, text,
        result["plagiarism_score"],
        result["ai_generated_score"],
        json.dumps(result["similarity_matches"]),
        result["granite_analysis"],
        datetime.utcnow().isoformat()
    ))
    db.commit()
    submission_id = cursor.lastrowid
    db.close()

    return jsonify({"submission_id": submission_id, **result})


@app.route("/api/submissions", methods=["GET"])
def api_list_submissions():
    """List all submissions (instructor dashboard)."""
    course_filter = request.args.get("course", "")
    db = get_db()
    cursor = db.cursor()
    if course_filter:
        cursor.execute(
            "SELECT id, student_name, course, assignment_title, plagiarism_score, "
            "ai_generated_score, submitted_at FROM submissions WHERE course=? ORDER BY submitted_at DESC",
            (course_filter,)
        )
    else:
        cursor.execute(
            "SELECT id, student_name, course, assignment_title, plagiarism_score, "
            "ai_generated_score, submitted_at FROM submissions ORDER BY submitted_at DESC"
        )
    rows = cursor.fetchall()
    db.close()
    submissions = [
        {
            "id": r[0], "student_name": r[1], "course": r[2],
            "assignment_title": r[3], "plagiarism_score": r[4],
            "ai_generated_score": r[5], "submitted_at": r[6]
        }
        for r in rows
    ]
    return jsonify(submissions)


@app.route("/api/submission/<int:sid>", methods=["GET"])
def api_get_submission(sid):
    """Get full details of a single submission."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM submissions WHERE id=?", (sid,))
    row = cursor.fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    keys = ["id","student_name","course","assignment_title","text",
            "plagiarism_score","ai_generated_score","similarity_matches",
            "granite_analysis","instructor_feedback","flag","submitted_at"]
    sub = dict(zip(keys, row))
    sub["similarity_matches"] = json.loads(sub["similarity_matches"] or "[]")
    return jsonify(sub)


@app.route("/api/feedback/<int:sid>", methods=["POST"])
def api_feedback(sid):
    """Instructor submits feedback on a submission."""
    data = request.get_json()
    feedback = data.get("feedback", "").strip()
    flag = data.get("flag", False)
    if not feedback:
        return jsonify({"error": "Feedback cannot be empty."}), 400

    db = get_db()
    db.execute(
        "UPDATE submissions SET instructor_feedback=?, flag=? WHERE id=?",
        (feedback, 1 if flag else 0, sid)
    )
    # Store feedback in learning corpus
    db.execute(
        "INSERT INTO feedback_corpus (submission_id, feedback, flag, created_at) VALUES (?,?,?,?)",
        (sid, feedback, 1 if flag else 0, datetime.utcnow().isoformat())
    )
    db.commit()
    db.close()
    return jsonify({"status": "ok"})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Aggregate statistics for dashboard."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM submissions")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM submissions WHERE plagiarism_score >= 70")
    high_plagiarism = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM submissions WHERE ai_generated_score >= 70")
    high_ai = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM submissions WHERE flag=1")
    flagged = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(plagiarism_score) FROM submissions")
    avg_plag = cursor.fetchone()[0] or 0
    cursor.execute(
        "SELECT course, COUNT(*) as cnt FROM submissions GROUP BY course ORDER BY cnt DESC LIMIT 5"
    )
    courses = [{"course": r[0], "count": r[1]} for r in cursor.fetchall()]
    db.close()
    return jsonify({
        "total": total,
        "high_plagiarism": high_plagiarism,
        "high_ai": high_ai,
        "flagged": flagged,
        "avg_plagiarism_score": round(avg_plag, 1),
        "top_courses": courses
    })


@app.route("/api/courses", methods=["GET"])
def api_courses():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT course FROM submissions ORDER BY course")
    courses = [r[0] for r in cursor.fetchall()]
    db.close()
    return jsonify(courses)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
