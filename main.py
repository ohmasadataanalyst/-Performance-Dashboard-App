import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
import shutil
import base64
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

# PDF generator (must be defined before usage)
def generate_pdf(html, fname='dashboard.pdf', wk_path=None):
    if not wk_path:
        st.error("Provide wkhtmltopdf path.")
        return None
    try:
        import pdfkit
        cfg = pdfkit.configuration(wkhtmltopdf=wk_path)
        pdfkit.from_string(html, fname, configuration=cfg)
        with open(fname, 'rb') as f:
            return f.read()
    except Exception as e:
        st.error(f"PDF error: {e}")
        return None

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

# Sidebar: filters & wkhtmltopdf path
st.sidebar.header("🔍 Filters & Options")
default_wk = shutil.which('wkhtmltopdf') or ''
wk_path = st.sidebar.text_input("Path to wkhtmltopdf:", default_wk, help="Install wkhtmltopdf and provide its path if not auto-detected.")

# Load data

# Upload selection

df_uploads = pd.read_sql('SELECT id, filename, uploader, file_type, category, timestamp FROM uploads ORDER BY timestamp DESC', conn)
scope_options = ['All uploads'] + df_uploads.apply(lambda x: f"{x.id} - {x.filename} [{x.file_type}/{x.category}] by {x.uploader}@{x.timestamp}", axis=1).tolist()
selection = st.sidebar.selectbox("Select upload scope", scope_options)
sel_id = None if selection.startswith('All') else int(selection.split(' - ')[0])

# Fetch issues
def load_issues(uid=None):
    sql = 'SELECT issues.*, u.category, u.uploader FROM issues JOIN uploads u ON u.id=issues.upload_id'
    params = ()
    if uid:
        sql += ' WHERE upload_id=?'
        params = (uid,)
    return pd.read_sql(sql, conn, params=params, parse_dates=['date'])

df = load_issues(sel_id)
if df.empty:
    st.warning("No data to display.")
    st.stop()

# Date filter
min_d, max_d = df['date'].min().date(), df['date'].max().date()
start_end = st.sidebar.date_input("Date range", [min_d, max_d])
if len(start_end) != 2:
    st.error("Select both start and end date.")
    st.stop()
start_date = datetime.combine(start_end[0], datetime.min.time())
end_date = datetime.combine(start_end[1], datetime.max.time())

# Category & branch filters
categories = df['category'].unique().tolist()
b_branches = df['branch'].unique().tolist()
sel_cats = st.sidebar.multiselect("Category", categories, default=categories)
sel_branches = st.sidebar.multiselect("Branch", b_branches, default=b_branches)

# Apply filters
df_filtered = df.loc[
    (df['date'] >= start_date) & (df['date'] <= end_date) &
    df['category'].isin(sel_cats) & df['branch'].isin(sel_branches)
]

# Dashboard header
st.subheader(f"Issues: {start_end[0]} to {start_end[1]}")
st.write(f"Total issues: {len(df_filtered)}")

# Build figures list
figs = []
# Branch bar
b_sum = df_filtered.groupby('branch').size().reset_index(name='total')
fig_branch = px.bar(b_sum, x='branch', y='total', title='Issues per Branch')
st.plotly_chart(fig_branch, use_container_width=True)
figs.append(('Issues per Branch', fig_branch))
# Area manager pie
am_sum = df_filtered.groupby('area_manager').size().reset_index(name='total')
fig_am = px.pie(am_sum, names='area_manager', values='total', title='Issues by Area Manager')
st.plotly_chart(fig_am, use_container_width=True)
figs.append(('Issues by Area Manager', fig_am))
# Report type bar
rt_sum = df_filtered.groupby('report_type').size().reset_index(name='total')
fig_rt = px.bar(rt_sum, x='report_type', y='total', title='Issues by Report Type')
st.plotly_chart(fig_rt, use_container_width=True)
figs.append(('Issues by Report Type', fig_rt))
# Category bar
cat_sum = df_filtered.groupby('category').size().reset_index(name='total')
fig_cat = px.bar(cat_sum, x='category', y='total', title='Issues by Category')
st.plotly_chart(fig_cat, use_container_width=True)
figs.append(('Issues by Category', fig_cat))
# Trend line
trend = df_filtered.groupby(df_filtered['date'].dt.date).size().reset_index(name='count')
fig_trend = px.line(trend, x='date', y='count', title='Daily Trend')
st.plotly_chart(fig_trend, use_container_width=True)
figs.append(('Daily Trend', fig_trend))

# Detailed records for single-day\if (end_date.date() - start_date.date()).days == 0:
    st.subheader("Detailed Records")
    st.dataframe(df_filtered)

# Top issues\st.subheader("Top Issues")
st.dataframe(df_filtered['issues'].value_counts().rename_axis('issue').reset_index(name='count').head(20))

# Download data\ st.download_button("📥 Download Data CSV", df_filtered.to_csv(index=False).encode(), "issues.csv")

# Download visuals as PDF
if st.button("📥 Download Visuals as PDF"):
    if not wk_path:
        st.error("Provide wkhtmltopdf path.")
    else:
        html_parts = ["<html><body>"]
        for title, fig in figs:
            buf = io.BytesIO()
            fig.write_image(buf, format='png')
            b64 = base64.b64encode(buf.getvalue()).decode()
            html_parts.append(f"<h2>{title}</h2><img src='data:image/png;base64,{b64}'/><br/>")
        html_parts.append("</body></html>")
        html_content = ''.join(html_parts)
        pdf_bytes = generate_pdf(html_content, fname='visuals.pdf', wk_path=wk_path)
        if pdf_bytes:
            st.download_button("Download Visuals PDF", pdf_bytes, "visuals.pdf", "application/pdf")

# Download full report PDF
if st.button("📄 Download Dashboard as PDF"):
    html = f"<h1>Dashboard Report</h1>{df_filtered.to_html(index=False)}"
    pdf = generate_pdf(html, wk_path=wk_path)
    if pdf:
        st.download_button("Download PDF", pdf, "dashboard.pdf", "application/pdf")
