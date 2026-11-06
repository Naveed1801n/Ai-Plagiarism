"""
plagiarism_engine.py
Core AI plagiarism detection using IBM Granite + sentence similarity.
"""

import os
import re
import json
import sqlite3
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# ── IBM watsonx.ai (Granite) ──────────────────────────────────
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False

# ── Sentence-Transformers for semantic similarity ─────────────
try:
    from sentence_transformers import SentenceTransformer, util
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

DB_PATH = os.path.join(os.path.dirname(__file__), "plagiarism.db")


class PlagiarismEngine:
    def __init__(self):
        self.model = self._load_granite()
        self.embedder = self._load_embedder()

    # ── Model loaders ─────────────────────────────────────────

    def _load_granite(self):
        """Load IBM Granite model via watsonx.ai."""
        if not WATSONX_AVAILABLE:
            print("[Engine] ibm-watsonx-ai not installed — Granite disabled.")
            return None
        api_key = os.getenv("IBM_WATSONX_API_KEY")
        project_id = os.getenv("IBM_WATSONX_PROJECT_ID")
        url = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        if not api_key or api_key.startswith("your_"):
            print("[Engine] IBM_WATSONX_API_KEY not configured — Granite disabled.")
            return None
        try:
            creds = Credentials(url=url, api_key=api_key)
            model = ModelInference(
                model_id="ibm/granite-13b-instruct-v2",
                credentials=creds,
                project_id=project_id,
                params={
                    "max_new_tokens": 512,
                    "temperature": 0.2,
                    "top_p": 0.9,
                }
            )
            print("[Engine] IBM Granite model loaded successfully.")
            return model
        except Exception as e:
            print(f"[Engine] Granite load error: {e}")
            return None

    def _load_embedder(self):
        """Load sentence-transformer for semantic similarity."""
        if not ST_AVAILABLE:
            print("[Engine] sentence-transformers not installed — similarity disabled.")
            return None
        try:
            embedder = SentenceTransformer("all-MiniLM-L6-v2")
            print("[Engine] Sentence embedder loaded.")
            return embedder
        except Exception as e:
            print(f"[Engine] Embedder load error: {e}")
            return None

    # ── Main analysis entry point ─────────────────────────────

    def analyze(self, text: str, course: str, assignment_title: str) -> dict:
        """
        Full analysis pipeline:
        1. Semantic similarity against existing submissions.
        2. IBM Granite analysis for AI-generation detection & contextual check.
        Returns a result dict with scores and details.
        """
        similarity_matches = self._similarity_check(text, course)
        plagiarism_score = self._compute_plagiarism_score(similarity_matches)
        granite_result = self._granite_analysis(text, assignment_title)
        ai_score = granite_result.get("ai_generated_score", self._heuristic_ai_score(text))
        analysis_text = granite_result.get("analysis", self._fallback_analysis(plagiarism_score, ai_score))

        return {
            "plagiarism_score": round(plagiarism_score, 1),
            "ai_generated_score": round(ai_score, 1),
            "similarity_matches": similarity_matches,
            "granite_analysis": analysis_text,
            "risk_level": self._risk_level(plagiarism_score, ai_score),
        }

    # ── Semantic similarity ────────────────────────────────────

    def _similarity_check(self, text: str, course: str) -> list:
        """Compare text against previous submissions in the same course."""
        matches = []
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, student_name, assignment_title, text FROM submissions WHERE course=?",
                (course,)
            )
            rows = cursor.fetchall()
            conn.close()
        except Exception:
            return matches

        if not rows or self.embedder is None:
            # Fallback: keyword overlap
            for row in rows:
                score = self._keyword_overlap(text, row[3])
                if score > 30:
                    matches.append({
                        "submission_id": row[0],
                        "student_name": row[1],
                        "assignment_title": row[2],
                        "similarity": round(score, 1)
                    })
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            return matches[:5]

        try:
            new_emb = self.embedder.encode(text, convert_to_tensor=True)
            for row in rows:
                old_emb = self.embedder.encode(row[3], convert_to_tensor=True)
                score = float(util.cos_sim(new_emb, old_emb)[0][0]) * 100
                if score > 30:
                    matches.append({
                        "submission_id": row[0],
                        "student_name": row[1],
                        "assignment_title": row[2],
                        "similarity": round(score, 1)
                    })
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            return matches[:5]
        except Exception as e:
            print(f"[Engine] Similarity error: {e}")
            return matches

    def _keyword_overlap(self, text1: str, text2: str) -> float:
        """Simple Jaccard similarity on word sets as fallback."""
        w1 = set(re.findall(r'\b\w{4,}\b', text1.lower()))
        w2 = set(re.findall(r'\b\w{4,}\b', text2.lower()))
        if not w1 or not w2:
            return 0.0
        return len(w1 & w2) / len(w1 | w2) * 100

    def _compute_plagiarism_score(self, matches: list) -> float:
        """Derive overall plagiarism score from top matches."""
        if not matches:
            return 0.0
        top = matches[0]["similarity"]
        # Weighted: top match carries 80%, rest contribute up to 20%
        rest = sum(m["similarity"] for m in matches[1:]) / max(len(matches) - 1, 1) if len(matches) > 1 else 0
        return min(top * 0.8 + rest * 0.2, 100.0)

    # ── IBM Granite analysis ───────────────────────────────────

    def _granite_analysis(self, text: str, assignment_title: str) -> dict:
        """Use IBM Granite to detect AI generation and contextual anomalies."""
        if self.model is None:
            return {}

        prompt = f"""You are an academic integrity expert. Analyze the following student assignment submission.

Assignment Title: {assignment_title}

Submission Text:
\"\"\"
{text[:2000]}
\"\"\"

Please provide:
1. An AI-Generated Score (0-100) indicating how likely this was written by an AI tool (not a human student). Consider: uniform tone, lack of personal voice, overly perfect grammar, generic phrasing.
2. A Plagiarism Concern Level (0-100) based on contextual cues (suspiciously polished, copied structure, inconsistent writing style).
3. A brief 2-3 sentence analysis explaining your findings.

Respond ONLY in this exact JSON format:
{{
  "ai_generated_score": <number>,
  "plagiarism_concern": <number>,
  "analysis": "<your brief analysis here>"
}}"""

        try:
            response = self.model.generate_text(prompt=prompt)
            # Parse JSON from response
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "ai_generated_score": float(parsed.get("ai_generated_score", 0)),
                    "analysis": str(parsed.get("analysis", ""))
                }
        except Exception as e:
            print(f"[Engine] Granite analysis error: {e}")
        return {}

    # ── Heuristic fallbacks ───────────────────────────────────

    def _heuristic_ai_score(self, text: str) -> float:
        """
        Simple heuristic AI-generation score when Granite is unavailable.
        Checks: avg sentence length, vocabulary diversity, filler phrases.
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if not sentences:
            return 0.0

        avg_len = np.mean([len(s.split()) for s in sentences])
        words = re.findall(r'\b\w+\b', text.lower())
        vocab_ratio = len(set(words)) / len(words) if words else 1

        # AI text tends to have longer, uniform sentences and high vocab diversity
        len_score = min((avg_len - 10) / 20 * 50, 50) if avg_len > 10 else 0
        vocab_score = max((vocab_ratio - 0.4) / 0.4 * 50, 0)

        ai_phrases = [
            "it is important to note", "in conclusion", "furthermore",
            "it is worth mentioning", "in summary", "to summarize",
            "it should be noted", "as previously mentioned"
        ]
        phrase_hits = sum(1 for p in ai_phrases if p in text.lower())
        phrase_score = min(phrase_hits * 8, 30)

        return min(len_score + vocab_score * 0.4 + phrase_score, 100)

    def _fallback_analysis(self, plagiarism_score: float, ai_score: float) -> str:
        if plagiarism_score >= 70 and ai_score >= 70:
            return ("High similarity with existing submissions and strong indicators of AI-generated content detected. "
                    "This submission requires immediate instructor review.")
        elif plagiarism_score >= 70:
            return ("High textual similarity with previous submissions detected. "
                    "Possible paraphrasing or direct copying. Instructor review recommended.")
        elif ai_score >= 70:
            return ("Writing patterns strongly suggest AI-generated content. "
                    "Uniform sentence structure, lack of personal voice, and generic phrasing detected.")
        elif plagiarism_score >= 40 or ai_score >= 40:
            return ("Moderate concern detected. Some similarities with existing work or possible AI assistance. "
                    "Instructor should review for context.")
        else:
            return ("No significant plagiarism or AI-generation indicators found. "
                    "Submission appears to be original student work.")

    def _risk_level(self, plagiarism_score: float, ai_score: float) -> str:
        combined = max(plagiarism_score, ai_score)
        if combined >= 70:
            return "HIGH"
        elif combined >= 40:
            return "MEDIUM"
        else:
            return "LOW"
