import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sqlite3
import pandas as pd
import random
import os
import hashlib
from datetime import datetime

DB_PATH = "exam_portal.db"
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-this-password")
QUESTION_COLUMNS = ["chapter", "question", "option_a", "option_b", "option_c", "option_d", "answer", "explanation"]

st.set_page_config(page_title="Class XI CS Exam Portal", page_icon="💻", layout="wide")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            answer TEXT NOT NULL,
            explanation TEXT DEFAULT ''
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            chapter TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            submitted_at TEXT NOT NULL
        )""")
        # Seed the included textbook MCQs once, when the questions table is empty.
        existing = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        bank_path = os.path.join(os.path.dirname(__file__), "question_bank.csv")
        if existing == 0 and os.path.exists(bank_path):
            bank = pd.read_csv(bank_path).fillna("")
            missing = [c for c in QUESTION_COLUMNS if c not in bank.columns]
            if not missing:
                bank = bank[QUESTION_COLUMNS]
                for _, row in bank.iterrows():
                    con.execute("""INSERT INTO questions
                        (chapter, question, option_a, option_b, option_c, option_d, answer, explanation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        tuple(str(row[c]).strip() for c in QUESTION_COLUMNS))

def load_questions(chapter=None):
    with get_conn() as con:
        if chapter and chapter != "All available chapters":
            df = pd.read_sql_query("SELECT * FROM questions WHERE chapter = ? ORDER BY id", con, params=(chapter,))
        else:
            df = pd.read_sql_query("SELECT * FROM questions ORDER BY id", con)
    return df

def save_result(name, chapter, score, total):
    with get_conn() as con:
        con.execute(
            "INSERT INTO results (student_name, chapter, score, total, submitted_at) VALUES (?, ?, ?, ?, ?)",
            (name, chapter, score, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

def import_questions(uploaded_file):
    df = pd.read_csv(uploaded_file)
    missing = [c for c in QUESTION_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(missing))
    df = df[QUESTION_COLUMNS].fillna("")
    df["answer"] = df["answer"].astype(str).str.strip().str.upper()
    if not df["answer"].isin(["A", "B", "C", "D"]).all():
        raise ValueError("Every answer must be A, B, C, or D.")
    if (df["chapter"].astype(str).str.strip() == "").any() or (df["question"].astype(str).str.strip() == "").any():
        raise ValueError("Chapter and question fields cannot be empty.")
    with get_conn() as con:
        for _, row in df.iterrows():
            con.execute("""INSERT INTO questions
                (chapter, question, option_a, option_b, option_c, option_d, answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                tuple(str(row[c]).strip() for c in QUESTION_COLUMNS))
    return len(df)

def reset_exam():
    for key in list(st.session_state.keys()):
        if key.startswith("answer_"):
            del st.session_state[key]
    st.session_state.exam_started = False
    st.session_state.exam_submitted = False
    st.session_state.exam_df = None
    st.session_state.student_name = ""
    st.session_state.exam_chapter = ""

init_db()

st.title("💻 Class XI Computer Science Exam Portal")
st.caption("One Mark Online Test • Practice and improve your knowledge")

tab_test, tab_leaderboard, tab_admin = st.tabs(["📝 Student Test", "🏆 Leaderboard", "🔐 Admin Panel"])

with tab_test:
    if "exam_started" not in st.session_state:
        st.session_state.exam_started = False
        st.session_state.exam_submitted = False
        st.session_state.exam_df = None

    if not st.session_state.exam_started and not st.session_state.exam_submitted:
        st.subheader("Start your examination")
        name = st.text_input("Student name", max_chars=60, placeholder="Enter your full name")
        all_q = load_questions()
        if all_q.empty:
            st.info("No questions have been added yet. Please ask the admin to upload a question CSV.")
        else:
            chapters = ["All available chapters"] + sorted(all_q["chapter"].dropna().unique().tolist())
            chapter = st.selectbox("Choose chapter", chapters)
            available = len(all_q) if chapter == "All available chapters" else len(all_q[all_q["chapter"] == chapter])
            st.write(f"Questions available: **{available}**")
            st.write("Test format: 25 questions • 25 marks • 25 minutes")
            if available < 25:
                st.warning("At least 25 questions are needed in the selected chapter/selection. Ask the admin to upload more.")
            if st.button("Start Test", type="primary", disabled=(not name.strip() or available < 25)):
                pool = all_q if chapter == "All available chapters" else all_q[all_q["chapter"] == chapter]
                chosen = pool.sample(n=25, replace=False, random_state=random.randint(0, 999999)).reset_index(drop=True)
                st.session_state.exam_df = chosen
                st.session_state.student_name = name.strip()
                st.session_state.exam_chapter = chapter
                st.session_state.exam_started = True
                st.session_state.exam_start_time = datetime.now().timestamp()
                st.rerun()

    elif st.session_state.exam_started and not st.session_state.exam_submitted:
        st_autorefresh(interval=1000, key="exam_countdown_refresh")
        df = st.session_state.exam_df
        elapsed = int(datetime.now().timestamp() - st.session_state.exam_start_time)
        remaining = max(0, 25 * 60 - elapsed)
        st.subheader(f"Welcome, {st.session_state.student_name}")
        st.write(f"Chapter selection: **{st.session_state.exam_chapter}**")
        mins, secs = divmod(remaining, 60)
        st.metric("Time remaining", f"{mins:02d}:{secs:02d}")
        if remaining == 0:
            st.warning("Time is up. Submit your answers now.")
        with st.form("exam_form"):
            for i, row in df.iterrows():
                st.markdown(f"**Q{i+1}. {row['question']}**")
                options = {
                    "A": str(row["option_a"]),
                    "B": str(row["option_b"]),
                    "C": str(row["option_c"]),
                    "D": str(row["option_d"])
                }
                st.radio("Choose one answer", options=list(options.keys()),
                         format_func=lambda x, opts=options: f"{x}. {opts[x]}",
                         key=f"answer_{i}", index=None, label_visibility="collapsed")
                st.divider()
            submitted = st.form_submit_button("Submit Test", type="primary")
        if submitted:
            score = 0
            review = []
            for i, row in df.iterrows():
                selected = st.session_state.get(f"answer_{i}")
                correct = str(row["answer"]).upper()
                if selected == correct:
                    score += 1
                review.append({
                    "Question": row["question"],
                    "Your answer": selected or "Not answered",
                    "Correct answer": correct,
                    "Result": "Correct" if selected == correct else "Incorrect",
                    "Explanation": row["explanation"]
                })
            save_result(st.session_state.student_name, st.session_state.exam_chapter, score, 25)
            st.session_state.exam_score = score
            st.session_state.exam_review = review
            st.session_state.exam_submitted = True
            st.session_state.exam_started = False
            st.rerun()

    if st.session_state.get("exam_submitted"):
        score = st.session_state.exam_score
        st.subheader("🎉 Test completed!")
        st.metric("Your score", f"{score} / 25")
        st.progress(score / 25)
        st.write(f"Correct: **{score}** · Incorrect or unanswered: **{25-score}**")
        if score >= 20:
            st.success("Excellent work!")
        elif score >= 12:
            st.info("Good effort. Keep practising!")
        else:
            st.warning("Keep learning and try again!")
        with st.expander("View answer review", expanded=True):
            for i, item in enumerate(st.session_state.exam_review, 1):
                st.markdown(f"**Q{i}. {item['Question']}**")
                st.write(f"Your answer: {item['Your answer']} · Correct answer: {item['Correct answer']} · {item['Result']}")
                if item["Explanation"]:
                    st.caption(item["Explanation"])
        if st.button("Take another test"):
            reset_exam()
            st.rerun()

with tab_leaderboard:
    st.subheader("🏆 Student Leaderboard")
    with get_conn() as con:
        board = pd.read_sql_query("""SELECT student_name AS Student, chapter AS Chapter,
            score AS Score, total AS Total, submitted_at AS 'Submitted at'
            FROM results ORDER BY score DESC, submitted_at ASC LIMIT 100""", con)
    if board.empty:
        st.info("No test results yet. Be the first to take a test!")
    else:
        st.dataframe(board, use_container_width=True, hide_index=True)

with tab_admin:
    st.subheader("🔐 Admin Panel")
    st.caption("Admin access is required to upload questions.")
    password = st.text_input("Admin password", type="password")
    if st.button("Login to Admin Panel"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
        else:
            st.session_state.admin_logged_in = False
            st.error("Incorrect password.")
    if st.session_state.get("admin_logged_in"):
        st.success("Admin access granted.")
        st.markdown("Upload a CSV file with these exact column names:")
        st.code(",".join(QUESTION_COLUMNS), language="text")
        st.download_button(
            "Download sample CSV template",
            data=("chapter,question,option_a,option_b,option_c,option_d,answer,explanation\n"
                  '"Chapter 1","Which device is called the brain of a computer?","Monitor","CPU","Keyboard","Mouse","B","CPU processes instructions."\n'),
            file_name="question_template.csv",
            mime="text/csv"
        )
        uploaded = st.file_uploader("Upload questions CSV", type=["csv"])
        if uploaded is not None and st.button("Import questions", type="primary"):
            try:
                count = import_questions(uploaded)
                st.success(f"Successfully imported {count} questions.")
            except Exception as e:
                st.error(f"Could not import CSV: {e}")
        current = load_questions()
        st.write(f"Total questions in database: **{len(current)}**")
        if not current.empty:
            st.dataframe(current[["chapter", "question", "answer"]], use_container_width=True, hide_index=True)
        if st.button("Admin logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

st.divider()
st.caption("Practice responsibly • One mark for each correct answer • No negative marking")
