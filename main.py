import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
from datetime import datetime, timedelta

# Database setup
# Note: If running first time, uploads table includes file_type and category fields
db_path = 'issues.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
# Create tables (initial schema)
c.execute(
    '''CREATE TABLE IF NOT EXISTS uploads (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           filename TEXT,
           uploader TEXT,
           timestamp TEXT,
           file BLOB
       )''')
# Ensure new columns exist for file_type and category
def add_column_if_not_exists(table, column, col_type):
    cols = [row[1] for row in c.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
add_column_if_not_exists('uploads','file_type','TEXT')
add_column_if_not_exists('uploads','category','TEXT')

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

# Authentication and data loading
if username in view_only_users or is_admin(username, password):
    if is_admin(username, password):
        st.success("Welcome Admin! Upload new files or search past uploads.")
        # Admin selects metadata before upload
        file_type = st.selectbox("Select file type", ["opening", "closing", "handover", "meal training"])
        category = st.selectbox(
            "Select category",
            ['operation-training', 'CCTV', 'complaints', 'missing', 'visits', 'meal training']
        )
        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"]) 
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            ts = datetime.now().isoformat()
            # Insert into uploads with metadata
            c.execute(
                'INSERT INTO uploads (filename, uploader, timestamp, file_type, category, file) VALUES (?,?,?,?,?,?)',
                (uploaded_file.name, username, ts, file_type, category, sqlite3.Binary(file_bytes))
            )
            upload_id = c.lastrowid
            df_upload = pd.read_excel(io.BytesIO(file_bytes))
            df_upload.columns = df_upload.columns.str.lower()
            df_upload['date'] = pd.to_datetime(df_upload['date'], dayfirst=True)
            # Insert each row
            for _, row in df_upload.iterrows():
                c.execute(
                    'INSERT INTO issues VALUES (?,?,?,?,?,?,?)',
                    (upload_id, row['code'], row['issues'], row['branch'], row['area manager'], row['date'].isoformat(), file_type)
                )
            conn.commit()
            st.success(
                f"Uploaded '{uploaded_file.name}' as {file_type}/{category} (ID {upload_id}) with {len(df_upload)} records."
            )
        # Search past uploads
        st.sidebar.header("🔍 Search Past Uploads")
        uploads = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category FROM uploads ORDER BY timestamp DESC', conn)
        if not uploads.empty:
            sel = st.sidebar.selectbox(
                "Select upload", 
                uploads.apply(lambda x: f"{x.id} - {x.filename} [{x.file_type}/{x.category}] by {x.uploader} @ {x.timestamp}", axis=1)
            )
            upload_id = int(sel.split(' - ')[0])
            file_row = c.execute('SELECT file, filename FROM uploads WHERE id=?', (upload_id,)).fetchone()
            if file_row:
                file_blob, fname = file_row
                st.sidebar.download_button("📥 Download original file", data=file_blob, file_name=fname)
            df = pd.read_sql('SELECT * FROM issues WHERE upload_id=?', conn, params=(upload_id,))
            df['date'] = pd.to_datetime(df['date'])
        else:
            st.sidebar.info("No uploads yet.")
            df = pd.DataFrame()
    else:
        st.info("View-only: Displaying latest combined issues report.")
        df = pd.read_sql('SELECT * FROM issues', conn)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
else:
    st.error("Unauthorized user. Please contact the administrator.")
    st.stop()

# Reporting section
if df.empty:
    st.warning("No issue data to display.")
else:
    st.sidebar.header("🛠️ Filters")
    # Date range filter
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    date_range = st.sidebar.date_input("Date range", [min_date, max_date])
    if len(date_range) != 2:
        st.error("Please select a valid start and end date.")
        st.stop()
    start_date, end_date = date_range
    start = datetime.combine(start_date, datetime.min.time())
    end = datetime.combine(end_date, datetime.max.time())

    # Category filter (upload category)
    categories = pd.read_sql('SELECT DISTINCT category FROM uploads', conn)['category'].tolist()
    selected_categories = st.sidebar.multiselect("Upload Category", categories, default=categories)

    mask = (
        (df['date'] >= start) & (df['date'] <= end)
    )
    # Join with uploads to filter by category
    df = pd.read_sql('''
        SELECT issues.*, uploads.category FROM issues
        JOIN uploads ON issues.upload_id = uploads.id
    ''', conn, parse_dates=['date'])
    mask &= df['category'].isin(selected_categories)
    filtered = df.loc[mask]

    st.subheader(f"📈 Issues Report: {start.date()} to {end.date()}")
    st.write(f"Total issues: {len(filtered)}")

    # Top branches
    branch_counts = filtered['branch'].value_counts().reset_index()
    branch_counts.columns = ['branch', 'count']
    st.plotly_chart(
        px.bar(branch_counts.head(10), x='branch', y='count', title='Top 10 Branches'),
        use_container_width=True
    )

    # Trend over time
    trend = filtered.groupby(filtered['date'].dt.date).size().reset_index(name='count')
    st.plotly_chart(
        px.line(trend, x='date', y='count', title='Daily Issue Trend'),
        use_container_width=True
    )

    # Top issue descriptions
    st.subheader("🔍 Top Issue Descriptions")
    issue_counts = filtered['issues'].value_counts().rename_axis('issue').reset_index(name='count')
    st.dataframe(issue_counts.head(20))

    # By area manager
    am_counts = filtered['area_manager'].value_counts().reset_index()
    am_counts.columns = ['area manager', 'count']
    st.plotly_chart(
        px.pie(am_counts, names='area manager', values='count', title='Issues by Area Manager'),
        use_container_width=True
    )

    # Download filtered data
    st.download_button(
        "📥 Download Filtered Data", filtered.to_csv(index=False).encode(), "issues_report.csv"
    )
