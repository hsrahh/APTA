# 🧠 APTA — AI Personal Tutor

**APTA** (AI Personal Tutor Application) is a web-based learning platform built for diploma-level students. It measures prior knowledge, guides personalized study with an AI tutor, re-tests learning with a final quiz, and presents a performance dashboard with improvement metrics suitable for machine learning analysis.

🔗 **Repository:** [github.com/hsrahh/APTA](https://github.com/hsrahh/APTA)

---

## 📌 Project Overview

Traditional e-learning often gives the same content to every student. APTA adapts the journey to each learner by:

1. Testing what they already know (initial quiz)
2. Capturing their own understanding in writing
3. Letting them study the topic in depth with an AI assistant
4. Measuring improvement with a final quiz
5. Summarizing results on an interactive dashboard

The system stores session data in **SQLite** and supports **ML-based prediction** of whether a student improved (via `Model Prediction.ipynb` and optional Power BI reporting).

---

## 🚀 Key Features

| Feature | Description |
|--------|-------------|
| 🔐 **Student Login** | Register with ID, name, age, gender, and profession |
| 🎯 **Topic Selection** | Choose from 7 Python topics (loops, functions, OOP, etc.) |
| 📋 **Initial Quiz** | 5 MCQs per topic to assess prior knowledge |
| ✍️ **Reflection Step** | Student writes what they understood from the quiz |
| 🤖 **AI Tutor Chat** | OpenAI GPT-powered chat scoped to the selected topic |
| 📚 **Knowledge Fallback** | Built-in answers from `knowledge_base.txt` if API is unavailable |
| 🧪 **Final Quiz** | Same topic, post-study — measures improvement |
| 📊 **Performance Dashboard** | Scores, %, improvement, AI study time, chat count, chart |
| 🧠 **ML Ready** | Exports features for Random Forest / other classifiers |
| 🎨 **Modern UI** | Clean blue & white theme with 7-step progress indicator |

---

## 🏗️ Application Flow

```
Login → Select Topic → Initial Quiz → Write What You Learned
    → Study with AI Tutor (timed) → Final Quiz → Performance Dashboard
```

| Step | Page | What happens |
|------|------|----------------|
| 1 | User Login | Student details saved to SQLite |
| 2 | Select Topic | Topic stored in session |
| 3 | Initial Quiz | Pre-score calculated (0–5) |
| 4 | Write Explanation | Student reflection saved |
| 5 | AI Chat | Timed study; AI interaction count tracked |
| 6 | Final Quiz | Post-score calculated |
| 7 | Dashboard | Results + chart + ML-friendly metrics stored |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js |
| **Backend** | Python 3, Flask |
| **AI** | OpenAI GPT-3.5-turbo (v1 API) + local knowledge base fallback |
| **Database** | SQLite (`knowledge.db`) |
| **Vector Search** (optional) | FAISS, Sentence Transformers (`vector_store.py`) |
| **ML / Analytics** | scikit-learn, Pandas, Matplotlib, Seaborn (`Model Prediction.ipynb`) |
| **BI Dashboard** | Power BI (`APTA_Dashboard.pbix`) |

---

## 📚 Available Topics

Each topic includes **5 multiple-choice questions**:

- Python basic  
- Loops in Python  
- Functions  
- Data structures  
- Conditional Statement  
- OOPs  
- File operations  

Questions are defined in `quizzes/quiz_data.json`.

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.9 or higher  
- pip  
- (Optional) OpenAI API key for full GPT responses  

### 1. Clone the repository

```bash
git clone https://github.com/hsrahh/APTA.git
cd APTA
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and add your OpenAI key:

```bash
copy .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

> **Note:** Without a valid API key, the app still works using the **built-in knowledge base tutor** (ideal for demos and viva).

### 4. (Optional) Build vector index for RAG

```bash
python build_knowledge.py
```

This creates `vector.index` from `data/knowledge_base.txt` for enhanced AI context.

### 5. Run the application

```bash
python app.py
```

Open in browser: **http://127.0.0.1:5000**

---

## 📊 Machine Learning Model

The notebook `Model Prediction.ipynb` trains models to predict whether a student **improved** after using the tutor.

### Input features

| Feature | Source |
|---------|--------|
| Initial quiz score | `pre_score` |
| Final quiz score | `final_score` |
| Time spent with AI | `chat_time` (seconds) |
| AI interaction count | `ai_interactions` |
| Explanation length | Student reflection text |
| Improvement score | `final_score - pre_score` |

### Target label

`Improved` → **Yes / No**

### Models used

- Random Forest Classifier *(primary)*  
- Decision Tree  
- Linear Regression  
- SVM  

### Example

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
```

Results can be visualized in **Power BI** using `APTA_Dashboard.pbix`.

---

## 📈 Web Dashboard (In-App)

The Flask dashboard displays:

- Initial vs final quiz scores (count and %)
- Score improvement (+/− marks)
- Time spent with AI tutor
- Number of AI chat messages
- Performance summary label (e.g. *Excellent – You improved!*)
- Bar chart (Chart.js) for quick visual comparison

---

## 📁 Project Structure

```bash
APTA/
│
├── app.py                      # Main Flask application (routes, DB, AI chat)
├── build_knowledge.py          # Build FAISS vector index from knowledge base
├── vector_store.py             # Embedding + FAISS search utilities
├── requirements.txt            # Python dependencies
├── .env.example                # API key template (copy to .env)
├── .gitignore                  # Excludes secrets & local DB from Git
│
├── data/
│   └── knowledge_base.txt      # Tutor reference content (fallback + RAG)
│
├── quizzes/
│   └── quiz_data.json          # MCQs for all topics
│
├── templates/                  # HTML pages (Jinja2)
│   ├── base.html               # Shared layout & blue/white theme
│   ├── user_info.html          # Login
│   ├── select_topic.html
│   ├── quiz.html               # Initial quiz
│   ├── write_explanation.html
│   ├── chat.html               # AI tutor + timer
│   ├── final_quiz.html
│   └── dashboard.html
│
├── chunks.json                 # Text chunks for vector search
├── knowledge.db                # SQLite (auto-created; not in Git)
├── Model Prediction.ipynb      # ML model training & evaluation
├── APTA_Dashboard.pbix         # Power BI dashboard (optional)
└── README.md
```

---

## 🔧 Challenges Solved During Development

| Problem | Solution |
|---------|----------|
| App returned to login after quiz (especially score 0) | Session check uses `key in session` instead of falsy value check |
| Quiz answers not reaching server | Direct POST form instead of hidden JavaScript form |
| AI chat: "Could not reach server" | OpenAI v1 API + improved fetch error handling |
| Invalid / missing API key | Automatic fallback to `knowledge_base.txt` search |
| Slow chat (vector model load) | Lazy import; lightweight text search for fallback mode |
| Inconsistent UI | Unified blue & white Bootstrap theme + step progress bar |
| Secrets on GitHub | `.gitignore` for `.env`, `.env.txt`, `knowledge.db` |

---

## 🗄️ Database Schema

**users** — `ref_id`, `name`, `gender`, `age`, `profession`

**results** — `ref_id`, `topic`, `pre_score`, `final_score`, `explanation`, `chat_time`, `ai_interactions`, `improvement`

---

## 👨‍💻 Author

**Harsh Joil** — Diploma project (APTA)  
GitHub: [@hsrahh](https://github.com/hsrahh)

---

## 📄 License

This project was created for academic purposes. Feel free to reference with credit.

---

## 🙏 Acknowledgments

- OpenAI for GPT API  
- Flask & Bootstrap communities  
- scikit-learn for ML components  

---

> *Built with ❤️ for personalized learning — assess, teach, measure, improve.*
