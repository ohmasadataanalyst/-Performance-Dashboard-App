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
import re # For parsing complaint details

# Streamlit config MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- Branch Code to Standardized Name Mapping (RE-INTRODUCED) ---
BRANCH_SCHEMA = {
    "B01": "NURUH B01", "B02": "KHRUH B02", "B03": "GHRUH B03", "B04": "NSRUH B04",
    "B05": "RAWRUH B05", "B06": "DARUH B06", "B07": "LBRUH B07", "B08": "SWRUH B08",
    "B09": "AZRUH B09", "B10": "SHRUH B10", "B11": "NRRUH B11", "B12": "TWRUH B12",
    "B13": "AQRUH B13", "B14": "RBRUH B14", "B15": "NDRUH B15", "B16": "BDRUH B16",
    "B17": "QRRUH B17", "B18": "TKRUH B18", "B19": "MURUH B19", "B21": "KRRUH B21",
    "B22": "OBJED B22", "B23": "SLAHS B23", "B24": "SFJED B24", "B25": "RWAHS B25",
    "B26": "HAJED B26", "B27": "SARUH B27", "B28": "MAJED B28", "B29": "Event B29",
    "B30": "QADRUH B30", "B31": "ANRUH B31", "B32": "FAYJED B32", "B33": "HIRJED B33",
    "B34": "URURUH B34", "LB01": "Alaqeq Branch LB01", "LB02": "Alkhaleej Branch LB02",
    "QB01": "As Suwaidi Branch QB01", "QB02": "Al Nargis Branch QB02", "TW01": "Twesste B01 TW01"
}
BRANCH_SCHEMA_NORMALIZED = {str(k).strip().upper(): v for k, v in BRANCH_SCHEMA.items()}

# --- Database setup ---
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
    file_type TEXT, category TEXT,
    submission_date TEXT,
    file BLOB
)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER, code TEXT, issues TEXT, branch TEXT, area_manager TEXT,
    date TEXT,
    report_type TEXT,
    shift TEXT,
    FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE
)''')
conn.commit()

try:
    c.execute("PRAGMA table_info(uploads)")
    existing_columns_uploads = [column[1] for column in c.fetchall()]
    if 'submission_date' not in existing_columns_uploads:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        if 'db_schema_updated_flag_uploads' not in st.session_state:
            st.session_state.db_schema_updated_flag_uploads = True
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not in st.session_state :
        st.session_state.db_critical_error_msg = f"Failed to update 'uploads' table schema: {e}"
try:
    c.execute("PRAGMA table_info(issues)")
    existing_columns_issues = [column[1] for column in c.fetchall()]
    if 'shift' not in existing_columns_issues:
        c.execute("ALTER TABLE issues ADD COLUMN shift TEXT")
        conn.commit()
        if 'db_schema_updated_flag_issues' not in st.session_state:
            st.session_state.db_schema_updated_flag_issues = True
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not in st.session_state :
        st.session_state.db_critical_error_msg = f"Failed to update 'issues' table schema: {e}"

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

if 'db_critical_error_msg' in st.session_state:
    st.error(f"DB Startup Error: {st.session_state.db_critical_error_msg}"); del st.session_state.db_critical_error_msg
if 'db_schema_updated_flag_uploads' in st.session_state and st.session_state.db_schema_updated_flag_uploads:
    st.toast("DB 'uploads' table schema updated.", icon="ℹ️"); st.session_state.db_schema_updated_flag_uploads = False
if 'db_schema_updated_flag_issues' in st.session_state and st.session_state.db_schema_updated_flag_issues:
    st.toast("DB 'issues' table schema updated with 'shift' column.", icon="ℹ️"); st.session_state.db_schema_updated_flag_issues = False

LOGO_PATH = "company_logo.png"

def check_login(): # ... (unchanged)
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None
    if not st.session_state.authenticated:
        col1_lgn, col2_lgn = st.columns([1,5]);
        with col1_lgn:
            try: st.image(LOGO_PATH, width=100)
            except Exception: pass
        with col2_lgn: st.title("📊 Login - Performance Dashboard")
        st.subheader("Please log in to continue")
        with st.form("login_form"):
            username = st.text_input("Full Name:", key="auth_username_login").strip().lower()
            password = st.text_input("Password:", type="password", key="auth_password_login")
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

col1_main_title, col2_main_title = st.columns([1, 5]) # ... (unchanged)
with col1_main_title:
    try: st.image(LOGO_PATH, width=100)
    except FileNotFoundError: st.error(f"Logo image not found: {LOGO_PATH}")
    except Exception as e: st.error(f"Error loading logo: {e}")
with col2_main_title: st.title("📊 Classic Dashboard for Performance")

user_name_display = st.session_state.get('user_name', "N/A").title() # ... (unchanged)
user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main"):
    st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.session_state.get('user_name', 'Unknown User')

def generate_pdf(html, wk_path=None): # ... (unchanged)
    if not wk_path or wk_path == "not found":
        st.error("wkhtmltopdf path not set in sidebar. PDF generation failed.")
        return None
    try:
        import pdfkit
        config = pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {
            'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8",
            'load-error-handling': 'ignore', 'load-media-error-handling': 'ignore',
            'disable-smart-shrinking': None, 'zoom': '0.85'
        }
        pdf_bytes = pdfkit.from_string(html, False, configuration=config, options=options)
        return pdf_bytes
    except FileNotFoundError:
        st.error(f"wkhtmltopdf not found at path: {wk_path}. Please ensure it's installed and the path is correct.")
        return None
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None

st.sidebar.header("🔍 Filters & Options") # ... (admin upload section unchanged)

if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("Set parameters, select Excel, specify import date range, then upload.")
    selected_category = st.sidebar.selectbox("Category for upload", options=all_categories, key="admin_category_select")

    _current_admin_category = st.session_state.get("admin_category_select", all_categories[0] if all_categories else None)
    valid_file_types = category_file_types.get(_current_admin_category, [])

    selected_file_type = st.sidebar.selectbox(
        "File type for upload",
        options=valid_file_types,
        key="admin_file_type_select",
        disabled=(not valid_file_types),
        help="Options change based on category. Select a category first."
    )

    st.sidebar.markdown("**Filter Excel Data by Date Range for this Import:**")
    import_from_date_val = st.sidebar.date_input("Import Data From Date:", value=date.today() - timedelta(days=7), key="import_from_date_upload")
    import_to_date_val = st.sidebar.date_input("Import Data To Date:", value=date.today(), key="import_to_date_upload")
    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if upload_btn:
        final_category = st.session_state.admin_category_select
        final_file_type = st.session_state.admin_file_type_select
        imp_from_dt = st.session_state.import_from_date_upload
        imp_to_dt = st.session_state.import_to_date_upload
        requires_file_type = bool(category_file_types.get(final_category, []))

        if requires_file_type and not final_file_type:
            st.sidebar.error(f"A file type is required for category '{final_category}'. Please select one and click 'Upload Data' again.")
            st.stop()
        if not up:
            st.sidebar.error("Please select an Excel file to upload.")
            st.stop()
        if not imp_from_dt or not imp_to_dt:
            st.sidebar.error("Please select both 'Import Data From Date' and 'Import Data To Date'.")
            st.stop()
        if imp_from_dt > imp_to_dt:
            st.sidebar.error("'Import Data From Date' cannot be after 'Import Data To Date'.")
            st.stop()

        if not requires_file_type:
            final_file_type = None

        data = up.getvalue()
        ts = datetime.now().isoformat()
        upload_submission_date_str = imp_from_dt.isoformat()

        try:
            c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                      (up.name, current_user, final_file_type, final_category, upload_submission_date_str))
            if c.fetchone()[0] > 0:
                st.sidebar.warning(f"Upload batch for '{up.name}' (Category: {final_category}, File Type: {final_file_type or 'N/A'}, Import From: {upload_submission_date_str}) seems duplicate. Processing anyway.")

            df_excel_full = pd.read_excel(io.BytesIO(data))
            
            original_columns = list(df_excel_full.columns)
            normalized_columns = [str(col).strip().lower().replace('\n', ' ').replace('\r', '') for col in df_excel_full.columns]
            df_excel_full.columns = normalized_columns
            
            print(f"DEBUG: Normalized Excel Columns for file '{up.name}': {normalized_columns}")

            EXCEL_CODE_COL = 'code'
            STD_EXCEL_ISSUES_COL = 'issues'
            STD_EXCEL_BRANCH_COL = 'branch' 
            STD_EXCEL_AM_COL = 'area manager'
            STD_EXCEL_DATE_COL = 'date'
            CCTV_EXCEL_VIOLATION_COL = 'choose the violation - اختر المخالفه'
            CCTV_EXCEL_SHIFT_COL = 'choose the shift - اختر الشفت'
            CCTV_EXCEL_DATE_COL = 'date submitted'
            CCTV_EXCEL_BRANCH_COL = 'branch' 
            CCTV_EXCEL_AM_COL = 'area manager'
            COMP_PERF_EXCEL_BRANCH_NAME_COL = 'branch'
            COMP_PERF_EXCEL_TYPE_COL = 'نوع الشكوى'
            COMP_PERF_EXCEL_PRODUCT_COL = 'الشكوى على اي منتج؟'
            COMP_PERF_EXCEL_QUALITY_COL = 'فى حاله كانت الشكوى جوده برجاء تحديد نوع الشكوى'
            COMP_PERF_EXCEL_ORDER_ERROR_COL = 'فى حاله خطاء فى الطلب برجاء تحديد نوع الشكوى'
            COMP_PERF_EXCEL_DATE_COL = 'date'

            required_cols_for_upload = []
            date_column_in_excel = ''

            if final_category == 'CCTV':
                required_cols_for_upload = [EXCEL_CODE_COL, CCTV_EXCEL_VIOLATION_COL, CCTV_EXCEL_SHIFT_COL, CCTV_EXCEL_DATE_COL, CCTV_EXCEL_BRANCH_COL, CCTV_EXCEL_AM_COL]
                date_column_in_excel = CCTV_EXCEL_DATE_COL
            elif final_category == 'complaints':
                if final_file_type == 'performance':
                    required_cols_for_upload = [
                        COMP_PERF_EXCEL_BRANCH_NAME_COL, 
                        EXCEL_CODE_COL,                 
                        COMP_PERF_EXCEL_TYPE_COL,
                        COMP_PERF_EXCEL_PRODUCT_COL,
                        COMP_PERF_EXCEL_QUALITY_COL,
                        COMP_PERF_EXCEL_ORDER_ERROR_COL,
                        COMP_PERF_EXCEL_DATE_COL        
                    ]
                    date_column_in_excel = COMP_PERF_EXCEL_DATE_COL
                elif final_file_type == 'اغلاق الشكاوي':
                    st.sidebar.error(f"Schema for 'complaints / اغلاق الشكاوي' is not yet implemented. Aborted.")
                    st.stop()
                else:
                    st.sidebar.error(f"Internal error: Invalid file type '{final_file_type}' for 'complaints'. Aborted.")
                    st.stop()
            elif final_category == 'visits':
                required_cols_for_upload = [EXCEL_CODE_COL, STD_EXCEL_DATE_COL]
                date_column_in_excel = STD_EXCEL_DATE_COL
            else:
                required_cols_for_upload = [EXCEL_CODE_COL, STD_EXCEL_ISSUES_COL, STD_EXCEL_BRANCH_COL, STD_EXCEL_AM_COL, STD_EXCEL_DATE_COL]
                date_column_in_excel = STD_EXCEL_DATE_COL

            missing_cols_detected = [col for col in required_cols_for_upload if col not in df_excel_full.columns]
            if missing_cols_detected:
                st.sidebar.error(f"Excel for '{final_category}' / '{final_file_type or 'N/A'}' is missing columns: {', '.join(list(set(missing_cols_detected)))}. Aborted.")
                st.sidebar.info(f"Normalized columns found in Excel: {list(df_excel_full.columns)}")
                st.sidebar.info(f"Expected columns were: {required_cols_for_upload}")
                st.stop()

            if not date_column_in_excel:
                st.sidebar.error(f"Internal error: Date column not defined for '{final_category}' / '{final_file_type or 'N/A'}'. Aborted.")
                st.stop()

            if date_column_in_excel not in df_excel_full.columns:
                st.sidebar.error(f"The expected date column '{date_column_in_excel}' was not found in the Excel file after header normalization. Aborted.")
                st.sidebar.info(f"Normalized columns found in Excel: {list(df_excel_full.columns)}")
                st.stop()

            df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full[date_column_in_excel], errors='coerce')
            original_excel_rows = len(df_excel_full)
            df_excel_full.dropna(subset=['parsed_date'], inplace=True)

            if len(df_excel_full) < original_excel_rows:
                st.sidebar.warning(f"{original_excel_rows - len(df_excel_full)} Excel rows dropped due to invalid/missing dates in '{date_column_in_excel}'.")

            if df_excel_full.empty:
                st.sidebar.error(f"No valid data rows remain in Excel after checking dates in column '{date_column_in_excel}'. Aborted.")
                st.stop()

            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) &
                                         (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()

            if df_to_import.empty:
                st.sidebar.info(f"No rows found in '{up.name}' matching the import date range ({imp_from_dt:%Y-%m-%d} to {imp_to_dt:%Y-%m-%d}). No data imported.")
                st.stop()

            c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (up.name, current_user, ts, final_file_type, final_category, upload_submission_date_str, sqlite3.Binary(data)))
            upload_id = c.lastrowid
            unmapped_branch_codes = set()
            inserted_issue_count = 0

            for _, row in df_to_import.iterrows():
                issue_date_str = row['parsed_date'].strftime('%Y-%m-%d')
                code_val_from_excel = str(row.get(EXCEL_CODE_COL)) if pd.notna(row.get(EXCEL_CODE_COL)) else ""

                issue_val = "N/A"
                am_val = "N/A"
                shift_val = None
                actual_branch_name_in_excel_for_fallback = "Unknown Branch"

                if final_category == 'complaints' and final_file_type == 'performance':
                    actual_branch_name_in_excel_for_fallback = str(row.get(COMP_PERF_EXCEL_BRANCH_NAME_COL, "Unknown Branch (Complaints)"))
                    am_val = "N/A - Complaints"
                    details = []
                    complaint_type_val = row.get(COMP_PERF_EXCEL_TYPE_COL)
                    product_val = row.get(COMP_PERF_EXCEL_PRODUCT_COL)
                    quality_val = row.get(COMP_PERF_EXCEL_QUALITY_COL)
                    order_error_val = row.get(COMP_PERF_EXCEL_ORDER_ERROR_COL)
                    if pd.notna(complaint_type_val) and str(complaint_type_val).strip(): details.append(f"Type: {str(complaint_type_val).strip()}")
                    product_str = str(product_val).strip() if pd.notna(product_val) else ""
                    if product_str and product_str.lower() != "لا علاقة لها بالمنتج":
                        details.append(f"Product: {product_str}")
                    if pd.notna(quality_val) and str(quality_val).strip(): details.append(f"Quality Detail: {str(quality_val).strip()}")
                    if pd.notna(order_error_val) and str(order_error_val).strip(): details.append(f"Order Error: {str(order_error_val).strip()}")
                    issue_val = "; ".join(details) if details else "No specific complaint details provided"
                elif final_category == 'CCTV':
                    actual_branch_name_in_excel_for_fallback = str(row.get(CCTV_EXCEL_BRANCH_COL, "Unknown Branch (CCTV)"))
                    am_val = str(row.get(CCTV_EXCEL_AM_COL, "N/A"))
                    issue_val = str(row.get(CCTV_EXCEL_VIOLATION_COL, "N/A"))
                    shift_val = str(row.get(CCTV_EXCEL_SHIFT_COL)) if pd.notna(row.get(CCTV_EXCEL_SHIFT_COL)) else None
                elif final_category == 'visits':
                    actual_branch_name_in_excel_for_fallback = str(row.get(STD_EXCEL_BRANCH_COL, "Unknown Visit Branch"))
                    am_val = str(row.get(STD_EXCEL_AM_COL, "N/A - Visits"))
                    issue_val = str(row.get(STD_EXCEL_ISSUES_COL, "Visit Logged"))
                else:
                    actual_branch_name_in_excel_for_fallback = str(row.get(STD_EXCEL_BRANCH_COL, "Unknown Branch (Standard)"))
                    am_val = str(row.get(STD_EXCEL_AM_COL, "N/A"))
                    issue_val = str(row.get(STD_EXCEL_ISSUES_COL, "N/A"))

                normalized_code_for_lookup = code_val_from_excel.strip().upper()
                standardized_branch_name = BRANCH_SCHEMA_NORMALIZED.get(normalized_code_for_lookup, actual_branch_name_in_excel_for_fallback)
                if normalized_code_for_lookup not in BRANCH_SCHEMA_NORMALIZED and normalized_code_for_lookup:
                    unmapped_branch_codes.add(f"{code_val_from_excel} (using name: {actual_branch_name_in_excel_for_fallback})")

                c.execute('''INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type, shift)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (upload_id, code_val_from_excel, issue_val, standardized_branch_name, am_val, issue_date_str, final_file_type, shift_val))
                inserted_issue_count += 1

            conn.commit()
            st.sidebar.success(f"Successfully imported {inserted_issue_count} issues from '{up.name}'.")
            if unmapped_branch_codes:
                st.sidebar.warning(f"Unmapped branch codes encountered. Original Excel branch name was used for: {', '.join(sorted(list(unmapped_branch_codes)))}. Consider updating BRANCH_SCHEMA.")

        except sqlite3.Error as e_sql:
            conn.rollback()
            st.sidebar.error(f"Database error during import: {e_sql}. Transaction rolled back.")
        except KeyError as e_key:
            conn.rollback()
            st.sidebar.error(f"Column access error: Missing key {e_key} during data processing for '{final_category}/{final_file_type or 'N/A'}'. Transaction rolled back.")
        except Exception as e_general:
            conn.rollback()
            st.sidebar.error(f"An unexpected error occurred processing '{up.name}': {e_general}. Transaction rolled back.")
        finally:
            st.rerun()

    st.sidebar.subheader("Manage Submissions") # ... (rest of admin controls unchanged)
    # ... (delete, db backup logic)
    df_uploads_raw_for_delete = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
    df_uploads_raw_for_delete['display_submission_date_fmt'] = df_uploads_raw_for_delete['submission_date'].apply(lambda d: datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A")
    delete_opts_list = [(f"{row['id']} - {row['filename']} ({row['category']}/{row['file_type'] or 'N/A'}) Imp.From: {row['display_submission_date_fmt']}") for index, row in df_uploads_raw_for_delete.iterrows()]
    delete_opts = ['Select ID to Delete'] + delete_opts_list
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission Batch:", delete_opts, key="delete_submission_id_select")
    if del_choice_display != 'Select ID to Delete':
        del_id_val = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id_val}", key=f"confirm_del_btn_{del_id_val}", type="primary"):
            try:
                c.execute('DELETE FROM uploads WHERE id=?', (del_id_val,)); conn.commit()
                st.sidebar.success(f"Deleted submission batch {del_id_val}."); st.rerun()
            except sqlite3.Error as e: conn.rollback(); st.sidebar.error(f"Failed to delete: {e}")

    st.sidebar.subheader("Database Management")
    st.sidebar.markdown(
        """
        **To persist data changes (e.g., on Streamlit Cloud):**
        1. After uploads/deletions, click "Download Database Backup".
        2. Rename the downloaded file to `issues.db`.
        3. Replace `issues.db` in your local Git project folder.
        4. Commit and push `issues.db` to GitHub.
        """
    )
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as fp:
            db_file_bytes = fp.read()
        current_timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_db_filename = f"issues_backup_{current_timestamp_str}.db"
        st.sidebar.download_button(
            label="Download Database Backup", data=db_file_bytes, file_name=backup_db_filename,
            mime="application/vnd.sqlite3", key="download_db_now_button_direct",
            help=f"Downloads current '{DB_PATH}'. Rename to '{os.path.basename(DB_PATH)}' for Git commit."
        )
    else:
        st.sidebar.warning(f"'{DB_PATH}' not found. Cannot offer download.")


default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path (for PDF reports):", default_wk, help="Required for PDF generation.")

# --- Data Loading & Filtering for Dashboard ---
df_uploads_raw_main = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A"
df_uploads_raw_main['display_submission_date_fmt'] = df_uploads_raw_main['submission_date'].apply(format_display_date)
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [(f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) Imp.From: {r['display_submission_date_fmt']}") for i,r in df_uploads_raw_main.iterrows()]
sel_display = st.sidebar.selectbox("Select upload batch to analyze:", scope_opts, key="select_upload_scope_main")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

df_all_issues = pd.read_sql('SELECT i.*, u.category as upload_category, u.id as upload_id_col FROM issues i JOIN uploads u ON u.id = i.upload_id', conn, parse_dates=['date'])
if df_all_issues.empty:
    st.warning("No issues data in database. Please upload data using Admin Controls.")
    st.stop()

st.sidebar.subheader("Dashboard Filters")
min_overall_date = df_all_issues['date'].min().date() if pd.notna(df_all_issues['date'].min()) else date.today()
max_overall_date = df_all_issues['date'].max().date() if pd.notna(df_all_issues['date'].max()) else date.today()
primary_date_range_val = st.sidebar.date_input("Primary Date Range (Issue Dates):", value=[min_overall_date, max_overall_date] if min_overall_date <= max_overall_date else [max_overall_date, min_overall_date], min_value=min_overall_date, max_value=max_overall_date, key="primary_date_range_filter")
if not primary_date_range_val or len(primary_date_range_val) != 2:
    primary_date_range = [min_overall_date, max_overall_date] if min_overall_date <= max_overall_date else [max_overall_date, min_overall_date]
    st.sidebar.warning("Invalid primary date range selected, defaulting to full range.")
elif primary_date_range_val[0] > primary_date_range_val[1]:
    primary_date_range = [primary_date_range_val[1], primary_date_range_val[0]]
    st.sidebar.warning("Primary date range re-ordered (start was after end).")
else:
    primary_date_range = primary_date_range_val

branch_opts = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist()); sel_branch = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")
cat_opts = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist()); sel_cat = st.sidebar.multiselect("Category (from Upload Batch):", cat_opts, default=['All'], key="category_filter")
am_opts = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist()); sel_am = st.sidebar.multiselect("Area Manager:", am_opts, default=['All'], key="area_manager_filter")
file_type_filter_opts = ['All'] + sorted(df_all_issues['report_type'].astype(str).unique().tolist()); sel_ft = st.sidebar.multiselect("File Type (from Upload Batch):", file_type_filter_opts, default=['All'], key="file_type_filter")

st.sidebar.subheader("📊 Period Comparison") # ... (comparison setup unchanged)
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox")
comparison_date_range_1, comparison_date_range_2 = None, None
if enable_comparison:
    st.sidebar.markdown("**Comparison Period 1 (Issue Dates):**")
    safe_default_p1_end = min(min_overall_date + timedelta(days=6), max_overall_date); safe_default_p1_end = max(safe_default_p1_end, min_overall_date)
    comparison_date_range_1_val = st.sidebar.date_input("Start & End Date (Period 1):", value=[min_overall_date, safe_default_p1_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period1_filter")
    if comparison_date_range_1_val and len(comparison_date_range_1_val) == 2 and comparison_date_range_1_val[0] <= comparison_date_range_1_val[1]:
        comparison_date_range_1 = comparison_date_range_1_val
        st.sidebar.markdown("**Comparison Period 2 (Issue Dates):**")
        default_p2_start = min(comparison_date_range_1[1] + timedelta(days=1), max_overall_date); default_p2_start = max(default_p2_start, min_overall_date)
        default_p2_end = min(default_p2_start + timedelta(days=6), max_overall_date); default_p2_end = max(default_p2_end, default_p2_start)
        comparison_date_range_2_val = st.sidebar.date_input("Start & End Date (Period 2):", value=[default_p2_start, default_p2_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period2_filter")
        if comparison_date_range_2_val and len(comparison_date_range_2_val) == 2 and comparison_date_range_2_val[0] <= comparison_date_range_2_val[1]:
            comparison_date_range_2 = comparison_date_range_2_val
        else: st.sidebar.warning("Period 2: Invalid date range."); comparison_date_range_2 = None
    else: st.sidebar.warning("Period 1: Invalid date range."); comparison_date_range_1 = None; comparison_date_range_2 = None

def apply_general_filters(df_input, sel_upload_id_val, selected_branches, selected_categories, selected_managers, selected_file_types): # ... (unchanged)
    df_filtered = df_input.copy()
    if sel_upload_id_val: df_filtered = df_filtered[df_filtered['upload_id_col'] == sel_upload_id_val]
    if 'All' not in selected_branches: df_filtered = df_filtered[df_filtered['branch'].isin(selected_branches)]
    if 'All' not in selected_categories: df_filtered = df_filtered[df_filtered['upload_category'].isin(selected_categories)]
    if 'All' not in selected_managers: df_filtered = df_filtered[df_filtered['area_manager'].isin(selected_managers)]
    if 'All' not in selected_file_types: df_filtered = df_filtered[df_filtered['report_type'].isin(selected_file_types)]
    return df_filtered

df_temp_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)
df_primary_period = df_temp_filtered.copy()
if primary_date_range and len(primary_date_range) == 2:
    start_date_filt, end_date_filt = primary_date_range[0], primary_date_range[1]
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']):
        df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= start_date_filt) & (df_primary_period['date'].dt.date <= end_date_filt)]
else:
    df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)

st.subheader(f"Filtered Data for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total records found in primary period: {len(df_primary_period)}")

# --- Charting Functions (Generic) ---
COMPLAINTS_COLOR_SEQUENCE = px.colors.qualitative.Vivid # Define preferred color sequence

def create_bar_chart(df_source, group_col, title_suffix="", chart_title=None, color_sequence=None): # Added color_sequence
    final_title = chart_title if chart_title else f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col not in df_source.columns: return None
    df_valid_data = df_source.copy()
    df_valid_data.dropna(subset=[group_col], inplace=True)
    if pd.api.types.is_string_dtype(df_valid_data[group_col]):
        df_valid_data[group_col] = df_valid_data[group_col].str.strip()
        df_valid_data = df_valid_data[df_valid_data[group_col] != '']
    elif pd.api.types.is_numeric_dtype(df_valid_data[group_col]):
        pass 
    else: 
        df_valid_data[group_col] = df_valid_data[group_col].astype(str).str.strip()
        df_valid_data = df_valid_data[df_valid_data[group_col] != '']
    if not df_valid_data.empty:
        data = df_valid_data.groupby(group_col).size().reset_index(name='count').sort_values('count', ascending=False)
        if not data.empty: 
            return px.bar(data, x=group_col, y='count', title=final_title, template="plotly_white",
                          color_discrete_sequence=color_sequence if color_sequence else px.colors.qualitative.Plotly) # Apply color
    return None

def create_pie_chart(df_source, group_col, title_suffix="", chart_title=None, color_sequence=None): # Added color_sequence
    final_title = chart_title if chart_title else f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col not in df_source.columns: return None
    df_valid_data = df_source.copy()
    df_valid_data.dropna(subset=[group_col], inplace=True)
    if pd.api.types.is_string_dtype(df_valid_data[group_col]):
        df_valid_data[group_col] = df_valid_data[group_col].str.strip()
        df_valid_data = df_valid_data[df_valid_data[group_col] != '']
    elif pd.api.types.is_numeric_dtype(df_valid_data[group_col]):
        pass
    else:
        df_valid_data[group_col] = df_valid_data[group_col].astype(str).str.strip()
        df_valid_data = df_valid_data[df_valid_data[group_col] != '']
    if not df_valid_data.empty:
        data = df_valid_data.groupby(group_col).size().reset_index(name='count')
        if not data.empty: 
            return px.pie(data, names=group_col, values='count', title=final_title, hole=0.3, template="plotly_white",
                          color_discrete_sequence=color_sequence if color_sequence else px.colors.qualitative.Plotly) # Apply color
    return None

def parse_complaint_details(issue_string): # ... (unchanged)
    details = {'Type': None, 'Product': None, 'Quality Detail': None, 'Order Error': None}
    if not isinstance(issue_string, str):
        return pd.Series(details)
    type_match = re.search(r"Type:\s*(.*?)(?:;|$)", issue_string)
    if type_match: details['Type'] = type_match.group(1).strip()
    product_match = re.search(r"Product:\s*(.*?)(?:;|$)", issue_string)
    if product_match:
        product_val = product_match.group(1).strip()
        details['Product'] = product_val # Keep original, filter "لا علاقة لها بالمنتج" during display if needed
    quality_match = re.search(r"Quality Detail:\s*(.*?)(?:;|$)", issue_string)
    if quality_match: details['Quality Detail'] = quality_match.group(1).strip()
    order_error_match = re.search(r"Order Error:\s*(.*?)(?:;|$)", issue_string)
    if order_error_match: details['Order Error'] = order_error_match.group(1).strip()
    return pd.Series(details)

# --- DASHBOARD DISPLAY FUNCTIONS ---
def display_general_dashboard(df_data, figs_container): # ... (unchanged)
    st.subheader("General Performance Analysis")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        figs_container['Branch'] = create_bar_chart(df_data, 'branch', '(Primary)')
        if figs_container['Branch']: st.plotly_chart(figs_container['Branch'], use_container_width=True)
        df_report_type_viz = df_data.copy()
        if 'upload_category' in df_report_type_viz.columns and 'report_type' in df_report_type_viz.columns:
            condition = (df_report_type_viz['report_type'] == 'issues') & (df_report_type_viz['upload_category'] == 'CCTV')
            df_report_type_viz.loc[condition, 'report_type'] = 'CCTV issues'
        figs_container['Report Type'] = create_bar_chart(df_report_type_viz, 'report_type', '(Primary)')
        if figs_container['Report Type']: st.plotly_chart(figs_container['Report Type'], use_container_width=True)
    with chart_cols[1]:
        figs_container['Area Manager'] = create_pie_chart(df_data, 'area_manager', '(Primary)')
        if figs_container['Area Manager']: st.plotly_chart(figs_container['Area Manager'], use_container_width=True)
        figs_container['Category'] = create_bar_chart(df_data, 'upload_category', '(Primary)')
        if figs_container['Category']: st.plotly_chart(figs_container['Category'], use_container_width=True)
    if 'shift' in df_data.columns and df_data['shift'].notna().any():
        df_shift_data = df_data[df_data['shift'].notna() & (df_data['shift'].astype(str).str.strip() != '')]
        if not df_shift_data.empty:
            with st.container():
                figs_container['Shift_Values'] = create_bar_chart(df_shift_data, 'shift', '(Primary - CCTV Shift Times)')
                if figs_container['Shift_Values']:
                    st.plotly_chart(figs_container['Shift_Values'], use_container_width=True)
    if 'date' in df_data.columns and pd.api.types.is_datetime64_any_dtype(df_data['date']) and not df_data['date'].isnull().all():
        trend_data_primary = df_data.groupby(df_data['date'].dt.date).size().reset_index(name='daily_issues')
        trend_data_primary['date'] = pd.to_datetime(trend_data_primary['date']); trend_data_primary = trend_data_primary.sort_values('date')
        if not trend_data_primary.empty:
            window_size = min(7, len(trend_data_primary)); window_size = max(2,window_size)
            trend_data_primary[f'{window_size}-Day MA'] = trend_data_primary['daily_issues'].rolling(window=window_size, center=True, min_periods=1).mean().round(1)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=trend_data_primary['date'], y=trend_data_primary['daily_issues'], name='Daily Issues', marker_color='lightblue', hovertemplate="<b>%{x|%A, %b %d}</b><br>Issues: %{y}<extra></extra>"))
            fig_trend.add_trace(go.Scatter(x=trend_data_primary['date'], y=trend_data_primary[f'{window_size}-Day MA'], name=f'{window_size}-Day Moving Avg.', mode='lines+markers', line=dict(color='royalblue', width=2), marker=dict(size=5), hovertemplate="<b>%{x|%A, %b %d}</b><br>Moving Avg: %{y:.1f}<extra></extra>"))
            fig_trend.update_layout(title_text='Issues Trend (Primary Period - Based on Issue Dates)', xaxis_title='Date', yaxis_title='Number of Issues', template="plotly_white", hovermode="x unified", legend_title_text='Metric')
            figs_container['Trend'] = fig_trend
            st.plotly_chart(figs_container['Trend'], use_container_width=True)
    if len(df_data) < 50 or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.subheader("Detailed Records (Primary Period - Filtered)")
        display_columns = ['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']
        if 'shift' in df_data.columns and df_data['shift'].notna().any():
            display_columns.append('shift')
        df_display_primary = df_data[display_columns].copy()
        if 'upload_category' in df_display_primary.columns and 'report_type' in df_display_primary.columns:
            condition_table = (df_display_primary['report_type'] == 'issues') & (df_display_primary['upload_category'] == 'CCTV')
            df_display_primary.loc[condition_table, 'report_type'] = 'CCTV issues'
        if pd.api.types.is_datetime64_any_dtype(df_display_primary['date']): df_display_primary['date'] = df_display_primary['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_display_primary.reset_index(drop=True), use_container_width=True)
    st.subheader("Top Issues (Primary Period - Filtered)")
    if 'issues' in df_data.columns and df_data['issues'].notna().any():
        df_issues_for_top = df_data[['issues']].copy()
        df_issues_for_top.dropna(subset=['issues'], inplace=True)
        df_issues_for_top['issues_str'] = df_issues_for_top['issues'].astype(str).str.strip()
        df_issues_for_top = df_issues_for_top[df_issues_for_top['issues_str'] != '']
        if not df_issues_for_top.empty:
            top_issues_primary = df_issues_for_top['issues_str'].value_counts().head(20).rename_axis('Issue/Violation Description').reset_index(name='Frequency')
            if not top_issues_primary.empty:
                st.dataframe(top_issues_primary, use_container_width=True)
            else: st.info("No non-empty issue descriptions found for 'Top Issues' (Primary Period).")
        else: st.info("No non-empty issue descriptions found for 'Top Issues' (Primary Period).")

def display_complaints_performance_dashboard(df_complaints_raw):
    st.subheader("Complaints Performance Dashboard")
    
    parsed_details = df_complaints_raw['issues'].apply(parse_complaint_details)
    df_complaints = pd.concat([df_complaints_raw.drop(columns=['issues']), parsed_details], axis=1)

    df_complaints.rename(columns={
        'Type': 'Complaint Type',
        'Product': 'Product Complained About', # Keep original, filter "لا علاقة لها بالمنتج" during display if needed
        'Quality Detail': 'Quality Issue Detail',
        'Order Error': 'Order Error Detail'
    }, inplace=True)

    # Filter out "لا علاقة لها بالمنتج" for product chart only
    df_product_chart = df_complaints[df_complaints['Product Complained About'].notna() & (df_complaints['Product Complained About'].str.lower() != 'لا علاقة لها بالمنتج')]


    col1, col2 = st.columns(2)
    with col1:
        fig_type = create_bar_chart(df_complaints, 'Complaint Type', chart_title="Complaints by Type", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
        if fig_type: st.plotly_chart(fig_type, use_container_width=True)
        
        if not df_product_chart.empty:
            fig_product = create_bar_chart(df_product_chart, 'Product Complained About', chart_title="Complaints by Product (Specific Products)", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
            if fig_product: st.plotly_chart(fig_product, use_container_width=True)
        else:
            st.info("No complaints related to specific products to display.")


    with col2:
        df_quality_issues = df_complaints[df_complaints['Complaint Type'] == 'جوده']
        if not df_quality_issues.empty:
            fig_quality_detail = create_bar_chart(df_quality_issues, 'Quality Issue Detail', chart_title="Quality Issue Details (for 'جوده' complaints)", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
            if fig_quality_detail: st.plotly_chart(fig_quality_detail, use_container_width=True)
        else:
            st.caption("No 'جوده' (Quality) type complaints to detail.")

        df_order_errors = df_complaints[df_complaints['Complaint Type'] == 'خطاء فى الطلب']
        if not df_order_errors.empty:
            fig_order_error_detail = create_bar_chart(df_order_errors, 'Order Error Detail', chart_title="Order Error Details (for 'خطاء فى الطلب' complaints)", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
            if fig_order_error_detail: st.plotly_chart(fig_order_error_detail, use_container_width=True)
        else:
            st.caption("No 'خطاء فى الطلب' (Order Error) type complaints to detail.")
            
    st.subheader("Complaints by Branch")
    fig_branch_complaints = create_bar_chart(df_complaints, 'branch', chart_title="Total Complaints per Branch", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
    if fig_branch_complaints: st.plotly_chart(fig_branch_complaints, use_container_width=True)
    
    if 'date' in df_complaints.columns and pd.api.types.is_datetime64_any_dtype(df_complaints['date']) and not df_complaints['date'].isnull().all():
        trend_data_complaints = df_complaints.groupby(df_complaints['date'].dt.date).size().reset_index(name='daily_complaints')
        trend_data_complaints['date'] = pd.to_datetime(trend_data_complaints['date'])
        trend_data_complaints = trend_data_complaints.sort_values('date')
        if not trend_data_complaints.empty:
            fig_complaints_trend = px.line(trend_data_complaints, x='date', y='daily_complaints', title='Daily Complaints Trend', markers=True, color_discrete_sequence=COMPLAINTS_COLOR_SEQUENCE)
            fig_complaints_trend.update_layout(template="plotly_white")
            st.plotly_chart(fig_complaints_trend, use_container_width=True)

    st.subheader("Detailed Complaints Data (Primary Period - Parsed)")
    display_cols_complaints = ['date', 'branch', 'code', 'Complaint Type', 'Product Complained About', 'Quality Issue Detail', 'Order Error Detail']
    df_display_complaints = df_complaints[display_cols_complaints].copy()
    if pd.api.types.is_datetime64_any_dtype(df_display_complaints['date']):
        df_display_complaints['date'] = df_display_complaints['date'].dt.strftime('%Y-%m-%d')
    st.dataframe(df_display_complaints.reset_index(drop=True), use_container_width=True)

# --- Main Dashboard Logic ---
figs_primary = {} 

is_complaints_performance_data = False
if not df_primary_period.empty:
    is_purely_complaints_perf = (
        (df_primary_period['upload_category'] == 'complaints').all() and
        (df_primary_period['report_type'] == 'performance').all() and
        df_primary_period['upload_category'].nunique() == 1 and
        df_primary_period['report_type'].nunique() == 1
    )
    if is_purely_complaints_perf:
        is_complaints_performance_data = True
    else:
        # Check if filters are EXPLICITLY set to complaints/performance
        sel_cat_list = [sc.lower() for sc in sel_cat] if isinstance(sel_cat, list) else [sel_cat.lower()]
        sel_ft_list = [sf.lower() for sf in sel_ft] if isinstance(sel_ft, list) else [sel_ft.lower()]

        # If 'all' is present, we rely on the is_purely_complaints_perf check.
        # This part is for when the user *specifically* selects only 'complaints' and 'performance'.
        if 'all' not in sel_cat_list and 'complaints' in sel_cat_list and len(sel_cat_list) == 1 and \
           'all' not in sel_ft_list and 'performance' in sel_ft_list and len(sel_ft_list) == 1:
            # Check if the filtered data *actually* only contains complaints/performance
            # This is to handle cases where filters might be specific, but data is mixed due to other filter dimensions
            if is_purely_complaints_perf: # Re-check content if filters are specific
                 is_complaints_performance_data = True
            # else:
                # If filters are specific but data is mixed, consider general dashboard
                # or a message. For now, this means is_complaints_performance_data remains False
                # st.info("Filters set to Complaints/Performance, but current data selection is mixed. Showing general dashboard.")


if is_complaints_performance_data and not df_primary_period.empty:
    display_complaints_performance_dashboard(df_primary_period.copy())
elif not df_primary_period.empty:
    display_general_dashboard(df_primary_period.copy(), figs_primary)
else:
    st.info("No data matches the current filter criteria for the primary period.")


df_comp1, df_comp2 = pd.DataFrame(), pd.DataFrame() # ... (comparison logic - minor update for complaint comp colors)
if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.markdown("---"); st.header("📊 Period Comparison Results (Based on Issue Dates)")
    df_comp1_base = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)
    df_comp1 = df_comp1_base[(df_comp1_base['date'].dt.date >= comparison_date_range_1[0]) & (df_comp1_base['date'].dt.date <= comparison_date_range_1[1])].copy()
    df_comp2_base = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)
    df_comp2 = df_comp2_base[(df_comp2_base['date'].dt.date >= comparison_date_range_2[0]) & (df_comp2_base['date'].dt.date <= comparison_date_range_2[1])].copy()
    p1_label = f"P1 ({comparison_date_range_1[0]:%b %d} - {comparison_date_range_1[1]:%b %d})"
    p2_label = f"P2 ({comparison_date_range_2[0]:%b %d} - {comparison_date_range_2[1]:%b %d})"
    if df_comp1.empty and df_comp2.empty:
        st.info("No data for comparison in either period with current filters.")
    else:
        is_comp_complaints_data_p1 = False
        if not df_comp1.empty:
            is_comp_complaints_data_p1 = (df_comp1['upload_category'] == 'complaints').all() and \
                                        (df_comp1['report_type'] == 'performance').all() and \
                                        df_comp1['upload_category'].nunique() == 1 and \
                                        df_comp1['report_type'].nunique() == 1
        is_comp_complaints_data_p2 = False
        if not df_comp2.empty:
            is_comp_complaints_data_p2 = (df_comp2['upload_category'] == 'complaints').all() and \
                                        (df_comp2['report_type'] == 'performance').all() and \
                                        df_comp2['upload_category'].nunique() == 1 and \
                                        df_comp2['report_type'].nunique() == 1
        if is_comp_complaints_data_p1 and is_comp_complaints_data_p2 :
            st.subheader("Complaints Performance Comparison")
            parsed_details_p1 = df_comp1['issues'].apply(parse_complaint_details)
            df_comp1_parsed = pd.concat([df_comp1.drop(columns=['issues']), parsed_details_p1], axis=1)
            df_comp1_parsed.rename(columns={'Type': 'Complaint Type'}, inplace=True)
            df_comp1_parsed['period_label'] = p1_label
            parsed_details_p2 = df_comp2['issues'].apply(parse_complaint_details)
            df_comp2_parsed = pd.concat([df_comp2.drop(columns=['issues']), parsed_details_p2], axis=1)
            df_comp2_parsed.rename(columns={'Type': 'Complaint Type'}, inplace=True)
            df_comp2_parsed['period_label'] = p2_label
            df_combined_complaints_comp = pd.concat([df_comp1_parsed, df_comp2_parsed])
            if not df_combined_complaints_comp.empty:
                complaint_type_comp_data = df_combined_complaints_comp.groupby(['Complaint Type', 'period_label']).size().reset_index(name='count')
                if not complaint_type_comp_data.empty:
                    fig_complaint_type_comp = px.bar(complaint_type_comp_data, x='Complaint Type', y='count', color='period_label', barmode='group', title='Complaint Types Comparison by Period', color_discrete_sequence=COMPLAINTS_COLOR_SEQUENCE)
                    st.plotly_chart(fig_complaint_type_comp, use_container_width=True)
        else: # ... (rest of general comparison unchanged)
            st.subheader("Overall Issue Counts")
            col_summary1, col_summary2 = st.columns(2)
            col_summary1.metric(label=f"Total Issues ({p1_label})", value=f"{len(df_comp1)}")
            delta_val_comp = len(df_comp2) - len(df_comp1)
            col_summary2.metric(label=f"Total Issues ({p2_label})", value=f"{len(df_comp2)}", delta=f"{delta_val_comp:+}" if delta_val_comp !=0 else None)
            st.subheader("Top 5 Issues Comparison (Raw)")
            col_comp1_disp, col_comp2_disp = st.columns(2)
            with col_comp1_disp:
                if not df_comp1.empty and 'issues' in df_comp1.columns:
                    df_issues_comp1 = df_comp1[['issues']].copy(); df_issues_comp1.dropna(subset=['issues'], inplace=True)
                    df_issues_comp1['issues_str'] = df_issues_comp1['issues'].astype(str).str.strip()
                    df_issues_comp1 = df_issues_comp1[df_issues_comp1['issues_str'] != '']
                    if not df_issues_comp1.empty:
                        st.markdown(f"**{p1_label}**")
                        st.dataframe(df_issues_comp1['issues_str'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue/Violation', 'count':'Count'}), height=220, use_container_width=True)
                    else: st.info(f"No non-empty issues for {p1_label}")
                else: st.info(f"No data for {p1_label}")
            with col_comp2_disp:
                if not df_comp2.empty and 'issues' in df_comp2.columns:
                    df_issues_comp2 = df_comp2[['issues']].copy(); df_issues_comp2.dropna(subset=['issues'], inplace=True)
                    df_issues_comp2['issues_str'] = df_issues_comp2['issues'].astype(str).str.strip()
                    df_issues_comp2 = df_issues_comp2[df_issues_comp2['issues_str'] != '']
                    if not df_issues_comp2.empty:
                        st.markdown(f"**{p2_label}**")
                        st.dataframe(df_issues_comp2['issues_str'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue/Violation', 'count':'Count'}), height=220, use_container_width=True)
                    else: st.info(f"No non-empty issues for {p2_label}")
                else: st.info(f"No data for {p2_label}")
            df_comp1_labeled = df_comp1.copy(); df_comp2_labeled = df_comp2.copy()
            df_comp1_labeled['period_label'] = p1_label
            df_comp2_labeled['period_label'] = p2_label
            dfs_to_concat = []
            if not df_comp1_labeled.empty: dfs_to_concat.append(df_comp1_labeled)
            if not df_comp2_labeled.empty: dfs_to_concat.append(df_comp2_labeled)
            if dfs_to_concat:
                df_combined_branch = pd.concat(dfs_to_concat)
                if not df_combined_branch.empty:
                    df_valid_branch_comp = df_combined_branch.copy(); df_valid_branch_comp.dropna(subset=['branch'], inplace=True)
                    df_valid_branch_comp['branch'] = df_valid_branch_comp['branch'].astype(str).str.strip()
                    df_valid_branch_comp = df_valid_branch_comp[df_valid_branch_comp['branch'] != '']
                    if not df_valid_branch_comp.empty:
                        branch_comp_data = df_valid_branch_comp.groupby(['branch', 'period_label']).size().reset_index(name='count')
                        if not branch_comp_data.empty:
                            fig_branch_comp = px.bar(branch_comp_data, x='branch', y='count', color='period_label', barmode='group', title='Issues by Branch (Comparison)')
                            st.plotly_chart(fig_branch_comp, use_container_width=True)
            st.markdown("#### Period-Level Trend (Average Daily Issues)")
            period_summary_data = []
            if not df_comp1.empty:
                avg_issues_p1 = df_comp1.groupby(df_comp1['date'].dt.date).size().mean()
                period_summary_data.append({'Period': p1_label, 'StartDate': pd.to_datetime(comparison_date_range_1[0]), 'AverageDailyIssues': round(avg_issues_p1, 2)})
            if not df_comp2.empty:
                avg_issues_p2 = df_comp2.groupby(df_comp2['date'].dt.date).size().mean()
                period_summary_data.append({'Period': p2_label, 'StartDate': pd.to_datetime(comparison_date_range_2[0]), 'AverageDailyIssues': round(avg_issues_p2, 2)})
            if len(period_summary_data) >= 1:
                df_period_trend = pd.DataFrame(period_summary_data).sort_values('StartDate')
                chart_title_trend = 'Avg Daily Issues by Period' if len(df_period_trend) == 1 else 'Trend of Avg Daily Issues Across Periods'
                trend_chart_type = px.bar if len(df_period_trend) == 1 else px.line
                fig_period_level_trend = trend_chart_type(df_period_trend, x='Period', y='AverageDailyIssues', text='AverageDailyIssues', title=chart_title_trend, markers=(len(df_period_trend) > 1))
                fig_period_level_trend.update_traces(texttemplate='%{text:.2f}', textposition='outside' if len(df_period_trend) == 1 else 'top center')
                fig_period_level_trend.update_layout(xaxis_title="Comparison Period", yaxis_title="Avg. Daily Issues", template="plotly_white")
                st.plotly_chart(fig_period_level_trend, use_container_width=True)
            else: st.info("Not enough data for period-level trend comparison.")
else:
    if enable_comparison:
        st.warning("Comparison periods not properly set. Please check the date ranges.")

# --- Downloads Section ---
st.sidebar.subheader("Downloads") # ... (unchanged from previous, includes adaptations for complaints data in Excel/PDF table)
# ... (rest of downloads logic)
if 'df_primary_period' in locals() and not df_primary_period.empty:
    st.sidebar.markdown("**Primary Period Data:**")
    try:
        csv_data_primary = df_primary_period.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("Download Primary (CSV)", csv_data_primary, f"primary_issues_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.csv", "text/csv", key="download_csv_primary")
    except Exception as e: st.sidebar.error(f"Primary CSV Error: {e}")
    try:
        output_excel = io.BytesIO()
        if is_complaints_performance_data: # Check if we are in complaints view
            parsed_details_dl = df_primary_period['issues'].apply(parse_complaint_details)
            df_primary_excel = pd.concat([df_primary_period.reset_index(drop=True).drop(columns=['issues'], errors='ignore'), parsed_details_dl.reset_index(drop=True)], axis=1)
            df_primary_excel.rename(columns={
                'Type': 'Complaint Type', 'Product': 'Product Complained About',
                'Quality Detail': 'Quality Issue Detail', 'Order Error': 'Order Error Detail'
            }, inplace=True)
        else:
            df_primary_excel = df_primary_period.copy()

        with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
            df_primary_excel.to_excel(writer, index=False, sheet_name='PrimaryData')
        excel_data = output_excel.getvalue()
        st.sidebar.download_button(label="Download Primary (Excel)", data=excel_data,
            file_name=f"primary_issues_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_primary_xlsx")
    except Exception as e: st.sidebar.error(f"Primary Excel Error: {e}")

    if not is_complaints_performance_data:
        if st.sidebar.button("Prepare Visuals PDF (Primary)", key="prep_visuals_pdf_primary"):
            if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set for PDF generation.")
            elif not figs_primary or not any(figs_primary.values()): st.sidebar.warning("No visuals generated for the primary period (general dashboard).")
            else:
                with st.spinner("Generating Visuals PDF for Primary Period..."):
                    html_content = f"<html><head><meta charset='utf-8'><title>Visuals Report (Primary)</title><style>body{{font-family: Arial, sans-serif; margin: 20px;}} h1,h2{{text-align:center; color: #333;}} img{{display:block;margin-left:auto;margin-right:auto;max-width:650px;height:auto;border:1px solid #ccc;padding:5px;margin-bottom:25px;}} @media print {{* {{-webkit-print-color-adjust:exact !important; color-adjust:exact !important; print-color-adjust:exact !important;}} body {{ background-color:white !important;}} }}</style></head><body>"
                    html_content += f"<h1>Visuals Report</h1><h2>Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}</h2>"
                    chart_titles_in_order = ["Branch", "Area Manager", "Report Type", "Category", "Shift_Values", "Trend"]
                    for title_key in chart_titles_in_order:
                        if figs_primary.get(title_key) and figs_primary[title_key] is not None:
                            fig_obj = figs_primary[title_key]
                            try:
                                img_bytes = fig_obj.to_image(format='png', engine='kaleido', scale=1.2, width=700, height=450)
                                b64_img = base64.b64encode(img_bytes).decode()
                                actual_chart_title = fig_obj.layout.title.text if hasattr(fig_obj, 'layout') and fig_obj.layout.title and hasattr(fig_obj.layout.title, 'text') else title_key.replace("_", " ")
                                html_content += f"<h2>{actual_chart_title}</h2><img src='data:image/png;base64,{b64_img}' alt='{actual_chart_title}'/>"
                            except Exception as e_img: st.sidebar.error(f"Error generating image for '{title_key}': {e_img}")
                    html_content += "</body></html>"
                    pdf_bytes_visuals = generate_pdf(html_content, wk_path=wk_path) 
                    if pdf_bytes_visuals:
                        st.session_state.pdf_visuals_primary_data = pdf_bytes_visuals
                        st.sidebar.success("Visuals PDF (Primary) ready for download.")
                    else: 
                        if 'pdf_visuals_primary_data' in st.session_state: del st.session_state.pdf_visuals_primary_data
        
        if 'pdf_visuals_primary_data' in st.session_state and st.session_state.pdf_visuals_primary_data:
            st.sidebar.download_button(label="Download Visuals PDF (Primary)", data=st.session_state.pdf_visuals_primary_data, 
                                    file_name=f"visuals_report_primary_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.pdf", 
                                    mime="application/pdf", key="action_dl_visuals_pdf_primary")

    if st.sidebar.button("Prepare Data Table PDF (Primary)", key="prep_dashboard_pdf_primary"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set for PDF generation.")
        else:
            with st.spinner("Generating Data Table PDF for Primary Period..."):
                df_pdf_view_final = pd.DataFrame()
                if is_complaints_performance_data:
                    parsed_details_pdf = df_primary_period['issues'].apply(parse_complaint_details)
                    df_pdf_view_final = pd.concat([df_primary_period.reset_index(drop=True).drop(columns=['issues'], errors='ignore'), parsed_details_pdf.reset_index(drop=True)], axis=1)
                    df_pdf_view_final.rename(columns={
                        'Type': 'Complaint Type', 'Product': 'Product Complained About',
                        'Quality Detail': 'Quality Issue Detail', 'Order Error': 'Order Error Detail'
                    }, inplace=True)
                    pdf_table_cols = ['date', 'branch', 'code', 'Complaint Type', 'Product Complained About', 'Quality Issue Detail', 'Order Error Detail']
                    # Ensure only existing columns are selected
                    pdf_table_cols_exist = [col for col in pdf_table_cols if col in df_pdf_view_final.columns]
                    df_pdf_view_final = df_pdf_view_final[pdf_table_cols_exist]

                else:
                    pdf_table_cols = ['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']
                    if 'shift' in df_primary_period.columns and df_primary_period['shift'].notna().any():
                        pdf_table_cols.append('shift')
                    df_pdf_view_final = df_primary_period[pdf_table_cols].copy()
                    if 'upload_category' in df_pdf_view_final.columns and 'report_type' in df_pdf_view_final.columns:
                        condition_pdf_table = (df_pdf_view_final['report_type'] == 'issues') & (df_pdf_view_final['upload_category'] == 'CCTV')
                        df_pdf_view_final.loc[condition_pdf_table, 'report_type'] = 'CCTV issues'
                
                if 'date' in df_pdf_view_final.columns and pd.api.types.is_datetime64_any_dtype(df_pdf_view_final['date']): 
                    df_pdf_view_final['date'] = df_pdf_view_final['date'].dt.strftime('%Y-%m-%d')

                html_full = f"<head><meta charset='utf-8'><title>Data Table Report</title><style>body{{font-family:Arial, sans-serif; margin: 20px;}} h1{{text-align:center; color:#333;}} table{{border-collapse: collapse; width: 100%; margin-top: 15px; font-size: 0.9em;}} th,td{{border:1px solid #ddd;padding:8px;text-align:left;}} th{{background-color:#f2f2f2;}} .dataframe tbody tr:nth-of-type(even) {{background-color: #f9f9f9;}} @media print {{* {{-webkit-print-color-adjust:exact !important; color-adjust:exact !important; print-color-adjust:exact !important;}} body {{ background-color:white !important;}} }}</style></head><body>"
                html_full += f"<h1>Data Table Report</h1><h2>Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}</h2>"
                html_full += f"<p><strong>Total Records:</strong> {len(df_pdf_view_final)}</p>"
                html_full += df_pdf_view_final.to_html(index=False, classes="dataframe", border=1) 
                html_full += "</body></html>"

                pdf_full_bytes = generate_pdf(html_full, wk_path=wk_path) 
                if pdf_full_bytes: 
                    st.session_state.pdf_dashboard_primary_data = pdf_full_bytes
                    st.sidebar.success("Data Table PDF (Primary) ready.")
                else:
                    if 'pdf_dashboard_primary_data' in st.session_state: del st.session_state.pdf_dashboard_primary_data
    
    if 'pdf_dashboard_primary_data' in st.session_state and st.session_state.pdf_dashboard_primary_data:
        st.sidebar.download_button(label="Download Data Table PDF (Primary)", data=st.session_state.pdf_dashboard_primary_data, 
                                   file_name=f"data_table_report_primary_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.pdf", 
                                   mime="application/pdf", key="action_dl_dashboard_pdf_primary")
else: 
    st.sidebar.info("No primary period data to download.")

if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.sidebar.markdown("**Comparison Period Data (CSV):**")
    df_comp1_exists = 'df_comp1' in locals() and not df_comp1.empty
    df_comp2_exists = 'df_comp2' in locals() and not df_comp2.empty
    if df_comp1_exists:
        try:
            csv_c1 = df_comp1.to_csv(index=False).encode('utf-8')
            st.sidebar.download_button(f"Download P1 Data ({comparison_date_range_1[0]:%b %d}-{comparison_date_range_1[1]:%b %d})", 
                                   csv_c1, f"comp_p1_{comparison_date_range_1[0]:%Y%m%d}-{comparison_date_range_1[1]:%Y%m%d}.csv", 
                                   "text/csv", key="dl_csv_comp1")
        except Exception as e: st.sidebar.error(f"P1 CSV Error: {e}")
    else: st.sidebar.caption(f"No data for P1 ({comparison_date_range_1[0]:%b %d}-{comparison_date_range_1[1]:%b %d})")
    if df_comp2_exists:
        try:
            csv_c2 = df_comp2.to_csv(index=False).encode('utf-8')
            st.sidebar.download_button(f"Download P2 Data ({comparison_date_range_2[0]:%b %d}-{comparison_date_range_2[1]:%b %d})", 
                                   csv_c2, f"comp_p2_{comparison_date_range_2[0]:%Y%m%d}-{comparison_date_range_2[1]:%Y%m%d}.csv", 
                                   "text/csv", key="dl_csv_comp2")
        except Exception as e: st.sidebar.error(f"P2 CSV Error: {e}")
    else: st.sidebar.caption(f"No data for P2 ({comparison_date_range_2[0]:%b %d}-{comparison_date_range_2[1]:%b %d})")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)")
