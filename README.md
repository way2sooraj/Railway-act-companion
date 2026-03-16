# 🚂 Railways Act 1989 — Companion App

A Streamlit-based study and reference tool for Railway officers.

## Features

| Module | Description |
|---|---|
| 📖 Browse & Read | Chapter-wise section browser with keyword search, bookmarks, notes |
| 🤖 AI Assistant | Conversational Q&A grounded in Act text (requires API key) |
| 🃏 Flashcards | Section number → topic recall cards with chapter filter |
| 📝 MCQ Quiz | Randomized quizzes with chapter filter, scoring, and answer review |
| ⏱️ Mock Test | Timed, full-length test with configurable question count |
| 📊 Progress | Reading progress by chapter, score history, bookmarks, notes |

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

### 3. Set your Anthropic API key

Open the app → ⚙️ Settings → paste your `sk-ant-...` key → Save.

AI features (AI Assistant, "Explain this section") will activate automatically.

## Deployment (Streamlit Community Cloud)

1. Push this folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set `ANTHROPIC_API_KEY` in Streamlit Secrets (optional — users can also enter it in Settings)
4. Deploy!

## TODO — Before Production Use

- [ ] Parse the full Railways Act 1989 PDF and replace `data/act_sections.json`
- [ ] Expand `data/quiz_bank.json` to 200+ questions
- [ ] Add `streamlit-autorefresh` for live mock test timer
- [ ] Add SQLite-based persistence for notes and progress across sessions
- [ ] Consider adding the Railway Property (Unlawful Possession) Act and key Rules

## Data Format

### act_sections.json

```json
[
  {
    "section_no": 137,
    "chapter": "Chapter XIV — Offences and Penalties",
    "title": "Travelling without pass or ticket",
    "content": "Full section text...",
    "penalty": "Fine not exceeding Rs. 1,000.",
    "tags": ["ticketless", "penalty", "passenger"]
  }
]
```

### quiz_bank.json

```json
[
  {
    "question": "Question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option B",
    "chapter": "Chapter XIV — Offences and Penalties",
    "explanation": "Explanation of why Option B is correct."
  }
]
```
