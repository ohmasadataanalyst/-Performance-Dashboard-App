import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
from datetime import datetime

# Database setup
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    uploader TEXT,
    timestamp TEXT,
    file_type TEXT,
    category TEXT,
    file BLOB
)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    upload_id INTEGER,
    code TEXT,
    issues TEXT,
    branch TEXT,
    area_manager TEXT,
    date TEXT,
    report_type TEXT,
    FOREIGN KEY(upload_id) REFERENCES uploads(id)
)''')
conn.commit()

# Credentials
db_admin = {
    "abdalziz alsalem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvpLxRumSduEte8MDAPkOnuXMdnW",
    "omar salah": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy",
    "ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEn.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG",
    "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe"
}
view_only = ["mohamed emad","mohamed houider","sujan podel","ali ismail","islam mostafa"]

# Streamlit config
st.set_page_config(page_title="Performance Dashboard", layout="wide")
st.title("📊 Performance Dashboard with SQLite Storage")

# Authentication
user = st.text_input("Enter your full name:").strip().lower()
pwd = st.text_input("Enter your password:", type="password")
if not user:
    st.info("Enter credentials to proceed.")
    st.stop()
is_admin = user in db_admin and bcrypt.checkpw(pwd.encode(), db_admin[user])
if not is_admin and user not in view_only:
    st.error("Unauthorized user.")
    st.stop()

# Admin controls
if is_admin:
    st.success("Admin access granted.")
    if st.button("🗑️ Clear all uploads and issues"):
        c.execute('DELETE FROM issues')
        c.execute('DELETE FROM uploads')
        conn.commit()
        st.warning("All uploads and issues cleared.")
    file_type = st.selectbox("File type", ["opening","closing","handover","meal training"])
    category = st.selectbox("Category", ['operation-training','CCTV','complaints','missing','visits','meal training'])
    up = st.file_uploader("Upload Excel", type=["xlsx"])
    if up:
        data = up.getvalue()
        ts = datetime.now().isoformat()
        c.execute(
            'INSERT INTO uploads (filename,uploader,timestamp,file_type,category,file) VALUES (?,?,?,?,?,?)',
            (up.name, user, ts, file_type, category, sqlite3.Binary(data))
        )
        uid = c.lastrowid
        df_up = pd.read_excel(io.BytesIO(data))
        df_up.columns = df_up.columns.str.lower()
        df_up['date'] = pd.to_datetime(df_up['date'], dayfirst=True)
        for _, row in df_up.iterrows():
            c.execute(
                'INSERT INTO issues VALUES (?,?,?,?,?,?,?)',
                (uid, row['code'], row['issues'], row['branch'], row['area manager'], row['date'].isoformat(), file_type)
            )
        conn.commit()
        st.success(f"Uploaded '{up.name}' as {file_type}/{category} with {len(df_up)} records.")

# Upload scope
st.sidebar.header("🔍 Choose Upload Scope")
uploads = pd.read_sql('SELECT id,filename,file_type,category,timestamp FROM uploads ORDER BY timestamp DESC', conn)
scope = ['All uploads'] + uploads.apply(lambda x: f"{x.id} - {x.filename} [{x.file_type}/{x.category}]", axis=1).tolist()
