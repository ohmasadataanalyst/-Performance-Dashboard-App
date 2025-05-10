import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
from datetime import datetime, timedelta

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

# Authentication
username = st.text_input("Enter your full name:").strip().lower()
password = st.text_input("Enter your password:", type="password")

def is_admin(user, pwd):
    return user in db_admin and bcrypt.checkpw(pwd.encode(), db_admin[user])

if username:
    if is_admin(username, password):
        st.success("Welcome Admin! You can upload and view detailed issue reports.")
        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            # Ensure expected columns
            expected = {"code", "issues", "branch", "area manager", "date", "report type"}
            if expected.issubset(df.columns.str.lower()):
                # Standardize column names
                df.columns = df.columns.str.lower()
                # Parse dates assuming day-first format (e.g., 10/5/2025 = 10 May 2025)
                df['date'] = pd.to_datetime(df['date'], dayfirst=True)

                # Sidebar filters
                st.sidebar.header("🛠️ Filters")
                freq = st.sidebar.selectbox("Frequency", ['Daily', 'Weekly', 'Monthly', 'Yearly'])
                report_types = st.sidebar.multiselect("Report Type", df['report type'].unique())

                # Date range
                now = datetime.now()
                if freq == 'Daily':
                    start = now - timedelta(days=1)
                elif freq == 'Weekly':
                    start = now - timedelta(weeks=1)
                elif freq == 'Monthly':
                    start = now - timedelta(days=30)
                else:
                    start = now - timedelta(days=365)

                mask = (df['date'] >= start) & (df['date'] <= now)
                if report_types:
                    mask &= df['report type'].isin(report_types)
                filtered = df.loc[mask]

                st.subheader(f"📈 Issues Report: {freq} ({start.date()} to {now.date()})")
                st.write(f"Total issues: {len(filtered)}")

                # Top 10 branches by issue count
                st.subheader("🏷️ Top Branches by Issue Count")
                branch_counts = filtered['branch'].value_counts().reset_index()
                branch_counts.columns = ['branch', 'count']
                fig1 = px.bar(
                    branch_counts.head(10), x='branch', y='count', title='Top 10 Branches'
                )
                st.plotly_chart(fig1, use_container_width=True)

                # Issues trend over time
                st.subheader("⏱️ Issue Trend Over Time")
                trend = (
                    filtered.groupby(filtered['date'].dt.date)
                    .size()
                    .reset_index(name='count')
                )
                fig2 = px.line(trend, x='date', y='count', title='Daily Issue Trend')
                st.plotly_chart(fig2, use_container_width=True)

                # Top issue types
                st.subheader("🔍 Top Issue Descriptions")
                issue_counts = filtered['issues'].value_counts().reset_index()
                issue_counts.columns = ['issue', 'count']
                st.dataframe(issue_counts.head(20))

                # By Area Manager
                st.subheader("👤 Issues by Area Manager")
                am_counts = filtered['area manager'].value_counts().reset_index()
                am_counts.columns = ['area manager', 'count']
                fig3 = px.pie(
                    am_counts, names='area manager', values='count', title='Issues by Area Manager'
                )
                st.plotly_chart(fig3, use_container_width=True)

                # Data download
                csv = filtered.to_csv(index=False).encode()
                st.download_button(
                    "📥 Download Filtered Data", data=csv, file_name="issues_report.csv"
                )
            else:
                st.error(f"Excel must contain columns: {', '.join(expected)}")
        else:
            st.info("Upload your data to generate reports.")

    elif username in view_only_users:
        st.info("View-only: You can view the latest issues report above.")
    else:
        st.error("Unauthorized user. Please contact the administrator.")
else:
    st.info("Enter full name and password to proceed.")
