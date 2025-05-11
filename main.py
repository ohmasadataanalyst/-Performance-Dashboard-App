import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
import shutil
import base64
from datetime import datetime, date # Import date

# Database setup
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Create/Update uploads table
# Base schema without submission_date initially
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    uploader TEXT,
    timestamp TEXT,          -- Actual system upload time
    file_type TEXT,
    category TEXT,
    file BLOB
)''')
conn.commit() 

# Add submission_date column to uploads if it doesn't exist
try:
    c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT") # User-specified effective date for the report
    conn.commit()
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        pass # Column already exists
    else:
        # This might occur if the script is run without write permissions to the DB file directory initially
        print(f"DB Warning (altering uploads table): {e}. This might be an issue if new features depend on this column.")


# Create issues table (idempotent)
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    upload_id INTEGER,
    code TEXT,
    issues TEXT,
    branch TEXT,
    area_manager TEXT,
    date TEXT,            -- This will store the effective_report_date from uploads.submission_date
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

# --- REVISED AUTHENTICATION FUNCTION ---
def check_login():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_name = None
        st.session_state.user_role = None

    if not st.session_state.authenticated:
        st.title("📊 Login - Performance Dashboard")
        st.subheader("Please log in to continue")
        
        with st.form("login_form"):
            username = st.text_input("Full Name:", key="auth_username").strip().lower()
            password = st.text_input("Password:", type="password", key="auth_password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if username in db_admin and bcrypt.checkpw(password.encode(), db_admin[username]):
                    st.session_state.authenticated = True
                    st.session_state.user_name = username
                    st.session_state.user_role = 'admin'
                    st.rerun() 
                elif username in view_only:
                    if password: 
                        st.session_state.authenticated = True
                        st.session_state.user_name = username
                        st.session_state.user_role = 'view_only'
                        st.rerun() 
                    else:
                        st.error("Password cannot be empty for view-only users.")
                elif username or password : 
                     st.error("Invalid username or password.")
                else:
                    st.info("Please enter your credentials.")
        return False 
    return True 

if not check_login():
    st.stop() 

st.title("📊 Classic Dashboard for Performance") 
st.sidebar.success(f"Logged in as: {st.session_state.user_name.title()} ({st.session_state.user_role})")
if st.sidebar.button("Logout", key="logout_button_main"):
    st.session_state.authenticated = False
    st.session_state.user_name = None
    st.session_state.user_role = None
    st.rerun()

is_admin = st.session_state.user_role == 'admin'
current_user = st.session_state.user_name
# --- END OF REVISED AUTHENTICATION ---


# PDF generator
def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path:
        st.error("wkhtmltopdf path not set. Please provide the path in the sidebar.")
        return None
    try:
        import pdfkit
        config = pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {
            'enable-local-file-access': None,
            'images': None,
            'encoding': "UTF-8",
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
        }
        pdfkit.from_string(html, fname, configuration=config, options=options)
        with open(fname, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"wkhtmltopdf not found at the specified path: {wk_path}. Please ensure it's installed and the path is correct.")
        return None
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None

# Sidebar: controls
st.sidebar.header("🔍 Filters & Options")

# Upload control for admins
if is_admin:
    st.sidebar.subheader("Admin Controls")
    file_type_upload = st.sidebar.selectbox("File type for upload", ["opening", "closing", "handover", "meal training"], key="upload_file_type")
    category_upload = st.sidebar.selectbox("Category for upload", ['operation-training', 'CCTV', 'complaints', 'missing', 'visits', 'meal training'], key="upload_category")
    
    effective_report_date = st.sidebar.date_input(
        "Effective Date of Report:",
        value=date.today(), # Use date.today() for st.date_input
        key="effective_report_date_upload"
    )

    up = st.sidebar.file_uploader("Upload Excel", type=["xlsx"], key="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if up and upload_btn and effective_report_date: 
        data = up.getvalue()
        ts = datetime.now().isoformat()
        effective_date_str = effective_report_date.isoformat()

        c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type=? AND category=? AND submission_date=?',
                  (up.name, current_user, file_type_upload, category_upload, effective_date_str))
        
        if c.fetchone()[0] == 0:
            c.execute(
                'INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (up.name, current_user, ts, file_type_upload, category_upload, effective_date_str, sqlite3.Binary(data))
            )
            uid = c.lastrowid
            try:
                df_up = pd.read_excel(io.BytesIO(data))
                df_up.columns = [col.strip().lower() for col in df_up.columns]
                
                required_cols = ['code', 'issues', 'branch', 'area manager', 'date']
                missing_cols = [col for col in required_cols if col not in df_up.columns]

                if missing_cols:
                    st.sidebar.error(f"Excel missing columns: {', '.join(missing_cols)}")
                    c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                    conn.commit()
                else:
                    df_up['excel_date_validated'] = pd.to_datetime(df_up['date'], dayfirst=True, errors='coerce')
                    original_len = len(df_up)
                    df_up.dropna(subset=['excel_date_validated'], inplace=True)
                    
                    if len(df_up) < original_len:
                        st.sidebar.warning(f"{original_len - len(df_up)} rows dropped due to invalid date format in Excel's 'date' column.")

                    if df_up.empty:
                        st.sidebar.error("No valid data rows to process after Excel date validation.")
                        c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                        conn.commit()
                    else:
                        for _, row in df_up.iterrows():
                            c.execute('INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (uid, row['code'], row['issues'], row['branch'], row['area manager'],
                                     effective_date_str, 
                                     file_type_upload))
                        conn.commit()
                        st.sidebar.success(f"Uploaded {up.name} ({len(df_up)} records) for effective date {effective_report_date.strftime('%Y-%m-%d')}")
                        # Consider st.rerun() if list of uploads needs immediate update
            except Exception as e:
                st.sidebar.error(f"Error processing Excel: {e}")
                c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                conn.commit()
        else:
            st.sidebar.warning(f"This file (name: {up.name}, uploader: {current_user}, type: {file_type_upload}, category: {category_upload}, effective date: {effective_date_str}) has already been uploaded or a similar record exists.")


# wkhtmltopdf path
default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk, help="Path to wkhtmltopdf executable.")

# Load uploads for selection and deletion
df_uploads = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY timestamp DESC', conn)

def format_display_date(date_val):
    if pd.isna(date_val) or date_val is None:
        return "N/A"
    try:
        return pd.to_datetime(date_val).strftime('%Y-%m-%d')
    except Exception: # Handle cases where date_val might not be a valid date string
        return str(date_val) if date_val else "N/A"

df_uploads['display_submission_date'] = df_uploads['submission_date'].apply(format_display_date)


# Scope selection
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [
    f"{row['id']} - {row['filename']} ({row['file_type']}) Eff.Date: {row['display_submission_date']}" 
    for index, row in df_uploads.iterrows()
]
sel_display = st.sidebar.selectbox("Select upload to analyze:", scope_opts, key="select_upload_scope")
sel_id = None
if sel_display != 'All uploads':
    sel_id = int(sel_display.split(' - ')[0])

# Admin: delete submission
if is_admin:
    st.sidebar.subheader("Manage Submissions")
    delete_opts = ['Select ID to Delete'] + [
        f"{row['id']} - {row['filename']} (Eff.Date: {row['display_submission_date']})" 
        for index, row in df_uploads.iterrows()
    ]
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission:", delete_opts, key="delete_submission_id")
    if del_choice_display != 'Select ID to Delete':
        del_id = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id}", key=f"confirm_del_{del_id}", type="primary"):
            c.execute('DELETE FROM issues WHERE upload_id=?', (del_id,))
            c.execute('DELETE FROM uploads WHERE id=?', (del_id,))
            conn.commit()
            st.sidebar.success(f"Deleted submission {del_id} and its associated issues.")
            st.rerun() 

# Fetch data for dashboard
sql = 'SELECT i.*, u.category as upload_category, u.file_type as master_file_type FROM issues i JOIN uploads u ON u.id = i.upload_id'
params = []
if sel_id:
    sql += ' WHERE i.upload_id = ?'
    params.append(sel_id)
df = pd.read_sql(sql, conn, params=params, parse_dates=['date']) 

if df.empty:
    st.warning("No data to display for the selected scope. Please upload data or broaden filters.")
    st.stop()

# Filters
st.sidebar.subheader("Dashboard Filters")
min_date_val = df['date'].min() 
max_date_val = df['date'].max()

min_report_date = min_date_val.date() if pd.notna(min_date_val) else date.today()
max_report_date = max_date_val.date() if pd.notna(max_date_val) else date.today()

date_range_val = [min_report_date, max_report_date]

date_range = st.sidebar.date_input(
    "Date range (based on Effective Report Date):", 
    value=date_range_val, 
    min_value=min_report_date, 
    max_value=max_report_date, 
    key="date_range_filter"
)
if not date_range or len(date_range) != 2: 
    date_range = [min_report_date, max_report_date]


branch_opts = ['All'] + sorted(df['branch'].astype(str).unique().tolist()) 
sel_br = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")

cat_opts = ['All'] + sorted(df['upload_category'].astype(str).unique().tolist())
sel_cat = st.sidebar.multiselect("Category:", cat_opts, default=['All'], key="category_filter")

file_type_filter_opts = ['All'] + sorted(df['report_type'].astype(str).unique().tolist())
sel_ft = st.sidebar.multiselect("File Type (Report Type):", file_type_filter_opts, default=['All'], key="file_type_filter")

# Apply filters
df_f = df.copy()
if date_range and len(date_range) == 2:
    start_date_filter = date_range[0]
    end_date_filter = date_range[1]
    df_f = df_f[(df_f['date'].dt.date >= start_date_filter) & (df_f['date'].dt.date <= end_date_filter)]

if 'All' not in sel_br:
    df_f = df_f[df_f['branch'].isin(sel_br)]
if 'All' not in sel_cat:
    df_f = df_f[df_f['upload_category'].isin(sel_cat)]
if 'All' not in sel_ft:
    df_f = df_f[df_f['report_type'].isin(sel_ft)]

# Dashboard
st.subheader(f"Filtered Issues from {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}")
st.write(f"Total issues found: {len(df_f)}")

if df_f.empty:
    st.info("No data matches the current filter criteria.")
    st.stop()

# Charts
figs = {}
if not df_f.empty:
    col1, col2 = st.columns(2)
    with col1:
        if 'branch' in df_f.columns and not df_f['branch'].isnull().all():
            branch_data = df_f.astype({'branch': str}).groupby('branch').size().reset_index(name='count').sort_values('count', ascending=False)
            if not branch_data.empty:
                figs['Branch'] = px.bar(branch_data, x='branch', y='count', title='Issues by Branch',
                                        template="plotly_white")
                st.plotly_chart(figs['Branch'], use_container_width=True)
        
        if 'report_type' in df_f.columns and not df_f['report_type'].isnull().all():
            rt_data = df_f.astype({'report_type': str}).groupby('report_type').size().reset_index(name='count').sort_values('count', ascending=False)
            if not rt_data.empty:
                figs['Report Type'] = px.bar(rt_data, x='report_type', y='count', title='Issues by Report Type',
                                             template="plotly_white")
                st.plotly_chart(figs['Report Type'], use_container_width=True)

    with col2:
        if 'area_manager' in df_f.columns and not df_f['area_manager'].isnull().all():
            am_data = df_f.astype({'area_manager': str}).groupby('area_manager').size().reset_index(name='count')
            if not am_data.empty:
                figs['Area Manager'] = px.pie(am_data, names='area_manager', values='count', title='Issues by Area Manager', hole=0.3,
                                              template="plotly_white")
                st.plotly_chart(figs['Area Manager'], use_container_width=True)

        if 'upload_category' in df_f.columns and not df_f['upload_category'].isnull().all():
            uc_data = df_f.astype({'upload_category': str}).groupby('upload_category').size().reset_index(name='count').sort_values('count', ascending=False)
            if not uc_data.empty:
                figs['Category'] = px.bar(uc_data, x='upload_category', y='count', title='Issues by Upload Category',
                                          template="plotly_white")
                st.plotly_chart(figs['Category'], use_container_width=True)

    if 'date' in df_f.columns and not df_f['date'].isnull().all(): 
        trend_data = df_f.groupby(df_f['date'].dt.date).size().reset_index(name='count')
        trend_data = trend_data.sort_values('date') 
        if not trend_data.empty:
            figs['Trend'] = px.line(trend_data, x='date', y='count', title='Issues Trend Over Time (by Effective Report Date)', markers=True,
                                    template="plotly_white")
            st.plotly_chart(figs['Trend'], use_container_width=True)


# Detailed records
if len(df_f) < 50 or (date_range and date_range[0] == date_range[1]):
    st.subheader("Detailed Records (Filtered)")
    df_display = df_f[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']].copy()
    df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
    st.dataframe(df_display)


# Top issues
st.subheader("Top Issues (Filtered)")
if 'issues' in df_f.columns and not df_f['issues'].isnull().all():
    top_issues_data = df_f['issues'].astype(str).value_counts().head(20).rename_axis('Issue Description').reset_index(name='Frequency')
    if not top_issues_data.empty:
        st.dataframe(top_issues_data)

# Downloads
st.sidebar.subheader("Downloads")
csv_data = df_f.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("Download Filtered Data as CSV", csv_data, "filtered_issues.csv", "text/csv", key="download_csv")

if st.sidebar.button("Prepare Visuals PDF", key="prep_visuals_pdf"):
    if not wk_path or wk_path == "not found":
        st.sidebar.error("wkhtmltopdf path not set or invalid. Cannot generate PDF.")
    elif not figs:
        st.sidebar.warning("No visuals to include in the PDF.")
    else:
        html = """
        <html><head><meta charset="utf-8"><title>Visuals Report</title>
        <style> /* ... existing styles ... */ </style></head><body>
        """
        html += f"<h1>Visuals Report ({date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')})</h1>"
        chart_titles_in_order = ["Branch", "Area Manager", "Report Type", "Category", "Trend"]
        
        for title in chart_titles_in_order:
            if title in figs:
                fig = figs[title]
                try:
                    img_bytes = fig.to_image(format='png', engine='kaleido', scale=2)
                    b64_img = base64.b64encode(img_bytes).decode()
                    html += f"<h2>{title}</h2><img src='data:image/png;base64,{b64_img}' alt='{title}'/>"
                except Exception as e:
                    st.sidebar.warning(f"Could not convert figure '{title}' to image: {e}. Ensure 'kaleido' is installed.")
        html += '</body></html>'
        
        pdf_content = generate_pdf(html, fname='visuals_report.pdf', wk_path=wk_path)
        if pdf_content:
            st.session_state.pdf_visuals_data = pdf_content
            st.sidebar.success("Visuals PDF is ready for download.")
        else:
            if 'pdf_visuals_data' in st.session_state:
                del st.session_state.pdf_visuals_data

if 'pdf_visuals_data' in st.session_state and st.session_state.pdf_visuals_data:
    st.sidebar.download_button(
        label="Download Visuals PDF Now",
        data=st.session_state.pdf_visuals_data,
        file_name="visuals_report.pdf",
        mime="application/pdf",
        key="action_download_visuals_pdf"
    )

if st.sidebar.button("Prepare Full Dashboard PDF", key="prep_dashboard_pdf"):
    if not wk_path or wk_path == "not found":
        st.sidebar.error("wkhtmltopdf path not set or invalid. Cannot generate PDF.")
    elif df_f.empty:
        st.sidebar.warning("No data to include in the Dashboard PDF.")
    else:
        html_full = f"<head><meta charset='utf-8'><style>body {{font-family: sans-serif;}} table {{border-collapse: collapse; width: 100%;}} th, td {{border: 1px solid #ddd; padding: 8px; text-align: left;}} th {{background-color: #f2f2f2;}}</style></head>"
        html_full += f"<h1>Dashboard Report ({date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')})</h1>"
        df_pdf_view = df_f[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']].copy()
        df_pdf_view['date'] = df_pdf_view['date'].dt.strftime('%Y-%m-%d')
        html_full += df_pdf_view.to_html(index=False, classes="dataframe", border=0)
        
        pdf_full_content = generate_pdf(html_full, fname='dashboard_report.pdf', wk_path=wk_path)
        if pdf_full_content:
            st.session_state.pdf_dashboard_data = pdf_full_content
            st.sidebar.success("Dashboard PDF is ready for download.")
        else:
            if 'pdf_dashboard_data' in st.session_state:
                del st.session_state.pdf_dashboard_data

if 'pdf_dashboard_data' in st.session_state and st.session_state.pdf_dashboard_data:
    st.sidebar.download_button(
        label="Download Dashboard PDF Now",
        data=st.session_state.pdf_dashboard_data,
        file_name="dashboard_report.pdf",
        mime="application/pdf",
        key="action_download_dashboard_pdf"
    )

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH}")
