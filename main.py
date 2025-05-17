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

def initialize_database_schema(cursor, connection):
    # st.write("DEBUG: Initializing/Verifying database schema...") 
    cursor.execute('''CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
        file_type TEXT, category TEXT, submission_date TEXT, file BLOB
    )''')
    connection.commit() 
    required_uploads_columns = {"submission_date": "TEXT", "category": "TEXT", "file_type": "TEXT", "uploader": "TEXT", "timestamp": "TEXT"}
    cursor.execute("PRAGMA table_info(uploads)")
    existing_uploads_cols = {col[1]: col[2] for col in cursor.fetchall()}
    for col_name, col_type in required_uploads_columns.items():
        if col_name not in existing_uploads_cols:
            try:
                cursor.execute(f"ALTER TABLE uploads ADD COLUMN {col_name} {col_type}")
                connection.commit(); st.toast(f"Added '{col_name}' to 'uploads'.", icon="🔧")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower(): raise 
    cursor.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id INTEGER, 
        code TEXT, issues TEXT, branch TEXT, area_manager TEXT, date TEXT, report_type TEXT, 
        FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE 
    )'''); connection.commit()
    cursor.execute('''CREATE TABLE IF NOT EXISTS cctv_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id INTEGER, 
        code TEXT, violation TEXT, shift TEXT, date_submitted TEXT, 
        branch_name TEXT, area_manager TEXT, report_type TEXT,
        FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE 
    )'''); connection.commit()

try:
    initialize_database_schema(c, conn)
except Exception as e_schema:
    st.error(f"CRITICAL SCHEMA ERROR: {e_schema}. Delete 'issues.db' & restart."); st.stop()

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
    'missing': ['performance'], 'visits': [], 
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
    "TW01": "Twesste",
    "B01": "Nuzhah - النزهة", "B02": "Alkaleej - الخليج", "B03": "Gurnatah - غرناطة", "B04": "Alnaseem Riyadh- النسيم الرياض",
    "B05": "Alrawabi - الروابي", "B06": "Aldaraiah - الدرعية", "B07": "Wadi Laban Riyadh - وادي لبن الرياض",
    "B08": "Alsweedi - السويدي", "B09": "Alaziziah - العزيزية", "B10": "Alshifa - الشفاء",
    "B11": "Alnargis - النرجس", "B12": "Twuaiq - طويق", "B14": "Alrabea - الربيع",
    "B16": "Albadeah - البديعة", "B17": "Alqairawan - القيروان", "B18": "Takhasussi Riyadh - التخصصي الرياض",
    "B19": "Alremal - الرمال", "B21": "Alkharj - الخرج", "B22": "Obhur Branch - فرع ابحر",
    "B23": "Al Sulimaniyah Al Hofuf - السلمانية الهفوف", "B24": "Alsafa Jeddah - الصفا جدة",
    "B25": "Al Rawdha Al Hofuf - الروضة الهفوف", "B26": "Al Hamadaniyyah  - الحمدانية",
    "B27": "Alsaadah branch - فرع السعادة", "B28": "Almarwah branch - فرع المروة",
    "B30": "Al Qadisiyyah branch - فرع القادسية", "B31": "Anas Ibn Malik - انس ابن مالك",
    "B32": "Alfayha branch - فرع الفيحاء", "B34": "Al Urubah Branch - فرع العروبة"
}
LOGO_PATH = "company_logo.png" 

def check_login():
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None
    if not st.session_state.authenticated:
        col1_lgn, col2_lgn = st.columns([2,6]);
        with col1_lgn:
            try: st.image(LOGO_PATH, width=120) 
            except Exception: pass 
        with col2_lgn: st.title("📊 Login - Dashboard")
        st.subheader("Please log in to continue")
        with st.form("login_form"):
            username = st.text_input("Full Name:", key="auth_username_login_widget").strip().lower(); password = st.text_input("Password:", type="password", key="auth_password_login_widget") 
            if st.form_submit_button("Login"):
                if username in db_admin and bcrypt.checkpw(password.encode(), db_admin[username]): st.session_state.authenticated = True; st.session_state.user_name = username; st.session_state.user_role = 'admin'; st.rerun()
                elif username in view_only and password: st.session_state.authenticated = True; st.session_state.user_name = username; st.session_state.user_role = 'view_only'; st.rerun()
                elif username in view_only and not password: st.error("Password required for view-only.")
                elif username or password: st.error("Invalid credentials.")
                else: st.info("Enter credentials.")
        return False
    return True
if not check_login(): st.stop()

col1_main_title, col2_main_title = st.columns([2, 6]);
with col1_main_title:
    try: st.image(LOGO_PATH, width=120)
    except Exception: pass
with col2_main_title: st.title("📊 Classic Dashboard for Performance")
user_name_display = st.session_state.get('user_name', "N/A").title(); user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main_widget"): st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'; current_user = st.session_state.get('user_name', 'Unknown User')

def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path or wk_path == "not found": st.error("wkhtmltopdf path not set."); return None
    try:
        import pdfkit; config = pdfkit.configuration(wkhtmltopdf=wk_path); options = {'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8",'load-error-handling': 'ignore','load-media-error-handling': 'ignore'}
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
                    c.execute('SELECT id FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                              (up.name, current_user, final_file_type, final_category, upload_submission_date_for_uploads_table.isoformat()))
                    existing_upload = c.fetchone()
                    if existing_upload: 
                        st.sidebar.warning(f"DUPLICATE: Upload batch (ID: {existing_upload[0]}) already exists for '{up.name}' with these exact settings. No action taken.")
                    else:
                        st.sidebar.info(f"Attempting to process new upload: {up.name}")
                        df_excel_full = pd.read_excel(io.BytesIO(excel_data_bytes))
                        df_excel_full.columns = [col.strip().lower() for col in df_excel_full.columns]
                        st.sidebar.text(f"DEBUG: Excel columns found: {str(list(df_excel_full.columns))}")

                        df_to_import = pd.DataFrame()
                        issues_prepared_count = 0
                        cctv_issues_to_insert_tuples = [] 
                        standard_issues_to_insert_tuples = []

                        if final_category == 'CCTV':
                            st.sidebar.info("--- CCTV Processing Started ---")
                            cctv_req_cols = ['code', 'choose the violation - اختر المخالفه', 'date submitted', 'branch', 'area manager']
                            missing_cctv_cols = [col for col in cctv_req_cols if col not in df_excel_full.columns]
                            if missing_cctv_cols: raise ValueError(f"CCTV Excel missing required columns: {', '.join(missing_cctv_cols)}")
                            
                            st.sidebar.info(f"All required CCTV columns found: {cctv_req_cols}")
                            if 'date submitted' in df_excel_full.columns: st.sidebar.info(f"Raw 'date submitted' head (first 5):\n{df_excel_full['date submitted'].head().to_string()}")
                            else: raise ValueError("'date submitted' column missing from CCTV Excel.")

                            df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full['date submitted'], errors='coerce', dayfirst=False) 
                            st.sidebar.info(f"Parsed 'parsed_date' head (NaT if parsing failed, first 5):\n{df_excel_full['parsed_date'].head().to_string()}")
                            st.sidebar.info(f"NaNs in parsed_date after to_datetime: {df_excel_full['parsed_date'].isnull().sum()}")
                            
                            original_len = len(df_excel_full); df_excel_full.dropna(subset=['parsed_date'], inplace=True)
                            rows_dropped_after_date_parse = original_len - len(df_excel_full)
                            if rows_dropped_after_date_parse > 0: st.sidebar.warning(f"{rows_dropped_after_date_parse} CCTV rows dropped (invalid 'date submitted').")
                            if df_excel_full.empty: raise ValueError("No valid CCTV data rows after date parsing.")
                            
                            st.sidebar.info(f"Number of rows after date parsing & dropna: {len(df_excel_full)}")
                            st.sidebar.info(f"Importing data for dates from: {imp_from_dt.strftime('%Y-%m-%d')} to {imp_to_dt.strftime('%Y-%m-%d')}")
                                
                            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()
                            st.sidebar.info(f"Number of rows in df_to_import (after date range filter): {len(df_to_import)}")
                            
                            if not df_to_import.empty:
                                st.sidebar.info("Preparing CCTV issues for DB insert...")
                                for index_row, row_data in df_to_import.iterrows():
                                    violation = str(row_data['choose the violation - اختر المخالفه'])
                                    shift = str(row_data.get('choose the shift - اختر الشفت', '')) 
                                    branch_code_excel = str(row_data['code']).strip().upper()
                                    excel_branch_name = str(row_data['branch']).strip() 
                                    branch_name_final = BRANCH_CODE_MAP.get(branch_code_excel, excel_branch_name)
                                    if branch_name_final == excel_branch_name and branch_code_excel not in BRANCH_CODE_MAP: st.sidebar.text(f"Info Row {index_row}: Code '{branch_code_excel}' not in BRANCH_CODE_MAP, using branch name '{excel_branch_name}' from Excel.")
                                    elif branch_name_final != excel_branch_name and branch_code_excel in BRANCH_CODE_MAP: st.sidebar.text(f"Info Row {index_row}: Code '{branch_code_excel}' mapped to '{branch_name_final}'. Excel had '{excel_branch_name}'.")
                                    cctv_issues_to_insert_tuples.append((branch_code_excel, violation, shift if shift else None, row_data['parsed_date'].strftime('%Y-%m-%d'), branch_name_final, str(row_data['area manager']), final_file_type))
                                if cctv_issues_to_insert_tuples: issues_prepared_count = len(cctv_issues_to_insert_tuples)
                            else: st.sidebar.info(f"No CCTV rows found within the selected import date range in '{up.name}'.")
                        
                        else: # Standard Processing
                            st.sidebar.info("--- Standard Processing Started ---")
                            required_cols = ['code', 'issues', 'branch', 'area manager', 'date']
                            missing_cols = [col for col in required_cols if col not in df_excel_full.columns]
                            if missing_cols: raise ValueError(f"Standard Excel missing: {', '.join(missing_cols)}.")
                            st.sidebar.info(f"Required Standard columns found: {required_cols}")
                            if 'date' in df_excel_full.columns: st.sidebar.info(f"Raw 'date' head:\n{df_excel_full['date'].head().to_string()}")
                            else: raise ValueError("'date' column not found in Standard Excel.")
                            df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full['date'], dayfirst=True, errors='coerce')
                            st.sidebar.info(f"Parsed 'parsed_date' head (NaT if failed):\n{df_excel_full['parsed_date'].head().to_string()}")
                            st.sidebar.info(f"NaNs in parsed_date after to_datetime: {df_excel_full['parsed_date'].isnull().sum()}")
                            original_len = len(df_excel_full); df_excel_full.dropna(subset=['parsed_date'], inplace=True)
                            if len(df_excel_full) < original_len: st.sidebar.warning(f"{original_len - len(df_excel_full)} rows dropped (invalid date).")
                            if df_excel_full.empty: raise ValueError("No valid data rows in Excel after date parsing.")
                            st.sidebar.info(f"Rows after NaT drop: {len(df_excel_full)}")
                            st.sidebar.info(f"Importing from: {imp_from_dt:%Y-%m-%d} to {imp_to_dt:%Y-%m-%d}")
                            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()
                            st.sidebar.info(f"Rows in df_to_import (after date range filter): {len(df_to_import)}")
                            if not df_to_import.empty:
                                st.sidebar.info("Preparing Standard issues for DB insert...")
                                for _, row_data in df_to_import.iterrows():
                                    standard_issues_to_insert_tuples.append((row_data['code'], row_data['issues'], str(row_data['branch']).strip(), row_data['area manager'], row_data['parsed_date'].strftime('%Y-%m-%d'), final_file_type))
                                if standard_issues_to_insert_tuples: issues_prepared_count = len(standard_issues_to_insert_tuples)
                            else: st.sidebar.info(f"No Standard rows found within the selected import date range in '{up.name}'.")

                        if issues_prepared_count > 0:
                            st.sidebar.info(f"DEBUG: {issues_prepared_count} issues prepared. Proceeding to insert into DB.")
                            c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                      (up.name, current_user, ts_now.isoformat(), final_file_type, final_category, upload_submission_date_for_uploads_table.isoformat(), sqlite3.Binary(excel_data_bytes)))
                            upload_id_for_op = c.lastrowid 
                            st.sidebar.info(f"DEBUG: Inserted into 'uploads' table, ID: {upload_id_for_op}")

                            if final_category == 'CCTV':
                                if cctv_issues_to_insert_tuples: 
                                    batch_data = [(upload_id_for_op,) + t for t in cctv_issues_to_insert_tuples] 
                                    c.executemany('''INSERT INTO cctv_issues (upload_id, code, violation, shift, date_submitted, branch_name, area_manager, report_type) 
                                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', batch_data)
                                    st.sidebar.info(f"DEBUG: Executed insert for {len(batch_data)} CCTV issues.")
                            else: 
                                if standard_issues_to_insert_tuples: 
                                    batch_data = [(upload_id_for_op,) + t for t in standard_issues_to_insert_tuples] 
                                    c.executemany('''INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) 
                                                     VALUES (?, ?, ?, ?, ?, ?, ?)''', batch_data)
                                    st.sidebar.info(f"DEBUG: Executed insert for {len(batch_data)} Standard issues.")
                            st.sidebar.success(f"Successfully imported {issues_prepared_count} issues from '{up.name}'. Rerunning app...")
                            st.rerun()
                        else: 
                             st.sidebar.info(f"No issues met criteria for import from '{up.name}'. No database changes made for this file for issues. 'Uploads' entry was not created as no issues were found to import.")
            except ValueError as ve: 
                 st.sidebar.error(f"DATA ERROR: {ve}. Upload process halted. Transaction (if started) rolled back.")
            except sqlite3.Error as e_sql: 
                st.sidebar.error(f"DB ERROR: {e_sql}. Transaction implicitly rolled back.")
            except Exception as e_general: 
                st.sidebar.error(f"UNEXPECTED ERROR processing '{up.name}': {e_general}. Transaction implicitly rolled back if DB ops started.")
    
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

try: 
    df_uploads_raw_main = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
except sqlite3.Error as e:
    st.error(f"Database error reading uploads list: {e}. The database file might be corrupted or schema is incorrect.")
    st.info("If this is the first run after schema changes, or if errors persist, try deleting 'issues.db' and restarting the app.")
    df_uploads_raw_main = pd.DataFrame() 

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

df_standard_issues = pd.DataFrame(); df_cctv_issues_raw = pd.DataFrame() 
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
    df_all_issues = pd.DataFrame() # Initialize to empty on error
    st.stop() # Stop further execution if we can't read issue details

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
    if 'date' in df_all_issues.columns: 
        df_all_issues['date'] = pd.to_datetime(df_all_issues['date'], errors='coerce')
        if df_all_issues['date'].isnull().all() and not df_all_issues.empty: # All dates are NaT
             st.warning("All date values in the combined dataset are invalid. Dashboard may not function correctly.")
             # Optionally allow proceeding with an empty date column or stop
    if df_all_issues.empty : # if still empty after concat or if date parsing resulted in empty
        st.warning("No issues data available after combining sources. Upload data or check filters."); st.stop()
else:
    st.warning("No issues data found in database (standard or CCTV). Upload data."); st.stop()


# --- Dashboard Filters ---
min_overall_date_calc = df_all_issues['date'].min().date() if pd.notna(df_all_issues['date'].min()) else date.today()
max_overall_date_calc = df_all_issues['date'].max().date() if pd.notna(df_all_issues['date'].max()) else date.today()
primary_date_range_val_calc = [min_overall_date_calc, max_overall_date_calc] if min_overall_date_calc <= max_overall_date_calc else [max_overall_date_calc, min_overall_date_calc]
primary_date_range = st.sidebar.date_input("Primary Date Range (Issue Dates):", value=primary_date_range_val_calc, min_value=min_overall_date_calc, max_value=max_overall_date_calc, key="primary_date_range_filter_widget_main")
if not primary_date_range or len(primary_date_range) != 2: primary_date_range = primary_date_range_val_calc
branch_opts_list = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist()); sel_branch = st.sidebar.multiselect("Branch:", branch_opts_list, default=['All'], key="branch_filter_widget_main")
cat_opts_list = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist()); sel_cat = st.sidebar.multiselect("Category (from Upload Batch):", cat_opts_list, default=['All'], key="category_filter_widget_main")
am_opts_list = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist()); sel_am = st.sidebar.multiselect("Area Manager:", am_opts_list, default=['All'], key="area_manager_filter_widget_main")
file_type_filter_opts_list = ['All'] + sorted(df_all_issues['report_type'].astype(str).unique().tolist()); sel_ft = st.sidebar.multiselect("File Type (from Upload Batch):", file_type_filter_opts_list, default=['All'], key="file_type_filter_widget_main")

# --- Period Comparison ---
st.sidebar.subheader("📊 Period Comparison")
enable_comparison_val = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox_widget_main")
comparison_date_range_1, comparison_date_range_2 = None, None 
if enable_comparison_val:
    st.sidebar.markdown("**Comparison Period 1 (Issue Dates):**")
    safe_default_p1_end = min_overall_date_calc + timedelta(days=6); safe_default_p1_end = min(safe_default_p1_end, max_overall_date_calc); safe_default_p1_end = max(safe_default_p1_end, min_overall_date_calc)
    comparison_date_range_1_val_input = st.sidebar.date_input("Start & End Date (Period 1):", value=[min_overall_date_calc, safe_default_p1_end], min_value=min_overall_date_calc, max_value=max_overall_date_calc, key="comparison_period1_filter_widget_main")
    if comparison_date_range_1_val_input and len(comparison_date_range_1_val_input) == 2:
        comparison_date_range_1 = comparison_date_range_1_val_input
        st.sidebar.markdown("**Comparison Period 2 (Issue Dates):**")
        default_p2_start = comparison_date_range_1[1] + timedelta(days=1); default_p2_start = min(default_p2_start, max_overall_date_calc); default_p2_start = max(default_p2_start, min_overall_date_calc)
        default_p2_end = default_p2_start + timedelta(days=6); default_p2_end = min(default_p2_end, max_overall_date_calc); default_p2_end = max(default_p2_end, default_p2_start)
        comparison_date_range_2_val_input = st.sidebar.date_input("Start & End Date (Period 2):", value=[default_p2_start, default_p2_end], min_value=min_overall_date_calc, max_value=max_overall_date_calc, key="comparison_period2_filter_widget_main")
        if comparison_date_range_2_val_input and len(comparison_date_range_2_val_input) == 2: comparison_date_range_2 = comparison_date_range_2_val_input
        else: comparison_date_range_2 = None 
    else: comparison_date_range_1 = None; comparison_date_range_2 = None 

# --- Apply Filters ---
def apply_general_filters(df_input, sel_upload_id_val, selected_branches, selected_categories, selected_managers, selected_file_types):
    df_filtered = df_input.copy()
    if sel_upload_id_val: df_filtered = df_filtered[df_filtered['upload_id_col'] == sel_upload_id_val]
    if 'All' not in selected_branches: df_filtered = df_filtered[df_filtered['branch'].isin(selected_branches)]
    if 'All' not in selected_categories: df_filtered = df_filtered[df_filtered['upload_category'].isin(selected_categories)] 
    if 'All' not in selected_managers: df_filtered = df_filtered[df_filtered['area_manager'].isin(selected_managers)]
    if 'All' not in selected_file_types: df_filtered = df_filtered[df_filtered['report_type'].isin(selected_file_types)]
    return df_filtered
df_temp_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)

df_primary_period = df_temp_filtered.copy() 
if primary_date_range and len(primary_date_range) == 2 and 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']):
    start_date_filter, end_date_filter = primary_date_range[0], primary_date_range[1]
    df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= start_date_filter) & (df_primary_period['date'].dt.date <= end_date_filter)]
else: 
    df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns if not df_temp_filtered.empty else df_all_issues.columns) # Ensure columns if df_temp_filtered is empty


st.subheader(f"Filtered Issues for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total issues found in primary period: {len(df_primary_period)}")

# --- Chart Functions ---
def create_bar_chart(df_source, group_col, title_suffix=""):
    # ... (same as before)
    title = f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col in df_source.columns and not df_source[group_col].isnull().all():
        data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count').sort_values('count', ascending=False)
        if not data.empty: return px.bar(data, x=group_col, y='count', title=title, template="plotly_white")
    return None
def create_pie_chart(df_source, group_col, title_suffix=""):
    # ... (same as before)
    title = f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col in df_source.columns and not df_source[group_col].isnull().all():
        data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count')
        if not data.empty: return px.pie(data, names=group_col, values='count', title=title, hole=0.3, template="plotly_white")
    return None

# --- Primary Period Display ---
if df_primary_period.empty:
    st.info("No data matches the current filter criteria for the primary period.")
else:
    figs_primary = {}
    # ... (Rest of primary period charts, detailed records, top issues display - ENSURE THIS IS COMPLETE from your working version)
    col1_charts, col2_charts = st.columns(2)
    with col1_charts:
        figs_primary['Branch'] = create_bar_chart(df_primary_period, 'branch', '(Primary)')
        if figs_primary['Branch']: st.plotly_chart(figs_primary['Branch'], use_container_width=True)
        figs_primary['Report Type'] = create_bar_chart(df_primary_period, 'report_type', '(Primary)')
        if figs_primary['Report Type']: st.plotly_chart(figs_primary['Report Type'], use_container_width=True)
    with col2_charts:
        figs_primary['Area Manager'] = create_pie_chart(df_primary_period, 'area_manager', '(Primary)')
        if figs_primary['Area Manager']: st.plotly_chart(figs_primary['Area Manager'], use_container_width=True)
        figs_primary['Category'] = create_bar_chart(df_primary_period, 'upload_category', '(Primary)') 
        if figs_primary['Category']: st.plotly_chart(figs_primary['Category'], use_container_width=True)
    
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']) and not df_primary_period['date'].isnull().all():
        trend_data_primary = df_primary_period.groupby(df_primary_period['date'].dt.date).size().reset_index(name='daily_issues')
        trend_data_primary['date'] = pd.to_datetime(trend_data_primary['date']); trend_data_primary = trend_data_primary.sort_values('date')
        if not trend_data_primary.empty:
            window_size = min(7, len(trend_data_primary)); window_size = max(2,window_size) 
            trend_data_primary[f'{window_size}-Day MA'] = trend_data_primary['daily_issues'].rolling(window=window_size, center=True, min_periods=1).mean().round(1)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=trend_data_primary['date'], y=trend_data_primary['daily_issues'], name='Daily Issues', marker_color='lightblue', hovertemplate="<b>%{x|%A, %b %d}</b><br>Issues: %{y}<extra></extra>"))
            fig_trend.add_trace(go.Scatter(x=trend_data_primary['date'], y=trend_data_primary[f'{window_size}-Day MA'], name=f'{window_size}-Day Moving Avg.', mode='lines+markers', line=dict(color='royalblue', width=2), marker=dict(size=5), hovertemplate="<b>%{x|%A, %b %d}</b><br>Moving Avg: %{y:.1f}<extra></extra>"))
            fig_trend.update_layout(title_text='Issues Trend (Primary Period - Based on Issue Dates)', xaxis_title='Date', yaxis_title='Number of Issues', template="plotly_white", hovermode="x unified", legend_title_text='Metric')
            figs_primary['Trend'] = fig_trend 
            st.plotly_chart(figs_primary['Trend'], use_container_width=True)
    
    if len(df_primary_period) < 50 or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.subheader("Detailed Records (Primary Period - Filtered)")
        df_display_primary = df_primary_period[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']].copy() 
        if 'date' in df_display_primary.columns and pd.api.types.is_datetime64_any_dtype(df_display_primary['date']): 
            df_display_primary['date'] = df_display_primary['date'].dt.strftime('%Y-%m-%d') 
        st.dataframe(df_display_primary, use_container_width=True)
    
    st.subheader("Top Issues (Primary Period - Filtered)")
    if 'issues' in df_primary_period.columns and not df_primary_period['issues'].isnull().all():
        top_issues_primary = df_primary_period['issues'].astype(str).value_counts().head(20).rename_axis('Issue Description').reset_index(name='Frequency')
        if not top_issues_primary.empty: st.dataframe(top_issues_primary, use_container_width=True)


# --- Comparison Period Display ---
if enable_comparison_val and comparison_date_range_1 and comparison_date_range_2:
    # ... (ALL YOUR COMPARISON DISPLAY LOGIC - ENSURE THIS IS COMPLETE from your working version)
    # This includes df_comp1, df_comp2 creation, metrics, branch comparison, and period-level trend
    st.markdown("---"); st.header("📊 Period Comparison Results (Based on Issue Dates)")
    df_comp1 = pd.DataFrame(columns=df_temp_filtered.columns); df_comp2 = pd.DataFrame(columns=df_temp_filtered.columns)
    start_c1_disp, end_c1_disp, start_c2_disp, end_c2_disp = "N/A", "N/A", "N/A", "N/A"
    if comparison_date_range_1 and len(comparison_date_range_1) == 2: # df_comp1 logic
        start_c1_dt_obj, end_c1_dt_obj = comparison_date_range_1[0], comparison_date_range_1[1]
        if 'date' in df_temp_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_temp_filtered['date']): 
            df_comp1 = df_temp_filtered[(df_temp_filtered['date'].dt.date >= start_c1_dt_obj) & (df_temp_filtered['date'].dt.date <= end_c1_dt_obj)].copy()
        start_c1_disp, end_c1_disp = start_c1_dt_obj.strftime('%Y-%m-%d'), end_c1_dt_obj.strftime('%Y-%m-%d')
    if comparison_date_range_2 and len(comparison_date_range_2) == 2: # df_comp2 logic
        start_c2_dt_obj, end_c2_dt_obj = comparison_date_range_2[0], comparison_date_range_2[1]
        if 'date' in df_temp_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_temp_filtered['date']): 
            df_comp2 = df_temp_filtered[(df_temp_filtered['date'].dt.date >= start_c2_dt_obj) & (df_temp_filtered['date'].dt.date <= end_c2_dt_obj)].copy()
        start_c2_disp, end_c2_disp = start_c2_dt_obj.strftime('%Y-%m-%d'), end_c2_dt_obj.strftime('%Y-%m-%d')
    # ... (rest of comparison display logic)

# --- Downloads ---
st.sidebar.subheader("Downloads")
# ... (ALL YOUR DOWNLOADS LOGIC - ENSURE THIS IS COMPLETE from your working version)
if 'df_primary_period' in locals() and not df_primary_period.empty:
    # ... (primary period downloads)
    pass
else: 
    st.sidebar.info("No primary period data to download.")

if enable_comparison_val and comparison_date_range_1 and comparison_date_range_2:
    # ... (comparison period CSV downloads)
    pass


st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)")
