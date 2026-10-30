# Class XI Computer Science Exam Portal

A beginner-friendly online one-mark test website built with Python, Streamlit and SQLite.

## Features
- Student name entry and chapter selection
- Random 25-question test (25 marks)
- 25-minute countdown display
- Automatic scoring and answer review
- Leaderboard
- Admin login and CSV question upload
- Includes 156 one-mark MCQs from the supplied Class XI Computer Science PDF
- The included question bank is imported automatically on first launch

## Run locally
1. Install Python 3.10 or newer: https://www.python.org/downloads/
2. Open this folder in Terminal / Command Prompt.
3. Run:

```bash
python -m venv .venv
```

Activate it:
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publish publicly with Streamlit Community Cloud

1. Create a GitHub account at https://github.com/ if you do not already have one.
2. Create a **new public repository** (for example `class11-cs-exam-portal`).
3. Upload these project files to the repository: `app.py`, `requirements.txt`, and `question_bank.csv`. You may also upload `README.md` and `question_template.csv`.
4. Open https://share.streamlit.io/ and sign in with GitHub.
5. Choose **Create app**, select your repository, branch (usually `main`), and main file path `app.py`.
6. Before deploying, open the app's **Advanced settings / Secrets** and add a strong password like this:

```toml
ADMIN_PASSWORD = "replace-this-with-a-long-unique-password"
```

7. Click **Deploy**. Streamlit will build the app and provide a public `streamlit.app` URL. Share that URL with students.

## Admin: upload more questions
1. Open the **Admin Panel** tab on the website.
2. Enter the admin password you added in Streamlit Secrets.
3. Download the sample CSV template.
4. Add questions and save as CSV UTF-8.
5. Required columns: `chapter`, `question`, `option_a`, `option_b`, `option_c`, `option_d`, `answer`, `explanation`.
6. `answer` must be A, B, C, or D. Upload the CSV and click **Import questions**.

At least 25 questions must exist in the selected chapter (or all-chapters pool) to start a test.

## Important before sharing with a whole school

- This starter app uses a local SQLite database (`exam_portal.db`). On cloud hosting, local files may be reset during redeploys or restarts. That can erase uploaded questions and leaderboard scores. For reliable long-term public use, connect a persistent hosted database such as PostgreSQL/Supabase and configure backups.
- The leaderboard displays student names publicly. Get permission before collecting or displaying students' names; consider using first names or student nicknames.
- This is a learning/demo portal, not a high-stakes examination system. The timer currently warns at zero but does not automatically submit or prevent late submissions.
- Check the supplied answer key with the teacher before using it for formal tests; the source PDF does not provide a complete answer key.
- Never commit passwords or database credentials to the GitHub repository. Use Streamlit Secrets.

## Included question bank
`question_bank.csv` contains 156 multiple-choice one-mark questions selected from the PDF's **Choose the correct answer** sections. Very Short Answers and longer-answer questions are excluded.
