````markdown
# 🧠 AI Personal Tutor

An AI-powered personalized tutor application designed to assess a student's knowledge, provide customized learning, and measure improvement using quizzes, interactive explanations, and machine learning analysis.

## 🚀 Features

- 🔐 User Login & Signup
- 🎯 Topic selection for learning
- 📋 Initial quiz to gauge prior knowledge
- ✍️ Space for students to write what they learned
- 🤖 AI explanations for weak concepts (OpenAI integration)
- 💬 Chat interface with AI Tutor
- 🧪 Final quiz to evaluate improvement
- 📊 Dashboard showing learning progress and performance
- 🧠 Machine Learning model to predict student improvement

## 🏗️ App Flow

1. **User Registration**
2. **Topic Selection**
3. **Initial Quiz (4–5 MCQs)**
4. **Student writes what they learned**
5. **AI analyzes weak areas and explains**
6. **Chat with AI for deeper understanding**
7. **Final Quiz**
8. **Dashboard view with insights**
9. **Machine Learning model predicts improvement**

## 🛠️ Tech Stack

| Component      | Technology               |
|----------------|--------------------------|
| Frontend       | HTML, CSS, JavaScript    |
| Backend        | Python (Flask / Streamlit)|
| AI Integration | OpenAI GPT (via API)     |
| Database       | SQLite / MongoDB         |
| ML Model       | Random Forest Classifier |
| Dashboard      | Streamlit / Power BI     |

## 📊 Machine Learning Model

We use a **Random Forest Classifier** to predict if a student has improved after using the tutor. Features include:
- Initial and Final Quiz Scores
- Time Spent Learning
- AI Interaction Count
- Explanation Length
- Calculated Improvement Score

**Target Label:** `Improved (Yes/No)`

### Example Model Code
```python
model = RandomForestClassifier()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
````

## 📈 Dashboard Insights

The dashboard shows:

* Initial vs Final quiz score comparison
* Time spent vs Improvement Score
* AI interaction frequency
* Student performance summaries

### Built with:

* 📍 **Streamlit** (Interactive Web UI)
* 📍 **Matplotlib / Seaborn** (Visualizations)
* 📍 **Pandas** (Data Processing)

## 📁 Folder Structure

```bash
AI-Tutor/
│
├── static/                     # Static assets (CSS, JS)
├── templates/                  # HTML templates (if Flask)
├── app.py                      # Main backend
├── ai_chat_module.py           # OpenAI integration logic
├── ml_model.py                 # Model training & prediction
├── dashboard.py                # Streamlit dashboard
├── student_learning_data.csv   # Collected student data
└── README.md                   # Project overview
```

