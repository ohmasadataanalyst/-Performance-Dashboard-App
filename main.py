import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
from datetime import datetime, timedelta

# Database setup
db_path = 'issues.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
# Create tables
c.execute(
    '''CREATE TABLE IF NOT EXISTS uploads (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           filename TEXT,
           uploader TEXT,
           timestamp TEXT,
           file BLOB
       )''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS issues (
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

# Store hashed passwords for admin users
db_admin = {
    "abdalziz alsalem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvpLxRumSduEte8MDAPkOnuXMdnW",
    "omar salah": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy",
    "ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEn.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG",
    "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe"
}
view_only_users = [
    "mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"
]

# Streamlit config
st.set_page_config(page_title="Performance Dashboard", layout="wide")
st.title("📊 Performance Dashboard with SQLite Storage")

# Authentication inputs
username = st.text_input("Enter your full name:").strip().lower()
password = st.text_input("Enter your password:", type="password")

def is_admin(user, pwd):
    return user in db_admin and bcrypt.checkpw(pwd.encode(), db_admin[user])

if not username:
    st.info("Enter full name and password to proceed.")
    st.stop()

if username in view_only_users or is_admin(username, password):
    if is_admin(username, password):
        st.success("Welcome Admin! Upload new files or search past uploads.")
        # Upload new file
        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"] )
        if uploaded_file:
            # Read bytes and store
            file_bytes = uploaded_file.getvalue()
            ts = datetime.now().isoformat()
            c.execute(
                'INSERT INTO uploads (filename, uploader, timestamp, file) VALUES (?,?,?,?)',
                (uploaded_file.name, username, ts, sqlite3.Binary(file_bytes))
            )
            upload_id = c.lastrowid
            df = pd.read_excel(io.BytesIO(file_bytes))
            df.columns = df.columns.str.lower()
            df['date'] = pd.to_datetime(df['date'], dayfirst=True)
            # Insert rows
            for _, row in df.iterrows():
                c.execute(
                    'INSERT INTO issues VALUES (?,?,?,?,?,?,?)',
                    (upload_id, row['code'], row['issues'], row['branch'], row['area manager'], row['date'].isoformat(), row['report type'])
                )
            conn.commit()
            st.success(f"File '{uploaded_file.name}' uploaded with ID {upload_id} and {len(df)} issues.")
        # Search past uploads
        st.sidebar.header("🔍 Search Past Uploads")
        uploads = pd.read_sql('SELECT id, filename, uploader, timestamp FROM uploads ORDER BY timestamp DESC', conn)
        if not uploads.empty:
            sel = st.sidebar.selectbox("Select upload", uploads.apply(lambda x: f"{x.id} - {x.filename} by {x.uploader} @ {x.timestamp}", axis=1))
            upload_id = int(sel.split(' - ')[0])
            # Offer download
            file_row = c.execute('SELECT file, filename FROM uploads WHERE id=?', (upload_id,)).fetchone()
            if file_row:
                file_blob, fname = file_row
                st.sidebar.download_button("📥 Download original file", data=file_blob, file_name=fname)
            # Load issues from that upload
            df = pd.read_sql('SELECT * FROM issues WHERE upload_id=?', conn, params=(upload_id,))
            df['date'] = pd.to_datetime(df['date'])
        else:
            st.sidebar.info("No uploads yet.")
            df = pd.DataFrame()
    else:
        st.info("View-only: Displaying latest combined issues report.")
        # Load all issues
        df = pd.read_sql('SELECT * FROM issues', conn)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
else:
    st.error("Unauthorized user. Please contact the administrator.")
    st.stop()

# Reporting
if df.empty:
    st.warning("No issue data to display.")
else:
    st.sidebar.header("🛠️ Filters")
    freq = st.sidebar.selectbox("Frequency", ['Daily', 'Weekly', 'Monthly', 'Yearly'])
    report_types = st.sidebar.multiselect("Report Type", df['report_type'].unique(), default=df['report_type'].unique())
    now = datetime.now()
    if freq == 'Daily': start = now - timedelta(days=1)
    elif freq == 'Weekly': start = now - timedelta(weeks=1)
    elif freq == 'Monthly': start = now - timedelta(days=30)
    else: start = now - timedelta(days=365)
    mask = (df['date'] >= start) & (df['date'] <= now) & df['report_type'].isin(report_types)
    filtered = df.loc[mask]
    st.subheader(f"📈 Issues Report: {freq} ({start.date()} to {now.date()})")
    st.write(f"Total issues: {len(filtered)}")
    # Charts and tables
    branch_counts = filtered['branch'].value_counts().reset_index()
    branch_counts.columns = ['branch', 'count']
    st.plotly_chart(px.bar(branch_counts.head(10), x='branch', y='count', title='Top 10 Branches'), use_container_width=True)
    trend = filtered.groupby(filtered['date'].dt.date).size().reset_index(name='count')
    st.plotly_chart(px.line(trend, x='date', y='count', title='Daily Issue Trend'), use_container_width=True)
    st.subheader("🔍 Top Issue Descriptions")
    st.dataframe(filtered['issues'].value_counts().rename_axis('issue').reset_index(name='count').head(20))
    am_counts = filtered['area_manager'].value_counts().reset_index()
    am_counts.columns = ['area manager', 'count']
    st.plotly_chart(px.pie(am_counts, names='area manager', values='count', title='Issues by Area Manager'), use_container_width=True)
    st.download_button("📥 Download Filtered Data", filtered.to_csv(index=False).encode(), "issues_report.csv")
