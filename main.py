import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
import shutil
import base64
from datetime import datetime, date

# --- Database setup ---
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Create uploads table if not exists (base schema)
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    uploader TEXT,
    timestamp TEXT,
    file_type TEXT,
    category TEXT,
    file BLOB
)''')
conn.commit()

# Add submission_date column to uploads if it doesn't exist (ROBUST CHECK)
c.execute("PRAGMA table_info(uploads)")
existing_columns = [column[1] for column in c.fetchall()]
if 'submission_date' not in existing_columns:
    try:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        if 'db_schema_updated_message_shown' not in st.session_state:
            st.session_state.db_schema_updated_message_shown = True
            st.toast("Database 'uploads' table schema updated. Column 'submission_date' added.", icon="ℹ️")
    except sqlite3.OperationalError as e:
        st.error(f"CRITICAL DATABASE ERROR: Could not add 'submission_date' column to 'uploads' table: {e}. "
                 f"The application cannot proceed. Please check DB permissions or delete '{DB_PATH}' and restart.")
        st.stop()

# Create issues table (idempotent)
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

st.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- AUTHENTICATION FUNCTION ---
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
                    st.session_state.user_role = 'admin' # Explicitly set role
                    st.rerun() 
                elif username in view_only:
                    if password: 
                        st.session_state.authenticated = True
                        st.session_state.user_name = username
                        st.session_state.user_role = 'view_only' # Explicitly set role
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

# --- User is Authenticated, Proceed with App ---
st.title("📊 Classic Dashboard for Performance") 

# DEBUG: Check session state immediately after successful login confirmation
# These should be populated if login was successful
user_name_display = "N/A"
user_role_display = "N/A"

if 'user_name' in st.session_state and st.session_state.user_name:
    user_name_display = st.session_state.user_name.title()
if 'user_role' in st.session_state and st.session_state.user_role:
    user_role_display = st.session_state.user_role

st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")

if st.sidebar.button("Logout", key="logout_button_main"):
    st.session_state.authenticated = False
    st.session_state.user_name = None
    st.session_state.user_role = None
    st.rerun()

# Determine admin status
is_admin = False # Default to false
if 'user_role' in st.session_state and st.session_state.user_role == 'admin':
    is_admin = True
current_user = st.session_state.get('user_name', 'Unknown User')


# --- MORE DEBUGGING FOR ADMIN SECTION ---
st.sidebar.markdown("---") # Separator for clarity
st.sidebar.markdown(f"**Debug Info:**")
st.sidebar.markdown(f"* `st.session_state.authenticated`: `{st.session_state.get('authenticated', 'Not Set')}`")
st.sidebar.markdown(f"* `st.session_state.user_name`: `{st.session_state.get('user_name', 'Not Set')}`")
st.sidebar.markdown(f"* `st.session_state.user_role`: `{st.session_state.get('user_role', 'Not Set')}`")
st.sidebar.markdown(f"* `is_admin` variable: `{is_admin}`")
st.sidebar.markdown("---")


# PDF generator
def generate_pdf(html, fname='report.pdf', wk_path=None):
    # (Same as before)
    if not wk_path or wk_path == "not found":
        st.error("wkhtmltopdf path not set or invalid. Please provide the path in the sidebar.")
        return None
    try:
        import pdfkit
        config = pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {
            'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8",
            'load-error-handling': 'ignore', 'load-media-error-handling': 'ignore',
        }
        pdfkit.from_string(html, fname, configuration=config, options=options)
        with open(fname, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"wkhtmltopdf not found at the specified path: {wk_path}. Ensure it's installed and path is correct.")
        return None
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None

# Sidebar: controls
st.sidebar.header("🔍 Filters & Options")

# Upload control for admins
if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("*(You are seeing this because `is_admin` is True)*") # Confirmation message
    st.sidebar.markdown("Set the parameters below, choose your Excel file, then click 'Upload Data'.")
    file_type_upload = st.sidebar.selectbox("File type for upload", ["opening", "closing", "handover", "meal training"], key="upload_file_type")
    category_upload = st.sidebar.selectbox("Category for upload", ['operation-training', 'CCTV', 'complaints', 'missing', 'visits', 'meal training'], key="upload_category")
    
    effective_report_date = st.sidebar.date_input(
        "**Effective Date of Report:**", 
        value=date.today(), 
        key="effective_report_date_upload",
        help="Select the date this report should be attributed to. All issues from the uploaded file will use this date."
    )

    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if upload_btn:
        if up and effective_report_date: 
            data = up.getvalue()
            ts = datetime.now().isoformat() 
            effective_date_str = effective_report_date.isoformat() 

            st.sidebar.info(f"Debug Upload: Effective Date selected: {effective_date_str}")

            c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type=? AND category=? AND submission_date=?',
                      (up.name, current_user, file_type_upload, category_upload, effective_date_str))
            
            if c.fetchone()[0] == 0:
                c.execute(
                    'INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (up.name, current_user, ts, file_type_upload, category_upload, effective_date_str, sqlite3.Binary(data))
                )
                uid = c.lastrowid
                st.sidebar.info(f"Debug Upload: DB insert for uploads.id {uid} with submission_date {effective_date_str}")
                try:
                    df_up = pd.read_excel(io.BytesIO(data))
                    df_up.columns = [col.strip().lower() for col in df_up.columns]
                    
                    required_cols = ['code', 'issues', 'branch', 'area manager', 'date'] 
                    missing_cols = [col for col in required_cols if col not in df_up.columns]

                    if missing_cols:
                        st.sidebar.error(f"Excel missing columns: {', '.join(missing_cols)}. Upload aborted.")
                        c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                        conn.commit()
                    else:
                        df_up['excel_date_validated'] = pd.to_datetime(df_up['date'], dayfirst=True, errors='coerce')
                        original_len = len(df_up)
                        df_up.dropna(subset=['excel_date_validated'], inplace=True)
                        
                        rows_dropped = original_len - len(df_up)
                        if rows_dropped > 0:
                            st.sidebar.warning(f"{rows_dropped} rows dropped from Excel due to invalid date format in its 'date' column.")

                        if df_up.empty:
                            st.sidebar.error("No valid data rows in Excel after 'date' column validation. Upload aborted.")
                            c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                            conn.commit()
                        else:
                            for _, row in df_up.iterrows():
                                c.execute('INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                        (uid, row['code'], row['issues'], row['branch'], row['area manager'],
                                         effective_date_str, 
                                         file_type_upload))
                            conn.commit()
                            st.sidebar.success(f"Uploaded '{up.name}' ({len(df_up)} records) with Effective Report Date: {effective_report_date.strftime('%Y-%m-%d')}")
                            st.rerun() 
                except Exception as e:
                    st.sidebar.error(f"Error processing Excel file '{up.name}': {e}. Upload rolled back.")
                    c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                    conn.commit()
            else:
                st.sidebar.warning(f"Duplicate: File '{up.name}' by '{current_user}' (type '{file_type_upload}', category '{category_upload}', effective date '{effective_date_str}') already uploaded.")
        else:
            if not up: st.sidebar.error("Please select an Excel file to upload.")
            # effective_report_date will always have a value from st.date_input
else: # This block executes if is_admin is False
    st.sidebar.warning("Admin controls are hidden. Please log in with an admin account to access them.")
    if st.session_state.get('authenticated'):
        st.sidebar.info(f"You are currently logged in as '{st.session_state.get('user_name', 'N/A')}' with role '{st.session_state.get('user_role', 'N/A')}'.")


# wkhtmltopdf path
default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk, help="Path to wkhtmltopdf executable. Required for PDF export.")

# Load uploads for selection and deletion
df_uploads = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)

def format_display_date(date_val_str):
    if pd.isna(date_val_str) or date_val_str is None: return "N/A"
    try: return datetime.strptime(str(date_val_str), '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError: return str(date_val_str) 

df_uploads['display_submission_date'] = df_uploads['submission_date'].apply(format_display_date)


# Scope selection
st.sidebar.subheader("Data Scope") # This subheader should always be visible if logged in
scope_opts_list = []
if not df_uploads.empty:
    scope_opts_list = [f"{row['id']} - {row['filename']} ({row['file_type']}) Eff.Date: {row['display_submission_date']}" for index, row in df_uploads.iterrows()]
scope_opts = ['All uploads'] + scope_opts_list
sel_display = st.sidebar.selectbox("Select upload to analyze:", scope_opts, key="select_upload_scope")
sel_id = None
if sel_display != 'All uploads': sel_id = int(sel_display.split(' - ')[0])

# Admin: delete submission (also conditional on is_admin)
if is_admin:
    st.sidebar.subheader("Manage Submissions") # This should also appear if Admin Controls appears
    delete_opts_list = []
    if not df_uploads.empty:
        delete_opts_list = [f"{row['id']} - {row['filename']} (Eff.Date: {row['display_submission_date']})" for index, row in df_uploads.iterrows()]
    delete_opts = ['Select ID to Delete'] + delete_opts_list
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission:", delete_opts, key="delete_submission_id")
    
    if del_choice_display != 'Select ID to Delete':
        del_id = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id}", key=f"confirm_del_btn_{del_id}", type="primary"): 
            c.execute('DELETE FROM issues WHERE upload_id=?', (del_id,))
            c.execute('DELETE FROM uploads WHERE id=?', (del_id,))
            conn.commit()
            st.sidebar.success(f"Deleted submission {del_id} and its associated issues.")
            st.rerun() 

# Fetch data for dashboard
sql = 'SELECT i.*, u.category as upload_category, u.file_type as master_file_type FROM issues i JOIN uploads u ON u.id = i.upload_id'
params = []
if sel_id:
    sql += ' WHERE i.upload_id = ?'; params.append(sel_id)
df = pd.read_sql(sql, conn, params=params, parse_dates=['date']) 

if df.empty:
    st.warning("No data to display for the selected scope. Please upload data or broaden filters.")
    st.stop()

# Filters
st.sidebar.subheader("Dashboard Filters") # This subheader should always be visible if logged in
min_date_val = df['date'].min(); max_date_val = df['date'].max()
min_report_date = min_date_val.date() if pd.notna(min_date_val) and hasattr(min_date_val, 'date') else date.today()
max_report_date = max_date_val.date() if pd.notna(max_date_val) and hasattr(max_date_val, 'date') else date.today()
if min_report_date > max_report_date: max_report_date = min_report_date
date_range_val = [min_report_date, max_report_date]
date_range = st.sidebar.date_input(
    "Filter by Effective Report Date:", value=date_range_val, 
    min_value=min_report_date, max_value=max_report_date, key="date_range_filter"
)
if not date_range or len(date_range) != 2: date_range = [min_report_date, max_report_date]

branch_opts = ['All'] + sorted(df['branch'].astype(str).unique().tolist()) 
sel_br = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")
cat_opts = ['All'] + sorted(df['upload_category'].astype(str).unique().tolist())
sel_cat = st.sidebar.multiselect("Category:", cat_opts, default=['All'], key="category_filter")
file_type_filter_opts = ['All'] + sorted(df['report_type'].astype(str).unique().tolist())
sel_ft = st.sidebar.multiselect("File Type (from Upload Setting):", file_type_filter_opts, default=['All'], key="file_type_filter")

# Apply filters
df_f = df.copy()
if date_range and len(date_range) == 2:
    start_date_filter, end_date_filter = date_range[0], date_range[1]
    if pd.api.types.is_datetime64_any_dtype(df_f['date']):
        df_f = df_f[(df_f['date'].dt.date >= start_date_filter) & (df_f['date'].dt.date <= end_date_filter)]
# ... (rest of filters are same) ...
if 'All' not in sel_br: df_f = df_f[df_f['branch'].isin(sel_br)]
if 'All' not in sel_cat: df_f = df_f[df_f['upload_category'].isin(sel_cat)]
if 'All' not in sel_ft: df_f = df_f[df_f['report_type'].isin(sel_ft)]


# Dashboard
st.subheader(f"Filtered Issues from Effective Report Date {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}")
st.write(f"Total issues found: {len(df_f)}")

if df_f.empty:
    st.info("No data matches the current filter criteria.")
    st.stop()

# Charts
figs = {}
if not df_f.empty:
    # (Chart generation logic same as before)
    col1, col2 = st.columns(2)
    def create_bar_chart(df_source, group_col, title):
        if group_col in df_source.columns and not df_source[group_col].isnull().all():
            data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count').sort_values('count', ascending=False)
            if not data.empty: return px.bar(data, x=group_col, y='count', title=title, template="plotly_white")
        return None
    def create_pie_chart(df_source, group_col, title):
        if group_col in df_source.columns and not df_source[group_col].isnull().all():
            data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count')
            if not data.empty: return px.pie(data, names=group_col, values='count', title=title, hole=0.3, template="plotly_white")
        return None
    with col1:
        figs['Branch'] = create_bar_chart(df_f, 'branch', 'Issues by Branch')
        if figs['Branch']: st.plotly_chart(figs['Branch'], use_container_width=True)
        figs['Report Type'] = create_bar_chart(df_f, 'report_type', 'Issues by Report Type (Upload Setting)')
        if figs['Report Type']: st.plotly_chart(figs['Report Type'], use_container_width=True)
    with col2:
        figs['Area Manager'] = create_pie_chart(df_f, 'area_manager', 'Issues by Area Manager')
        if figs['Area Manager']: st.plotly_chart(figs['Area Manager'], use_container_width=True)
        figs['Category'] = create_bar_chart(df_f, 'upload_category', 'Issues by Upload Category')
        if figs['Category']: st.plotly_chart(figs['Category'], use_container_width=True)
    if 'date' in df_f.columns and pd.api.types.is_datetime64_any_dtype(df_f['date']) and not df_f['date'].isnull().all(): 
        trend_data = df_f.groupby(df_f['date'].dt.date).size().reset_index(name='count').sort_values('date') 
        if not trend_data.empty:
            figs['Trend'] = px.line(trend_data, x='date', y='count', title='Issues Trend (by Effective Report Date)', markers=True, template="plotly_white")
            st.plotly_chart(figs['Trend'], use_container_width=True)

# Detailed records
if len(df_f) < 50 or (date_range and date_range[0] == date_range[1]):
    st.subheader("Detailed Records (Filtered)")
    df_display = df_f[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']].copy()
    if pd.api.types.is_datetime64_any_dtype(df_display['date']):
        df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d') 
    st.dataframe(df_display)

# Top issues
st.subheader("Top Issues (Filtered)")
if 'issues' in df_f.columns and not df_f['issues'].isnull().all():
    top_issues_data = df_f['issues'].astype(str).value_counts().head(20).rename_axis('Issue Description').reset_index(name='Frequency')
    if not top_issues_data.empty: st.dataframe(top_issues_data)

# Downloads
st.sidebar.subheader("Downloads") # This should always be visible if logged in
if not df_f.empty:
    # (Download logic same as before)
    csv_data = df_f.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download Filtered Data as CSV", csv_data, "filtered_issues.csv", "text/csv", key="download_csv")
    if st.sidebar.button("Prepare Visuals PDF", key="prep_visuals_pdf"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set or invalid. Cannot generate PDF.")
        elif not any(figs.values()): st.sidebar.warning("No visuals to include in the PDF.")
        else:
            # PDF generation code ... (shortened for brevity, it's the same)
            html_content = "..." # (as before)
            pdf_bytes = generate_pdf(html_content, fname='visuals_report.pdf', wk_path=wk_path)
            if pdf_bytes: st.session_state.pdf_visuals_data = pdf_bytes; st.sidebar.success("Visuals PDF ready.")
            else:
                if 'pdf_visuals_data' in st.session_state: del st.session_state.pdf_visuals_data
    if 'pdf_visuals_data' in st.session_state and st.session_state.pdf_visuals_data:
        st.sidebar.download_button(label="Download Visuals PDF Now", data=st.session_state.pdf_visuals_data, file_name="visuals_report.pdf", mime="application/pdf", key="action_download_visuals_pdf")
    if st.sidebar.button("Prepare Full Dashboard PDF", key="prep_dashboard_pdf"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set or invalid.")
        else:
            # PDF generation code ... (shortened for brevity, it's the same)
            html_full = "..." # (as before)
            pdf_full_bytes = generate_pdf(html_full, fname='dashboard_report.pdf', wk_path=wk_path)
            if pdf_full_bytes: st.session_state.pdf_dashboard_data = pdf_full_bytes; st.sidebar.success("Dashboard PDF ready.")
            else:
                if 'pdf_dashboard_data' in st.session_state: del st.session_state.pdf_dashboard_data
    if 'pdf_dashboard_data' in st.session_state and st.session_state.pdf_dashboard_data:
        st.sidebar.download_button(label="Download Dashboard PDF Now", data=st.session_state.pdf_dashboard_data, file_name="dashboard_report.pdf", mime="application/pdf", key="action_download_dashboard_pdf")
else:
    st.sidebar.info("No filtered data available for download.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH}")
