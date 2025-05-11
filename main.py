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

# (Database schema setup - same as before, shortened for brevity)
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
    file_type TEXT, category TEXT, file BLOB
)''')
conn.commit()
c.execute("PRAGMA table_info(uploads)")
existing_columns = [column[1] for column in c.fetchall()]
if 'submission_date' not in existing_columns:
    try:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        if 'db_schema_updated_message_shown' not in st.session_state:
            st.session_state.db_schema_updated_message_shown = True
            st.toast("DB 'uploads' schema updated: 'submission_date' added.", icon="ℹ️")
    except sqlite3.OperationalError as e:
        st.error(f"CRITICAL DB ERROR: {e}. Cannot proceed.")
        st.stop()
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    upload_id INTEGER, code TEXT, issues TEXT, branch TEXT, area_manager TEXT,
    date TEXT, report_type TEXT, FOREIGN KEY(upload_id) REFERENCES uploads(id)
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
                    st.session_state.user_role = 'admin'
                    st.rerun() 
                elif username in view_only and password:
                    st.session_state.authenticated = True
                    st.session_state.user_name = username
                    st.session_state.user_role = 'view_only'
                    st.rerun() 
                elif username in view_only and not password:
                    st.error("Password cannot be empty for view-only users.")
                elif username or password: 
                     st.error("Invalid username or password.")
                else:
                    st.info("Please enter your credentials.")
        return False 
    return True 

if not check_login():
    st.stop() 

# --- User is Authenticated, Proceed with App ---
st.title("📊 Classic Dashboard for Performance") 

user_name_display = st.session_state.get('user_name', "N/A").title()
user_role_display = st.session_state.get('user_role', "N/A")

st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
st.sidebar.error("DEBUG MARKER 1: AFTER LOGIN CONFIRMED") # <<< NEW MARKER

if st.sidebar.button("Logout", key="logout_button_main"):
    st.session_state.authenticated = False
    st.session_state.user_name = None
    st.session_state.user_role = None
    st.rerun()

st.sidebar.error("DEBUG MARKER 2: BEFORE is_admin CHECK") # <<< NEW MARKER

# Determine admin status
is_admin = False 
if 'user_role' in st.session_state and st.session_state.user_role == 'admin':
    is_admin = True
current_user = st.session_state.get('user_name', 'Unknown User')

st.sidebar.error("DEBUG MARKER 3: AFTER is_admin CHECK, BEFORE ADMIN CONTROLS") # <<< NEW MARKER
st.sidebar.markdown(f"*(DEBUG: is_admin is currently: {is_admin})*") # Explicit check of is_admin

# PDF generator (same as before, condensed)
def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path or wk_path == "not found": st.error("wkhtmltopdf path not set."); return None
    try:
        import pdfkit; config = pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8",'load-error-handling': 'ignore','load-media-error-handling': 'ignore'}
        pdfkit.from_string(html, fname, configuration=config, options=options)
        with open(fname, 'rb') as f: return f.read()
    except Exception as e: st.error(f"PDF error: {e}"); return None

# Sidebar: controls
st.sidebar.header("🔍 Filters & Options")

# Upload control for admins
if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("*(You are seeing this because `is_admin` is True)*") 
    st.sidebar.markdown("Set parameters, choose Excel, then 'Upload Data'.")
    file_type_upload = st.sidebar.selectbox("File type for upload", ["opening", "closing", "handover", "meal training"], key="upload_file_type")
    category_upload = st.sidebar.selectbox("Category for upload", ['operation-training', 'CCTV', 'complaints', 'missing', 'visits', 'meal training'], key="upload_category")
    
    effective_report_date = st.sidebar.date_input(
        "**Effective Date of Report:**", 
        value=date.today(), 
        key="effective_report_date_upload",
        help="Date for all issues in the uploaded file."
    )

    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if upload_btn:
        if up and effective_report_date: 
            data = up.getvalue(); ts = datetime.now().isoformat(); effective_date_str = effective_report_date.isoformat() 
            st.sidebar.info(f"DBG_UP: Eff.Date: {effective_date_str}")
            c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type=? AND category=? AND submission_date=?',
                      (up.name, current_user, file_type_upload, category_upload, effective_date_str))
            if c.fetchone()[0] == 0:
                c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                          (up.name, current_user, ts, file_type_upload, category_upload, effective_date_str, sqlite3.Binary(data)))
                uid = c.lastrowid; st.sidebar.info(f"DBG_UP: ID {uid} uses {effective_date_str}")
                try:
                    df_up = pd.read_excel(io.BytesIO(data)); df_up.columns = [col.strip().lower() for col in df_up.columns]
                    required_cols = ['code', 'issues', 'branch', 'area manager', 'date'] 
                    missing_cols = [col for col in required_cols if col not in df_up.columns]
                    if missing_cols:
                        st.sidebar.error(f"Excel missing: {', '.join(missing_cols)}. Aborted."); c.execute('DELETE FROM uploads WHERE id=?', (uid,)); conn.commit()
                    else:
                        df_up['excel_date_validated'] = pd.to_datetime(df_up['date'], dayfirst=True, errors='coerce')
                        original_len = len(df_up); df_up.dropna(subset=['excel_date_validated'], inplace=True)
                        if len(df_up) < original_len: st.sidebar.warning(f"{original_len - len(df_up)} rows dropped from Excel (bad date).")
                        if df_up.empty:
                            st.sidebar.error("No valid data rows in Excel. Aborted."); c.execute('DELETE FROM uploads WHERE id=?', (uid,)); conn.commit()
                        else:
                            for _, row in df_up.iterrows():
                                c.execute('INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                          (uid, row['code'], row['issues'], row['branch'], row['area manager'], effective_date_str, file_type_upload))
                            conn.commit(); st.sidebar.success(f"Uploaded '{up.name}' ({len(df_up)} recs) Eff.Date: {effective_date_str}"); st.rerun() 
                except Exception as e:
                    st.sidebar.error(f"Excel processing error '{up.name}': {e}. Rolled back."); c.execute('DELETE FROM uploads WHERE id=?', (uid,)); conn.commit()
            else:
                st.sidebar.warning(f"Duplicate: File '{up.name}' for '{effective_date_str}' already uploaded.")
        else:
            if not up: st.sidebar.error("Please select an Excel file.")
else: 
    st.sidebar.warning("Admin controls are hidden. Log in as admin.")
    if st.session_state.get('authenticated'):
        st.sidebar.info(f"Current role: '{st.session_state.get('user_role', 'N/A')}' for user '{st.session_state.get('user_name', 'N/A')}'.")


# (The rest of the script: wkhtmltopdf, Data Scope, Manage Submissions (if admin), Dashboard Filters, Charts, Downloads - same as before, condensed)
# wkhtmltopdf path
default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk, help="Path to wkhtmltopdf executable.")

# Load uploads for selection and deletion
df_uploads = pd.read_sql('SELECT id, filename, uploader, submission_date, file_type, category FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A"
df_uploads['display_submission_date'] = df_uploads['submission_date'].apply(format_display_date)

# Scope selection
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [f"{r['id']} - {r['filename']} ({r['file_type']}) Eff.Date: {r['display_submission_date']}" for i,r in df_uploads.iterrows()]
sel_display = st.sidebar.selectbox("Select upload to analyze:", scope_opts, key="select_upload_scope")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

# Admin: delete submission
if is_admin:
    st.sidebar.subheader("Manage Submissions")
    del_opts = ['Select ID to Delete'] + [f"{r['id']} - {r['filename']} (Eff.Date: {r['display_submission_date']})" for i,r in df_uploads.iterrows()]
    del_choice = st.sidebar.selectbox("🗑️ Delete Submission:", del_opts, key="delete_submission_id")
    if del_choice != 'Select ID to Delete':
        del_id_val = int(del_choice.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete #{del_id_val}", key=f"del_btn_{del_id_val}",type="primary"):
            c.execute('DELETE FROM issues WHERE upload_id=?',(del_id_val,)); c.execute('DELETE FROM uploads WHERE id=?',(del_id_val,)); conn.commit()
            st.sidebar.success(f"Deleted submission {del_id_val}."); st.rerun()

sql = 'SELECT i.*, u.category as upload_category, u.file_type as master_file_type FROM issues i JOIN uploads u ON u.id = i.upload_id'
params = []
if sel_id: sql += ' WHERE i.upload_id = ?'; params.append(sel_id)
df = pd.read_sql(sql, conn, params=params, parse_dates=['date'])

if df.empty: st.warning("No data for selected scope/filters."); st.stop()

st.sidebar.subheader("Dashboard Filters")
min_d, max_d = (d.date() if pd.notna(d) and hasattr(d,'date') else date.today() for d in (df['date'].min(), df['date'].max()))
if min_d > max_d: max_d = min_d
date_rng_val = [min_d, max_d]
date_rng = st.sidebar.date_input("Filter by Effective Report Date:", value=date_rng_val, min_value=min_d, max_value=max_d, key="date_filter")
if not date_rng or len(date_rng)!=2: date_rng = date_rng_val

df_f = df.copy()
if date_rng and len(date_rng)==2:
    df_f = df_f[(df_f['date'].dt.date >= date_rng[0]) & (df_f['date'].dt.date <= date_rng[1])]

# Other filters (branch, category, file_type - shortened)
for col, sel_items_key in [('branch', 'branch_filter'), ('upload_category', 'category_filter'), ('report_type', 'file_type_filter')]:
    opts = ['All'] + sorted(df[col].astype(str).unique().tolist())
    sel_items = st.sidebar.multiselect(f"{col.replace('_',' ').title()}:", opts, default=['All'], key=sel_items_key)
    if 'All' not in sel_items: df_f = df_f[df_f[col].isin(sel_items)]

st.subheader(f"Filtered Issues ({date_rng[0]:%Y-%m-%d} to {date_rng[1]:%Y-%m-%d}) - Total: {len(df_f)}")
if df_f.empty: st.info("No data matches current filters."); st.stop()

# Charts and Data display (highly condensed, logic assumed correct from before)
st.write("... Charts and data tables would be here ...") 

# Downloads (highly condensed)
st.sidebar.subheader("Downloads")
if not df_f.empty:
    st.sidebar.download_button("CSV", df_f.to_csv(index=False).encode('utf-8'), "filtered.csv", "text/csv")
    # PDF buttons if wk_path is set etc.

st.sidebar.markdown("---"); st.sidebar.caption(f"DB: {DB_PATH}")
