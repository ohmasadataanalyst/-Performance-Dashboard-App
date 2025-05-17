import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.jan podel", "ali ismail", "islam mostafa"]
category_file_types = {
    'operation-graph_objects as go
import bcrypt
import sqlite3
import io
import shutil
import base64
fromtraining': ['opening', 'closing', 'handover', 'store arranging', 'tempreature of heaters', ' datetime import datetime, date, timedelta
import os

# Streamlit config MUST BE THE FIRST STREAMLIT COMMAND
stdefrost', 'clean AC'],
    'CCTV': ['issues', 'submission time'], # These are '.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- Database setup ---
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_report_type' values for CCTV uploads
    'complaints': ['performance', 'اغلاق الشكاوي'],
    same_thread=False, timeout=10)
c = conn.cursor()

# Create uploads table
c.'missing': ['performance'],
    'visits': [],
    'meal training': ['performance', 'missing typesexecute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT']
}
all_categories = list(category_file_types.keys())

if 'db_critical, timestamp TEXT,
    file_type TEXT, category TEXT,
    submission_date TEXT,
    file_error_msg' in st.session_state:
    st.error(f"DB Startup Error: BLOB
)''')

# Create issues table (with new 'shift' column)
c.execute('''CREATE TABLE {st.session_state.db_critical_error_msg}"); del st.session_state.db_critical_error IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER, code TEXT, issues TEXT_msg
if 'db_schema_updated_flag' in st.session_state and st.session_, branch TEXT, area_manager TEXT,
    date TEXT,
    report_type TEXT,
    shiftstate.db_schema_updated_flag:
    st.toast("DB 'uploads' table schema updated.", TEXT, -- Added for CCTV data
    FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE
)'' icon="ℹ️"); st.session_state.db_schema_updated_flag = False
if 'issues_schema')
conn.commit()

# Schema migration for 'uploads' table (submission_date column)
try:_updated_flag' in st.session_state and st.session_state.issues_schema_updated_
    c.execute("PRAGMA table_info(uploads)")
    existing_columns_uploads = [flag:
    st.toast("DB 'issues' table schema updated with 'shift' column.", icon="ℹcolumn[1] for column in c.fetchall()]
    if 'submission_date' not in existing_columns_uploads:️"); st.session_state.issues_schema_updated_flag = False


LOGO_PATH = "company_logo
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        if 'db.png"

def check_login():
    if 'authenticated' not in st.session_state:
_schema_updated_flag_uploads' not in st.session_state:
            st.session_state        st.session_state.authenticated = False; st.session_state.user_name = None; st.db_schema_updated_flag_uploads = True
except sqlite3.OperationalError as e:
    .session_state.user_role = None
    if not st.session_state.authenticated:
        if "duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not in stcol1_lgn, col2_lgn = st.columns([2,6]);
        with col1_lgn:
            try: st.image(LOGO_PATH, width=120)
.session_state :
        st.session_state.db_critical_error_msg = f"Failed to            except Exception: pass
        with col2_lgn: st.title("📊 Login - Dashboard")
        st update 'uploads' table schema: {e}"

# Schema migration for 'issues' table (shift column)
try:
.subheader("Please log in to continue")
        with st.form("login_form"):
            username =    c.execute("PRAGMA table_info(issues)")
    existing_columns_issues = [column st.text_input("Full Name:", key="auth_username_login").strip().lower()
            password = st.text_input("Password:", type="password", key="auth_password_login")
            submitted = st[1] for column in c.fetchall()]
    if 'shift' not in existing_columns_issues:.form_submit_button("Login")
            if submitted:
                if username in db_admin and bcrypt
        c.execute("ALTER TABLE issues ADD COLUMN shift TEXT")
        conn.commit()
        if 'db_schema.checkpw(password.encode(), db_admin[username]):
                    st.session_state.authenticated =_updated_flag_issues' not in st.session_state:
            st.session_state.db True; st.session_state.user_name = username; st.session_state.user_role =_schema_updated_flag_issues = True
except sqlite3.OperationalError as e:
    if " 'admin'; st.rerun()
                elif username in view_only and password:
                    st.session_state.duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not inauthenticated = True; st.session_state.user_name = username; st.session_state.user_ st.session_state :
        st.session_state.db_critical_error_msg = f"Failed to update 'issues' table schema: {e}"


db_admin = {
    "abdalziz alsrole = 'view_only'; st.rerun()
                elif username in view_only and not password: st.error("Password cannot be empty for view-only users.")
                elif username or password: st.erroralem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OL("Invalid username or password.")
                else: st.info("Please enter your credentials.")
        return False
K7mvpLxRumSduEte8MDAPkOnuXMdnW",
    "omar salah    return True
if not check_login(): st.stop()

col1_main_title, col2_main_title = st.columns([2, 6])
with col1_main_title:
": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01    try: st.image(LOGO_PATH, width=120)
    except FileNotFoundError: stecj1cEShMAZGYbFCE3JdGagfaWomy",
    ".error(f"Logo image not found: {LOGO_PATH}")
    except Exception as e: st.ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEnerror(f"Error loading logo: {e}")
with col2_main_title: st.title("📊 Classic Dashboard for Performance")

user_name_display = st.session_state.get('user_name', "N.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG",
/A").title()
user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user    "mohamed hattab": b"$2b$12$X5hWO55U9Y0_role_display})")
if st.sidebar.button("Logout", key="logout_button_main"):RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwg
    st.session_state.authenticated = False; st.session_state.user_name = None;Y/bYIqe"
}
view_only = ["mohamed emad", "mohamed houider", st.session_state.user_role = None; st.rerun()
is_admin = st.session_ "sujan podel", "ali ismail", "islam mostafa"]
category_file_types = {state.get('user_role') == 'admin'
current_user = st.session_state.get
    'operation-training': ['opening', 'closing', 'handover', 'store arranging', 'tempreature of heaters('user_name', 'Unknown User')

def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path or wk_path == "not found": st.error("wkhtml', 'defrost', 'clean AC'],
    'CCTV': ['issues', 'submission time'], # CCTVtopdf path not set."); return None
    try:
        import pdfkit; config = pdfkit.configuration specific file types
    'complaints': ['performance', 'اغلاق الشكاوي'],
    'missing': ['(wkhtmltopdf=wk_path)
        options = {'enable-local-file-access': Noneperformance'],
    'visits': [],
    'meal training': ['performance', 'missing types']
}
, 'images': None, 'encoding': "UTF-8",'load-error-handling': 'ignore','load-mediaall_categories = list(category_file_types.keys())

if 'db_critical_error_msg-error-handling': 'ignore'}
        pdfkit.from_string(html, fname, configuration=config, options' in st.session_state:
    st.error(f"DB Startup Error: {st.session=options);
        with open(fname, 'rb') as f: return f.read()
    except_state.db_critical_error_msg}"); del st.session_state.db_critical_error_msg
if Exception as e: st.error(f"PDF error: {e}"); return None

st.sidebar.header("🔍 Filters 'db_schema_updated_flag_uploads' in st.session_state and st.session_state. & Options")

if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.db_schema_updated_flag_uploads:
    st.toast("DB 'uploads' table schema updated.", icon="ℹ️"); st.session_state.db_schema_updated_flag_uploads = False
if 'db_sidebar.markdown("Set parameters, select Excel, specify import date range, then upload.")
    selected_category = st.sidebarschema_updated_flag_issues' in st.session_state and st.session_state.db_schema.selectbox("Category for upload", options=all_categories, key="admin_category_select")
    valid_file_updated_flag_issues:
    st.toast("DB 'issues' table schema updated with 'shift' column_types = category_file_types.get(st.session_state.get("admin_category_select", all.", icon="ℹ️"); st.session_state.db_schema_updated_flag_issues = False


_categories[0]), [])
    selected_file_type = st.sidebar.selectbox("File type for uploadLOGO_PATH = "company_logo.png"

def check_login():
    if 'authenticated' not", options=valid_file_types, key="admin_file_type_select", disabled=(not valid_ in st.session_state:
        st.session_state.authenticated = False; st.session_statefile_types), help="Options change based on category.")
    st.sidebar.markdown("**Filter Excel Data by Date Range for.user_name = None; st.session_state.user_role = None
    if not st. this Import:**")
    import_from_date_val = st.sidebar.date_input("Import Datasession_state.authenticated:
        col1_lgn, col2_lgn = st.columns([ From Date:", value=date.today() - timedelta(days=7), key="import_from_date_upload")
    import_to_date_val = st.sidebar.date_input("Import Data To Date2,6]);
        with col1_lgn:
            try: st.image(LOGO_PATH:", value=date.today(), key="import_to_date_upload")
    up = st.sidebar, width=120)
            except Exception: pass
        with col2_lgn: st..file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    uploadtitle("📊 Login - Dashboard")
        st.subheader("Please log in to continue")
        with st.form("login_form"):
            username = st.text_input("Full Name:", key="auth_username_login").strip()._btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if uploadlower()
            password = st.text_input("Password:", type="password", key="auth_password__btn:
        final_category = st.session_state.admin_category_select
        final_filelogin")
            submitted = st.form_submit_button("Login")
            if submitted:
                if_type = st.session_state.admin_file_type_select
        imp_from_dt = username in db_admin and bcrypt.checkpw(password.encode(), db_admin[username]):
                    st.session_ st.session_state.import_from_date_upload
        imp_to_dt = st.sessionstate.authenticated = True; st.session_state.user_name = username; st.session_state._state.import_to_date_upload
        requires_file_type = bool(category_file_user_role = 'admin'; st.rerun()
                elif username in view_only and password: #types.get(final_category, []))

        if requires_file_type and not final_file_type: st Assuming view_only also need a password now (even if it's a generic one not bcrypt hashed)
                    st.session_state.authenticated = True; st.session_state.user_name = username; st.session.sidebar.warning(f"Please select a file type for '{final_category}'.")
        elif not up_state.user_role = 'view_only'; st.rerun()
                elif username in view_: st.sidebar.error("Please select an Excel file.")
        elif not imp_from_dt or notonly and not password: st.error("Password cannot be empty for view-only users.")
                elif username or imp_to_dt: st.sidebar.error("Please select both Import From and To Dates.")
        elif imp_from_dt > imp_to_dt: st.sidebar.error("Import From Date cannot be after password: st.error("Invalid username or password.")
                else: st.info("Please enter your credentials.") Import To Date.")
        else:
            if not requires_file_type: final_file_type =
        return False
    return True

if not check_login(): st.stop()

col1_main_ None
            data = up.getvalue(); ts = datetime.now().isoformat(); upload_submission_date_strtitle, col2_main_title = st.columns([2, 6])
with col1_main = imp_from_dt.isoformat()
            try:
                c.execute('SELECT COUNT(*) FROM uploads WHERE_title:
    try: st.image(LOGO_PATH, width=120)
    except filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                          (up.name, current_user, final_file_type, final_category, upload_submission_date_str))
 FileNotFoundError: st.error(f"Logo image not found: {LOGO_PATH}")
    except Exception as e:                if c.fetchone()[0] > 0: st.sidebar.warning(f"Upload batch for '{up. st.error(f"Error loading logo: {e}")
with col2_main_title: st.name}' seems duplicate.")
                else:
                    df_excel_full = pd.read_excel(iotitle("📊 Classic Dashboard for Performance")

user_name_display = st.session_state.get('user_name.BytesIO(data))
                    is_cctv_category = (final_category == 'CCTV', "N/A").title()
user_role_display = st.session_state.get('user')

                    if is_cctv_category:
                        # CCTV specific column handling and renaming
                        # Expected Excel columns: code, Choose the violation..., Choose the shift..., Date Submitted, branch, area manager
                        cctv_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout__col_rename_map = {}
                        for col in df_excel_full.columns:
                            colbutton_main"):
    st.session_state.authenticated = False; st.session_state.user__lower_stripped = col.strip().lower()
                            if col_lower_stripped == 'code': cname = None; st.session_state.user_role = None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.sessionctv_col_rename_map[col] = 'code'
                            elif 'violation' in col_state.get('user_name', 'Unknown User')

def generate_pdf(html, fname='report.pdf',_lower_stripped: cctv_col_rename_map[col] = 'issues' # Violation description wk_path=None):
    if not wk_path or wk_path == "not found": st.
                            elif 'shift' in col_lower_stripped: cctv_col_rename_map[colerror("wkhtmltopdf path not set."); return None
    try:
        import pdfkit; config =] = 'shift'
                            elif 'date submitted' in col_lower_stripped: cctv_col pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {'enable-local-file_rename_map[col] = 'date'
                            elif col_lower_stripped == 'branch': cctv_-access': None, 'images': None, 'encoding': "UTF-8",'load-error-handling': 'ignorecol_rename_map[col] = 'branch'
                            elif col_lower_stripped == 'area manager','load-media-error-handling': 'ignore'}
        pdfkit.from_string(html, fname': cctv_col_rename_map[col] = 'area manager' # Keep space for consistency
                            #, configuration=config, options=options);
        with open(fname, 'rb') as f: return f.read Add any other expected CCTV columns here if needed
                        df_excel_full.rename(columns=cctv_col_()
    except Exception as e: st.error(f"PDF error: {e}"); return None

st.sidebar.rename_map, inplace=True)
                        required_cols = ['code', 'issues', 'shift', 'header("🔍 Filters & Options")

if is_admin:
    st.sidebar.subheader("Admin Controls")date', 'branch', 'area manager']
                        # Date parsing for CCTV: Assuming 'Date Submitted' might be MM
    st.sidebar.markdown("Set parameters, select Excel, specify import date range, then upload.")
    selected_category = st.sidebar.selectbox("Category for upload", options=all_categories, key="admin_/DD/YYYY or DD/MM/YYYY.
                        # Using dayfirst=True for consistency, adjust if CCTVcategory_select")
    valid_file_types = category_file_types.get(st.session_state.get("admin_category_select", all_categories[0]), [])
    selected_file_type = st. is strictly MM/DD/YYYY (then use dayfirst=False or no arg)
                        df_excel_fullsidebar.selectbox("File type for upload", options=valid_file_types, key="admin_file_type_select['parsed_date'] = pd.to_datetime(df_excel_full['date'], dayfirst=True,", disabled=(not valid_file_types), help="Options change based on category.")
    st.sidebar. errors='coerce')

                    else: # For other categories
                        df_excel_full.columns = [col.strip().markdown("**Filter Excel Data by Date Range for this Import:**")
    import_from_date_val = st.lower() for col in df_excel_full.columns]
                        required_cols = ['code', 'issuessidebar.date_input("Import Data From Date:", value=date.today() - timedelta(days=7),', 'branch', 'area manager', 'date']
                        df_excel_full['parsed_date'] = key="import_from_date_upload")
    import_to_date_val = st.sidebar. pd.to_datetime(df_excel_full['date'], dayfirst=True, errors='coerce')

                    missing_date_input("Import Data To Date:", value=date.today(), key="import_to_date_uploadcols = [col for col in required_cols if col not in df_excel_full.columns]
                    ")
    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], keyif missing_cols: st.sidebar.error(f"Excel missing required columns: {', '.join(missing="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if upload_btn:
        final_category = st.session_state.admin_cols)}. Aborted.")
                    else:
                        original_excel_rows = len(df_excel__category_select
        final_file_type = st.session_state.admin_file_type_full)
                        df_excel_full.dropna(subset=['parsed_date'], inplace=True)
                        if lenselect
        imp_from_dt = st.session_state.import_from_date_upload
        (df_excel_full) < original_excel_rows: st.sidebar.warning(f"{original_excel_rows - len(df_excel_full)} Excel rows dropped (invalid date).")

                        if dfimp_to_dt = st.session_state.import_to_date_upload
        requires_file_type = bool(category_file_types.get(final_category, []))

        if requires__excel_full.empty: st.sidebar.error("No valid data rows in Excel after date parsing. Aborted.")
                        else:
                            df_to_import = df_excel_full[(df_excel_fullfile_type and not final_file_type:
            st.sidebar.warning(f"Please select a['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date file type for '{final_category}'.")
        elif not up:
            st.sidebar.error("Please'].dt.date <= imp_to_dt)].copy()
                            if df_to_import.empty: st select an Excel file.")
        elif not imp_from_dt or not imp_to_dt:
            st.sidebar.error("Please select both Import From and To Dates.")
        elif imp_from_dt >.sidebar.info(f"No rows in '{up.name}' for the selected import date range.")
                            else: imp_to_dt:
            st.sidebar.error("Import From Date cannot be after Import To Date.")
                                c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date
        else:
            if not requires_file_type: final_file_type = None # Will be NULL, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                          (up.name, current_user, ts in DB
            data = up.getvalue()
            ts = datetime.now().isoformat()
            upload_, final_file_type, final_category, upload_submission_date_str, sqlite3.Binary(submission_date_str = imp_from_dt.isoformat() # This is the 'Import Data From Datedata)))
                                upload_id = c.lastrowid
                                for _, row in df_to_import.iterrows():
                                    issue_date_str = row['parsed_date'].strftime('%Y-%m-%' for the batch

            try:
                c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                          (up.name,d')
                                    # 'area manager' from Excel (with space) maps to 'area_manager' DB current_user, final_file_type, final_category, upload_submission_date_str))
                 column (with underscore)
                                    area_manager_val = row.get('area manager', None)
if c.fetchone()[0] > 0:
                    st.sidebar.warning(f"Upload batch for '{up                                    shift_val = row.get('shift', None) if is_cctv_category else None

.name}' (Category: {final_category}, File Type: {final_file_type or 'N/A                                    c.execute('INSERT INTO issues (upload_id, code, issues, branch, area_manager,'}, Import From: {upload_submission_date_str}) seems duplicate.")
                else:
                    df_ date, report_type, shift) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                              (upload_excel_full = pd.read_excel(io.BytesIO(data))
                    # Standardize column namesid, row['code'], row['issues'], row['branch'], area_manager_val, issue_date_str: lowercase, strip whitespace, replace newlines with spaces
                    df_excel_full.columns = [col.strip()., final_file_type, shift_val))
                                conn.commit(); st.sidebar.success(flower().replace('\n', ' ') for col in df_excel_full.columns]

                    missing_cols"Imported {len(df_to_import)} issues from '{up.name}'."); st.rerun_detected = []
                    date_column_in_excel = ''

                    if final_category == 'CCTV':
()
            except sqlite3.Error as e_sql: conn.rollback(); st.sidebar.error(f"DB                        # Note: Excel column names here must match *after* the standardization above
                        required_cols_cctv error: {e_sql}. Rolled back.")
            except Exception as e_general: conn.rollback(); st.sidebar.error(f"Error processing '{up.name}': {e_general}. Rolled back.")

     = ['code', 'choose the violation - اختر المخالفه', 'choose the shift - اختر الشفت', 'st.sidebar.subheader("Manage Submissions")
    df_uploads_raw_for_delete = pd.read_sqldate submitted', 'branch', 'area manager']
                        missing_cols_detected = [col for col in required_cols_cctv if col not in df_excel_full.columns]
                        date_column_('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
    df_uploads_raw_for_delete['display_in_excel = 'date submitted'
                    else: # Standard format for other categories
                        required_cols_submission_date_fmt'] = df_uploads_raw_for_delete['submission_date'].apply(lambdastd = ['code', 'issues', 'branch', 'area manager', 'date']
                        missing_cols_ d: datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%ddetected = [col for col in required_cols_std if col not in df_excel_full.columns]
                        date_column_in_excel = 'date'

                    if missing_cols_detected:
                        ') if pd.notna(d) else "N/A")
    delete_opts_list = [(st.sidebar.error(f"Excel for '{final_category}' category is missing required columns: {', '.join(missingf"{row['id']} - {row['filename']} ({row['category']}/{row['file_type'] or 'N_cols_detected)}. Please check the file format. Aborted.")
                    else:
                        df_excel_full['parsed/A'}) Imp.From: {row['display_submission_date_fmt']}") for index, row in df_date'] = pd.to_datetime(df_excel_full[date_column_in_excel],_uploads_raw_for_delete.iterrows()]
    delete_opts = ['Select ID to Delete'] + delete_opts_list
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission Batch:", delete_opts, key="delete_submission_id_select")
    if del_choice_display != errors='coerce') # dayfirst=True removed for broader compatibility, Excel should ideally have unambiguous dates or use YYYY-MM 'Select ID to Delete':
        del_id_val = int(del_choice_display.split('-DD
                        original_excel_rows = len(df_excel_full)
                        df_excel_ - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id_val}", key=full.dropna(subset=['parsed_date'], inplace=True)

                        if len(df_excel_full) < originalf"confirm_del_btn_{del_id_val}", type="primary"):
            try:
                _excel_rows:
                            st.sidebar.warning(f"{original_excel_rows - len(dfc.execute('DELETE FROM uploads WHERE id=?', (del_id_val,)); conn.commit() # ON DELETE CASCADE handles issues
                st.sidebar.success(f"Deleted submission batch {del_id_val}.");_excel_full)} Excel rows dropped due to invalid/missing dates in '{date_column_in_excel}' column.")

                        if df_excel_full.empty:
                            st.sidebar.error(f"No valid st.rerun()
            except sqlite3.Error as e: conn.rollback(); st.sidebar.error data rows in Excel after checking dates in '{date_column_in_excel}'. Aborted.")
                        else:
                            (f"Failed to delete: {e}")

    st.sidebar.subheader("Database Management")
    st.sidebar.df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= impmarkdown(
        """
        **To persist data changes (e.g., on Streamlit Cloud):**
        1._from_dt) &
                                                         (df_excel_full['parsed_date'].dt.date <= After uploads/deletions, click "Download Database Backup".
        2. Rename the downloaded file to `issues.db`.
        3. Replace `issues.db` in your local Git project folder.
        4. imp_to_dt)].copy()

                            if df_to_import.empty:
                                st.sidebar Commit and push `issues.db` to GitHub.
        """
    )
    if os.path..info(f"No rows found in '{up.name}' that match the selected import date range ({imp_from_exists(DB_PATH):
        with open(DB_PATH, "rb") as fp:
            dbdt.strftime('%Y-%m-%d')} to {imp_to_dt.strftime('%Y-%m-%_file_bytes = fp.read()
        current_timestamp_str = datetime.now().strftime("%Yd')}).")
                            else:
                                c.execute('INSERT INTO uploads (filename, uploader, timestamp, file%m%d_%H%M%S")
        backup_db_filename = f"issues_backup_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                          (_{current_timestamp_str}.db"
        st.sidebar.download_button(
            label="Downloadup.name, current_user, ts, final_file_type, final_category, upload_submission_ Database Backup",
            data=db_file_bytes,
            file_name=backup_db_filenamedate_str, sqlite3.Binary(data)))
                                upload_id = c.lastrowid

                               ,
            mime="application/vnd.sqlite3",
            key="download_db_now_button_ for _, row in df_to_import.iterrows():
                                    issue_date_str = row['parseddirect",
            help=f"Downloads current '{DB_PATH}'. Rename to '{os.path.basename(_date'].strftime('%Y-%m-%d')
                                    code_val = row['code']
                               DB_PATH)}' for Git commit."
        )
    else:
        st.sidebar.warning(f"'{     branch_val = row['branch']
                                    am_val = row['area manager']

                                    DB_PATH}' not found. Cannot offer download. Upload data first or ensure initial DB is in your repo.")

default_if final_category == 'CCTV':
                                        issue_val = row['choose the violation - اختر المخwk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebarالفه'] # Mapped to 'issues' column in DB
                                        shift_val = row['choose the.text_input("wkhtmltopdf path:", default_wk)

df_uploads_raw_main = shift - اختر الشفت']
                                        c.execute('''INSERT INTO issues (upload_id, code, issues pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date, branch, area_manager, date, report_type, shift)
                                                     VALUES (?, ?, ?, ?, ?, FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') ?, ?, ?)''',
                                                  (upload_id, code_val, issue_val, branch_val, am_val, issue_date_str, final_file_type, shift_val))
                                    else: # if pd.notna(d) else "N/A"
df_uploads_raw_main['display Standard format
                                        issue_val = row['issues']
                                        c.execute('''INSERT INTO issues (_submission_date_fmt'] = df_uploads_raw_main['submission_date'].apply(format_upload_id, code, issues, branch, area_manager, date, report_type, shift)
                                                     VALUES (?, ?, ?, ?, ?, ?, ?, NULL)''', # shift is NULL for non-CCTV
                               display_date)
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] +                   (upload_id, code_val, issue_val, branch_val, am_val, issue_ [(f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'date_str, final_file_type))
                                conn.commit()
                                st.sidebar.success(N/A'}) Imp.From: {r['display_submission_date_fmt']}") for i,r inf"Successfully imported {len(df_to_import)} issues from '{up.name}' for category '{final_category}'. df_uploads_raw_main.iterrows()]
sel_display = st.sidebar.selectbox("Select upload batch to analyze:",")
                                st.rerun()
            except sqlite3.Error as e_sql:
                conn. scope_opts, key="select_upload_scope_main")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

# df_all_issuesrollback()
                st.sidebar.error(f"Database error during import: {e_sql}. Rolled will now include the 'shift' column (NULL for non-CCTV)
df_all_issues = pd.read_sql('SELECT i.*, u.category as upload_category, u.id as upload_id_col FROM back.")
            except KeyError as e_key:
                conn.rollback()
                st.sidebar.error(f"Column mapping error: Missing expected column {e_key} in the Excel file for '{final_category}' issues i JOIN uploads u ON u.id = i.upload_id', conn, parse_dates=['date']) category. Please check the file format. Rolled back.")
            except Exception as e_general:
                conn
if df_all_issues.empty: st.warning("No issues data in database."); st.stop().rollback()
                st.sidebar.error(f"An unexpected error occurred while processing '{up.name}': {

st.sidebar.subheader("Dashboard Filters")
min_overall_date = df_all_issues['datee_general}. Rolled back.")

    st.sidebar.subheader("Manage Submissions")
    df_uploads'].min().date() if pd.notna(df_all_issues['date'].min()) else date._raw_for_delete = pd.read_sql('SELECT id, filename, uploader, timestamp, filetoday()
max_overall_date = df_all_issues['date'].max().date() if pd._type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
    notna(df_all_issues['date'].max()) else date.today()
primary_date_rangedf_uploads_raw_for_delete['display_submission_date_fmt'] = df_uploads_raw = st.sidebar.date_input("Primary Date Range (Issue Dates):", value=[min_overall_date, max_for_delete['submission_date'].apply(lambda d: datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N_overall_date] if min_overall_date <= max_overall_date else [max_overall_date/A")
    delete_opts_list = [(f"{row['id']} - {row['filename']} ({row, min_overall_date], min_value=min_overall_date, max_value=max_overall_date, key="primary_date_range_filter")
if not primary_date_range or len(['category']}/{row['file_type'] or 'N/A'}) Imp.From: {row['displayprimary_date_range) != 2: primary_date_range = [min_overall_date, max_submission_date_fmt']}") for index, row in df_uploads_raw_for_delete.iterrows()]
_overall_date]

branch_opts = ['All'] + sorted(df_all_issues['branch'].astype    delete_opts = ['Select ID to Delete'] + delete_opts_list
    del_choice_display(str).unique().tolist()); sel_branch = st.sidebar.multiselect("Branch:", branch_opts = st.sidebar.selectbox("🗑️ Delete Submission Batch:", delete_opts, key="delete_submission_id_select")
    if del_choice_display != 'Select ID to Delete':
        del_id_, default=['All'], key="branch_filter")
cat_opts = ['All'] + sorted(df_val = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"all_issues['upload_category'].astype(str).unique().tolist()); sel_cat = st.sidebar.multiselect("Category (from Upload Batch):", cat_opts, default=['All'], key="category_filterConfirm Delete Submission #{del_id_val}", key=f"confirm_del_btn_{del_id_val}", type="primary"):
            try:
                c.execute('DELETE FROM uploads WHERE id=?', (")
am_opts = ['All'] + sorted(df_all_issues['area_manager'].astype(del_id_val,)); conn.commit() # ON DELETE CASCADE handles issues
                st.sidebar.successstr).unique().tolist()); sel_am = st.sidebar.multiselect("Area Manager:", am_opts(f"Deleted submission batch {del_id_val}."); st.rerun()
            except sqlite3, default=['All'], key="area_manager_filter")
file_type_filter_opts = ['All'] + sorted(df_all_issues['report_type'].astype(str).unique().tolist()); sel_.Error as e: conn.rollback(); st.sidebar.error(f"Failed to delete: {e}")

    st.sidebar.subheader("Database Management")
    st.sidebar.markdown(
        """
        **ft = st.sidebar.multiselect("File Type (from Upload Batch):", file_type_filter_opts, default=['All'], key="file_type_filter")

# New filter for Shift (primarily for CCTV data)
shift_opts_raw = df_all_issues['shift'].dropna().unique() # Get unique non-nullTo persist data changes (e.g., on Streamlit Cloud):**
        1. After uploads/deletions, click "Download Database Backup".
        2. Rename the downloaded file to `issues.db`.
        3. Replace `issues.db` in your local Git project folder.
        4. Commit and push `issues.db` shifts
shift_opts = ['All'] + sorted([str(s) for s in shift_opts_raw to GitHub.
        """
    )
    if os.path.exists(DB_PATH):
         if s]) # Ensure they are strings and not empty
sel_shift = st.sidebar.multiselect("Shift (with open(DB_PATH, "rb") as fp:
            db_file_bytes = fp.readCCTV):", shift_opts, default=['All'], key="shift_filter")


st.sidebar.subheader("📊 Period()
        current_timestamp_str = datetime.now().strftime("%Y%m%d_%H%M Comparison")
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox")
%S")
        backup_db_filename = f"issues_backup_{current_timestamp_str}.dbcomparison_date_range_1, comparison_date_range_2 = None, None
if enable_comparison"
        st.sidebar.download_button(
            label="Download Database Backup",
            data=db_file_bytes,
            file_name=backup_db_filename,
            mime="application/vnd.sqlite3:
    st.sidebar.markdown("**Comparison Period 1 (Issue Dates):**")
    safe_default_p1_end = min_overall_date + timedelta(days=6); safe_default_p1_end =",
            key="download_db_now_button_direct",
            help=f"Downloads current '{DB_PATH}'. Rename to '{os.path.basename(DB_PATH)}' for Git commit."
        ) min(safe_default_p1_end, max_overall_date); safe_default_p1_
    else:
        st.sidebar.warning(f"'{DB_PATH}' not found. Cannot offerend = max(safe_default_p1_end, min_overall_date)
    comparison_date download. Upload data first or ensure initial DB is in your repo.")

default_wk = shutil.which('wkhtmltopdf_range_1_val = st.sidebar.date_input("Start & End Date (Period 1):') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path", value=[min_overall_date, safe_default_p1_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period1_filter")
    if:", default_wk)

df_uploads_raw_main = pd.read_sql('SELECT id, filename, uploader comparison_date_range_1_val and len(comparison_date_range_1_val) == 2:
        comparison_date_range_1 = comparison_date_range_1_val
        st, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC',.sidebar.markdown("**Comparison Period 2 (Issue Dates):**")
        default_p2_start = conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-% comparison_date_range_1[1] + timedelta(days=1); default_p2_start =m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/ min(default_p2_start, max_overall_date); default_p2_start = max(A"
df_uploads_raw_main['display_submission_date_fmt'] = df_uploads_default_p2_start, min_overall_date)
        default_p2_end = default_raw_main['submission_date'].apply(format_display_date)
st.sidebar.subheader("Datap2_start + timedelta(days=6); default_p2_end = min(default_p2_end, max_overall_date); default_p2_end = max(default_p2_end Scope")
scope_opts = ['All uploads'] + [(f"{r['id']} - {r['filename']}, default_p2_start)
        comparison_date_range_2_val = st.sidebar. ({r['category']}/{r['file_type'] or 'N/A'}) Imp.From: {r['display_submission_date_fmt']}") for i,r in df_uploads_raw_main.iterrows()]
sel_display =date_input("Start & End Date (Period 2):", value=[default_p2_start, default_p2_end], min_value=min_overall_date, max_value=max_overall_ st.sidebar.selectbox("Select upload batch to analyze:", scope_opts, key="select_upload_scope_date, key="comparison_period2_filter")
        if comparison_date_range_2_val andmain")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All len(comparison_date_range_2_val) == 2: comparison_date_range_2 = uploads' else None

# df_all_issues will now include the 'shift' column from the issues table ( comparison_date_range_2_val
        else: comparison_date_range_2 = None
    else: comparisonit will be None for non-CCTV issues)
df_all_issues = pd.read_sql('SELECT i_date_range_1 = None; comparison_date_range_2 = None

def apply_general_.*, u.category as upload_category, u.id as upload_id_col FROM issues i JOIN uploads ufilters(df_input, sel_upload_id_val, selected_branches, selected_categories, selected_managers, selected ON u.id = i.upload_id', conn, parse_dates=['date'])
if df_all_file_types, selected_shifts):
    df_filtered = df_input.copy()
    if_issues.empty: st.warning("No issues data in database."); st.stop()

st.sidebar. sel_upload_id_val: df_filtered = df_filtered[df_filtered['upload_id_subheader("Dashboard Filters")
min_overall_date = df_all_issues['date'].min().date() if pd.notna(df_all_issues['date'].min()) else date.today()
max_overallcol'] == sel_upload_id_val]
    if 'All' not in selected_branches: df_date = df_all_issues['date'].max().date() if pd.notna(df_all_filtered = df_filtered[df_filtered['branch'].isin(selected_branches)]
    if 'All_issues['date'].max()) else date.today()
primary_date_range = st.sidebar.date_input' not in selected_categories: df_filtered = df_filtered[df_filtered['upload_category'].isin(selected_categories)]
    if 'All' not in selected_managers: df_filtered = df_filtered("Primary Date Range (Issue Dates):", value=[min_overall_date, max_overall_date] if min_overall[df_filtered['area_manager'].isin(selected_managers)]
    if 'All' not in selected_date <= max_overall_date else [max_overall_date, min_overall_date], min__file_types: df_filtered = df_filtered[df_filtered['report_type'].isin(selectedvalue=min_overall_date, max_value=max_overall_date, key="primary_date__file_types)]
    if 'All' not in selected_shifts:
        # This will filter forrange_filter")
if not primary_date_range or len(primary_date_range) != 2: primary_date_range = [min_overall_date, max_overall_date]
branch_opts = [' specific shifts. Rows with NULL shift (non-CCTV or CCTV without shift) will be excluded.
        dfAll'] + sorted(df_all_issues['branch'].astype(str).unique().tolist()); sel_branch = st_filtered = df_filtered[df_filtered['shift'].isin(selected_shifts)]
    return df_.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")
filtered

df_temp_filtered = apply_general_filters(df_all_issues, sel_id, selcat_opts = ['All'] + sorted(df_all_issues['upload_category'].astype(str)._branch, sel_cat, sel_am, sel_ft, sel_shift)
df_primary_unique().tolist()); sel_cat = st.sidebar.multiselect("Category (from Upload Batch):", catperiod = df_temp_filtered.copy()
if primary_date_range and len(primary_date__opts, default=['All'], key="category_filter")
am_opts = ['All'] + sorted(range) == 2:
    start_date_filt, end_date_filt = primary_date_df_all_issues['area_manager'].astype(str).unique().tolist()); sel_am = st.sidebar.multiselect("Area Manager:", am_opts, default=['All'], key="area_manager_filterrange[0], primary_date_range[1]
    if 'date' in df_primary_period")
file_type_filter_opts = ['All'] + sorted(df_all_issues['report_type'].astype.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period(str).unique().tolist()); sel_ft = st.sidebar.multiselect("File Type (from Upload['date']):
        df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= start_date_filt) & (df_primary_period['date'].dt.date <= end_date_filt)]
else: df_primary_period = pd.DataFrame(columns=df_ Batch):", file_type_filter_opts, default=['All'], key="file_type_filter")

temp_filtered.columns)
st.subheader(f"Filtered Issues for Primary Period: {primary_date_range[0st.sidebar.subheader("📊 Period Comparison")
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st="enable_comparison_checkbox")
comparison_date_range_1, comparison_date_range_2 =.write(f"Total issues found in primary period: {len(df_primary_period)}")

def create_bar_ None, None
if enable_comparison:
    st.sidebar.markdown("**Comparison Period 1 (Issue Dates):chart(df_source, group_col, title_suffix=""):
    title = f"Issues by {**")
    safe_default_p1_end = min_overall_date + timedelta(days=6); safe_group_col.replace('_',' ').title()} {title_suffix}"
    if group_col in df_source.columnsdefault_p1_end = min(safe_default_p1_end, max_overall_date); safe_default_p1_end = max(safe_default_p1_end, min_overall_ and not df_source[group_col].isnull().all():
        # Ensure group_col is string for grouping, especiallydate)
    comparison_date_range_1_val = st.sidebar.date_input("Start & End Date (Period 1):", value=[min_overall_date, safe_default_p1_end if it might contain mixed types or NaNs
        data = df_source.astype({group_col: str}).groupby], min_value=min_overall_date, max_value=max_overall_date, key="comparison(group_col).size().reset_index(name='count').sort_values('count', ascending=False_period1_filter")
    if comparison_date_range_1_val and len(comparison_date)
        if not data.empty: return px.bar(data, x=group_col, y='_range_1_val) == 2:
        comparison_date_range_1 = comparison_datecount', title=title, template="plotly_white")
    return None

def create_pie_chart(df_range_1_val
        st.sidebar.markdown("**Comparison Period 2 (Issue Dates):**")
        default_p2_start = comparison_date_range_1[1] + timedelta(days=_source, group_col, title_suffix=""):
    title = f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col in df_source.columns1); default_p2_start = min(default_p2_start, max_overall_date); and not df_source[group_col].isnull().all():
        data = df_source.astype({ default_p2_start = max(default_p2_start, min_overall_date)
        group_col: str}).groupby(group_col).size().reset_index(name='count')
        default_p2_end = default_p2_start + timedelta(days=6); default_p2if not data.empty: return px.pie(data, names=group_col, values='count', title_end = min(default_p2_end, max_overall_date); default_p2_end=title, hole=0.3, template="plotly_white")
    return None

if df_primary = max(default_p2_end, default_p2_start)
        comparison_date_range_period.empty:
    st.info("No data matches the current filter criteria for the primary period.")
_2_val = st.sidebar.date_input("Start & End Date (Period 2):", valueelse:
    figs_primary = {}
    col1_charts, col2_charts, col3_charts=[default_p2_start, default_p2_end], min_value=min_overall_date = st.columns(3) # Added a third column for potential shift chart
    with col1_charts:
        , max_value=max_overall_date, key="comparison_period2_filter")
        if comparisonfigs_primary['Branch'] = create_bar_chart(df_primary_period, 'branch', '(Primary_date_range_2_val and len(comparison_date_range_2_val) == 2: comparison_date_range_2 = comparison_date_range_2_val
        else: comparison_)')
        if figs_primary['Branch']: st.plotly_chart(figs_primary['Branch'], use_date_range_2 = None
    else: comparison_date_range_1 = None; comparison_datecontainer_width=True)
        figs_primary['Report Type'] = create_bar_chart(df__range_2 = None

def apply_general_filters(df_input, sel_upload_id_val, selectedprimary_period, 'report_type', '(Primary)')
        if figs_primary['Report Type']: st._branches, selected_categories, selected_managers, selected_file_types):
    df_filtered = dfplotly_chart(figs_primary['Report Type'], use_container_width=True)
    with col2_input.copy()
    if sel_upload_id_val: df_filtered = df_filtered[_charts:
        figs_primary['Area Manager'] = create_pie_chart(df_primary_perioddf_filtered['upload_id_col'] == sel_upload_id_val]
    if 'All, 'area_manager', '(Primary)')
        if figs_primary['Area Manager']: st.plotly_chart' not in selected_branches: df_filtered = df_filtered[df_filtered['branch'].isin(selected(figs_primary['Area Manager'], use_container_width=True)
        figs_primary['Category']_branches)]
    if 'All' not in selected_categories: df_filtered = df_filtered[df = create_bar_chart(df_primary_period, 'upload_category', '(Primary)')
        if_filtered['upload_category'].isin(selected_categories)]
    if 'All' not in selected_managers figs_primary['Category']: st.plotly_chart(figs_primary['Category'], use_container_width=: df_filtered = df_filtered[df_filtered['area_manager'].isin(selected_managers)]
True)
    with col3_charts: # For shift chart if applicable
        # Only show shift chart if there    if 'All' not in selected_file_types: df_filtered = df_filtered[df_filtered's shift data (i.e., CCTV data is present and filtered)
        if 'shift' in df_['report_type'].isin(selected_file_types)]
    return df_filtered

df_temp_primary_period.columns and df_primary_period['shift'].notna().any():
            figs_primary['Shiftfiltered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel'] = create_bar_chart(df_primary_period[df_primary_period['shift'].notna_am, sel_ft)
df_primary_period = df_temp_filtered.copy()
if()], 'shift', '(Primary - CCTV Shifts)')
            if figs_primary['Shift']: st.plotly_chart( primary_date_range and len(primary_date_range) == 2:
    start_date_filt, end_date_filt = primary_date_range[0], primary_date_range[1]
figs_primary['Shift'], use_container_width=True)
        else:
            st.empty()    if 'date' in df_primary_period.columns and pd.api.types.is_datetime6 # Keep column spacing

    if 'date' in df_primary_period.columns and pd.api.types4_any_dtype(df_primary_period['date']):
        df_primary_period = df_.is_datetime64_any_dtype(df_primary_period['date']) and not df_primaryprimary_period[(df_primary_period['date'].dt.date >= start_date_filt) & (_period['date'].isnull().all():
        trend_data_primary = df_primary_period.groupby(df_df_primary_period['date'].dt.date <= end_date_filt)]
else: df_primaryprimary_period['date'].dt.date).size().reset_index(name='daily_issues')
        _period = pd.DataFrame(columns=df_temp_filtered.columns)

st.subheader(f"Filteredtrend_data_primary['date'] = pd.to_datetime(trend_data_primary['date']); trend_data_ Issues for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total issues found inprimary = trend_data_primary.sort_values('date')
        if not trend_data_primary. primary period: {len(df_primary_period)}")

def create_bar_chart(df_source,empty:
            window_size = min(7, len(trend_data_primary)); window_size = group_col, title_suffix=""):
    title = f"Issues by {group_col.replace('_ max(2,window_size)
            trend_data_primary[f'{window_size}-Day MA',' ').title()} {title_suffix}"
    if group_col in df_source.columns and not df_'] = trend_data_primary['daily_issues'].rolling(window=window_size, center=True, min_periodssource[group_col].isnull().all():
        # Ensure the group_col is treated as string for grouping=1).mean().round(1)
            fig_trend = go.Figure()
            fig_trend to avoid issues with mixed types or numbers
        data = df_source.astype({group_col: str}).groupby.add_trace(go.Bar(x=trend_data_primary['date'], y=trend_data(group_col).size().reset_index(name='count').sort_values('count', ascending=False_primary['daily_issues'], name='Daily Issues', marker_color='lightblue', hovertemplate="<b>%{x)
        if not data.empty: return px.bar(data, x=group_col, y='count', title=title, template="plotly_white")
    return None

def create_pie_chart(df|%A, %b %d}</b><br>Issues: %{y}<extra></extra>"))
            fig_source, group_col, title_suffix=""):
    title = f"Issues by {group_col_trend.add_trace(go.Scatter(x=trend_data_primary['date'], y=trend.replace('_',' ').title()} {title_suffix}"
    if group_col in df_source.columns_data_primary[f'{window_size}-Day MA'], name=f'{window_size}-Day Moving and not df_source[group_col].isnull().all():
        data = df_source.astype({ Avg.', mode='lines+markers', line=dict(color='royalblue', width=2), marker=dict(size=5group_col: str}).groupby(group_col).size().reset_index(name='count')
        ), hovertemplate="<b>%{x|%A, %b %d}</b><br>Moving Avg: %if not data.empty: return px.pie(data, names=group_col, values='count', title{y:.1f}<extra></extra>"))
            fig_trend.update_layout(title_text='Issues=title, hole=0.3, template="plotly_white")
    return None

if df_primary Trend (Primary Period - Based on Issue Dates)', xaxis_title='Date', yaxis_title='Number of Issues_period.empty:
    st.info("No data matches the current filter criteria for the primary period.")
', template="plotly_white", hovermode="x unified", legend_title_text='Metric')
            figs_primary['Trend'] = fig_trend
            st.plotly_chart(figs_primary['Trend'], use_container_else:
    figs_primary = {}
    col1_charts, col2_charts = st.columns(2)
    with col1_charts:
        figs_primary['Branch'] = create_bar_width=True)

    if len(df_primary_period) < 50 or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.chart(df_primary_period, 'branch', '(Primary)')
        if figs_primary['Branch']: stsubheader("Detailed Records (Primary Period - Filtered)")
        # Added 'shift' to the detailed records
        df_display_primary = df_primary_period[['date', 'branch', 'report_type', 'upload_category',.plotly_chart(figs_primary['Branch'], use_container_width=True)

        figs_primary 'issues', 'area_manager', 'code', 'shift']].copy()
        if pd.api.types['Report Type'] = create_bar_chart(df_primary_period, 'report_type', '(Primary.is_datetime64_any_dtype(df_display_primary['date']): df_display_primary['date'] = df_display_primary['date'].dt.strftime('%Y-%m-%d')
        )')
        if figs_primary['Report Type']: st.plotly_chart(figs_primary['Report Type'], use_container_width=True)

        # New: CCTV Shift Chart (conditionally) - Placed in firstst.dataframe(df_display_primary, use_container_width=True)

    st.subheader("Top Issues ( column for space
        df_cctv_shifts = df_primary_period[df_primary_period['uploadPrimary Period - Filtered)")
    if 'issues' in df_primary_period.columns and not df_primary_period['issues'].isnull().all():
        # For CCTV, 'issues' column contains the violation type, so this will_category'] == 'CCTV']
        if not df_cctv_shifts.empty and 'shift' in df_cctv_shifts.columns and not df_cctv_shifts['shift'].isnull show top violations.
        top_issues_primary = df_primary_period['issues'].astype(str).().all():
            figs_primary['CCTV Shifts'] = create_bar_chart(df_cctvalue_counts().head(20).rename_axis('Issue/Violation Description').reset_index(name='Frequency')
v_shifts, 'shift', '(Primary - CCTV Shifts)')
            if figs_primary['CCTV Shifts']:        if not top_issues_primary.empty: st.dataframe(top_issues_primary, use_container st.plotly_chart(figs_primary['CCTV Shifts'], use_container_width=True)

    with col2_charts:
        figs_primary['Area Manager'] = create_pie_chart(df__width=True)

if enable_comparison and comparison_date_range_1 and comparison_date_rangeprimary_period, 'area_manager', '(Primary)')
        if figs_primary['Area Manager']: st._2:
    st.markdown("---"); st.header("📊 Period Comparison Results (Based on Issue Datesplotly_chart(figs_primary['Area Manager'], use_container_width=True)

        figs_primary)")
    df_comp1 = pd.DataFrame(columns=df_temp_filtered.columns); df_['Category'] = create_bar_chart(df_primary_period, 'upload_category', '(Primary)')comp2 = pd.DataFrame(columns=df_temp_filtered.columns)
    start_c1_
        if figs_primary['Category']: st.plotly_chart(figs_primary['Category'], use_containerdisp, end_c1_disp, start_c2_disp, end_c2_disp = "_width=True)


    if 'date' in df_primary_period.columns and pd.api.typesN/A", "N/A", "N/A", "N/A"
    if comparison_date_range_1 and len(comparison_date_range_1) == 2:
        start_.is_datetime64_any_dtype(df_primary_period['date']) and not df_primary_period['date'].isnull().all():
        trend_data_primary = df_primary_period.groupby(df_c1, end_c1 = comparison_date_range_1[0], comparison_date_range_1[1]
        if 'date' in df_temp_filtered.columns and pd.api.typesprimary_period['date'].dt.date).size().reset_index(name='daily_issues')
        .is_datetime64_any_dtype(df_temp_filtered['date']): df_comp1 =trend_data_primary['date'] = pd.to_datetime(trend_data_primary['date']); trend_data_primary = trend_data_primary.sort_values('date')
        if not trend_data_primary. df_temp_filtered[(df_temp_filtered['date'].dt.date >= start_c1) &empty:
            window_size = min(7, len(trend_data_primary)); window_size = (df_temp_filtered['date'].dt.date <= end_c1)].copy()
        start_ max(2,window_size)
            trend_data_primary[f'{window_size}-Day MA'] = trend_data_primary['daily_issues'].rolling(window=window_size, center=True, min_periodsc1_disp, end_c1_disp = start_c1.strftime('%Y-%m-%d=1).mean().round(1)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=trend_data_primary['date'], y=trend_data'), end_c1.strftime('%Y-%m-%d')
    if comparison_date_range_2_primary['daily_issues'], name='Daily Issues', marker_color='lightblue', hovertemplate="<b>%{x| and len(comparison_date_range_2) == 2:
        start_c2, end_%A, %b %d}</b><br>Issues: %{y}<extra></extra>"))
            fig_trend.add_trace(go.Scatter(x=trend_data_primary['date'], yc2 = comparison_date_range_2[0], comparison_date_range_2[1]
        if 'date' in df_temp_filtered.columns and pd.api.types.is_datetime6=trend_data_primary[f'{window_size}-Day MA'], name=f'{window_size}-4_any_dtype(df_temp_filtered['date']): df_comp2 = df_temp_filteredDay Moving Avg.', mode='lines+markers', line=dict(color='royalblue', width=2), marker=dict(size=5), hovertemplate="<b>%{x|%A, %b %d}</b><br>[(df_temp_filtered['date'].dt.date >= start_c2) & (df_temp_filtered['date'].dt.date <= end_c2)].copy()
        start_c2_disp,Moving Avg: %{y:.1f}<extra></extra>"))
            fig_trend.update_layout(title_text='Issues Trend (Primary Period - Based on Issue Dates)', xaxis_title='Date', yaxis_title end_c2_disp = start_c2.strftime('%Y-%m-%d'), end_c2.strftime('%Y-%m-%d')

    if not df_comp1.empty or not df_comp2.empty:
        if comparison_date_range_1: st.subheader(f"Period 1: {start_c1_disp} to {end_c1_disp} (Total: {len(df_comp='Number of Issues', template="plotly_white", hovermode="x unified", legend_title_text='Metric')
            figs_primary['Trend'] = fig_trend
            st.plotly_chart(figs_primary['Trend'], use_container_width=True)

    if len(df_primary_period) < 501)} issues)")
        if comparison_date_range_2: st.subheader(f"Period 2: {start_c2_disp} to {end_c2_disp} (Total: {len(df_comp2)} issues)")
        col_comp1_disp, col_comp2_disp = st.columns(2)
        with col_comp1_disp:
            st.metric(label=f or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.subheader("Detailed Records (Primary Period - Filtered)")
        df_display_primary_cols = ['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']
        # Conditionally add 'shift' column if it exists and has non-null data
        if 'shift"Total Issues (P1)", value=len(df_comp1))
            if not df_comp1.empty: st.dataframe(df_comp1['issues'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue/Violation', 'issues':'Count'}), height=220, use_container_width=' in df_primary_period.columns and not df_primary_period['shift'].isnull().all():
            df_display_primary_cols.append('shift')
        
        # Ensure all selected columns actually exist in dfTrue)
        with col_comp2_disp:
            delta_val = len(df_comp2) - len(df_comp1); st.metric(label=f"Total Issues (P2)", value=len(df_comp2), delta=f"{delta_val:+}" if delta_val !=0 else None)
            if not df_comp2.empty: st.dataframe(df_comp2['issues']._primary_period before trying to select them
        df_display_primary_cols_exist = [col for col in df_display_primary_cols if col in df_primary_period.columns]
        df_display_primary = df_primary_period[df_display_primary_cols_exist].copy()

        if 'date' in df_display_primary.columns and pd.api.types.is_datetime64_any_value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue/Violation', 'issues':'Count'}), height=220, use_container_width=True)

        if not df_comp1dtype(df_display_primary['date']):
             df_display_primary['date'] = df_display_primary['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_display.empty or not df_comp2.empty:
            df_comp1_labeled = df_comp1.copy(); df_comp2_labeled = df_comp2.copy()
            if comparison_date_range_1: df_comp1_labeled['period_label'] = f"P1: {comparison__primary, use_container_width=True)

    st.subheader("Top Issues (Primary Period - Filtered)")
    if 'issues' in df_primary_period.columns and not df_primary_period['issues'].date_range_1[0]:%d%b}-{comparison_date_range_1[1]:%d%b}"
            if comparison_date_range_2: df_comp2_labeled['period_label'] = f"P2: {comparison_date_range_2[0]:%d%b}-{comparisonisnull().all():
        top_issues_primary = df_primary_period['issues'].astype(str).value_counts().head(20).rename_axis('Issue Description').reset_index(name='Frequency')
        if not top__date_range_2[1]:%d%b}"
            dfs_to_concat = [];
            if not df_comp1_labeled.empty and 'period_label' in df_comp1_labeled.columns : dfs_to_concat.append(df_comp1_labeled)
            if not df_comp2_issues_primary.empty: st.dataframe(top_issues_primary, use_container_width=True)

if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.markdown("---"); st.header("📊 Period Comparison Results (Based on Issue Dates)")
    df_comp1 =labeled.empty and 'period_label' in df_comp2_labeled.columns : dfs_to_concat pd.DataFrame(columns=df_temp_filtered.columns); df_comp2 = pd.DataFrame(columns=df_temp_filtered.columns)
    start_c1_disp, end_c1_disp.append(df_comp2_labeled)
            if dfs_to_concat:
                df_combined_branch = pd.concat(dfs_to_concat)
                if not df_combined_branch.empty, start_c2_disp, end_c2_disp = "N/A", "N/A:
                    branch_comp_data = df_combined_branch.groupby(['branch', 'period_label']).", "N/A", "N/A"
    if comparison_date_range_1 and len(size().reset_index(name='count')
                    if not branch_comp_data.empty:
                        comparison_date_range_1) == 2:
        start_c1, end_c1 =fig_branch_comp = px.bar(branch_comp_data, x='branch', y='count', color='period_label', barmode='group', title='Issues by Branch (Comparison)')
                        st. comparison_date_range_1[0], comparison_date_range_1[1]
        if 'date' in df_temp_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_temp_filtered['date']): df_comp1 = df_temp_filtered[(df_plotly_chart(fig_branch_comp, use_container_width=True)
            st.markdown("#### Period-Level Trend (Average Daily Issues)")
            period_summary_data = []
            if comparison_date_rangetemp_filtered['date'].dt.date >= start_c1) & (df_temp_filtered['date'].dt.date <= end_c1)].copy()
        start_c1_disp, end_c1_disp = start_c1.strftime('%Y-%m-%d'), end_c1.strftime('%_1 and not df_comp1.empty: avg_issues_p1 = df_comp1.groupby(df_comp1['date'].dt.date).size().mean(); period_summary_data.append({'Period': f"Period 1 ({comparison_date_range_1[0]:%b %d} -Y-%m-%d')
    if comparison_date_range_2 and len(comparison_date_range_2) == 2:
        start_c2, end_c2 = comparison_date_range_2[0], comparison_date_range_2[1]
        if 'date' in df_temp_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_temp_filtered['date']): df_comp2 = df_temp_filtered[(df_temp_filtered['date {comparison_date_range_1[1]:%b %d})", 'StartDate': pd.to_datetime(comparison_date_range_1[0]), 'AverageDailyIssues': round(avg_issues_p1, 2)})
            if comparison_date_range_2 and not df_comp2.empty: avg_issues_p2 = df_comp2.groupby(df_comp2['date'].dt.date).size().mean(); period_summary_data.append({'Period': f"Period 2 ({comparison_date_range_2[0]:%b %d} - {comparison_date_range_2[1]:%b'].dt.date >= start_c2) & (df_temp_filtered['date'].dt.date <= end_c2)].copy()
        start_c2_disp, end_c2_disp = start_c2.strftime('%Y-%m-%d'), end_c2.strftime('%Y-%m-%d')

    if not df_comp1.empty or not df_comp2.empty:
        if comparison_date_range_1: st.subheader(f"Period 1: {start_c1_disp} %d})", 'StartDate': pd.to_datetime(comparison_date_range_2[0]), 'AverageDailyIssues': round(avg_issues_p2, 2)})
            if len(period_summary_data) >= 1:
                df_period_trend = pd.DataFrame(period_summary_data to {end_c1_disp} (Total: {len(df_comp1)} issues)")
        if comparison_date_range_2: st.subheader(f"Period 2: {start_c2_disp} to {end_c2_disp} (Total: {len(df_comp2)} issues).sort_values('StartDate')
                if len(df_period_trend) == 1: fig_period_level_trend = px.bar(df_period_trend, x='Period', y='AverageDailyIssues', text='AverageDailyIssues', title='Avg Daily Issues by Period'); fig_period_level_trend.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                else: fig_period_level_trend = px.line(df_period_trend, x='Period', y='AverageDailyIssues)")
        col_comp1_disp, col_comp2_disp = st.columns(2)
        with col_comp1_disp:
            st.metric(label=f"Total Issues (P1)", value=len(df_comp1))
            if not df_comp1.empty: st.dataframe', markers=True, text='AverageDailyIssues', title='Trend of Avg Daily Issues Across Periods'); fig_period_level_trend.update_traces(texttemplate='%{text:.2f}', textposition='top center')
                fig_period_level_trend.update_layout(xaxis_title="Comparison Period", yaxis_title="(df_comp1['issues'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue', 'issues':'Count'}), height=220, use_container_width=True)
Avg. Daily Issues", template="plotly_white"); st.plotly_chart(fig_period_level_trend        with col_comp2_disp:
            delta_val = len(df_comp2) - len(df_comp1); st.metric(label=f"Total Issues (P2)", value=len(, use_container_width=True)
            else: st.info("Not enough data for period-level trend.")
    else: st.warning("No data for either comparison period with current general filters.")

st.sidebar.df_comp2), delta=f"{delta_val:+}" if delta_val !=0 else None)
subheader("Downloads")
if 'df_primary_period' in locals() and not df_primary_period.empty:
    csv_data_primary = df_primary_period.to_csv(index=False).            if not df_comp2.empty: st.dataframe(df_comp2['issues'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue', 'issues':'Count'}), heightencode('utf-8')
    st.sidebar.download_button("Download Primary Period Data as CSV", csv_data_=220, use_container_width=True)

        if not df_comp1.empty or not df_comp2.empty:
            df_comp1_labeled = df_comp1.copy(); df_primary, "primary_period_issues.csv", "text/csv", key="download_csv_primary")comp2_labeled = df_comp2.copy()
            if comparison_date_range_1: df_comp1
    if st.sidebar.button("Prepare Visuals PDF (Primary Period)", key="prep_visuals_pdf_primary_labeled['period_label'] = f"P1: {comparison_date_range_1[0]:%d"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wk%b}-{comparison_date_range_1[1]:%d%b}"
            if comparison_date_range_htmltopdf path not set.")
        elif 'figs_primary' not in locals() or not figs_primary2: df_comp2_labeled['period_label'] = f"P2: {comparison_date_range_2[0]:%d%b}-{comparison_date_range_2[1]:%d% or not any(figs_primary.values()): st.sidebar.warning("No visuals for primary period.")
        b}"
            dfs_to_concat = [];
            if not df_comp1_labeled.empty and 'period_else:
            html_content = "<html><head><meta charset='utf-8'><title>Visuals Report (Primary)</title><style>body{font-family:sans-serif;} h1,h2{text-label' in df_comp1_labeled.columns : dfs_to_concat.append(df_comp1align:center;} img{display:block;margin-left:auto;margin-right:auto;max-_labeled)
            if not df_comp2_labeled.empty and 'period_label' in df_width:90%;height:auto;border:1px solid #ccc;padding:5px;margin-comp2_labeled.columns : dfs_to_concat.append(df_comp2_labeled)
            bottom:20px;} @media print {* {-webkit-print-color-adjust:exact !important; color-if dfs_to_concat:
                df_combined_branch = pd.concat(dfs_to_concatadjust:exact !important; print-color-adjust:exact !important;} body { background-color:white !)
                if not df_combined_branch.empty:
                    branch_comp_data = df_combined_branch.groupby(['branch', 'period_label']).size().reset_index(name='count')
                    important;}}</style></head><body>"
            html_content += f"<h1>Visuals Report (Primaryif not branch_comp_data.empty:
                        fig_branch_comp = px.bar(branch_: {primary_date_range[0]:%Y-%m-%d} to {primary_date_rangecomp_data, x='branch', y='count', color='period_label', barmode='group', title='Issues[1]:%Y-%m-%d})</h1>";
            chart_titles_in_order = ["Branch", by Branch (Comparison)')
                        st.plotly_chart(fig_branch_comp, use_container_width "Area Manager", "Report Type", "Category", "Shift", "Trend"] # Added Shift
            for title in=True)

            st.markdown("#### Period-Level Trend (Average Daily Issues)")
            period_summary chart_titles_in_order:
                if figs_primary.get(title):
                    fig_obj_data = []
            if comparison_date_range_1 and not df_comp1.empty: avg = figs_primary[title]; img_bytes = fig_obj.to_image(format='png', engine='_issues_p1 = df_comp1.groupby(df_comp1['date'].dt.date).kaleido', scale=1.5); b64_img = base64.b64encode(img_size().mean(); period_summary_data.append({'Period': f"Period 1 ({comparison_date_bytes).decode() # Reduced scale slightly
                    html_content += f"<h2>{title.replace('(Primary -range_1[0]:%b %d} - {comparison_date_range_1[1]:%b % CCTV Shifts)', '(CCTV Shifts)')}</h2><img src='data:image/png;base64,{b64d})", 'StartDate': pd.to_datetime(comparison_date_range_1[0]), 'AverageDailyIssues': round(avg_issues_p1, 2)})
            if comparison_date_range__img}' alt='{title}'/>"
            html_content += "</body></html>"; pdf_bytes =2 and not df_comp2.empty: avg_issues_p2 = df_comp2.groupby( generate_pdf(html_content, fname='visuals_report_primary.pdf', wk_path=wkdf_comp2['date'].dt.date).size().mean(); period_summary_data.append({'Period_path)
            if pdf_bytes: st.session_state.pdf_visuals_primary_data = pdf_bytes; st.sidebar.success("Visuals PDF (Primary) ready.")
            else:
': f"Period 2 ({comparison_date_range_2[0]:%b %d} - {comparison_date_range_2[1]:%b %d})", 'StartDate': pd.to_datetime                if 'pdf_visuals_primary_data' in st.session_state: del st.session_state.pdf_visuals_primary_data
    if 'pdf_visuals_primary_data' in(comparison_date_range_2[0]), 'AverageDailyIssues': round(avg_issues_p2, 2)})
            if len(period_summary_data) >= 1:
                df_period st.session_state and st.session_state.pdf_visuals_primary_data:
        st_trend = pd.DataFrame(period_summary_data).sort_values('StartDate')
                if len(.sidebar.download_button(label="Download Visuals PDF (Primary) Now", data=st.session_state.pdf_visuals_primary_data, file_name="visuals_report_primary.pdf", mime="application/pdf", key="action_dl_visuals_pdf_primary")

    if st.df_period_trend) == 1: fig_period_level_trend = px.bar(df_period_trend, x='Period', y='AverageDailyIssues', text='AverageDailyIssues', title='Avg Daily Issues by Period'); fig_period_level_trend.update_traces(texttemplate='%{text:.2fsidebar.button("Prepare Full Dashboard PDF (Primary Period)", key="prep_dashboard_pdf_primary"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not}', textposition='outside')
                else: fig_period_level_trend = px.line(df_ set.")
        else:
            html_full = "<head><meta charset='utf-8'><style>body{font-family:sans-serif;} table{border-collapse:collapse;width:100%;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background-colorperiod_trend, x='Period', y='AverageDailyIssues', markers=True, text='AverageDailyIssues', title='Trend of Avg Daily Issues Across Periods'); fig_period_level_trend.update_traces(texttemplate:#f2f2f2;}</style></head>"
            html_full += f"<h1>Dashboard Report (Primary: {primary_date_range[0]:%Y-%m-%d} to {primary_date_='%{text:.2f}', textposition='top center')
                fig_period_level_trend.update_layout(xaxis_title="Comparison Period", yaxis_title="Avg. Daily Issues", template="plotly_range[1]:%Y-%m-%d})</h1>"
            # Added 'shift' to PDF table
            df_pdf_view = df_primary_period[['date', 'branch', 'report_type', 'upload_white"); st.plotly_chart(fig_period_level_trend, use_container_width=True)
            else: st.info("Not enough data for period-level trend.")
    else: st.warningcategory', 'issues', 'area_manager', 'code', 'shift']].copy()
            if pd.api.types("No data for either comparison period with current general filters.")

st.sidebar.subheader("Downloads")
if '.is_datetime64_any_dtype(df_pdf_view['date']): df_pdf_view['date'] = df_pdf_view['date'].dt.strftime('%Y-%m-%d')
            html_full += df_pdf_view.to_html(index=False, classes="dataframe", border=df_primary_period' in locals() and not df_primary_period.empty:
    csv_data_primary = df_primary_period.to_csv(index=False).encode('utf-8')
    0)
            pdf_full_bytes = generate_pdf(html_full, fname='dashboard_report_primary.pdfst.sidebar.download_button("Download Primary Period Data as CSV", csv_data_primary, "primary_period_issues.csv", "text/csv", key="download_csv_primary")

    if st.sidebar.button("Prepare Visuals PDF (Primary Period)", key="prep_visuals_pdf_primary"):
        if not wk', wk_path=wk_path)
            if pdf_full_bytes: st.session_state.pdf_dashboard_primary_data = pdf_full_bytes; st.sidebar.success("Dashboard PDF (Primary) ready.")
            else:
                if 'pdf_dashboard_primary_data' in st.session_state: del st.session_state.pdf_dashboard_primary_data
    if 'pdf_dashboard_primary_data' in_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        elif 'figs_primary' not in locals() or not figs_primary or not any(figs_primary.values()): st.sidebar.warning("No visuals generated for the primary period.")
        else:
            html_content st.session_state and st.session_state.pdf_dashboard_primary_data:
        st.sidebar.download_button(label="Download Dashboard PDF (Primary) Now", data=st.session_state.pdf_dashboard_primary_data, file_name="dashboard_report_primary.pdf", mime="application/pdf", key="action_dl_dashboard_pdf_primary")
else: st.sidebar.info("No = "<html><head><meta charset='utf-8'><title>Visuals Report (Primary)</title><style>body{font-family:sans-serif;} h1,h2{text-align:center;} img primary period data to download.")

if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    df_comp1_exists = 'df_comp1' in locals() and not df_comp1.empty; df_comp2_exists = 'df_comp2' in locals() and{display:block;margin-left:auto;margin-right:auto;max-width:90%;height:auto;border:1px solid #ccc;padding:5px;margin-bottom:20px;} @media print {* {-webkit-print-color-adjust:exact !important; color-adjust:exact !important; print-color-adjust:exact !important;} body { background-color:white !important;}}</style></head><body>"
            html_content += f"<h1>Visuals Report (Primary: {primary_date_range[0]: not df_comp2.empty
    start_c1_str = comparison_date_range_1[0].strftime('%Y%m%d') if df_comp1_exists and comparison_date_range_1 else "P1"; end_c1_str = comparison_date_range_1[1].strftime%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d})</h1>"
            
            chart_titles_in_order = ["Branch", "Area Manager", "Report Type('%Y%m%d') if df_comp1_exists and comparison_date_range_1 else ""
    start_c2_str = comparison_date_range_2[0].strftime('%Y%m%d') if df_comp2_exists and comparison_date_range_2 else "P2"; end", "Category"]
            if 'CCTV Shifts' in figs_primary and figs_primary['CCTV Shifts'] is not None:
                chart_titles_in_order.append("CCTV Shifts") # Add CCTV_c2_str = comparison_date_range_2[1].strftime('%Y%m%d') if df_comp2_exists and comparison_date_range_2 else ""
    if df_comp1 shifts if chart exists
            chart_titles_in_order.append("Trend") # Trend is usually last

_exists: st.sidebar.download_button(f"CSV (Comp P1: {comparison_date_range_1[0]:%b%d}-{comparison_date_range_1[1]:%b%d})",            for title_key in chart_titles_in_order:
                if figs_primary.get(title_key):
                    fig_obj = figs_primary[title_key]
                    try:
                        img_bytes = fig df_comp1.to_csv(index=False).encode('utf-8'), f"comp_p1_{start_c1_str}-{end_c1_str}.csv", "text/csv", key_obj.to_image(format='png', engine='kaleido', scale=1.5) # scale can be adjusted
                        b64_img = base64.b64encode(img_bytes).="dl_csv_comp1")
    if df_comp2_exists: st.sidebar.download_button(f"CSV (Comp P2: {comparison_date_range_2[0]:%b%decode()
                        chart_title_display = title_key.replace('_', ' ').title()
                        if '(Primary)' in chart_title_display or '(Primary - Cctv Shifts)' in chart_title_display : # Use the chart's actual title if available
                            actual_chart_title = fig_obj.layout.title.textd}-{comparison_date_range_2[1]:%b%d})", df_comp2.to_csv(index=False).encode('utf-8'), f"comp_p2_{start_c2_str}-{end_c2_str}.csv", "text/csv", key="dl_csv_comp2")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB if fig_obj.layout.title and fig_obj.layout.title.text else chart_title_display
                        else:
                            actual_chart_title = chart_title_display
                        html_content += f"<h2>{_PATH} (Local SQLite)")
