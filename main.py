import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
import bcrypt
import sqlite3
import io
import shutil
import base64
from datetime import datetime, date, timedelta
import os 

# Streamlit config MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- Database setup ---
DB_PATH = 'issues.db' 
conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=20) 
c = conn.cursor()

# --- Robust Schema Creation and Verification ---
def initialize_database_schema(cursor, connection):
    st.write("DEBUG: Initializing/Verifying database schema...") 
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
        file_type TEXT, category TEXT, submission_date TEXT, file BLOB
    )''')
    connection.commit() 

    required_uploads_columns = {
        "submission_date": "TEXT", "category": "TEXT", "file_type": "TEXT",
        "uploader": "TEXT", "timestamp": "TEXT"
    }
    cursor.execute("PRAGMA table_info(uploads)")
    existing_uploads_cols = {col[1]: col[2] for col in cursor.fetchall()}
    
    for col_name, col_type in required_uploads_columns.items():
        if col_name not in existing_uploads_cols:
            try:
                cursor.execute(f"ALTER TABLE uploads ADD COLUMN {col_name} {col_type}")
                connection.commit()
                st.toast(f"Added column '{col_name}' to 'uploads' table.", icon="🔧")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower(): raise 
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id INTEGER, 
        code TEXT, issues TEXT, branch TEXT, area_manager TEXT, date TEXT, report_type TEXT, 
        FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE 
    )''')
    connection.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS cctv_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id INTEGER, 
        code TEXT, violation TEXT, shift TEXT, date_submitted TEXT, 
        branch_name TEXT, area_manager TEXT, report_type TEXT,
        FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE 
    )''')
    connection.commit()
    st.toast("Database schema initialized/verified successfully.", icon="✅")

try:
    initialize_database_schema(c, conn)
except Exception as e_schema:
    st.error(f"CRITICAL ERROR during database schema initialization: {e_schema}")
    st.error("Delete 'issues.db' and restart. If persists, check permissions or schema definition.")
    st.stop()

db_admin = {
    "abdalziz alsalem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvpLxRumSduEte8MDAPkOnuXMdnW",
    "omar salah": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy",
    "ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEn.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG",
    "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe"
}
view_only = ["mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"]
category_file_types = {
    'operation-training': ['opening', 'closing', 'handover', 'store arranging', 'tempreature of heaters', 'defrost', 'clean AC'],
    'CCTV': ['issues', 'submission time'], 
    'complaints': ['performance', 'اغلاق الشكاوي'], 
    'missing': ['performance'],
    'visits': [], 
    'meal training': ['performance', 'missing types']
}
all_categories = list(category_file_types.keys())

BRANCH_CODE_MAP = {
    "NURUH B01": "Nuzhah - النزهة", "KHRUH B02": "Alkaleej - الخليج", "GHRUH B03": "Gurnatah - غرناطة",
    "NSRUH B04": "Alnaseem Riyadh- النسيم الرياض", "RAWRUH B05": "Alrawabi - الروابي", "DARUH B06": "Aldaraiah - الدرعية",
    "LBRUH B07": "Wadi Laban Riyadh - وادي لبن الرياض", "SWRUH B08": "Alsweedi - السويدي", "AZRUH B09": "Alaziziah - العزيزية",
    "SHRUH B10": "Alshifa - الشفاء", "NRRUH B11": "Alnargis - النرجس", "TWRUH B12": "Twuaiq - طويق",
    "AQRUH B13": "Al Aqiq - العقيق", "RBRUH B14": "Alrabea - الربيع", "NDRUH B15": "Nad Al Hamar", 
    "BDRUH B16": "Albadeah - البديعة", "QRRUH B17": "Alqairawan - القيروان", "TKRUH B18": "Takhasussi Riyadh - التخصصي الرياض",
    "MURUH B19": "Alremal - الرمال", "KRRUH B21": "Alkharj - الخرج", "OBJED B22": "Obhur Branch - فرع ابحر",
    "SLAHS B23": "Al Sulimaniyah Al Hofuf - السلمانية الهفوف", "SFJED B24": "Alsafa Jeddah - الصفا جدة",
    "RWAHS B25": "Al Rawdha Al Hofuf - الروضة الهفوف", "HAJED B26": "Al Hamadaniyyah  - الحمدانية",
    "SARUH B27": "Alsaadah branch - فرع السعادة", "MAJED B28": "Almarwah branch - فرع المروة",
    "EVENT B29": "Event Location B29", "QADRUH B30": "Al Qadisiyyah branch - فرع القادسية",
    "ANRUH B31": "Anas Ibn Malik - انس ابن مالك", "FAYJED B32": "Alfayha branch - فرع الفيحاء",
    "HIRJED B33": "Hira Jeddah", "URURUH B34": "Al Urubah Branch - فرع العروبة",
    "LB01": "Lubda - لبدة", "LB02": "Alkhaleej Branch LB02", 
    "QB01": "Shawarma Garatis As Suwaidi - شاورما قراطيس السويدي",
    "QB02": "Shawarma Garatis Alnargis B02 -  B02 شاورما قراطيس النرجس",
    "TW01": "Twesste"
    # ** COMPLETE THIS MAP WITH ALL YOUR CODES (UPPERCASE) AND FULL NAMES **
}

LOGO_PATH = "company_logo.png" 

def check_login():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None
    if not st.session_state.authenticated:
        col1_lgn, col2_lgn = st.columns([2,6]);
        with col1_lgn:
            try: st.image(LOGO_PATH, width=120) 
            except Exception: pass 
        with col2_lgn: st.title("📊 Login - Dashboard")
        st.subheader("Please log in to continue")
        with st.form("login_form"):
            username = st.text_input("Full Name:", key="auth_username_login_widget").strip().lower() 
            password = st.text_input("Password:", type="password", key="auth_password_login_widget") 
            submitted = st.form_submit_button("Login")
            if submitted:
                if username in db_admin and bcrypt.checkpw(password.encode(), db_admin[username]):
                    st.session_state.authenticated = True; st.session_state.user_name = username; st.session_state.user_role = 'admin'; st.rerun()
                elif username in view_only and password: 
                    st.session_state.authenticated = True; st.session_state.user_name = username; st.session_state.user_role = 'view_only'; st.rerun()
                elif username in view_only and not password: st.error("Password cannot be empty for view-only users.")
                elif username or password: st.error("Invalid username or password.")
                else: st.info("Please enter your credentials.")
        return False
    return True
if not check_login(): st.stop()

col1_main_title, col2_main_title = st.columns([2, 6]) 
with col1_main_title:
    try: st.image(LOGO_PATH, width=120)
    except FileNotFoundError: st.error(f"Logo image not found: {LOGO_PATH}") 
    except Exception as e: st.error(f"Error loading logo: {e}")
with col2_main_title: st.title("📊 Classic Dashboard for Performance")

user_name_display = st.session_state.get('user_name', "N/A").title()
user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main_widget"):
    st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.session_state.get('user_name', 'Unknown User')

def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path or wk_path == "not found": st.error("wkhtmltopdf path not set."); return None
    try:
        import pdfkit; config = pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8",'load-error-handling': 'ignore','load-media-error-handling': 'ignore'}
        pdfkit.from_string(html, fname, configuration=config, options=options);
        with open(fname, 'rb') as f: return f.read()
    except Exception as e: st.error(f"PDF error: {e}"); return None

st.sidebar.header("🔍 Filters & Options")

if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("Set parameters, select Excel, specify import date range, then upload.")
    selected_category_val = st.sidebar.selectbox("Category for upload", options=all_categories, key="admin_category_select_widget")
    valid_file_types = category_file_types.get(selected_category_val, [])
    selected_file_type_val = st.sidebar.selectbox("File type for upload", options=valid_file_types, key="admin_file_type_select_widget", disabled=(not valid_file_types), help="Options change based on category.")
    st.sidebar.markdown("**Filter Excel Data by Date Range for this Import:**")
    import_from_date_widget_val = st.sidebar.date_input("Import Data From Date:", value=date.today() - timedelta(days=7), key="import_from_date_upload_widget")
    import_to_date_widget_val = st.sidebar.date_input("Import Data To Date:", value=date.today(), key="import_to_date_upload_widget")
    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader_widget")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button_widget")

    if upload_btn: 
        final_category = selected_category_val; final_file_type = selected_file_type_val
        imp_from_dt = import_from_date_widget_val; imp_to_dt = import_to_date_widget_val 
        requires_file_type = bool(category_file_types.get(final_category, []))

        if requires_file_type and not final_file_type: st.sidebar.warning(f"Please select a file type for '{final_category}'.")
        elif not up: st.sidebar.error("Please select an Excel file.")
        elif not imp_from_dt or not imp_to_dt: st.sidebar.error("Please select both Import From and To Dates.")
        elif imp_from_dt > imp_to_dt: st.sidebar.error("Import From Date cannot be after Import To Date.")
        else: 
            if not requires_file_type: final_file_type = None 
            excel_data_bytes = up.getvalue(); ts_now = datetime.now()
            upload_submission_date_for_uploads_table = imp_from_dt 
            
            upload_id_for_op = None 
            try:
                with conn: 
                    # Check for duplicate upload batch first
                    c.execute('SELECT id FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                              (up.name, current_user, final_file_type, final_category, upload_submission_date_for_uploads_table.isoformat()))
                    existing_upload = c.fetchone()
                    if existing_upload: 
                        st.sidebar.warning(f"Duplicate upload batch (ID: {existing_upload[0]}) found for '{up.name}' with these settings. No action taken.")
                    else:
                        df_excel_full = pd.read_excel(io.BytesIO(excel_data_bytes))
                        df_excel_full.columns = [col.strip().lower() for col in df_excel_full.columns]
                        
                        df_to_import = pd.DataFrame() # Initialize df_to_import
                        issues_prepared_count = 0

                        if final_category == 'CCTV':
                            st.sidebar.info("Processing CCTV file format...")
                            cctv_req_cols = ['code', 'choose the violation - اختر المخالفه', 'date submitted', 'area manager']
                            missing_cctv_cols = [col for col in cctv_req_cols if col not in df_excel_full.columns]
                            if missing_cctv_cols: raise ValueError(f"CCTV Excel missing: {', '.join(missing_cctv_cols)}.")
                            
                            df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full['date submitted'], errors='coerce', dayfirst=False) # MM/DD/YYYY common for 'date submitted'
                            original_len = len(df_excel_full); df_excel_full.dropna(subset=['parsed_date'], inplace=True)
                            if len(df_excel_full) < original_len: st.sidebar.warning(f"{original_len - len(df_excel_full)} CCTV rows dropped (invalid 'date submitted').")
                            if df_excel_full.empty: raise ValueError("No valid CCTV data rows after date parsing.")
                                
                            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()
                        else: # Standard Processing
                            required_cols = ['code', 'issues', 'branch', 'area manager', 'date']
                            missing_cols = [col for col in required_cols if col not in df_excel_full.columns]
                            if missing_cols: raise ValueError(f"Standard Excel missing: {', '.join(missing_cols)}.")
                            
                            df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full['date'], dayfirst=True, errors='coerce')
                            original_len = len(df_excel_full); df_excel_full.dropna(subset=['parsed_date'], inplace=True)
                            if len(df_excel_full) < original_len: st.sidebar.warning(f"{original_len - len(df_excel_full)} rows dropped (invalid date).")
                            if df_excel_full.empty: raise ValueError("No valid data rows in Excel after date parsing.")
                                
                            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()

                        # --- Common Insertion Logic ---
                        if not df_to_import.empty:
                            c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                      (up.name, current_user, ts_now.isoformat(), final_file_type, final_category, upload_submission_date_for_uploads_table.isoformat(), sqlite3.Binary(excel_data_bytes)))
                            upload_id_for_op = c.lastrowid 

                            if final_category == 'CCTV':
                                cctv_issues_to_insert_tuples = []
                                for _, row in df_to_import.iterrows():
                                    violation = row['choose the violation - اختر المخالفه']
                                    shift = row.get('choose the shift - اختر الشفت', None) 
                                    branch_code_excel = str(row['code']).strip().upper()
                                    branch_name = BRANCH_CODE_MAP.get(branch_code_excel, str(row.get('branch', branch_code_excel))).strip() 
                                    cctv_issues_to_insert_tuples.append((upload_id_for_op, branch_code_excel, violation, shift, row['parsed_date'].strftime('%Y-%m-%d'), branch_name, row['area manager'], final_file_type))
                                if cctv_issues_to_insert_tuples:
                                    c.executemany('''INSERT INTO cctv_issues (upload_id, code, violation, shift, date_submitted, branch_name, area_manager, report_type) 
                                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', cctv_issues_to_insert_tuples)
                                    issues_prepared_count = len(cctv_issues_to_insert_tuples)
                            else: # Standard issues
                                standard_issues_to_insert_tuples = []
                                for _, row in df_to_import.iterrows():
                                    standard_issues_to_insert_tuples.append((upload_id_for_op, row['code'], row['issues'], str(row['branch']).strip(), row['area manager'], row['parsed_date'].strftime('%Y-%m-%d'), final_file_type))
                                if standard_issues_to_insert_tuples:
                                    c.executemany('''INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) 
                                                     VALUES (?, ?, ?, ?, ?, ?, ?)''', standard_issues_to_insert_tuples)
                                    issues_prepared_count = len(standard_issues_to_insert_tuples)
                            
                            # conn.commit() is handled by 'with conn:'
                            st.sidebar.success(f"Imported {issues_prepared_count} issues from '{up.name}'.")
                            st.rerun()
                        else: # df_to_import was empty
                             st.sidebar.info(f"No issues found within the import date range in '{up.name}'. No data imported.")
            except ValueError as ve: 
                 st.sidebar.error(f"Data Error: {ve} Upload process halted.")
            except sqlite3.Error as e_sql: 
                st.sidebar.error(f"DB error during upload: {e_sql}. Transaction implicitly rolled back.")
            except Exception as e_general: 
                st.sidebar.error(f"Error processing file '{up.name}': {e_general}. Transaction implicitly rolled back if DB ops started.")
    
    st.sidebar.subheader("Manage Submissions")
    df_uploads_for_delete = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn) 
    if 'submission_date' in df_uploads_for_delete.columns: 
        df_uploads_for_delete['display_submission_date_fmt'] = df_uploads_for_delete['submission_date'].apply(lambda d: datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) and isinstance(d, str) else "N/A")
    else: df_uploads_for_delete['display_submission_date_fmt'] = "N/A"
    delete_opts_list = [(f"{row['id']} - {row['filename']} ({row['category']}/{row['file_type'] or 'N/A'}) Imp.From: {row['display_submission_date_fmt']}") for index, row in df_uploads_for_delete.iterrows()]
    delete_opts = ['Select ID to Delete'] + delete_opts_list
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission Batch:", delete_opts, key="delete_submission_id_select_widget")
    if del_choice_display != 'Select ID to Delete':
        del_id_val = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id_val}", key=f"confirm_del_btn_widget_{del_id_val}", type="primary"):
            try:
                with conn: c.execute('DELETE FROM uploads WHERE id=?', (del_id_val,))
                st.sidebar.success(f"Deleted submission batch {del_id_val}."); st.rerun()
            except sqlite3.Error as e: st.sidebar.error(f"Failed to delete: {e}")
    
    st.sidebar.subheader("Database Management")
    st.sidebar.markdown( """**To persist data (e.g., on Streamlit Cloud):** After uploads/deletions, "Download Database Backup", rename to `issues.db`, replace in local Git, then commit & push.""" )
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as fp: db_file_bytes = fp.read() 
        current_timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S"); backup_db_filename = f"issues_backup_{current_timestamp_str}.db"
        st.sidebar.download_button(label="Download Database Backup", data=db_file_bytes, file_name=backup_db_filename,
                                   mime="application/vnd.sqlite3", key="download_db_button_widget", 
                                   help=f"Downloads current '{DB_PATH}'. Rename to '{os.path.basename(DB_PATH)}' for Git commit.")
    else: st.sidebar.warning(f"'{DB_PATH}' not found. Cannot offer download.")

default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk, key="wk_path_widget")

try: # Added try-except around initial data loading
    df_uploads_raw_main = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
except sqlite3.Error as e:
    st.error(f"Database error reading uploads list: {e}. The database file might be corrupted or schema is incorrect.")
    st.info("If this is the first run after schema changes, or if errors persist, try deleting 'issues.db' and restarting the app.")
    df_uploads_raw_main = pd.DataFrame() # Ensure it's an empty DataFrame

def format_display_date(d_str): 
    try: return datetime.strptime(d_str,'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d_str) and isinstance(d_str, str) else "N/A"
    except ValueError: return "N/A" 
df_uploads_raw_main['display_submission_date_fmt'] = df_uploads_raw_main['submission_date'].apply(format_display_date) if 'submission_date' in df_uploads_raw_main else "N/A"

st.sidebar.subheader("Data Scope")
scope_opts_list = []
if not df_uploads_raw_main.empty:
    scope_opts_list = [(f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) Imp.From: {r['display_submission_date_fmt']}") for i,r in df_uploads_raw_main.iterrows()]
scope_opts = ['All uploads'] + scope_opts_list
sel_display = st.sidebar.selectbox("Select upload batch to analyze:", scope_opts, key="select_upload_scope_main_widget")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

df_standard_issues = pd.DataFrame(); df_cctv_issues_raw = pd.DataFrame() # Initialize
try:
    df_standard_issues = pd.read_sql(
        '''SELECT i.id as issue_id, i.upload_id, i.code, i.issues, i.branch, i.area_manager, i.date, i.report_type, 
            u.category as upload_category, u.id as upload_id_col 
        FROM issues i JOIN uploads u ON u.id = i.upload_id''', conn, parse_dates=['date'])
    df_cctv_issues_raw = pd.read_sql(
        '''SELECT c.id as issue_id, c.upload_id, c.code, c.violation, c.shift, c.date_submitted, c.branch_name, c.area_manager, c.report_type,
            u.category as upload_category, u.id as upload_id_col
        FROM cctv_issues c JOIN uploads u ON u.id = c.upload_id''', conn, parse_dates=['date_submitted'])
except sqlite3.Error as e:
    st.error(f"Database error fetching issue details: {e}. Check schema or DB file.")
    # df_all_issues will be empty if this fails early

df_cctv_issues_processed = pd.DataFrame()
if not df_cctv_issues_raw.empty:
    df_cctv_issues_processed = df_cctv_issues_raw.copy()
    df_cctv_issues_processed.rename(columns={'violation': 'issues', 'date_submitted': 'date', 'branch_name': 'branch'}, inplace=True)
    if 'shift' in df_cctv_issues_processed.columns and 'issues' in df_cctv_issues_processed.columns:
         df_cctv_issues_processed['issues'] = df_cctv_issues_processed.apply(lambda row: f"{row['issues']} (Shift: {row['shift']})" if pd.notna(row['shift']) and row['shift']!='' else row['issues'], axis=1)
    common_cols_for_display = ['issue_id', 'upload_id', 'code', 'issues', 'branch', 'area_manager', 'date', 'report_type', 'upload_category', 'upload_id_col']
    current_cctv_cols = df_cctv_issues_processed.columns.tolist()
    df_cctv_issues_processed = df_cctv_issues_processed[[col for col in common_cols_for_display if col in current_cctv_cols]]
    for col in common_cols_for_display: 
        if col not in df_cctv_issues_processed.columns: df_cctv_issues_processed[col] = pd.NA
df_all_issues_list = []
if not df_standard_issues.empty: df_all_issues_list.append(df_standard_issues)
if not df_cctv_issues_processed.empty: df_all_issues_list.append(df_cctv_issues_processed)

if df_all_issues_list:
    df_all_issues = pd.concat(df_all_issues_list, ignore_index=True)
    if 'date' in df_all_issues.columns: df_all_issues['date'] = pd.to_datetime(df_all_issues['date'], errors='coerce')
    # Critical check: if 'date' column becomes all NaT or df is empty after concat
    if df_all_issues.empty or ('date' in df_all_issues.columns and df_all_issues['date'].isnull().all()):
        st.warning("No issues data with valid dates available after combining/processing. Dashboard cannot be generated."); st.stop()
else:
    st.warning("No issues data found in database from any source (standard or CCTV). Upload data."); st.stop()


# --- Dashboard Filters & Display ---
# (The rest of your code: st.sidebar.subheader("Dashboard Filters") onwards, including apply_general_filters,
#  primary period processing, chart functions, primary display, comparison logic, and downloads.
#  This part is assumed to be largely correct from your previous versions and will now operate on the combined df_all_issues)

# Make sure to copy the full dashboard display logic from your previous complete version here.
# For brevity, I am adding placeholders for the main sections.
# You NEED to ensure these are complete in your actual script.

st.sidebar.subheader("Dashboard Filters")
# ... (min_overall_date, max_overall_date, primary_date_range, filter widgets for branch, cat, am, ft) ...
min_overall_date_calc = df_all_issues['date'].min().date() if pd.notna(df_all_issues['date'].min()) else date.today()
max_overall_date_calc = df_all_issues['date'].max().date() if pd.notna(df_all_issues['date'].max()) else date.today()
primary_date_range_val_calc = [min_overall_date_calc, max_overall_date_calc] if min_overall_date_calc <= max_overall_date_calc else [max_overall_date_calc, min_overall_date_calc]
primary_date_range = st.sidebar.date_input("Primary Date Range (Issue Dates):", value=primary_date_range_val_calc, min_value=min_overall_date_calc, max_value=max_overall_date_calc, key="primary_date_range_filter_widget")
if not primary_date_range or len(primary_date_range) != 2: primary_date_range = primary_date_range_val_calc
branch_opts_list = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist()); sel_branch = st.sidebar.multiselect("Branch:", branch_opts_list, default=['All'], key="branch_filter_widget")
cat_opts_list = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist()); sel_cat = st.sidebar.multiselect("Category (from Upload Batch):", cat_opts_list, default=['All'], key="category_filter_widget")
am_opts_list = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist()); sel_am = st.sidebar.multiselect("Area Manager:", am_opts_list, default=['All'], key="area_manager_filter_widget")
file_type_filter_opts_list = ['All'] + sorted(df_all_issues['report_type'].astype(str).unique().tolist()); sel_ft = st.sidebar.multiselect("File Type (from Upload Batch):", file_type_filter_opts_list, default=['All'], key="file_type_filter_widget")


st.sidebar.subheader("📊 Period Comparison")
# ... (enable_comparison checkbox and comparison_date_range_1/2 inputs) ...
enable_comparison_val = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox_widget") # Renamed
comparison_date_range_1_calc, comparison_date_range_2_calc = None, None 
if enable_comparison_val:
    # ... (your logic for comparison_date_range_1_val and comparison_date_range_2_val) ...
    pass


# df_temp_filtered_calc = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)
# df_primary_period_calc = df_temp_filtered_calc.copy()
# ... (filtering df_primary_period_calc by primary_date_range) ...
df_temp_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft) # Apply general filters
df_primary_period = df_temp_filtered.copy() # Start with generally filtered data
if primary_date_range and len(primary_date_range) == 2: # Apply primary date range
    start_date_filter, end_date_filter = primary_date_range[0], primary_date_range[1]
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']):
        df_primary_period = df_primary_period[
            (df_primary_period['date'].dt.date >= start_date_filter) & 
            (df_primary_period['date'].dt.date <= end_date_filter)
        ]
    else: # If date column issues persist or df is empty
        df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns) # Make it empty with correct columns
else: # If primary_date_range isn't valid
    df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)

st.subheader(f"Filtered Issues for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total issues found in primary period: {len(df_primary_period)}")

# Primary period display
if df_primary_period.empty:
    st.info("No data matches the current filter criteria for the primary period.")
else:
    # ... (ALL YOUR CHARTING AND DATA DISPLAY LOGIC for df_primary_period) ...
    # This includes figs_primary, col1_charts, col2_charts, trend chart, detailed records, top issues
    figs_primary = {} # Ensure initialized
    # ... (Example, ensure this is complete from your previous version)
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']) and not df_primary_period['date'].isnull().all():
        # ... (Primary trend chart logic) ...
        pass

# Comparison period display
if enable_comparison_val and comparison_date_range_1 and comparison_date_range_2: # Use the ones from enable_comparison block
    st.markdown("---"); st.header("📊 Period Comparison Results (Based on Issue Dates)")
    # ... (ALL YOUR COMPARISON LOGIC: df_comp1, df_comp2, metrics, branch comparison, period-level trend) ...
    # ... (Example, ensure this is complete from your previous version)
    if 'df_comp1' in locals() and 'df_comp2' in locals() and (not df_comp1.empty or not df_comp2.empty):
        # ... (Comparison charts) ...
        pass
    else:
        st.warning("No data found for comparison periods with current filters.")


# Downloads
st.sidebar.subheader("Downloads")
if 'df_primary_period' in locals() and not df_primary_period.empty: # Check df_primary_period exists
    # ... (ALL YOUR DOWNLOAD BUTTON LOGIC for primary period) ...
    pass
else: 
    st.sidebar.info("No primary period data to download.")

if enable_comparison_val and comparison_date_range_1 and comparison_date_range_2: # Use the ones from enable_comparison
    # ... (ALL YOUR DOWNLOAD BUTTON LOGIC for comparison periods, checking if df_comp1/df_comp2 exist) ...
    pass

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)")
