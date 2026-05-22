from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import json
import sqlite3
import os
import re
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env.txt"))

OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        client = None

app = Flask(__name__)
app.secret_key = 'apta_secret_key_2024'

with open(os.path.join(BASE_DIR, "quizzes", "quiz_data.json"), encoding="utf-8") as f:
    quiz_data = json.load(f)

KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.txt")


def init_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, "knowledge.db"))
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        ref_id TEXT PRIMARY KEY,
        name TEXT,
        gender TEXT,
        age INTEGER,
        profession TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        ref_id TEXT,
        topic TEXT,
        pre_score INTEGER,
        final_score INTEGER,
        explanation TEXT,
        chat_time INTEGER DEFAULT 0,
        ai_interactions INTEGER DEFAULT 0,
        improvement INTEGER DEFAULT 0
    )
    """)
    for col, col_type in [
        ("chat_time", "INTEGER DEFAULT 0"),
        ("ai_interactions", "INTEGER DEFAULT 0"),
        ("improvement", "INTEGER DEFAULT 0"),
    ]:
        try:
            cur.execute(f"ALTER TABLE results ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


init_db()


def require_session(*keys):
    for key in keys:
        if key not in session:
            return redirect(url_for("user_info"))
    return None


def get_topic_questions(topic):
    return quiz_data.get(topic, [])


def score_quiz(questions, form):
    return sum(form.get(f"q{i}") == q["answer"] for i, q in enumerate(questions))


def format_learning_time(seconds):
    seconds = int(seconds or 0)
    if seconds < 60:
        return f"{seconds} sec", seconds
    minutes = round(seconds / 60, 1)
    if minutes < 60:
        return f"{minutes} min", minutes
    hours = round(minutes / 60, 1)
    return f"{hours} hr", minutes


def get_performance_label(pre, final, time_min):
    improvement = final - pre
    if improvement > 0 and time_min >= 5:
        return "Excellent – You improved!", "success"
    if improvement > 0:
        return "Good – Score improved", "primary"
    if improvement == 0 and time_min >= 10:
        return "Stable – Keep practicing", "info"
    if improvement < 0:
        return "Needs focus – Review the topic", "warning"
    return "Getting started – Try more AI study", "secondary"


def load_knowledge_chunks():
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        return []
    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        return [c.strip() for c in f.read().split("\n\n") if c.strip()]


def search_knowledge_base(user_msg, topic, k=2):
    chunks = load_knowledge_chunks()
    if not chunks:
        return []
    words = set(re.findall(r"[a-zA-Z0-9]+", user_msg.lower()))
    topic_words = set(re.findall(r"[a-zA-Z0-9]+", topic.lower()))
    words |= topic_words
    scored = []
    for chunk in chunks:
        chunk_words = set(re.findall(r"[a-zA-Z0-9]+", chunk.lower()))
        score = len(words & chunk_words)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:k]]


def get_fallback_response(user_msg, topic):
    matches = search_knowledge_base(user_msg, topic, k=2)
    if matches:
        answer = "\n\n".join(matches)
        note = "\n\n_(Using built-in knowledge base. Add a valid OpenAI API key in .env for full GPT answers.)_"
        return f"**{topic} – Tutor answer:**\n\n{answer}{note}"
    return (
        f"I'm your **{topic}** tutor. You asked: \"{user_msg}\"\n\n"
        f"Try asking about specific concepts in {topic} — for example: loops, functions, variables, or syntax.\n\n"
        "_(Built-in tutor mode — add a valid OPENAI_API_KEY in a `.env` file for ChatGPT answers.)_"
    )


def get_openai_reply(user_msg, topic):
    if not client:
        return None, "OpenAI not configured"

    matches = search_knowledge_base(user_msg, topic, k=3)
    system_prompt = (
        f"You are a helpful AI tutor teaching: '{topic}'. "
        "Explain clearly with short examples for a diploma student."
    )
    if matches:
        system_prompt += "\n\nUse this reference material:\n" + "\n".join(matches)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ],
        max_tokens=500,
        timeout=45
    )
    return response.choices[0].message.content, None


@app.route("/", methods=["GET", "POST"])
def user_info():
    if request.method == "POST":
        session.clear()
        session['ref_id'] = request.form['ref_id'].strip()
        session['name'] = request.form['name'].strip()
        session['gender'] = request.form['gender']
        session['age'] = int(request.form['age'])
        session['profession'] = request.form['profession']
        session['ai_interactions'] = 0
        session['chat_time'] = 0

        conn = sqlite3.connect(os.path.join(BASE_DIR, "knowledge.db"))
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)", (
            session['ref_id'], session['name'], session['gender'],
            session['age'], session['profession']
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("select_topic"))
    return render_template("user_info.html", step=1)


@app.route("/select_topic", methods=["GET", "POST"])
def select_topic():
    guard = require_session('ref_id', 'name')
    if guard:
        return guard

    if request.method == "POST":
        topic = request.form['topic']
        if topic not in quiz_data:
            return render_template(
                "select_topic.html",
                topics=list(quiz_data.keys()),
                error="Please select a valid topic.",
                step=2
            )
        session['topic'] = topic
        session.pop('pre_score', None)
        session.pop('final_score', None)
        session.pop('explanation', None)
        session['ai_interactions'] = 0
        session['chat_time'] = 0
        return redirect(url_for("quiz"))
    return render_template("select_topic.html", topics=list(quiz_data.keys()), step=2)


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    guard = require_session('ref_id', 'topic')
    if guard:
        return guard

    topic = session.get("topic")
    questions = get_topic_questions(topic)

    if request.method == "POST":
        session["pre_score"] = score_quiz(questions, request.form)
        session.modified = True
        return redirect(url_for("write_explanation"))
    return render_template("quiz.html", topic=topic, questions=questions, step=3)


@app.route("/write_explanation", methods=["GET", "POST"])
def write_explanation():
    guard = require_session('ref_id', 'topic', 'pre_score')
    if guard:
        return guard

    if request.method == "POST":
        session["explanation"] = request.form["explanation"].strip()
        return redirect(url_for("chat"))
    return render_template(
        "write_explanation.html",
        topic=session.get("topic"),
        pre_score=session.get("pre_score", 0),
        total=len(get_topic_questions(session.get("topic"))),
        step=4
    )


@app.route("/chat")
def chat():
    guard = require_session('ref_id', 'topic', 'pre_score', 'explanation')
    if guard:
        return guard
    return render_template(
        "chat.html",
        topic=session.get("topic"),
        name=session.get("name"),
        ai_ready=bool(client),
        step=5
    )


@app.route("/chat_api", methods=["POST"])
def chat_api():
    if 'topic' not in session:
        return jsonify({"error": "Session expired. Please login again."}), 401

    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return jsonify({"error": "Please enter a message."}), 400

    topic = session.get("topic", "Python")
    reply = None
    used_fallback = False

    try:
        reply, err = get_openai_reply(user_msg, topic)
        if reply is None:
            raise Exception(err or "OpenAI unavailable")
    except Exception:
        reply = get_fallback_response(user_msg, topic)
        used_fallback = True

    session['ai_interactions'] = session.get('ai_interactions', 0) + 1
    session.modified = True
    return jsonify({"response": reply, "fallback": used_fallback})


@app.route("/final_quiz", methods=["GET", "POST"])
def final_quiz():
    guard = require_session('ref_id', 'topic', 'pre_score', 'explanation')
    if guard:
        return guard

    topic = session.get("topic")
    questions = get_topic_questions(topic)

    if request.method == "POST":
        if 'chat_time' in request.form and not any(
            key.startswith('q') for key in request.form if key != 'chat_time'
        ):
            session['chat_time'] = int(request.form.get('chat_time', 0))
            return render_template("final_quiz.html", topic=topic, questions=questions, step=6)

        session["final_score"] = score_quiz(questions, request.form)
        session.modified = True
        return redirect(url_for("dashboard"))

    if 'chat_time' not in session:
        session['chat_time'] = 0
    return render_template("final_quiz.html", topic=topic, questions=questions, step=6)


@app.route("/dashboard")
def dashboard():
    guard = require_session('ref_id', 'topic', 'pre_score', 'final_score')
    if guard:
        return guard

    topic = session.get("topic")
    questions = get_topic_questions(topic)
    total = len(questions) or 5
    pre = session.get("pre_score", 0)
    final = session.get("final_score", 0)
    improvement = final - pre
    time_display, time_min = format_learning_time(session.get("chat_time", 0))
    ai_count = session.get("ai_interactions", 0)
    perf_label, perf_class = get_performance_label(pre, final, time_min)

    conn = sqlite3.connect(os.path.join(BASE_DIR, "knowledge.db"))
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO results
           (ref_id, topic, pre_score, final_score, explanation, chat_time, ai_interactions, improvement)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session['ref_id'], topic, pre, final,
            session.get("explanation", ""),
            session.get("chat_time", 0), ai_count, improvement
        )
    )
    conn.commit()
    conn.close()

    pre_pct = round((pre / total) * 100) if total else 0
    final_pct = round((final / total) * 100) if total else 0

    return render_template(
        "dashboard.html",
        name=session['name'],
        topic=topic,
        pre=pre,
        final=final,
        total=total,
        pre_pct=pre_pct,
        final_pct=final_pct,
        improvement=improvement,
        explanation=session.get("explanation", ""),
        time_spent_display=time_display,
        time_min=time_min,
        ai_count=ai_count,
        perf_label=perf_label,
        perf_class=perf_class,
        improved="Yes" if improvement > 0 else ("No" if improvement < 0 else "Same"),
        step=7
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
