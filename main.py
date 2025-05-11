import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
import shutil
import base64
from datetime import datetime, date

# Streamlit config MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Performance Dashboard", layout="wide") # MOVED HERE

# --- Database setup ---
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# (Database schema setup)
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
    file_type TEXT, category TEXT, file BLOB
)''')
conn.commit()
c.execute("PRAGMA table_info(uploads)")
existing_columns = [column[1] for column in c.fetchall()]
if 'submission_date' not in existing_columns:
    try:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        # We can't use st.toast here because set_page_config hasn't run.
        # We'll set a flag and show the toast later if needed.
        if 'db_schema_updated_flag' not in st.session_state:
            st.session_state.db_schema_updated_flag = True 
    except sqlite3.OperationalError as e:
        # Can't use st.error here either yet. Print to console.
        print(f"CRITICAL DB ERROR: {e}. Cannot proceed.") 
        # A proper app might raise an exception or sys.exit() here
        # For now, Streamlit will likely show a generic error if this happens.
        # Or, we can attempt st.error later if this path is taken.
        st.session_state.db_critical_error = str(e) 
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    upload_id INTEGER, code TEXT, issues TEXT, branch TEXT, area_manager TEXT,
    date TEXT, report_type TEXT, FOREIGN KEY(upload_id) REFERENCES uploads(id)
)''')
conn.commit()

# Credentials
db_admin = {
    "abdalziz alsalem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvpLxRumSduEte8MDAPkOnuXMdnW",
    "omar salah": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy",
    "ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEn.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG",
    "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe"
}
view_only = ["mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"]


# --- CHECK FOR CRITICAL DB ERROR FROM SETUP ---
if 'db_critical_error' in st.session_state:
    st.error(f"A critical database error occurred during startup: {st.session_state.db_critical_error}. The application may not function correctly. Please check logs or contact support.")
    del st.session_state.db_critical_error # Show once
    st.stop()


# --- SHOW DB SCHEMA UPDATE TOAST IF FLAG IS SET ---
if 'db_schema_updated_flag' in st.session_state and st.session_state.db_schema_updated_flag:
    st.toast("Database 'uploads' table schema updated successfully with 'submission_date' column.", icon="ℹ️")
    st.session_state.db_schema_updated_flag = False # Clear flag so it only shows once per update

# --- AUTHENTICATION FUNCTION ---
def check_login():
    # ... (rest of check_login is the same)
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_name = None
        st.session_state.user_role = None

    if not st.session_state.authenticated:
        st.title("📊 Login - Performance Dashboard") # Now this is fine
        st.subheader("Please log in to continue")
        with st.form("login_form"):
            username = st.text_input("Full Name:", key="auth_username").strip().lower()
            password = st.text_input("Password:", type="password", key="auth_password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if username in db_admin and bcrypt.checkpw(password.encode(), db_admin[username]):
                    st.session_state.authenticated = True
                    st.session_state.user_name = username
                    st.session_state.user_role = 'admin'
                    st.rerun() 
                elif username in view_only and password:
                    st.session_state.authenticated = True
                    st.session_state.user_name = username
                    st.session_state.user_role = 'view_only'
                    st.rerun() 
                elif username in view_only and not password:
                    st.error("Password cannot be empty for view-only users.")
                elif username or password: 
                     st.error("Invalid username or password.")
                else:
                    st.info("Please enter your credentials.")
        return False 
    return True 

if not check_login():
    st.stop() 

# --- User is Authenticated, Proceed with App ---
st.title("📊 Classic Dashboard for Performance") # Now this is fine

user_name_display = st.session_state.get('user_name', "N/A").title()
user_role_display = st.session_state.get('user_role', "N/A")

st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
# No debug markers needed here for now, as the set_page_config was the issue.

if st.sidebar.button("Logout", key="logout_button_main"):
    st.session_state.authenticated = False
    st.session_state.user_name = None
    st.session_state.user_role = None
    st.rerun()

# Determine admin status
is_admin = False 
if 'user_role' in st.session_state and st.session_state.user_role == 'admin':
    is_admin = True
current_user = st.session_state.get('user_name', 'Unknown User')

# (The rest of your script, including PDF generator, Admin Controls section, etc., follows here)
# ...
