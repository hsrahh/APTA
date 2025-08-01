from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import json
import sqlite3
import os
from vector_store import query_index  

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Simple rule-based responses for common Python questions
PYTHON_RESPONSES = {
    "print": "The print() function is used to output text to the console. Example: print('Hello, World!')",
    "Hello": "Hello , How can i help you?",
    "variable": "Variables in Python are containers for storing data values. Example: x = 5",
    "function": "Functions are reusable blocks of code. Use 'def' to define them. Example: def greet(): print('Hello')",
    "loop": "Loops repeat code. 'for' loops iterate over sequences, 'while' loops repeat while condition is True.",
    "list": "Lists are ordered collections of items. Example: my_list = [1, 2, 3]",
    "dictionary": "Dictionaries store key-value pairs. Example: my_dict = {'name': 'John', 'age': 30}",
    "string": "Strings are sequences of characters. Example: text = 'Hello World'",
    "integer": "Integers are whole numbers. Example: number = 42",
    "float": "Floats are decimal numbers. Example: pi = 3.14",
    "boolean": "Booleans are True or False values. Example: is_valid = True",
    "if": "Use 'if' statements for conditional logic. Example: if x > 0: print('Positive')",
    "else": "Use 'else' with 'if' for alternative actions. Example: if x > 0: print('Positive') else: print('Negative')",
    "elif": "Use 'elif' for multiple conditions. Example: if x > 0: print('Positive') elif x < 0: print('Negative')",
    "import": "Use 'import' to include modules. Example: import math",
    "class": "Classes are blueprints for creating objects. Example: class Person: pass",
    "method": "Methods are functions that belong to objects. Example: my_list.append(5)",
    "module": "Modules are Python files containing functions and variables. Example: import random",
    "package": "Packages are directories containing multiple modules.",
    "exception": "Exceptions handle errors. Use try/except blocks. Example: try: x = 1/0 except: print('Error')",
    "file": "Use 'open()' to work with files. Example: with open('file.txt', 'r') as f: content = f.read()",
    "syntax": "Python syntax uses indentation (4 spaces) to define code blocks instead of braces.",
    "indentation": "Python uses indentation (typically 4 spaces) to define blocks of code instead of braces.",
    "comment": "Use # for single-line comments. Example: # This is a comment",
    "docstring": "Docstrings document functions. Use triple quotes. Example: '''This is a docstring'''",
    "return": "Use 'return' to send values back from functions. Example: def add(a, b): return a + b",
    "parameter": "Parameters are variables in function definitions. Example: def greet(name): print('Hello', name)",
    "argument": "Arguments are values passed to functions. Example: greet('John')",
    "default": "Default parameters have preset values. Example: def greet(name='World'): print('Hello', name)",
    "lambda": "Lambda functions are small anonymous functions. Example: add = lambda x, y: x + y",
    "list comprehension": "List comprehensions create lists from expressions. Example: squares = [x**2 for x in range(5)]",
    "generator": "Generators yield values one at a time. Example: def count(): yield 1; yield 2",
    "decorator": "Decorators modify functions. Example: @property def name(self): return self._name",
    "context manager": "Context managers handle setup/cleanup. Example: with open('file.txt') as f: pass",
    "iterator": "Iterators allow looping over objects. Example: for item in my_list: print(item)",
    "recursion": "Recursion is when a function calls itself. Example: def factorial(n): return n * factorial(n-1) if n > 1 else 1",
    "algorithm": "Algorithms are step-by-step procedures for solving problems.",
    "data structure": "Data structures organize and store data efficiently (lists, dictionaries, sets, etc.).",
    "object oriented": "Object-oriented programming uses classes and objects to organize code.",
    "inheritance": "Inheritance allows classes to inherit attributes from other classes.",
    "polymorphism": "Polymorphism allows objects to take multiple forms.",
    "encapsulation": "Encapsulation bundles data and methods that work on that data within a single unit.",
    "abstraction": "Abstraction hides complex implementation details and shows only necessary features."
}

# Load quiz data from file
with open("quizzes/quiz_data.json") as f:
    quiz_data = json.load(f)

# Load final quiz data from file
with open("quizzes/final_quiz_data.json") as f:
    final_quiz_data = json.load(f)

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

def get_chatbot_response(user_msg):
    """Simple rule-based chatbot that works without any API"""
    user_msg_lower = user_msg.lower()
    
    # First, try to get relevant information from the knowledge base
    try:
        top_chunks = query_index(user_msg, k=2)
        if top_chunks:
            return f"Based on the knowledge base:\n\n{top_chunks[0]}"
    except Exception as e:
        print(f"Error accessing knowledge base: {e}")
    
    # Check for specific Python keywords and concepts
    for keyword, response in PYTHON_RESPONSES.items():
        if keyword in user_msg_lower:
            return response
    
    # Handle common question patterns
    if "what is" in user_msg_lower:
        if "python" in user_msg_lower:
            return "Python is a high-level, interpreted programming language known for its simplicity and readability. It's great for beginners and widely used in web development, data science, AI, and automation."
        elif "programming" in user_msg_lower:
            return "Programming is the process of creating instructions for computers to follow. It involves writing code in programming languages to solve problems and create software applications."
    
    if "how to" in user_msg_lower:
        if "start" in user_msg_lower or "begin" in user_msg_lower:
            return "To start programming in Python:\n1. Install Python from python.org\n2. Use a text editor or IDE like VS Code\n3. Write your first program: print('Hello, World!')\n4. Run it and see the output!"
        elif "learn" in user_msg_lower:
            return "To learn Python effectively:\n1. Start with basics (variables, functions, loops)\n2. Practice with small projects\n3. Read documentation and tutorials\n4. Join coding communities\n5. Build real-world projects"
    
    if "hello" in user_msg_lower or "hi" in user_msg_lower:
        return "Hello! I'm your Python tutor. Ask me anything about Python programming!"
    
    if "help" in user_msg_lower:
        return "I can help you with Python programming! Try asking about:\n- Python basics (variables, functions, loops)\n- Data structures (lists, dictionaries)\n- Object-oriented programming\n- File handling\n- And much more!"
    
    # Default response
    return "I'm a Python tutor chatbot! I can help you with Python programming concepts. Try asking about specific topics like 'print()', 'variables', 'functions', 'loops', or 'lists'. You can also ask 'What is Python?' or 'How to start programming?'"

@app.route("/chat_api", methods=["POST"])
def chat_api():
    user_msg = request.json["message"]
    response = get_chatbot_response(user_msg)
    return jsonify({"response": response})

@app.route("/final_quiz", methods=["GET", "POST"])
def final_quiz():
    topic = session.get("topic")
    questions = final_quiz_data.get(topic, [])  # Use final quiz data instead

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
