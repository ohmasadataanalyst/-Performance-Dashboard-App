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
view_only_users = ["mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"]

# Streamlit config
st.set_page_config(page_title="Performance Dashboard", layout="wide")
st.title("📊 Performance Dashboard from Excel")

# Authentication inputs
username = st.text_input("Enter your full name:").strip().lower()
password = st.text_input("Enter your password:", type="password")

# Authorized logic
def is_admin(user, pwd):
    if user in db_admin:
        return bcrypt.checkpw(pwd.encode(), db_admin[user])
    return False

if username:
    if is_admin(username, password):
        st.success("Welcome Admin! You have full access.")
        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            if {'Date','Category','Performance'}.issubset(df.columns):
                df['Date'] = pd.to_datetime(df['Date'])
                # Sidebar
                st.sidebar.header("🛠️ Report Filters")
                freq = st.sidebar.selectbox("Select frequency", ['Daily','Weekly','Monthly','Yearly'])
                cats = st.sidebar.multiselect("Select category", ['operation-training','CCTV','complaints','missing','visits'], default=['operation-training','CCTV','complaints','missing','visits'])
                # Date range
                now = datetime.now()
                if freq=='Daily': start = now - timedelta(days=1)
                elif freq=='Weekly': start = now - timedelta(weeks=1)
                elif freq=='Monthly': start = now - timedelta(days=30)
                else: start = now - timedelta(days=365)
                filt = df[(df['Date']>=start)&(df['Date']<=now)&df['Category'].isin(cats)]
                st.subheader(f"📈 {freq} {', '.join(cats)} Report")
                st.write(f"From {start.date()} to {now.date()}")
                st.dataframe(filt)
                fig=px.line(filt.groupby('Date')['Performance'].mean().reset_index(),x='Date',y='Performance',title='Average Performance')
                st.plotly_chart(fig,use_container_width=True)
                csv = filt.to_csv(index=False).encode()
                st.download_button("📥 Download Filtered Data",csv,"filtered.csv")
            else:
                st.error("Your file needs 'Date', 'Category', and 'Performance' columns.")
    elif username in view_only_users:
        st.info("View-only: Upload disabled. Ask admin for updates.")
    else:
        st.error("Unauthorized user. Please contact the administrator.")
else:
    st.info("Enter full name and password to proceed.")
