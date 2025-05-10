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
# Create uploads table if not exists
c.execute(
    '''CREATE TABLE IF NOT EXISTS uploads (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           filename TEXT,
           uploader TEXT,
           timestamp TEXT,
           file BLOB
       )''')
# Ensure metadata columns
def add_column(table, column, col_type):
    cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
add_column('uploads','file_type','TEXT')
add_column('uploads','category','TEXT')
# Create issues table
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

# Auth
user = st.text_input("Enter your full name:").strip().lower()
pwd = st.text_input("Enter your password:", type="password")

if not user:
    st.info("Enter credentials to proceed.")
    st.stop()

is_admin = user in db_admin and bcrypt.checkpw(pwd.encode(), db_admin[user])
if not is_admin and user not in view_only:
    st.error("Unauthorized user.")
    st.stop()

# Admin upload
if is_admin:
    st.success("Admin access granted.")
    file_type = st.selectbox("File type", ["opening","closing","handover","meal training"])
    category = st.selectbox("Category", ['operation-training','CCTV','complaints','missing','visits','meal training'])
    up = st.file_uploader("Upload Excel", type=["xlsx"] )
    if up:
        b = up.getvalue()
        ts = datetime.now().isoformat()
        c.execute(
            'INSERT INTO uploads (filename,uploader,timestamp,file_type,category,file) VALUES (?,?,?,?,?,?)',
            (up.name,user,ts,file_type,category,sqlite3.Binary(b))
        )
        uid = c.lastrowid
        dfu = pd.read_excel(io.BytesIO(b))
        dfu.columns = dfu.columns.str.lower()
        dfu['date'] = pd.to_datetime(dfu['date'],dayfirst=True)
        for _,r in dfu.iterrows():
            c.execute(
                'INSERT INTO issues VALUES (?,?,?,?,?,?,?)',
                (uid,r['code'],r['issues'],r['branch'],r['area manager'],r['date'].isoformat(),file_type)
            )
        conn.commit()
        st.success(f"Uploaded {up.name} as {file_type}/{category} with {len(dfu)} records.")
    st.sidebar.header("Past Uploads")
    ups = pd.read_sql('SELECT id,filename,uploader,timestamp,file_type,category FROM uploads ORDER BY timestamp DESC',conn)
    if not ups.empty:
        choice = st.sidebar.selectbox("Upload",ups.apply(lambda x:f"{x.id}-{x.filename}[{x.file_type}/{x.category}]",axis=1))
        sel_id=int(choice.split('-')[0])
    else:
        sel_id=None
else:
    st.info("View-only mode.")
    # show latest combined
    sel_id=None

# Load issues based on selection or all
def load_issues(uid):
    if uid:
        return pd.read_sql(f"SELECT issues.*,u.category FROM issues JOIN uploads u ON u.id=issues.upload_id WHERE upload_id={uid}",conn,parse_dates=['date'])
    return pd.read_sql("SELECT issues.*,u.category FROM issues JOIN uploads u ON u.id=issues.upload_id",conn,parse_dates=['date'])

df = load_issues(sel_id)
if df.empty:
    st.warning("No data.")
    st.stop()

# Filters
dates = st.sidebar.date_input("Date range",[df['date'].min().date(),df['date'].max().date()])
if len(dates)!=2:
    st.error("Select start and end")
    st.stop()
start,end=[datetime.combine(d,datetime.min.time()) if i==0 else datetime.combine(d,datetime.max.time()) for i,d in enumerate(dates)]
cats = st.sidebar.multiselect("Upload Category",df['category'].unique(),default=df['category'].unique())
mask=(df['date']>=start)&(df['date']<=end)&df['category'].isin(cats)
f=df.loc[mask]

# Report
st.subheader(f"Report: {start.date()} to {end.date()}")
st.write(f"Total issues: {len(f)}")
# Charts
t1=f['branch'].value_counts().head(10).reset_index();t1.columns=['branch','count']
st.plotly_chart(px.bar(t1,x='branch',y='count',title='Top Branches'),use_container_width=True)
t2=f.groupby(f['date'].dt.date).size().reset_index(name='count')
st.plotly_chart(px.line(t2,x='date',y='count',title='Trend'),use_container_width=True)
st.subheader("Top Issues")
st.dataframe(f['issues'].value_counts().rename_axis('issue').reset_index(name='count').head(20))
t3=f['area_manager'].value_counts().reset_index();t3.columns=['area_manager','count']
st.plotly_chart(px.pie(t3,names='area_manager',values='count',title='By Area Manager'),use_container_width=True)
st.download_button("Download CSV",f.to_csv(index=False).encode(),"issues.csv")
