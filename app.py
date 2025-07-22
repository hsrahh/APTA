from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import json
import sqlite3
import os
from dotenv import load_dotenv
import openai
from vector_store import query_index  # 🔁 for custom knowledge search

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Load .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load quiz data from file
with open("quizzes/quiz_data.json") as f:
    quiz_data = json.load(f)

# Initialize database
def init_db():
    conn = sqlite3.connect("knowledge.db")
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
        explanation TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def user_info():
    if request.method == "POST":
        session['ref_id'] = request.form['ref_id']
        session['name'] = request.form['name']
        session['gender'] = request.form['gender']
        session['age'] = request.form['age']
        session['profession'] = request.form['profession']

        conn = sqlite3.connect("knowledge.db")
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)", (
            session['ref_id'], session['name'], session['gender'], session['age'], session['profession']
        ))
        conn.commit()
        conn.close()

        return redirect("/select_topic")
    return render_template("user_info.html")

@app.route("/select_topic", methods=["GET", "POST"])
def select_topic():
    if request.method == "POST":
        session['topic'] = request.form['topic']
        return redirect("/quiz")
    return render_template("select_topic.html", topics=list(quiz_data.keys()))

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    topic = session.get("topic")
    questions = quiz_data.get(topic, [])
    if request.method == "POST":
        score = sum(request.form.get(f"q{i}") == q["answer"] for i, q in enumerate(questions))
        session["pre_score"] = score
        return redirect("/write_explanation")
    return render_template("quiz.html", topic=topic, questions=questions)

@app.route("/write_explanation", methods=["GET", "POST"])
def write_explanation():
    if request.method == "POST":
        session["explanation"] = request.form["explanation"]
        return redirect("/chat")
    return render_template("write_explanation.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/chat_api", methods=["POST"])
def chat_api():
    user_msg = request.json["message"]

    try:
        # 🔍 Attempt to search custom knowledge base
        top_chunks = query_index(user_msg, k=3)
        context = "\n".join(top_chunks)

        system_prompt = f"""
You are a helpful Python tutor. Only use the information provided below to answer the user's question.

Knowledge Base:
{context}
"""
    except FileNotFoundError:
        # Fallback if vector.index is missing
        system_prompt = "You are a helpful Python tutor. Please answer the user's question using your general knowledge."

    # 🧠 Generate response using OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
    )

    return jsonify({"response": response["choices"][0]["message"]["content"]})

@app.route("/final_quiz", methods=["GET", "POST"])
def final_quiz():
    topic = session.get("topic")
    questions = quiz_data.get(topic, [])

    if request.method == "POST":
        # If chat_time was sent from chat.html, store it
        if 'chat_time' in request.form:
            session['chat_time'] = int(request.form['chat_time'])
            # Show the quiz now (don't score yet!)
            return render_template("final_quiz.html", topic=topic, questions=questions)

        # Else this POST is submitting quiz answers
        score = sum(request.form.get(f"q{i}") == q["answer"] for i, q in enumerate(questions))
        session["final_score"] = score
        return redirect("/dashboard")

    return render_template("final_quiz.html", topic=topic, questions=questions)

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("knowledge.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO results VALUES (?, ?, ?, ?, ?)", (
        session['ref_id'],
        session['topic'],
        session.get("pre_score", 0),
        session.get("final_score", 0),
        session.get("explanation", "")
    ))
    conn.commit()
    conn.close()

    time_spent_sec = session.get("chat_time", 0)
    time_spent_min = round(time_spent_sec / 60)
    time_spent_display = f"{time_spent_min} min"

    return render_template("dashboard.html",
        name=session['name'],
        topic=session['topic'],
        pre=session.get("pre_score", 0),
        final=session.get("final_score", 0),
        explanation=session.get("explanation", ""),
        time_spent=time_spent_min,
        time_spent_display=time_spent_display
    )

if __name__ == "__main__":
    app.run(debug=True)
