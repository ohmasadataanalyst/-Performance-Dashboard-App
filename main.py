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
view_only = ["mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"]

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

# PDF generator
def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path:
        st.error("wkhtmltopdf path not set.")
        return None
    try:
        import pdfkit
        config = pdfkit.configuration(wkhtmltopdf=wk_path)
        pdfkit.from_string(html, fname, configuration=config)
        with open(fname, 'rb') as f:
            return f.read()
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None

# Sidebar: controls
st.sidebar.header("🔍 Filters & Options")
# Upload control for admins\if is_admin:
    file_type = st.sidebar.selectbox("File type", ["opening", "closing", "handover", "meal training"])
    category = st.sidebar.selectbox("Category", ['operation-training', 'CCTV', 'complaints', 'missing', 'visits', 'meal training'])
    up = st.sidebar.file_uploader("Upload Excel", type=["xlsx"])
    if up:
        data = up.getvalue()
        ts = datetime.now().isoformat()
        c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, file) VALUES (?, ?, ?, ?, ?, ?)',
                  (up.name, user, ts, file_type, category, sqlite3.Binary(data)))
        uid = c.lastrowid
        df_up = pd.read_excel(io.BytesIO(data))
        df_up.columns = df_up.columns.str.lower()
        df_up['date'] = pd.to_datetime(df_up['date'], dayfirst=True)
        for _, row in df_up.iterrows():
            c.execute('INSERT INTO issues VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (uid, row['code'], row['issues'], row['branch'], row['area manager'], row['date'].isoformat(), file_type))
        conn.commit()
        st.sidebar.success(f"Uploaded {up.name} ({len(df_up)} records)")

# wkhtmltopdf path
default_wk = shutil.which('wkhtmltopdf') or ''
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk)

# Load uploads
df_uploads = pd.read_sql('SELECT id, filename, uploader, timestamp FROM uploads ORDER BY timestamp DESC', conn)

# Scope selection
scope_opts = ['All uploads'] + df_uploads['id'].astype(str).tolist()
sel = st.sidebar.selectbox("Select upload ID:", scope_opts)
sel_id = None if sel == 'All uploads' else int(sel)

# Branch & Category filters
# Fetch data
sql = 'SELECT i.*, u.category FROM issues i JOIN uploads u ON u.id = i.upload_id'
params = []
if sel_id:
    sql += ' WHERE upload_id = ?'
    params.append(sel_id)
df = pd.read_sql(sql, conn, params=params, parse_dates=['date'])
if df.empty:
    st.warning("No data to display.")
    st.stop()
df['date'] = pd.to_datetime(df['date'])

date_range = st.sidebar.date_input("Date range:", [df['date'].min().date(), df['date'].max().date()])
branch_opts = df['branch'].unique().tolist()
cat_opts = df['category'].unique().tolist()
sel_br = st.sidebar.multiselect("Branch:", branch_opts, default=branch_opts)
sel_cat = st.sidebar.multiselect("Category:", cat_opts, default=cat_opts)

# Apply filters
mask = (df['branch'].isin(sel_br)) & (df['category'].isin(sel_cat)) & \
       (df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])
df_f = df.loc[mask]

# Dashboard
st.subheader(f"Issues from {date_range[0]} to {date_range[1]}")
st.write(f"Total: {len(df_f)}")

# Charts
figs = {}
figs['Branch'] = px.bar(df_f.groupby('branch').size().reset_index(name='count'), x='branch', y='count', title='By Branch')
st.plotly_chart(figs['Branch'], use_container_width=True)

figs['Area Manager'] = px.pie(df_f.groupby('area_manager').size().reset_index(name='count'), names='area_manager', values='count', title='By Area Manager')
st.plotly_chart(figs['Area Manager'], use_container_width=True)

figs['Report Type'] = px.bar(df_f.groupby('report_type').size().reset_index(name='count'), x='report_type', y='count', title='By Report Type')
st.plotly_chart(figs['Report Type'], use_container_width=True)

figs['Category'] = px.bar(df_f.groupby('category').size().reset_index(name='count'), x='category', y='count', title='By Category')
st.plotly_chart(figs['Category'], use_container_width=True)

# Detailed for single day
if date_range[0] == date_range[1]:
    st.subheader("Detailed Records")
    st.dataframe(df_f)

# Top issues & Trend
st.subheader("Top Issues")
st.dataframe(df_f['issues'].value_counts().head(20).rename_axis('issue').reset_index(name='count'))

figs['Trend'] = px.line(df_f.groupby(df_f['date'].dt.date).size().reset_index(name='count'), x='date', y='count', title='Trend')
    
st.plotly_chart(figs['Trend'], use_container_width=True)

# Downloads
st.download_button("Download CSV", df_f.to_csv(index=False).encode(), "issues.csv")

# Download visuals as PDF
if st.button("Download Visuals PDF"):
    if not wk_path:
        st.error("wkhtmltopdf path not set.")
    else:
        html = '<html><body>'
        for title, fig in figs.items():
            img = fig.to_image(format='png')
            b64 = base64.b64encode(img).decode()
            html += f"<h2>{title}</h2><img src='data:image/png;base64,{b64}'/><br/>"
        html += '</body></html>'
        pdf = generate_pdf(html, fname='visuals.pdf', wk_path=wk_path)
        if pdf:
            st.download_button("Download Visuals PDF", pdf, "visuals.pdf", "application/pdf")

# Download full PDF
if st.button("Download Dashboard PDF"):
    html_full = df_f.to_html(index=False)
    pdf_full = generate_pdf(f"<h1>Dashboard Report</h1>{html_full}", wk_path=wk_path)
    if pdf_full:
        st.download_button("Download Dashboard PDF", pdf_full, "dashboard.pdf", "application/pdf")
