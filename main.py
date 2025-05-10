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
scope = ['All uploads'] + uploads.apply(lambda x: f"{x.id} - {x.filename} [{x.file_type}/{x.category}]","axis=1).tolist()
selection = st.sidebar.selectbox("Select upload scope", scope)
sel_id = None if selection.startswith('All') else int(selection.split(' - ')[0])

# Load data
def load_issues(uid):
    base = 'SELECT issues.*, u.category FROM issues JOIN uploads u ON u.id=issues.upload_id'
    if uid:
        base += ' WHERE upload_id=?'
        return pd.read_sql(base, conn, params=(uid,), parse_dates=['date'])
    return pd.read_sql(base, conn, parse_dates=['date'])

df = load_issues(sel_id)
if df.empty:
    st.warning("No data to display.")
    st.stop()

# Filters
st.sidebar.header("🛠️ Filters")
min_d, max_d = df['date'].min().date(), df['date'].max().date()
start_end = st.sidebar.date_input("Date range", [min_d, max_d])
if len(start_end) != 2:
    st.error("Please select a start and end date.")
    st.stop()
start_date, end_date = pd.to_datetime(start_end[0]), pd.to_datetime(start_end[1]) + pd.Timedelta(days=1)
cats = st.sidebar.multiselect("Upload Category", df['category'].unique(), default=df['category'].unique())

mask = (df['date'] >= start_date) & (df['date'] < end_date) & df['category'].isin(cats)
filtered = df.loc[mask]

# Aggregation: group counts per branch
st.subheader(f"Issues Summary: {start_end[0]} to {start_end[1]}")
st.write(f"Total issues in range: {len(filtered)}")

# Summary by Branch
st.subheader("🏷️ Total Issues by Branch")
branch_summary = filtered.groupby('branch').size().reset_index(name='total_issues')
st.dataframe(branch_summary)
# Bar chart
st.plotly_chart(px.bar(branch_summary, x='branch', y='total_issues', title='Issues per Branch'), use_container_width=True)

# Summary by Area Manager
st.subheader("👤 Total Issues by Area Manager")
am_summary = filtered.groupby('area_manager').size().reset_index(name='total_issues')
st.dataframe(am_summary)
st.plotly_chart(px.pie(am_summary, names='area_manager', values='total_issues', title='Issues by Area Manager'), use_container_width=True)

# Summary by Report Type
st.subheader("📂 Total Issues by Report Type")
rt_summary = filtered.groupby('report_type').size().reset_index(name='total_issues')
st.dataframe(rt_summary)
st.plotly_chart(px.bar(rt_summary, x='report_type', y='total_issues', title='Issues by Report Type'), use_container_width=True)

# Summary by Category
st.subheader("📑 Total Issues by Category")
cat_summary = filtered.groupby('category').size().reset_index(name='total_issues')
st.dataframe(cat_summary)
st.plotly_chart(px.bar(cat_summary, x='category', y='total_issues', title='Issues by Category'), use_container_width=True)

# Download filtered data
st.download_button("📥 Download Filtered Data", filtered.to_csv(index=False).encode(), "issues_report.csv")
