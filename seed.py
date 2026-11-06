"""
seed.py — Populate the DB with sample data for demo purposes.
Run: python seed.py
"""
import json
import sqlite3
from datetime import datetime, timedelta
from db import init_db, DB_PATH

SAMPLES = [
    {
        "student_name": "Alice Johnson",
        "course": "CS101",
        "assignment_title": "Introduction to Algorithms",
        "text": "An algorithm is a step-by-step procedure for solving a problem. Algorithms are fundamental to computer science and are used in every software application. The efficiency of an algorithm is measured using Big-O notation, which describes how the runtime grows with the size of the input. Common sorting algorithms include bubble sort, merge sort, and quicksort. Binary search is an efficient algorithm for finding elements in sorted arrays with O(log n) complexity.",
        "plagiarism_score": 12.0,
        "ai_generated_score": 18.0,
    },
    {
        "student_name": "Bob Smith",
        "course": "CS101",
        "assignment_title": "Introduction to Algorithms",
        "text": "An algorithm is a step-by-step procedure for solving a problem. Algorithms are fundamental to computer science and are used in every software application. The efficiency of an algorithm is measured using Big-O notation, which describes how the runtime grows with the size of the input. Common sorting algorithms include bubble sort, merge sort, and quicksort. Binary search is an efficient algorithm for finding elements in sorted arrays with O(log n) complexity.",
        "plagiarism_score": 94.0,
        "ai_generated_score": 22.0,
    },
    {
        "student_name": "Carol White",
        "course": "CS101",
        "assignment_title": "Data Structures Overview",
        "text": "It is important to note that data structures are fundamental components of computer science. In summary, arrays provide O(1) access time while linked lists offer dynamic sizing. Furthermore, trees and graphs enable hierarchical and network data representation respectively. It should be noted that hash tables provide average O(1) insertion and lookup. To summarize, understanding these structures is critical for efficient algorithm design and software development in any modern computing environment.",
        "plagiarism_score": 5.0,
        "ai_generated_score": 78.0,
    },
    {
        "student_name": "David Lee",
        "course": "ENG201",
        "assignment_title": "Critical Analysis of Modern Literature",
        "text": "The novel explores themes of identity and belonging through the protagonist's journey. The author uses vivid imagery and metaphor to convey the emotional struggles of growing up in a divided society. Personal experiences with similar challenges gave me a deeper understanding of the text. The use of stream-of-consciousness narrative technique draws the reader into the character's psyche. I found the ending particularly moving because it reminded me of my own community.",
        "plagiarism_score": 8.0,
        "ai_generated_score": 15.0,
    },
    {
        "student_name": "Emma Davis",
        "course": "ENG201",
        "assignment_title": "Critical Analysis of Modern Literature",
        "text": "The novel explores themes of identity and belonging through the protagonist's journey. The author uses vivid imagery and metaphor to convey the emotional struggles of growing up in a divided society. The use of stream-of-consciousness narrative technique draws the reader into the character's psyche. Furthermore, the author's use of symbolism is particularly noteworthy. It is important to note that the ending provides a sense of resolution.",
        "plagiarism_score": 65.0,
        "ai_generated_score": 52.0,
    },
    {
        "student_name": "Frank Chen",
        "course": "MATH301",
        "assignment_title": "Linear Algebra Applications",
        "text": "In conclusion, linear algebra provides the mathematical foundation for machine learning and data science. It is worth mentioning that matrices represent linear transformations in n-dimensional space. Eigenvalues and eigenvectors are particularly important in dimensionality reduction algorithms such as PCA. Furthermore, the dot product and cross product operations have numerous applications in physics and engineering. To summarize, mastery of linear algebra is essential for any aspiring data scientist or machine learning engineer.",
        "plagiarism_score": 10.0,
        "ai_generated_score": 82.0,
    },
    {
        "student_name": "Grace Kim",
        "course": "MATH301",
        "assignment_title": "Linear Algebra Applications",
        "text": "Linear algebra forms the backbone of modern machine learning. Matrices encode linear transformations, and operations like matrix multiplication enable us to compose transformations efficiently. When I worked on implementing gradient descent from scratch, I realized how central these concepts are. Eigendecomposition reveals the intrinsic geometry of data, and PCA leverages this to reduce dimensionality without losing key structure. The singular value decomposition has practical uses in image compression and recommender systems.",
        "plagiarism_score": 7.0,
        "ai_generated_score": 11.0,
    },
]

def seed():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM submissions")
    if cursor.fetchone()[0] > 0:
        print("Database already has data. Skipping seed.")
        conn.close()
        return

    base_time = datetime.utcnow() - timedelta(days=7)
    for i, s in enumerate(SAMPLES):
        submitted_at = (base_time + timedelta(hours=i * 8)).isoformat()
        cursor.execute("""
            INSERT INTO submissions
                (student_name, course, assignment_title, text, plagiarism_score,
                 ai_generated_score, similarity_matches, granite_analysis, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s["student_name"], s["course"], s["assignment_title"], s["text"],
            s["plagiarism_score"], s["ai_generated_score"],
            "[]",
            "Analysis generated by heuristic engine (seed data).",
            submitted_at
        ))

    conn.commit()
    conn.close()
    print(f"Seeded {len(SAMPLES)} sample submissions.")

if __name__ == "__main__":
    seed()
