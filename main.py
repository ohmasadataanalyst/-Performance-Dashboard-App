import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import os
from datetime import datetime, timedelta

# Persistent storage path
STORAGE_PATH = 'stored_issues.csv'

# Load existing storage or initialize empty DataFrame
if os.path.exists(STORAGE_PATH):
    stored_df = pd.read_csv(STORAGE_PATH, parse_dates=['date'])
else:
    stored_df = pd.DataFrame(columns=['code','issues','branch','area manager','date','report type'])

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
st.title("📊 Performance Dashboard from Excel")

# Authentication inputs
username = st.text_input("Enter your full name:").strip().lower()
password = st.text_input("Enter your password:", type="password")

# Helper to check admin credentials
def is_admin(user, pwd):
    return user in db_admin and bcrypt.checkpw(pwd.encode(), db_admin[user])

# Decide on data source: for admins after upload, storage updates, for view-only, just storage
if username:
    if is_admin(username, password):
        st.success("Welcome Admin! You can upload new data or view reports.")
        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
        if uploaded_file:
            upload_df = pd.read_excel(uploaded_file)
            # Standardize and validate
            expected = {"code","issues","branch","area manager","date","report type"}
            if expected.issubset(upload_df.columns.str.lower()):
                upload_df.columns = upload_df.columns.str.lower()
                upload_df['date'] = pd.to_datetime(upload_df['date'], dayfirst=True)
                # Append new data, drop duplicates
                combined = pd.concat([stored_df, upload_df], ignore_index=True)
                combined.drop_duplicates(subset=combined.columns.tolist(), inplace=True)
                # Save back to storage
                combined.to_csv(STORAGE_PATH, index=False)
                stored_df = combined
                st.success(f"Data uploaded and saved. Total records: {len(stored_df)}")
            else:
                st.error(f"Excel must contain columns: {', '.join(expected)}")
        # Use stored_df for reporting
        df = stored_df.copy()
    elif username in view_only_users:
        st.info("View-only: Displaying saved reports.")
        df = stored_df.copy()
    else:
        st.error("Unauthorized user. Please contact the administrator.")
        st.stop()
else:
    st.info("Enter full name and password to proceed.")
    st.stop()

# If we reach here, df contains data to report
if df.empty:
    st.warning("No data available. Admins can upload new data.")
else:
    # Sidebar filters
    st.sidebar.header("🛠️ Filters")
    freq = st.sidebar.selectbox("Frequency", ['Daily', 'Weekly', 'Monthly', 'Yearly'])
    report_types = st.sidebar.multiselect("Report Type", df['report type'].unique(), default=df['report type'].unique())

    # Compute date range based on freq
    now = datetime.now()
    if freq == 'Daily': start = now - timedelta(days=1)
    elif freq == 'Weekly': start = now - timedelta(weeks=1)
    elif freq == 'Monthly': start = now - timedelta(days=30)
    else: start = now - timedelta(days=365)

    mask = (df['date'] >= start) & (df['date'] <= now) & df['report type'].isin(report_types)
    filtered = df.loc[mask]

    st.subheader(f"📈 Issues Report: {freq} ({start.date()} to {now.date()})")
    st.write(f"Total issues: {len(filtered)}")

    # Top branches
    st.subheader("🏷️ Top Branches by Issue Count")
    branch_counts = filtered['branch'].value_counts().reset_index()
    branch_counts.columns = ['branch', 'count']
    fig1 = px.bar(branch_counts.head(10), x='branch', y='count', title='Top 10 Branches')
    st.plotly_chart(fig1, use_container_width=True)

    # Trend over time
    st.subheader("⏱️ Issue Trend Over Time")
    trend = filtered.groupby(filtered['date'].dt.date).size().reset_index(name='count')
    fig2 = px.line(trend, x='date', y='count', title='Daily Issue Trend')
    st.plotly_chart(fig2, use_container_width=True)

    # Top issue types
    st.subheader("🔍 Top Issue Descriptions")
    issue_counts = filtered['issues'].value_counts().reset_index()
    issue_counts.columns = ['issue', 'count']
    st.dataframe(issue_counts.head(20))

    # By area manager
    st.subheader("👤 Issues by Area Manager")
    am_counts = filtered['area manager'].value_counts().reset_index()
    am_counts.columns = ['area manager', 'count']
    fig3 = px.pie(am_counts, names='area manager', values='count', title='Issues by Area Manager')
    st.plotly_chart(fig3, use_container_width=True)

    # Download
    csv = filtered.to_csv(index=False).encode()
    st.download_button("📥 Download Filtered Data", data=csv, file_name="issues_report.csv")
