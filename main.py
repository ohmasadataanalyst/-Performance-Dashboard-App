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

# --- Branch Code to Standardized Name Mapping ---
BRANCH_SCHEMA = {
    "B01": "NURUH B01", "B02": "KHRUH B02", "B03": "GHRUH B03", "B04": "NSRUH B04",
    "B05": "RAWRUH B05", "B06": "DARUH B06", "B07": "LBRUH B07", "B08": "SWRUH B08",
    "B09": "AZRUH B09", "B10": "SHRUH B10", "B11": "NRRUH B11", "B12": "TWRUH B12",
    "B13": "AQRUH B13", "B14": "RBRUH B14", "B15": "NDRUH B15", "B16": "BDRUH B16",
    "B17": "QRRUH B17", "B18": "TKRUH B18", "B19": "MURUH B19", "B21": "KRRUH B21",
    "B22": "OBJED B22", "B23": "SLAHS B23", "B24": "SFJED B24", "B25": "RWAHS B25",
    "B26": "HAJED B26", "B27": "SARUH B27", "B28": "MAJED B28", "B29": "Event B29",
    "B30": "QADRUH B30", "B31": "ANRUH B31", "B32": "FAYJED B32", "B33": "HIRJED B33",
    "B34": "URURUH B34", "B35": "IRRUH B35",
    "LB01": "Alaqeq Branch LB01", "LB02": "Alkhaleej Branch LB02",
    "QB01": "As Suwaidi Branch QB01", "QB02": "Al Nargis Branch QB02", "TW01": "Twesste B01 TW01"
}
BRANCH_SCHEMA_NORMALIZED = {str(k).strip().upper(): v for k, v in BRANCH_SCHEMA.items()}

# --- Project Frequencies for 'Missing' Category ---
PROJECT_FREQUENCIES = {
    "Check all expiration date": {"type": "weekly", "weekday": 0},
    "Cheese powder SOP (in opening)": {"type": "daily"}, "Clean drive thru branches": {"type": "daily"},
    "Clean ice maker": {"type": "daily"}, "clean shawarma cutter machine  1": {"type": "daily"},
    "clean shawarma cutter machine  2": {"type": "daily"}, "Cleaning AC filters": {"type": "weekly", "weekday": 0},
    "Cleaning Toilet -- 2-5 am": {"type": "daily"}, "Deeply cleaning": {"type": "weekly", "weekday": 0},
    "Defrost bread to next day": {"type": "daily"}, "Government papers/الأوراق الحكومية": {"type": "weekly", "weekday": 0},
    "Open The Signboard": {"type": "daily"}, "Preparation A": {"type": "daily"},
    "Quality of  items 12 - 6": {"type": "daily"}, "Shawarma Classic - Closing Checklist": {"type": "daily"},
    "Shawarma Classic - Handover Shift": {"type": "daily"}, "Shawarma Classic - Opening Checklist": {"type": "daily"},
    "Shawarma machine cleaning ELECTRIC": {"type": "daily"}, "SOP of disc": {"type": "weekly", "weekday": 0},
    "Staff Schedule": {"type": "daily"}, "store arranging": {"type": "daily"},
    "temperature of heaters 1": {"type": "daily"}, "Temperature of heaters 2": {"type": "daily"},
    "Weekly maintenance": {"type": "weekly", "weekday": 0},
    "Shawarma Classic - Opening Checklist- IRRUH NEW": {"type": "daily"},
}
ALL_DEFINED_PROJECT_NAMES = list(PROJECT_FREQUENCIES.keys())


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
    "omarsalah":b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy",
    "ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEn.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG",
    "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe",
    "mohamedhattab":b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe"
}
view_only = ["mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"]
category_file_types = {
    'operation-training': ['opening', 'closing', 'handover', 'store arranging', 'tempreature of heaters', 'defrost', 'clean AC'],
    'CCTV': ['issues', 'submission time'],
    'complaints': ['performance', 'اغلاق الشكاوي'],
    'missing': ['performance'], # MODIFIED
    'visits': [],
    'meal training': ['performance', 'missing types']
}
all_categories = list(category_file_types.keys())
MULTI_VALUE_COMPLAINT_COLS = ['Complaint Type', 'Quality Issue Detail', 'Order Error Detail']


if 'db_critical_error_msg' in st.session_state:
    st.error(f"DB Startup Error: {st.session_state.db_critical_error_msg}"); del st.session_state.db_critical_error_msg
if 'db_schema_updated_flag_uploads' in st.session_state and st.session_state.db_schema_updated_flag_uploads:
    st.toast("DB 'uploads' table schema updated.", icon="ℹ️"); st.session_state.db_schema_updated_flag_uploads = False
if 'db_schema_updated_flag_issues' in st.session_state and st.session_state.db_schema_updated_flag_issues:
    st.toast("DB 'issues' table schema updated with 'shift' column.", icon="ℹ️"); st.session_state.db_schema_updated_flag_issues = False

LOGO_PATH = "company_logo.png"

def check_login():
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
            username_input = st.text_input("Full Name:", key="auth_username_login").strip()
            password = st.text_input("Password:", type="password", key="auth_password_login")
            submitted = st.form_submit_button("Login")
            if submitted:
                username_lower = username_input.lower()
                admin_hashed_pw = db_admin.get(username_lower)
                if not admin_hashed_pw:
                    admin_hashed_pw = db_admin.get(username_lower.replace(" ", ""))

                if admin_hashed_pw and bcrypt.checkpw(password.encode('utf-8'), admin_hashed_pw):
                    st.session_state.authenticated = True; st.session_state.user_name = username_input; st.session_state.user_role = 'admin'; st.rerun()
                elif username_lower in view_only and password:
                    st.session_state.authenticated = True; st.session_state.user_name = username_input; st.session_state.user_role = 'view_only'; st.rerun()
                elif username_lower in view_only and not password: st.error("Password cannot be empty for view-only users.")
                elif username_input or password: st.error("Invalid username or password.")
                else: st.info("Please enter your credentials.")
        return False
    return True

if not check_login(): st.stop()

col1_main_title, col2_main_title = st.columns([1, 5])
with col1_main_title:
    try: st.image(LOGO_PATH, width=100)
    except FileNotFoundError: st.error(f"Logo image not found: {LOGO_PATH}")
    except Exception as e: st.error(f"Error loading logo: {e}")
with col2_main_title: st.title("📊 Classic Dashboard for Performance")

user_name_display = st.session_state.get('user_name', "N/A").title()
user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main"):
    st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.session_state.get('user_name', 'Unknown User')

def generate_pdf(html, wk_path=None):
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

st.sidebar.header("🔍 Filters & Options")

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
        st.sidebar.info(f"--- Upload: Cat='{st.session_state.get('admin_category_select')}', FileType='{st.session_state.get('admin_file_type_select')}' ---") # Keep this debug

        final_category = st.session_state.admin_category_select
        final_file_type = st.session_state.admin_file_type_select
        imp_from_dt = st.session_state.import_from_date_upload
        imp_to_dt = st.session_state.import_to_date_upload
        requires_file_type = bool(category_file_types.get(final_category, []))

        if requires_file_type and not final_file_type:
            st.sidebar.error(f"A file type is required for category '{final_category}'. Please select one and click 'Upload Data' again.")
            st.stop()
        if not up: st.sidebar.error("Please select an Excel file to upload."); st.stop()
        if not imp_from_dt or not imp_to_dt: st.sidebar.error("Please select both 'Import Data From Date' and 'Import Data To Date'."); st.stop()
        if imp_from_dt > imp_to_dt: st.sidebar.error("'Import Data From Date' cannot be after 'Import Data To Date'."); st.stop()
        if not requires_file_type: final_file_type = None

        data = up.getvalue()
        ts = datetime.now().isoformat()
        upload_submission_date_str = imp_from_dt.isoformat()

        try:
            c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                      (up.name, current_user, final_file_type, final_category, upload_submission_date_str))
            if c.fetchone()[0] > 0:
                st.sidebar.warning(f"Upload batch for '{up.name}' (Cat: {final_category}, Type: {final_file_type or 'N/A'}, From: {upload_submission_date_str}) seems duplicate. Processing.")

            df_excel_full = pd.read_excel(io.BytesIO(data))
            df_excel_full.columns = [str(col).strip().lower().replace('\n', ' ').replace('\r', '') for col in df_excel_full.columns]

            EXCEL_CODE_COL = 'code'; STD_EXCEL_ISSUES_COL = 'issues'; STD_EXCEL_BRANCH_COL = 'branch'
            STD_EXCEL_AM_COL = 'area manager'; STD_EXCEL_DATE_COL = 'date'
            CCTV_EXCEL_VIOLATION_COL = 'choose the violation - اختر المخالفه'; CCTV_EXCEL_SHIFT_COL = 'choose the shift - اختر الشفت'
            CCTV_EXCEL_DATE_COL = 'date submitted'; CCTV_EXCEL_BRANCH_COL = 'branch'; CCTV_EXCEL_AM_COL = 'area manager'
            COMP_PERF_EXCEL_BRANCH_NAME_COL = 'branch'; COMP_PERF_EXCEL_TYPE_COL = 'نوع الشكوى'
            COMP_PERF_EXCEL_PRODUCT_COL = 'الشكوى على اي منتج؟'; COMP_PERF_EXCEL_QUALITY_COL = 'فى حاله كانت الشكوى جوده برجاء تحديد نوع الشكوى'
            COMP_PERF_EXCEL_ORDER_ERROR_COL = 'فى حاله خطاء فى الطلب برجاء تحديد نوع الشكوى'; COMP_PERF_EXCEL_DATE_COL = 'date'
            MISSING_EXCEL_PROJECT_COL = 'project'; MISSING_EXCEL_BRANCH_COL = 'branch'; MISSING_EXCEL_AM_COL = 'area manager'; MISSING_EXCEL_DATE_COL = 'date'
            
            required_cols_for_upload = []
            date_column_in_excel = ''
            
            norm_cat = str(final_category).lower().strip()
            norm_ft = str(final_file_type).lower().strip() if final_file_type else ""

            if norm_cat == 'cctv':
                required_cols_for_upload = [EXCEL_CODE_COL, CCTV_EXCEL_VIOLATION_COL, CCTV_EXCEL_SHIFT_COL, CCTV_EXCEL_DATE_COL, CCTV_EXCEL_BRANCH_COL, CCTV_EXCEL_AM_COL]; date_column_in_excel = CCTV_EXCEL_DATE_COL
            elif norm_cat == 'complaints':
                if norm_ft == 'performance': required_cols_for_upload = [COMP_PERF_EXCEL_BRANCH_NAME_COL, EXCEL_CODE_COL, COMP_PERF_EXCEL_TYPE_COL, COMP_PERF_EXCEL_PRODUCT_COL, COMP_PERF_EXCEL_QUALITY_COL, COMP_PERF_EXCEL_ORDER_ERROR_COL, COMP_PERF_EXCEL_DATE_COL]; date_column_in_excel = COMP_PERF_EXCEL_DATE_COL
                elif norm_ft == 'اغلاق الشكاوي': st.sidebar.error("Schema for 'complaints / اغلاق الشكاوي' not implemented."); st.stop()
                else: st.sidebar.error(f"Invalid file type '{final_file_type}' for 'complaints'."); st.stop()
            elif norm_cat == 'missing':
                if norm_ft == 'performance': required_cols_for_upload = [MISSING_EXCEL_PROJECT_COL, MISSING_EXCEL_BRANCH_COL, MISSING_EXCEL_AM_COL, MISSING_EXCEL_DATE_COL]; date_column_in_excel = MISSING_EXCEL_DATE_COL
                else: st.sidebar.error(f"Invalid file type '{final_file_type}' for 'missing'."); st.stop()
            elif norm_cat == 'visits':
                required_cols_for_upload = [EXCEL_CODE_COL, STD_EXCEL_BRANCH_COL, STD_EXCEL_AM_COL, STD_EXCEL_ISSUES_COL, STD_EXCEL_DATE_COL]; date_column_in_excel = STD_EXCEL_DATE_COL
            else: 
                required_cols_for_upload = [EXCEL_CODE_COL, STD_EXCEL_ISSUES_COL, STD_EXCEL_BRANCH_COL, STD_EXCEL_AM_COL, STD_EXCEL_DATE_COL]; date_column_in_excel = STD_EXCEL_DATE_COL

            missing_cols_detected = [col for col in required_cols_for_upload if col not in df_excel_full.columns]
            if missing_cols_detected:
                st.sidebar.error(f"Excel for '{final_category}' / '{final_file_type or 'N/A'}' missing columns: {', '.join(list(set(missing_cols_detected)))}. Aborted.")
                st.sidebar.info(f"Normalized columns found in Excel: {list(df_excel_full.columns)}")
                st.sidebar.info(f"Expected columns were: {required_cols_for_upload}"); st.stop()

            if not date_column_in_excel: st.sidebar.error(f"Internal error: Date column not defined for '{final_category}' / '{final_file_type or 'N/A'}'. Aborted."); st.stop()
            if date_column_in_excel not in df_excel_full.columns:
                st.sidebar.error(f"The expected date column '{date_column_in_excel}' was not found. Aborted."); st.sidebar.info(f"Normalized columns: {list(df_excel_full.columns)}"); st.stop()

            df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full[date_column_in_excel], errors='coerce')
            original_excel_rows = len(df_excel_full)
            df_excel_full.dropna(subset=['parsed_date'], inplace=True)
            if len(df_excel_full) < original_excel_rows: st.sidebar.warning(f"{original_excel_rows - len(df_excel_full)} Excel rows dropped due to invalid/missing dates in '{date_column_in_excel}'.")
            if df_excel_full.empty: st.sidebar.error(f"No valid data rows in Excel after checking dates in '{date_column_in_excel}'. Aborted."); st.stop()

            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()
            if df_to_import.empty: 
                st.sidebar.error(f"No rows found within the selected import date range ({imp_from_dt.strftime('%Y-%m-%d')} to {imp_to_dt.strftime('%Y-%m-%d')}). Please check Excel dates and your import range selection.")
                min_excel_dt_after_parse = df_excel_full['parsed_date'].min(); max_excel_dt_after_parse = df_excel_full['parsed_date'].max()
                st.sidebar.info(f"Date range in (validly parsed) Excel: {min_excel_dt_after_parse.strftime('%Y-%m-%d') if pd.notna(min_excel_dt_after_parse) else 'N/A'} to {max_excel_dt_after_parse.strftime('%Y-%m-%d') if pd.notna(max_excel_dt_after_parse) else 'N/A'}")
                st.stop()

            c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (up.name, current_user, ts, final_file_type, final_category, upload_submission_date_str, sqlite3.Binary(data)))
            upload_id = c.lastrowid
            unmapped_branch_codes = set(); inserted_issue_count = 0

            for _, row in df_to_import.iterrows():
                issue_date_str = row['parsed_date'].strftime('%Y-%m-%d')
                issue_val, am_val, shift_val = "N/A", "N/A", None
                excel_branch_field = "Unknown Branch"; code_val_from_excel = "" 

                if norm_cat == 'complaints' and norm_ft == 'performance':
                    excel_branch_field = str(row.get(COMP_PERF_EXCEL_BRANCH_NAME_COL, "Unk Comp Branch"))
                    code_val_from_excel = str(row.get(EXCEL_CODE_COL, "")).strip()
                    am_val = "N/A - Complaints"; details = []
                    complaint_type_val = row.get(COMP_PERF_EXCEL_TYPE_COL); product_val = row.get(COMP_PERF_EXCEL_PRODUCT_COL)
                    quality_val = row.get(COMP_PERF_EXCEL_QUALITY_COL); order_error_val = row.get(COMP_PERF_EXCEL_ORDER_ERROR_COL)
                    if pd.notna(complaint_type_val): details.append(f"Type: {str(complaint_type_val).strip()}")
                    if pd.notna(product_val): details.append(f"Product: {str(product_val).strip()}")
                    if pd.notna(quality_val): details.append(f"Quality Detail: {str(quality_val).strip()}")
                    if pd.notna(order_error_val): details.append(f"Order Error: {str(order_error_val).strip()}")
                    issue_val = "; ".join(details) if details else "No specific complaint details"
                elif norm_cat == 'cctv':
                    excel_branch_field = str(row.get(CCTV_EXCEL_BRANCH_COL, "Unk CCTV Branch"))
                    code_val_from_excel = str(row.get(EXCEL_CODE_COL, "")).strip()
                    am_val = str(row.get(CCTV_EXCEL_AM_COL, "N/A")); issue_val = str(row.get(CCTV_EXCEL_VIOLATION_COL, "N/A"))
                    shift_val = str(row.get(CCTV_EXCEL_SHIFT_COL)) if pd.notna(row.get(CCTV_EXCEL_SHIFT_COL)) else None
                elif norm_cat == 'missing' and norm_ft == 'performance':
                    excel_branch_field = str(row.get(MISSING_EXCEL_BRANCH_COL, "Unk Missing Branch")).strip()
                    issue_val = str(row.get(MISSING_EXCEL_PROJECT_COL, "Unk Project")).strip() 
                    am_val = str(row.get(MISSING_EXCEL_AM_COL, "N/A")).strip()
                elif norm_cat == 'visits': 
                    excel_branch_field = str(row.get(STD_EXCEL_BRANCH_COL, "Unk Visit Branch"))
                    code_val_from_excel = str(row.get(EXCEL_CODE_COL, "")).strip()
                    am_val = str(row.get(STD_EXCEL_AM_COL, "N/A - Visits")); issue_val = str(row.get(STD_EXCEL_ISSUES_COL, "Visit Logged"))
                else: 
                    excel_branch_field = str(row.get(STD_EXCEL_BRANCH_COL, "Unk Std Branch"))
                    code_val_from_excel = str(row.get(EXCEL_CODE_COL, "")).strip()
                    am_val = str(row.get(STD_EXCEL_AM_COL, "N/A")); issue_val = str(row.get(STD_EXCEL_ISSUES_COL, "N/A"))

                standardized_branch_name = "Unknown Branch"; code_val_to_db = ""
                normalized_excel_branch_field = excel_branch_field.strip().upper()
                extracted_code_from_branch_field = None
                branch_field_match = re.search(r'\b([A-Z0-9]{2,5})\b(?![A-Z0-9])', normalized_excel_branch_field) 
                if branch_field_match: extracted_code_from_branch_field = branch_field_match.group(1).upper()

                if extracted_code_from_branch_field and extracted_code_from_branch_field in BRANCH_SCHEMA_NORMALIZED:
                    standardized_branch_name = BRANCH_SCHEMA_NORMALIZED[extracted_code_from_branch_field]; code_val_to_db = extracted_code_from_branch_field
                elif code_val_from_excel and code_val_from_excel.upper() in BRANCH_SCHEMA_NORMALIZED:
                    standardized_branch_name = BRANCH_SCHEMA_NORMALIZED[code_val_from_excel.upper()]; code_val_to_db = code_val_from_excel.upper()
                else:
                    found_direct_name_match = False
                    for schema_code_key, schema_name_val in BRANCH_SCHEMA_NORMALIZED.items():
                        if normalized_excel_branch_field == schema_name_val.upper():
                            standardized_branch_name = schema_name_val; code_val_to_db = schema_code_key; found_direct_name_match = True; break
                    if not found_direct_name_match:
                        standardized_branch_name = excel_branch_field; code_val_to_db = code_val_from_excel
                        unmapped_branch_codes.add(f"{excel_branch_field} (Code: {code_val_to_db or 'N/A'})")
                if not code_val_to_db and standardized_branch_name not in ["Unknown Branch", excel_branch_field] and standardized_branch_name.upper() != excel_branch_field.upper() :
                    for schema_c, schema_n in BRANCH_SCHEMA_NORMALIZED.items():
                        if standardized_branch_name.upper() == schema_n.upper(): code_val_to_db = schema_c; break
                code_val_to_db = code_val_to_db or ""
                
                c.execute('''INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type, shift)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (upload_id, code_val_to_db, issue_val, standardized_branch_name, am_val, issue_date_str, final_file_type, shift_val))
                inserted_issue_count += 1
            
            conn.commit()
            st.sidebar.success(f"Successfully imported {inserted_issue_count} issues from '{up.name}'.")
            if unmapped_branch_codes: st.sidebar.warning(f"Unmapped branches: {', '.join(sorted(list(unmapped_branch_codes)))}.")
        except Exception as e_general: conn.rollback(); st.sidebar.error(f"Error processing '{up.name}': {e_general}. Rolled back."); st.exception(e_general)
        finally: st.rerun()

    st.sidebar.subheader("Manage Submissions")
    df_uploads_raw_for_delete = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
    df_uploads_raw_for_delete['display_submission_date_fmt'] = df_uploads_raw_for_delete['submission_date'].apply(lambda d: datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) and str(d) else "N/A")
    delete_opts_list = [(f"{row['id']} - {row['filename']} ({row['category']}/{row['file_type'] or 'N/A'}) Imp.From: {row['display_submission_date_fmt']}") for index, row in df_uploads_raw_for_delete.iterrows()]
    delete_opts = ['Select ID to Delete'] + delete_opts_list
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission Batch:", delete_opts, key="delete_submission_id_select")
    if del_choice_display != 'Select ID to Delete':
        del_id_val = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id_val}", key=f"confirm_del_btn_{del_id_val}", type="primary"):
            try: c.execute('DELETE FROM uploads WHERE id=?', (del_id_val,)); conn.commit(); st.sidebar.success(f"Deleted {del_id_val}."); st.rerun()
            except sqlite3.Error as e: conn.rollback(); st.sidebar.error(f"Failed to delete: {e}")

    st.sidebar.subheader("Database Management")
    st.sidebar.markdown("""**To persist data changes...**""") # Shortened for brevity
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as fp: db_file_bytes = fp.read()
        backup_db_filename = f"issues_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        st.sidebar.download_button("Download Database Backup", db_file_bytes, backup_db_filename, "application/vnd.sqlite3", key="dl_db_backup")
    else: st.sidebar.warning(f"'{DB_PATH}' not found.")


default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path (for PDF reports):", default_wk, help="Required for PDF generation.")

df_uploads_raw_main = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) and str(d) else "N/A"
df_uploads_raw_main['display_submission_date_fmt'] = df_uploads_raw_main['submission_date'].apply(format_display_date)
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [(f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) Imp.From: {r['display_submission_date_fmt']}") for i,r in df_uploads_raw_main.iterrows()]
sel_display = st.sidebar.selectbox("Select upload batch to analyze:", scope_opts, key="select_upload_scope_main")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

df_all_issues = pd.read_sql('SELECT i.*, u.category as upload_category, u.id as upload_id_col FROM issues i JOIN uploads u ON u.id = i.upload_id', conn, parse_dates=['date'])
if df_all_issues.empty: st.warning("No issues data in database."); st.stop()

st.sidebar.subheader("Dashboard Filters")
min_overall_date = df_all_issues['date'].min().date() if not df_all_issues['date'].isnull().all() else date.today()
max_overall_date = df_all_issues['date'].max().date() if not df_all_issues['date'].isnull().all() else date.today()
if min_overall_date > max_overall_date: max_overall_date = min_overall_date

primary_date_range_val = st.sidebar.date_input("Primary Date Range (Issue Dates):", value=[min_overall_date, max_overall_date], min_value=min_overall_date, max_value=max_overall_date, key="primary_date_range_filter")
primary_date_range = [min_overall_date, max_overall_date] 
if primary_date_range_val and len(primary_date_range_val) == 2:
    primary_date_range = [primary_date_range_val[0], primary_date_range_val[1]] if primary_date_range_val[0] <= primary_date_range_val[1] else [primary_date_range_val[1], primary_date_range_val[0]]
elif primary_date_range_val: st.sidebar.warning("Invalid primary date range, defaulting.")

branch_opts = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist()); sel_branch = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")
cat_opts = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist()); sel_cat = st.sidebar.multiselect("Category:", cat_opts, default=['All'], key="category_filter")
am_opts = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist()); sel_am = st.sidebar.multiselect("Area Manager:", am_opts, default=['All'], key="area_manager_filter")
unique_report_types = df_all_issues['report_type'].astype(str).unique()
filtered_report_types = sorted([rt for rt in unique_report_types if rt.lower() not in ['none', 'nan', '']])
file_type_filter_opts = ['All'] + filtered_report_types
sel_ft = st.sidebar.multiselect("File Type:", file_type_filter_opts, default=['All'], key="file_type_filter")

st.sidebar.subheader("📊 Period Comparison")
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox")
comparison_date_range_1, comparison_date_range_2 = None, None
if enable_comparison: 
    st.sidebar.markdown("Comparison Period 1:"); safe_p1_end = min(min_overall_date + timedelta(days=6), max_overall_date)
    comp_dr1_val = st.sidebar.date_input("Start & End (P1):", value=[min_overall_date, safe_p1_end], min_value=min_overall_date, max_value=max_overall_date, key="comp_p1_filter")
    if comp_dr1_val and len(comp_dr1_val)==2 and comp_dr1_val[0]<=comp_dr1_val[1]: comparison_date_range_1 = comp_dr1_val
    else: st.sidebar.warning("P1: Invalid range."); comparison_date_range_1 = None
    if comparison_date_range_1:
        st.sidebar.markdown("Comparison Period 2:"); def_p2_start = min(comparison_date_range_1[1] + timedelta(days=1), max_overall_date); def_p2_end = min(def_p2_start + timedelta(days=6), max_overall_date)
        comp_dr2_val = st.sidebar.date_input("Start & End (P2):", value=[def_p2_start, def_p2_end], min_value=min_overall_date, max_value=max_overall_date, key="comp_p2_filter")
        if comp_dr2_val and len(comp_dr2_val)==2 and comp_dr2_val[0]<=comp_dr2_val[1]: comparison_date_range_2 = comp_dr2_val
        else: st.sidebar.warning("P2: Invalid range."); comparison_date_range_2 = None
    else: comparison_date_range_2 = None

def apply_general_filters(df_input, sel_upload_id_val, selected_branches, selected_categories, selected_managers, selected_file_types_val):
    df_filtered = df_input.copy()
    if sel_upload_id_val: df_filtered = df_filtered[df_filtered['upload_id_col'] == sel_upload_id_val]
    if 'All' not in selected_branches: df_filtered = df_filtered[df_filtered['branch'].isin(selected_branches)]
    if 'All' not in selected_categories: df_filtered = df_filtered[df_filtered['upload_category'].isin(selected_categories)]
    if 'All' not in selected_managers: df_filtered = df_filtered[df_filtered['area_manager'].isin(selected_managers)]
    if 'All' not in selected_file_types_val:
        is_na_report_type = df_filtered['report_type'].isnull() | df_filtered['report_type'].astype(str).str.lower().isin(['none', 'nan', ''])
        valid_selected_ft = [str(ft).lower() for ft in selected_file_types_val if pd.notna(ft) and str(ft).strip() != '']
        if not valid_selected_ft: pass
        else:
            include_na_types = any(na_val in valid_selected_ft for na_val in ['none', 'nan', ''])
            df_filtered_specific_types = df_filtered[df_filtered['report_type'].astype(str).str.lower().isin(valid_selected_ft)]
            if include_na_types: df_filtered = pd.concat([df_filtered_specific_types, df_filtered[is_na_report_type]]).drop_duplicates().reset_index(drop=True)
            else: 
                na_like_mask = df_filtered['report_type'].isnull() | df_filtered['report_type'].astype(str).str.lower().isin(['none', 'nan', ''])
                df_filtered = df_filtered_specific_types[~na_like_mask].reset_index(drop=True)
    return df_filtered

df_temp_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)
df_primary_period = df_temp_filtered.copy()
if primary_date_range and len(primary_date_range) == 2:
    start_date_filt, end_date_filt = primary_date_range[0], primary_date_range[1]
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']):
        df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= start_date_filt) & (df_primary_period['date'].dt.date <= end_date_filt)]
    else: df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)
else: df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)

st.subheader(f"Filtered Data for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total records found in primary period: {len(df_primary_period)}")

COMPLAINTS_COLOR_SEQUENCE = px.colors.qualitative.Vivid

def create_bar_chart(df_source, group_col, title_suffix="", chart_title=None, color_sequence=None, barmode='group', sort_ascending=False, sort_values_by='count'):
    final_title = chart_title if chart_title else f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col not in df_source.columns or df_source.empty: return None
    df_valid_data = df_source.copy(); df_valid_data.dropna(subset=[group_col], inplace=True)
    df_valid_data[group_col] = df_valid_data[group_col].astype(str).str.strip()
    df_valid_data = df_valid_data[df_valid_data[group_col] != '']; df_valid_data = df_valid_data[~df_valid_data[group_col].str.lower().isin(['nan', 'none', '<na>'])]
    if not df_valid_data.empty:
        if 'period_label' in df_valid_data.columns:
            data = df_valid_data.groupby([group_col, 'period_label']).size().reset_index(name='count'); data = data.sort_values(by=[group_col, 'period_label'], ascending=[True, True])
            if not data.empty: return px.bar(data, x=group_col, y='count', color='period_label', barmode=barmode, title=final_title, template="plotly_white", color_discrete_sequence=color_sequence or px.colors.qualitative.Plotly)
        else:
            if group_col in df_source.columns and sort_values_by in df_source.columns and group_col != sort_values_by: # Forcing sort order for ranking charts
                 data_to_plot = df_source.copy(); data_to_plot[group_col] = data_to_plot[group_col].astype(str)
                 fig = px.bar(data_to_plot, x=group_col, y=sort_values_by, title=final_title, template="plotly_white", color_discrete_sequence=color_sequence or px.colors.qualitative.Plotly)
                 ordered_categories = data_to_plot.sort_values(by=sort_values_by, ascending=sort_ascending)[group_col].tolist() # Sort by value then get category order
                 fig.update_xaxes(categoryorder='array', categoryarray=ordered_categories); return fig
            else: # Standard count-based bar chart
                data = df_valid_data.groupby(group_col).size().reset_index(name='count'); data = data.sort_values(by='count', ascending=sort_ascending)
                if not data.empty: return px.bar(data, x=group_col, y='count', title=final_title, template="plotly_white", color_discrete_sequence=color_sequence or px.colors.qualitative.Plotly)
    return None

def create_pie_chart(df_source, group_col, title_suffix="", chart_title=None, color_sequence=None):
    final_title = chart_title if chart_title else f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col not in df_source.columns or df_source.empty: return None
    df_valid_data = df_source.copy(); df_valid_data.dropna(subset=[group_col], inplace=True); df_valid_data[group_col] = df_valid_data[group_col].astype(str).str.strip()
    df_valid_data = df_valid_data[df_valid_data[group_col] != '']; df_valid_data = df_valid_data[~df_valid_data[group_col].str.lower().isin(['nan', 'none', '<na>'])]
    if not df_valid_data.empty:
        data = df_valid_data.groupby(group_col).size().reset_index(name='count')
        if not data.empty: return px.pie(data, names=group_col, values='count', title=final_title, hole=0.3, template="plotly_white", color_discrete_sequence=color_sequence or px.colors.qualitative.Plotly)
    return None

def parse_complaint_details(issue_string):
    details = {'Type': [], 'Product': None, 'Quality Detail': [], 'Order Error': []}
    if not isinstance(issue_string, str): return pd.Series(details)
    def _get_value(pattern, text, is_multi_value=False):
        match = re.search(pattern, text)
        if match and match.group(1):
            value_str = match.group(1).strip()
            if value_str: return [s.strip() for s in value_str.split(',') if s.strip()] if is_multi_value else value_str
        return [] if is_multi_value else None
    details['Type'] = _get_value(r"Type:\s*(.*?)(?:;|$)", issue_string, is_multi_value=True)
    details['Product'] = _get_value(r"Product:\s*(.*?)(?:;|$)", issue_string, is_multi_value=False)
    details['Quality Detail'] = _get_value(r"Quality Detail:\s*(.*?)(?:;|$)", issue_string, is_multi_value=True)
    details['Order Error'] = _get_value(r"Order Error:\s*(.*?)(?:;|$)", issue_string, is_multi_value=True)
    return pd.Series(details)

def display_general_dashboard(df_data, figs_container): # From base
    if df_data.empty: st.info("No data available for general performance analysis with current filters."); return figs_container
    chart_cols = st.columns(2) # ... (full implementation as provided in base)
    with chart_cols[0]:
        figs_container['Branch_Issues'] = create_bar_chart(df_data, 'branch', '(Primary)')
        if figs_container.get('Branch_Issues'): st.plotly_chart(figs_container['Branch_Issues'], use_container_width=True)
        else: st.caption("No data for Branch chart.")
        df_report_type_viz = df_data.copy()
        if 'upload_category' in df_report_type_viz.columns and 'report_type' in df_report_type_viz.columns:
            condition = (df_report_type_viz['report_type'] == 'issues') & (df_report_type_viz['upload_category'] == 'CCTV')
            df_report_type_viz.loc[condition, 'report_type'] = 'CCTV issues'
        figs_container['Report_Type'] = create_bar_chart(df_report_type_viz, 'report_type', '(Primary)')
        if figs_container.get('Report_Type'): st.plotly_chart(figs_container['Report_Type'], use_container_width=True)
        else: st.caption("No data for Report Type chart.")
    with chart_cols[1]:
        figs_container['Area_Manager'] = create_pie_chart(df_data, 'area_manager', '(Primary)')
        if figs_container.get('Area_Manager'): st.plotly_chart(figs_container['Area_Manager'], use_container_width=True)
        else: st.caption("No data for Area Manager chart.")
        figs_container['Category'] = create_bar_chart(df_data, 'upload_category', '(Primary)')
        if figs_container.get('Category'): st.plotly_chart(figs_container['Category'], use_container_width=True)
        else: st.caption("No data for Category chart.")
    if 'shift' in df_data.columns and df_data['shift'].notna().any():
        df_shift_data = df_data[df_data['shift'].notna() & (df_data['shift'].astype(str).str.strip() != '')].copy()
        if not df_shift_data.empty:
            with st.container():
                figs_container['Shift_Values'] = create_bar_chart(df_shift_data, 'shift', '(Primary - CCTV Shift Times)')
                if figs_container.get('Shift_Values'): st.plotly_chart(figs_container['Shift_Values'], use_container_width=True)
                else: st.caption("No valid shift data to display.")
    if 'date' in df_data.columns and pd.api.types.is_datetime64_any_dtype(df_data['date']) and not df_data['date'].isnull().all():
        trend_data_primary = df_data.groupby(df_data['date'].dt.date).size().reset_index(name='daily_issues')
        trend_data_primary['date'] = pd.to_datetime(trend_data_primary['date']); trend_data_primary = trend_data_primary.sort_values('date')
        if not trend_data_primary.empty:
            window_size = min(7, len(trend_data_primary)); window_size = max(2,window_size)
            trend_data_primary[f'{window_size}-Day MA'] = trend_data_primary['daily_issues'].rolling(window=window_size, center=True, min_periods=1).mean().round(1)
            fig_trend = go.Figure(); fig_trend.add_trace(go.Bar(x=trend_data_primary['date'], y=trend_data_primary['daily_issues'], name='Daily Issues', marker_color='lightblue', hovertemplate="<b>%{x|%A, %b %d}</b><br>Issues: %{y}<extra></extra>"))
            fig_trend.add_trace(go.Scatter(x=trend_data_primary['date'], y=trend_data_primary[f'{window_size}-Day MA'], name=f'{window_size}-Day Moving Avg.', mode='lines+markers', line=dict(color='royalblue', width=2), marker=dict(size=5), hovertemplate="<b>%{x|%A, %b %d}</b><br>Moving Avg: %{y:.1f}<extra></extra>"))
            fig_trend.update_layout(title_text='Issues Trend (Primary Period)', xaxis_title='Date', yaxis_title='Number of Issues', template="plotly_white", hovermode="x unified", legend_title_text='Metric')
            figs_container['Trend'] = fig_trend
            if figs_container.get('Trend'): st.plotly_chart(figs_container['Trend'], use_container_width=True)
        else: st.caption("No data for trend analysis.")
    if len(df_data) < 50 or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.subheader("Detailed Records (Primary Period - Filtered)"); display_columns = ['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']
        if 'shift' in df_data.columns and df_data['shift'].notna().any(): display_columns.append('shift')
        df_display_primary = df_data[[col for col in display_columns if col in df_data.columns]].copy()
        if 'upload_category' in df_display_primary.columns and 'report_type' in df_display_primary.columns:
            condition_table = (df_display_primary['report_type'] == 'issues') & (df_display_primary['upload_category'] == 'CCTV'); df_display_primary.loc[condition_table, 'report_type'] = 'CCTV issues'
        if 'date' in df_display_primary.columns: df_display_primary['date'] = df_display_primary['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_display_primary.reset_index(drop=True), use_container_width=True)
    st.subheader("Top Issues (Primary Period - Filtered)")
    if 'issues' in df_data.columns and df_data['issues'].notna().any():
        df_issues_for_top = df_data[['issues']].copy(); df_issues_for_top.dropna(subset=['issues'], inplace=True)
        df_issues_for_top['issues_str'] = df_issues_for_top['issues'].astype(str).str.strip()
        df_issues_for_top = df_issues_for_top[df_issues_for_top['issues_str'] != '']
        if not df_issues_for_top.empty:
            top_issues_primary = df_issues_for_top['issues_str'].value_counts().head(20).rename_axis('Issue/Violation').reset_index(name='Frequency')
            if not top_issues_primary.empty: st.dataframe(top_issues_primary, use_container_width=True)
            else: st.info("No non-empty issue descriptions for 'Top Issues'.")
        else: st.info("No non-empty issue descriptions for 'Top Issues'.")
    else: st.info("'issues' column not available or empty.")
    return figs_container

def display_complaints_performance_dashboard(df_complaints_raw, figs_container): # From base
    if df_complaints_raw.empty: st.info("No complaints data for performance with current filters."); return figs_container
    parsed_details = df_complaints_raw['issues'].apply(parse_complaint_details) # ... (full implementation as provided in base)
    df_complaints = pd.concat([df_complaints_raw.reset_index(drop=True).drop(columns=['issues'], errors='ignore'), parsed_details.reset_index(drop=True)], axis=1)
    df_complaints.rename(columns={'Type': 'Complaint Type', 'Product': 'Product Complained About', 'Quality Detail': 'Quality Issue Detail', 'Order Error': 'Order Error Detail'}, inplace=True)
    for col_name in MULTI_VALUE_COMPLAINT_COLS:
        if col_name in df_complaints.columns:
            def _sanitize_and_split_elements(entry_list_or_str):
                if not isinstance(entry_list_or_str, list):
                    if isinstance(entry_list_or_str, str): entry_list_or_str = [entry_list_or_str]
                    else: return []
                final_elements = []
                for element in entry_list_or_str:
                    if isinstance(element, str): final_elements.extend([s.strip() for s in element.split(',') if s.strip()])
                    elif element is not None : final_elements.append(str(element).strip())
                return final_elements
            df_complaints[col_name] = df_complaints[col_name].apply(_sanitize_and_split_elements)
    col1, col2 = st.columns(2)
    with col1:
        df_type_chart_data = df_complaints.explode('Complaint Type').dropna(subset=['Complaint Type']); df_type_chart_data = df_type_chart_data[df_type_chart_data['Complaint Type'] != '']
        figs_container['Complaint_Type'] = create_bar_chart(df_type_chart_data, 'Complaint Type', chart_title="Complaints by Type", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
        if figs_container.get('Complaint_Type'): st.plotly_chart(figs_container['Complaint_Type'], use_container_width=True)
        else: st.caption("No data for Complaint Type chart.")
        df_product_chart_source = df_complaints[df_complaints['Product Complained About'].notna() & (df_complaints['Product Complained About'] != '') & (df_complaints['Product Complained About'].str.lower() != 'لا علاقة لها بالمنتج')].copy()
        if not df_product_chart_source.empty:
            figs_container['Product_Complained_About'] = create_bar_chart(df_product_chart_source, 'Product Complained About', chart_title="Complaints by Product (Specific)", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
            if figs_container.get('Product_Complained_About'): st.plotly_chart(figs_container['Product_Complained_About'], use_container_width=True)
            else: st.caption("No data for Product chart (filtered).")
        else: st.info("No complaints on specific products (excluding 'لا علاقة لها بالمنتج').")
    with col2:
        df_exploded_types_for_quality = df_complaints.explode('Complaint Type').dropna(subset=['Complaint Type']); df_exploded_types_for_quality = df_exploded_types_for_quality[df_exploded_types_for_quality['Complaint Type'] != '']
        df_quality_issues_source = df_exploded_types_for_quality[df_exploded_types_for_quality['Complaint Type'] == 'جوده'].copy()
        if not df_quality_issues_source.empty:
            df_quality_detail_chart_data = df_quality_issues_source.explode('Quality Issue Detail').dropna(subset=['Quality Issue Detail']); df_quality_detail_chart_data = df_quality_detail_chart_data[df_quality_detail_chart_data['Quality Issue Detail'] != '']
            figs_container['Quality_Issue_Detail'] = create_bar_chart(df_quality_detail_chart_data, 'Quality Issue Detail', chart_title="Quality Issue Details ('جوده')", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
            if figs_container.get('Quality_Issue_Detail'): st.plotly_chart(figs_container['Quality_Issue_Detail'], use_container_width=True)
            else: st.caption("No specific quality details for 'جوده'.")
        else: st.caption("No 'جوده' (Quality) type complaints.")
        df_exploded_types_for_order_error = df_complaints.explode('Complaint Type').dropna(subset=['Complaint Type']); df_exploded_types_for_order_error = df_exploded_types_for_order_error[df_exploded_types_for_order_error['Complaint Type'] != '']
        df_order_errors_source = df_exploded_types_for_order_error[df_exploded_types_for_order_error['Complaint Type'] == 'خطاء فى الطلب'].copy()
        if not df_order_errors_source.empty:
            df_order_error_detail_chart_data = df_order_errors_source.explode('Order Error Detail').dropna(subset=['Order Error Detail']); df_order_error_detail_chart_data = df_order_error_detail_chart_data[df_order_error_detail_chart_data['Order Error Detail'] != '']
            figs_container['Order_Error_Detail'] = create_bar_chart(df_order_error_detail_chart_data, 'Order Error Detail', chart_title="Order Error Details ('خطاء فى الطلب')", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
            if figs_container.get('Order_Error_Detail'): st.plotly_chart(figs_container['Order_Error_Detail'], use_container_width=True)
            else: st.caption("No specific order error details for 'خطاء فى الطلب'.")
        else: st.caption("No 'خطاء فى الطلب' (Order Error) type complaints.")
    st.subheader("Complaints by Branch")
    figs_container['Complaints_by_Branch'] = create_bar_chart(df_complaints, 'branch', chart_title="Total Complaints per Branch", color_sequence=COMPLAINTS_COLOR_SEQUENCE)
    if figs_container.get('Complaints_by_Branch'): st.plotly_chart(figs_container['Complaints_by_Branch'], use_container_width=True)
    else: st.caption("No data for Complaints by Branch chart.")
    if 'date' in df_complaints.columns and pd.api.types.is_datetime64_any_dtype(df_complaints['date']) and not df_complaints['date'].isnull().all():
        trend_data_complaints = df_complaints.groupby(df_complaints['date'].dt.date).size().reset_index(name='daily_complaints'); trend_data_complaints['date'] = pd.to_datetime(trend_data_complaints['date']); trend_data_complaints = trend_data_complaints.sort_values('date')
        if not trend_data_complaints.empty:
            fig_complaints_trend = px.line(trend_data_complaints, x='date', y='daily_complaints', title='Daily Complaints Trend', markers=True, color_discrete_sequence=COMPLAINTS_COLOR_SEQUENCE); fig_complaints_trend.update_layout(template="plotly_white")
            figs_container['Complaints_Trend'] = fig_complaints_trend
            if figs_container.get('Complaints_Trend'): st.plotly_chart(figs_container['Complaints_Trend'], use_container_width=True)
        else: st.caption("No data for daily complaints trend.")
    st.subheader("Detailed Complaints Data (Primary Period - Parsed)")
    display_cols_complaints_options = ['date', 'branch', 'code', 'Complaint Type', 'Product Complained About', 'Quality Issue Detail', 'Order Error Detail']
    display_cols_complaints_final = [col for col in display_cols_complaints_options if col in df_complaints.columns]
    df_display_complaints = df_complaints[display_cols_complaints_final].copy()
    if 'date' in df_display_complaints.columns: df_display_complaints['date'] = df_display_complaints['date'].dt.strftime('%Y-%m-%d')
    for col in MULTI_VALUE_COMPLAINT_COLS:
        if col in df_display_complaints.columns: df_display_complaints[col] = df_display_complaints[col].apply(lambda x: ', '.join(x) if isinstance(x, list) and x else (x if not isinstance(x,list) else ''))
    st.dataframe(df_display_complaints.reset_index(drop=True), use_container_width=True)
    return figs_container

def get_expected_task_count(project_name, start_date_obj, end_date_obj):
    if project_name not in PROJECT_FREQUENCIES: return 0
    config = PROJECT_FREQUENCIES[project_name]; expected_count = 0
    if start_date_obj > end_date_obj: return 0
    current_date = start_date_obj
    while current_date <= end_date_obj:
        if config["type"] == "daily": expected_count += 1
        elif config["type"] == "weekly" and current_date.weekday() == config["weekday"]: expected_count += 1
        current_date += timedelta(days=1)
    return expected_count

def display_missing_performance_dashboard(df_missing_raw_period_data, figs_container, date_range_for_calc, dashboard_title_suffix=""):
    if df_missing_raw_period_data.empty and not list(BRANCH_SCHEMA_NORMALIZED.values()):
        st.info(f"No 'missing' task data for analysis {dashboard_title_suffix}."); return figs_container, pd.DataFrame()
    start_date_calc, end_date_calc = date_range_for_calc[0], date_range_for_calc[1]; results = []
    all_branches_to_calculate_for = sorted(list(BRANCH_SCHEMA_NORMALIZED.values()))
    for branch_name in all_branches_to_calculate_for:
        total_expected_for_branch, total_missed_for_branch = 0, 0
        if 'issues' not in df_missing_raw_period_data.columns or 'branch' not in df_missing_raw_period_data.columns: pass
        df_branch_missed_tasks = df_missing_raw_period_data[df_missing_raw_period_data['branch'] == branch_name]
        for project_name in ALL_DEFINED_PROJECT_NAMES:
            expected_for_project = get_expected_task_count(project_name, start_date_calc, end_date_calc)
            if expected_for_project == 0: continue
            total_expected_for_branch += expected_for_project
            missed_count_for_project = len(df_branch_missed_tasks[df_branch_missed_tasks['issues'] == project_name])
            total_missed_for_branch += missed_count_for_project
        done_rate = 100.0 if total_expected_for_branch == 0 else ((total_expected_for_branch - total_missed_for_branch) / total_expected_for_branch) * 100
        missing_rate_calc = 0.0 if total_expected_for_branch == 0 else (total_missed_for_branch / total_expected_for_branch) * 100
        results.append({"branch": branch_name, "done rate": f"{done_rate:.1f}%", "missing rate": f"{missing_rate_calc:.0f}%", "_done_rate_numeric": done_rate, "_missing_rate_numeric": missing_rate_calc})
    df_results = pd.DataFrame(results)
    if df_results.empty: st.info(f"No missing performance data {dashboard_title_suffix}."); return figs_container, pd.DataFrame()
    df_results_sorted = df_results.sort_values(by="_done_rate_numeric", ascending=False)
    def get_color(val): 
        if val == 100.0: return ('#2ca02c', 'white'); 
        if val >= 99.0: return ('#90EE90', 'black')
        elif val >= 98.0: return ('#ADFF2F', 'black'); 
        elif val >= 96.0: return ('#FFFF99', 'black')
        elif val >= 93.0: return ('#FFD700', 'black'); 
        elif val >= 90.0: return ('#FFA500', 'black')
        elif val >= 85.0: return ('#FF7F50', 'white'); 
        else: return ('#FF6347', 'white')
    def style_row(row): bg, txt = get_color(row['_done_rate_numeric']); return [f'background-color: {bg}; color: {txt}; text-align: right;'] * 2
    st.subheader(f"Missing Tasks Performance by Branch {dashboard_title_suffix}")
    df_for_styling = df_results_sorted[['branch', 'done rate', 'missing rate', '_done_rate_numeric']].copy()
    html_table_styler = df_for_styling.style.apply(style_row, axis=1, subset=['done rate', 'missing rate']) \
        .set_properties(**{'text-align': 'left', 'min-width': '150px', 'font-weight': 'bold'}, subset=['branch']) \
        .set_properties(**{'text-align': 'right'}, subset=['done rate', 'missing rate']) \
        .set_table_styles([{'selector': 'th', 'props': 'background-color: #E8E8E8; text-align: center; font-weight: bold; padding: 5px;'}, 
                           {'selector': 'td', 'props': 'padding: 5px; border: 1px solid #ddd;'},
                           {'selector': 'thead th:first-child', 'props': 'text-align: left;'}]) \
        .hide(axis='index').set_table_attributes('class="dataframe styled-missing-table"')
    html_table_output = html_table_styler.to_html(columns=['branch', 'done rate', 'missing rate'])
    html_table_output = html_table_output.replace("<th>branch</th>", "<th>Branch <small>↕</small></th>", 1).replace("<th>done rate</th>", "<th>Done Rate <small>↕</small></th>", 1).replace("<th>missing rate</th>", "<th>Missing Rate <small>↕</small></th>", 1)
    st.markdown(html_table_output, unsafe_allow_html=True)
    figs_container[f'missing_perf_table_df{dashboard_title_suffix.replace(" ", "_")}'] = df_results_sorted
    csv_sum = df_results_sorted[['branch', 'done rate', 'missing rate']].to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"Download Missing Summary (CSV) {dashboard_title_suffix}", csv_sum, f"missing_perf{dashboard_title_suffix.replace(' ', '_')}.csv", "text/csv", key=f"dl_csv_miss_sum{dashboard_title_suffix.replace(' ', '_')}")
    return figs_container, df_results_sorted

# --- Main Dashboard Logic ---
figs_primary = {}
figs_complaints_primary = {}
figs_missing_primary = {} 
df_missing_perf_results_primary = pd.DataFrame() 

if not df_primary_period.empty:
    is_purely_complaints_perf = ((df_primary_period['upload_category'] == 'complaints').all() and (df_primary_period['report_type'] == 'performance').all() and df_primary_period['upload_category'].nunique() == 1 and df_primary_period['report_type'].nunique() == 1)
    is_purely_missing_perf = ((df_primary_period['upload_category'] == 'missing').all() and (df_primary_period['report_type'] == 'performance').all() and df_primary_period['upload_category'].nunique() == 1 and df_primary_period['report_type'].nunique() == 1)

    if is_purely_complaints_perf:
        st.subheader("Complaints Performance Dashboard (Primary Period)")
        figs_complaints_primary = display_complaints_performance_dashboard(df_primary_period.copy(), figs_complaints_primary)
    elif is_purely_missing_perf:
        figs_missing_primary, df_missing_perf_results_primary = display_missing_performance_dashboard(df_primary_period.copy(), figs_missing_primary, primary_date_range, "(Primary Period)")
    else: 
        st.subheader("General Performance Analysis (Primary Period)")
        figs_primary = display_general_dashboard(df_primary_period.copy(), figs_primary)
        df_complaints_subset_in_primary = df_primary_period[(df_primary_period['upload_category'] == 'complaints') & (df_primary_period['report_type'] == 'performance')].copy()
        if not df_complaints_subset_in_primary.empty:
            st.markdown("---"); st.subheader("Complaints Analysis (Subset of Primary Period)")
            temp_figs_subset_complaints = display_complaints_performance_dashboard(df_complaints_subset_in_primary, {})
            if figs_primary and temp_figs_subset_complaints:
                 for key, fig_val in temp_figs_subset_complaints.items(): figs_primary[f"Subset_Complaints_{key}"] = fig_val
        df_missing_subset_in_primary = df_primary_period[(df_primary_period['upload_category'] == 'missing') & (df_primary_period['report_type'] == 'performance')].copy()
        if not df_missing_subset_in_primary.empty:
            st.markdown("---"); st.subheader("Missing Tasks Analysis (Subset of Primary Period)")
            temp_figs_subset_missing, _ = display_missing_performance_dashboard(df_missing_subset_in_primary, {}, primary_date_range, "(Subset of Primary)")
            if figs_primary and temp_figs_subset_missing: 
                for key, data_val in temp_figs_subset_missing.items(): figs_primary[f"Subset_Missing_{key}"] = data_val

    st.markdown("---")
    if st.button("🏆 Show Branch Rankings (Current Filters)", key="show_rankings_button"):
        if not df_primary_period.empty and 'branch' in df_primary_period.columns:
            st.subheader(f"Branch Performance Ranking (Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d})")
            if is_purely_missing_perf and not df_missing_perf_results_primary.empty:
                st.markdown("_Based on 'Missing Rate'. Lower is better._")
                ranked_missing_df = df_missing_perf_results_primary.sort_values(by='_missing_rate_numeric', ascending=True).copy()
                ranked_missing_df['Rank'] = ranked_missing_df['_missing_rate_numeric'].rank(method='min', ascending=True).astype(int)
                st.dataframe(ranked_missing_df[['Rank', 'branch', 'done rate', 'missing rate']].reset_index(drop=True), use_container_width=True)
                if len(ranked_missing_df) > 1:
                    rank_chart_cols = st.columns(2); top_n = min(10, len(ranked_missing_df))
                    with rank_chart_cols[0]: fig_top = create_bar_chart(ranked_missing_df.head(top_n), 'branch', chart_title=f"Top {top_n} (Lowest Missing)", sort_values_by='_missing_rate_numeric', sort_ascending=True); st.plotly_chart(fig_top, use_container_width=True) if fig_top else None
                    with rank_chart_cols[1]: fig_bot = create_bar_chart(ranked_missing_df.tail(top_n).sort_values('_missing_rate_numeric',ascending=False), 'branch', chart_title=f"Bottom {top_n} (Highest Missing)", sort_values_by='_missing_rate_numeric', sort_ascending=False); st.plotly_chart(fig_bot, use_container_width=True) if fig_bot else None
            else: 
                st.markdown("_Based on total count of issues/complaints. Lower count is better._")
                branch_counts_df = df_primary_period.groupby('branch').size().reset_index(name='Total Issues/Complaints').sort_values(by='Total Issues/Complaints', ascending=True)
                branch_counts_df['Rank'] = branch_counts_df['Total Issues/Complaints'].rank(method='min', ascending=True).astype(int)
                st.dataframe(branch_counts_df[['Rank', 'branch', 'Total Issues/Complaints']].reset_index(drop=True), use_container_width=True)
                if len(branch_counts_df) > 1:
                    rank_chart_cols = st.columns(2); top_n = min(10, len(branch_counts_df))
                    with rank_chart_cols[0]: fig_top = create_bar_chart(branch_counts_df.head(top_n), 'branch', chart_title=f"Top {top_n} (Best)", sort_values_by='Total Issues/Complaints', sort_ascending=True); st.plotly_chart(fig_top, use_container_width=True) if fig_top else None
                    with rank_chart_cols[1]: fig_bot = create_bar_chart(branch_counts_df.tail(top_n).sort_values('Total Issues/Complaints',ascending=False), 'branch', chart_title=f"Bottom {top_n} (Needs Improvement)", sort_values_by='Total Issues/Complaints', sort_ascending=False); st.plotly_chart(fig_bot, use_container_width=True) if fig_bot else None
        else: st.info("No data or branch info for rankings with current filters.")
else:
    st.info("No data matches the current filter criteria for the primary period.")

if enable_comparison and comparison_date_range_1 and comparison_date_range_2: 
    st.markdown("---"); st.header("📊 Period Comparison Results")
    df_comp1_all = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft) # sel_id was correct from base
    df_comp1 = df_comp1_all[(df_comp1_all['date'].dt.date >= comparison_date_range_1[0]) & (df_comp1_all['date'].dt.date <= comparison_date_range_1[1])].copy()
    df_comp2_all = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft) # sel_id was correct from base
    df_comp2 = df_comp2_all[(df_comp2_all['date'].dt.date >= comparison_date_range_2[0]) & (df_comp2_all['date'].dt.date <= comparison_date_range_2[1])].copy()
    p1_lab, p2_lab = f"P1 ({comparison_date_range_1[0]:%b %d}-{comparison_date_range_1[1]:%b %d})", f"P2 ({comparison_date_range_2[0]:%b %d}-{comparison_date_range_2[1]:%b %d})"
    
    if df_comp1.empty and df_comp2.empty: st.info("No data for comparison in either period.")
    else:
        # Missing Comparison
        df_comp1_miss_data = df_comp1[(df_comp1['upload_category'] == 'missing') & (df_comp1['report_type'] == 'performance')].copy()
        df_comp2_miss_data = df_comp2[(df_comp2['upload_category'] == 'missing') & (df_comp2['report_type'] == 'performance')].copy()
        if not df_comp1_miss_data.empty or not df_comp2_miss_data.empty:
            st.subheader("Missing Tasks Performance Comparison")
            _, df_miss_res_c1 = display_missing_performance_dashboard(df_comp1_miss_data, {}, comparison_date_range_1, f"({p1_lab})")
            st.markdown("---"); _, df_miss_res_c2 = display_missing_performance_dashboard(df_comp2_miss_data, {}, comparison_date_range_2, f"({p2_lab})")
            if not df_miss_res_c1.empty and not df_miss_res_c2.empty:
                df_miss_comp_chart = pd.merge(df_miss_res_c1[['branch', '_done_rate_numeric']].rename(columns={'_done_rate_numeric': p1_lab}), df_miss_res_c2[['branch', '_done_rate_numeric']].rename(columns={'_done_rate_numeric': p2_lab}), on='branch', how='outer').fillna(0).melt(id_vars='branch', var_name='Period', value_name='Done Rate (%)')
                if not df_miss_comp_chart.empty: fig_m_comp = px.bar(df_miss_comp_chart, x='branch', y='Done Rate (%)', color='Period', barmode='group', title='Missing Tasks: Done Rate Comparison'); fig_m_comp.update_layout(yaxis_ticksuffix="%"); st.plotly_chart(fig_m_comp, use_container_width=True)
            st.markdown("---")
        
        # Complaints Comparison (Adapted from your provided code structure)
        df_comp1_complaints = df_comp1[(df_comp1['upload_category'] == 'complaints') & (df_comp1['report_type'] == 'performance')].copy()
        df_comp2_complaints = df_comp2[(df_comp2['upload_category'] == 'complaints') & (df_comp2['report_type'] == 'performance')].copy()
        if not df_comp1_complaints.empty or not df_comp2_complaints.empty:
            st.subheader("Complaints Performance Comparison")
            # This section requires adapting the logic from display_complaints_performance_dashboard
            # to handle two dataframes (df_comp1_complaints, df_comp2_complaints) and create comparative charts.
            # This involves:
            # 1. Parsing details for both.
            # 2. Adding a 'period_label' to each.
            # 3. Concatenating them.
            # 4. Calling create_bar_chart/create_pie_chart with the combined dataframe and 'period_label' as color.
            # The following is a conceptual outline:
            parsed_c1 = df_comp1_complaints['issues'].apply(parse_complaint_details) if not df_comp1_complaints.empty else pd.DataFrame()
            df_c1_parsed = pd.concat([df_comp1_complaints.reset_index(drop=True), parsed_c1.reset_index(drop=True)], axis=1)
            if not df_c1_parsed.empty: df_c1_parsed['period_label'] = p1_lab

            parsed_c2 = df_comp2_complaints['issues'].apply(parse_complaint_details) if not df_comp2_complaints.empty else pd.DataFrame()
            df_c2_parsed = pd.concat([df_comp2_complaints.reset_index(drop=True), parsed_c2.reset_index(drop=True)], axis=1)
            if not df_c2_parsed.empty: df_c2_parsed['period_label'] = p2_lab
            
            # Sanitize multi-value columns for both parsed dataframes...
            # ... (loop through MULTI_VALUE_COMPLAINT_COLS and apply _sanitize_and_split_elements_comp_local as in previous full code)

            df_combined_comp_compl = pd.concat([df for df in [df_c1_parsed, df_c2_parsed] if not df.empty], ignore_index=True)
            
            if not df_combined_comp_compl.empty:
                # Example for Complaint Type comparison:
                # df_type_comp_exploded = df_combined_comp_compl.explode('Complaint Type').dropna(subset=['Complaint Type'])
                # ... create_bar_chart(df_type_comp_exploded, 'Complaint Type', ...)
                st.info("Full period comparison logic for Complaints details needs to be implemented here based on the combined dataframe.")

        # General Issues Comparison (Excluding Missing and Complaints)
        df_comp1_gen_issues = df_comp1[~((df_comp1['upload_category'] == 'complaints') & (df_comp1['report_type'] == 'performance')) & ~((df_comp1['upload_category'] == 'missing') & (df_comp1['report_type'] == 'performance'))].copy()
        df_comp2_gen_issues = df_comp2[~((df_comp2['upload_category'] == 'complaints') & (df_comp2['report_type'] == 'performance')) & ~((df_comp2['upload_category'] == 'missing') & (df_comp2['report_type'] == 'performance'))].copy()
        if not df_comp1_gen_issues.empty or not df_comp2_gen_issues.empty:
            st.subheader("General Issues Comparison")
            st.markdown("_(Excluding Complaints & Missing Performance data shown above)_")
            # ... (This would mirror the structure of complaints comparison: add period_label, concat, then chart)
            st.info("Full period comparison logic for General Issues needs to be implemented here.")

st.sidebar.subheader("Downloads")
# --- Downloads Section (Adapted for Missing Data) ---
is_primary_data_purely_complaints_check = False 
is_primary_data_purely_missing_check = False    

if 'df_primary_period' in locals() and not df_primary_period.empty:
    is_purely_complaints_check = ((df_primary_period['upload_category'] == 'complaints').all() and (df_primary_period['report_type'] == 'performance').all() and df_primary_period['upload_category'].nunique() == 1 and df_primary_period['report_type'].nunique() == 1)
    is_purely_missing_check = ((df_primary_period['upload_category'] == 'missing').all() and (df_primary_period['report_type'] == 'performance').all() and df_primary_period['upload_category'].nunique() == 1 and df_primary_period['report_type'].nunique() == 1) 
    is_complaints_subset_displayed = not is_purely_complaints_check and not is_purely_missing_check and not df_primary_period[(df_primary_period['upload_category'] == 'complaints') & (df_primary_period['report_type'] == 'performance')].empty 
    is_missing_subset_displayed = not is_purely_complaints_check and not is_purely_missing_check and not df_primary_period[(df_primary_period['upload_category'] == 'missing') & (df_primary_period['report_type'] == 'performance')].empty 

    st.sidebar.markdown("Primary Period Data:")
    try: # CSV Primary
        csv_data_primary = df_primary_period.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.sidebar.download_button("Download Primary (CSV)", csv_data_primary, f"primary_data_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.csv", "text/csv", key="download_csv_primary")
    except Exception as e: st.sidebar.error(f"Primary CSV Error: {e}")
    
    try: # Excel Primary
        output_excel = io.BytesIO()
        df_primary_excel_export = df_primary_period.copy()
        excel_file_suffix = "data"
        if is_purely_complaints_check:
            excel_file_suffix = "complaints_data"
            parsed_details_excel = df_primary_excel_export['issues'].apply(parse_complaint_details)
            df_primary_excel_export = pd.concat([df_primary_excel_export.reset_index(drop=True).drop(columns=['issues'], errors='ignore'), parsed_details_excel.reset_index(drop=True)], axis=1)
            df_primary_excel_export.rename(columns={'Type': 'Complaint Type', 'Product': 'Product Complained About', 'Quality Detail': 'Quality Issue Detail', 'Order Error': 'Order Error Detail'}, inplace=True)
            for col_name_excel in MULTI_VALUE_COMPLAINT_COLS:
                if col_name_excel in df_primary_excel_export.columns: df_primary_excel_export[col_name_excel] = df_primary_excel_export[col_name_excel].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        elif is_purely_missing_check and not df_missing_perf_results_primary.empty: # MODIFIED
            excel_file_suffix = "missing_perf_summary"
            df_primary_excel_export = df_missing_perf_results_primary[['branch', 'done rate', 'missing rate']].copy()

        with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer: df_primary_excel_export.to_excel(writer, index=False, sheet_name='PrimaryData')
        excel_data = output_excel.getvalue()
        st.sidebar.download_button(label=f"Download Primary ({excel_file_suffix.replace('_',' ').title()}) (Excel)", data=excel_data, file_name=f"primary_{excel_file_suffix}_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_primary_{excel_file_suffix}_xlsx")
    except Exception as e: st.sidebar.error(f"Primary Excel Error: {e}")

    active_pdf_visuals_type = None; current_figs_for_pdf = {}; pdf_visual_button_label = "Prepare Visuals PDF"
    if is_purely_complaints_check: active_pdf_visuals_type = "complaints_visuals_primary"; current_figs_for_pdf = figs_complaints_primary; pdf_visual_button_label = "Prepare Complaints Visuals PDF"
    elif is_purely_missing_check: active_pdf_visuals_type = "missing_visuals_primary"; current_figs_for_pdf = figs_missing_primary; pdf_visual_button_label = "Prepare Missing Perf. Visuals PDF"
    else: active_pdf_visuals_type = "general_or_combined_visuals"; current_figs_for_pdf = figs_primary.copy(); pdf_visual_button_label = "Prepare Combined Visuals PDF" if (is_complaints_subset_displayed or is_missing_subset_displayed) else "Prepare General Visuals PDF"
    
    if st.sidebar.button(pdf_visual_button_label, key=f"prep_{active_pdf_visuals_type}_pdf"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        elif not current_figs_for_pdf or not any(isinstance(fig, go.Figure) for fig in current_figs_for_pdf.values()):
            if active_pdf_visuals_type == "missing_visuals_primary" and f'missing_performance_table_df(Primary_Period)' in current_figs_for_pdf: st.sidebar.warning("Missing Perf table displayed directly. No separate charts for PDF.")
            else: st.sidebar.warning("No chart visuals to generate PDF.")
        else:
            with st.spinner("Generating Visuals PDF..."):
                html_content = f"<html><head><meta charset='utf-8'><title>Visuals Report</title><style>body{{font-family:Arial,sans-serif;margin:20px}}h1,h2{{text-align:center;color:#333;page-break-after:avoid}}img{{display:block;margin-left:auto;margin-right:auto;max-width:650px;height:auto;border:1px solid #ccc;padding:5px;margin-bottom:25px;page-break-inside:avoid}}@media print{{*{{-webkit-print-color-adjust:exact !important;color-adjust:exact !important;print-color-adjust:exact !important}}body{{background-color:white !important}}}}</style></head><body>"
                report_title_pdf = pdf_visual_button_label.replace("Prepare ", "").replace(" PDF", "")
                html_content += f"<h1>{report_title_pdf}</h1><h2>Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}</h2>"
                ordered_keys = []; has_charts_to_render = False
                if active_pdf_visuals_type == "complaints_visuals_primary": ordered_keys = ["Complaint_Type", "Product_Complained_About", "Quality_Issue_Detail", "Order_Error_Detail", "Complaints_by_Branch", "Complaints_Trend"]
                elif active_pdf_visuals_type == "missing_visuals_primary": ordered_keys = [k for k,v in current_figs_for_pdf.items() if isinstance(v, go.Figure)]
                else: # general_or_combined
                    gen_order = ["Branch_Issues", "Area_Manager", "Report_Type", "Category", "Shift_Values", "Trend"]
                    sub_compl_order = [f"Subset_Complaints_{k}" for k in ["Complaint_Type", "Product_Complained_About", "Quality_Issue_Detail", "Order_Error_Detail", "Complaints_by_Branch", "Complaints_Trend"]]
                    sub_miss_order = [k for k in current_figs_for_pdf if k.startswith("Subset_Missing_") and isinstance(current_figs_for_pdf[k], go.Figure)]
                    ordered_keys = [k for k in gen_order if k in current_figs_for_pdf and isinstance(current_figs_for_pdf[k],go.Figure)] + \
                                   [k for k in sub_compl_order if k in current_figs_for_pdf and isinstance(current_figs_for_pdf[k],go.Figure)] + sub_miss_order
                for title_key in ordered_keys:
                    fig_obj_cand = current_figs_for_pdf.get(title_key)
                    if fig_obj_cand and isinstance(fig_obj_cand, go.Figure):
                        has_charts_to_render = True; img_bytes = fig_obj_cand.to_image(format='png', engine='kaleido', scale=1.2, width=700, height=450)
                        b64_img = base64.b64encode(img_bytes).decode(); chart_title_actual = fig_obj_cand.layout.title.text or title_key.replace("_"," ")
                        html_content += f"<h2>{chart_title_actual}</h2><img src='data:image/png;base64,{b64_img}' alt='{chart_title_actual}'/>"
                if not has_charts_to_render: st.sidebar.warning("No chart figures found to include in PDF.")
                else:
                    html_content += "</body></html>"; pdf_bytes = generate_pdf(html_content, wk_path=wk_path)
                    if pdf_bytes: st.session_state[f'pdf_data_{active_pdf_visuals_type}'] = pdf_bytes; st.sidebar.success("Visuals PDF ready.")
                    else: st.session_state.pop(f'pdf_data_{active_pdf_visuals_type}', None)
    if f'pdf_data_{active_pdf_visuals_type}' in st.session_state and st.session_state[f'pdf_data_{active_pdf_visuals_type}']:
        dl_fn_prefix_vis = active_pdf_visuals_type.replace("_primary","").replace("_visuals","").replace("_or_","/")
        st.sidebar.download_button(f"Download {pdf_visual_button_label.replace('Prepare ','')}", st.session_state[f'pdf_data_{active_pdf_visuals_type}'], f"{dl_fn_prefix_vis}_visuals_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.pdf", "application/pdf", key=f"action_dl_{active_pdf_visuals_type}_pdf", on_click=lambda: st.session_state.pop(f'pdf_data_{active_pdf_visuals_type}', None))

    if st.sidebar.button("Prepare Data Table PDF (Primary)", key="prep_dashboard_pdf_primary"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        else:
            with st.spinner("Generating Data Table PDF..."):
                df_pdf_final = df_primary_period.copy(); pdf_title_suffix = "Data"; html_table_content = ""
                if is_purely_complaints_check: 
                    pdf_title_suffix = "Complaints Data"; parsed_pdf = df_pdf_final['issues'].apply(parse_complaint_details)
                    df_pdf_final = pd.concat([df_pdf_final.reset_index(drop=True).drop(columns=['issues'],errors='ignore'), parsed_pdf.reset_index(drop=True)],axis=1)
                    df_pdf_final.rename(columns={'Type':'Complaint Type','Product':'Product Complained About','Quality Detail':'Quality Issue Detail','Order Error':'Order Error Detail'},inplace=True)
                    pdf_table_cols = ['date','branch','code','Complaint Type','Product Complained About','Quality Issue Detail','Order Error Detail']
                    for col_pdf in MULTI_VALUE_COMPLAINT_COLS:
                        if col_pdf in df_pdf_final.columns: df_pdf_final[col_pdf] = df_pdf_final[col_pdf].apply(lambda x: ', '.join(x) if isinstance(x,list) else x)
                elif is_purely_missing_check and not df_missing_perf_results_primary.empty:
                    pdf_title_suffix = "Missing Performance Summary"
                    # Use the Styler method to get HTML for missing performance table
                    df_styled_missing_pdf = df_missing_perf_results_primary[['branch', 'done rate', 'missing rate', '_done_rate_numeric']].copy()
                    html_table_content = df_styled_missing_pdf.style.apply(lambda row: style_row(row) if '_done_rate_numeric' in row else [''] * 2, axis=1, subset=['done rate', 'missing rate']) \
                        .set_properties(**{'text-align': 'left', 'min-width': '150px', 'font-weight': 'bold'}, subset=['branch']) \
                        .set_properties(**{'text-align': 'right'}, subset=['done rate', 'missing rate']) \
                        .set_table_styles([{'selector': 'th', 'props': 'background-color: #E8E8E8; text-align: center; font-weight: bold; padding: 5px;'}, 
                                           {'selector': 'td', 'props': 'padding: 5px; border: 1px solid #ddd;'},
                                           {'selector': 'thead th:first-child', 'props': 'text-align: left;'}]) \
                        .hide(axis='index').to_html(columns=['branch', 'done rate', 'missing rate']) # Render only desired columns
                else: 
                    pdf_table_cols = ['date','branch','report_type','upload_category','issues','area_manager','code']
                    if 'shift' in df_pdf_final.columns and df_pdf_final['shift'].notna().any(): pdf_table_cols.append('shift')
                    if 'upload_category' in df_pdf_final.columns and 'report_type' in df_pdf_final.columns:
                        cond_pdf = (df_pdf_final['report_type']=='issues') & (df_pdf_final['upload_category']=='CCTV'); df_pdf_final.loc[cond_pdf,'report_type'] = 'CCTV issues'
                
                if not html_table_content: # If not already set by missing_perf
                    pdf_table_cols_exist = [col for col in pdf_table_cols if col in df_pdf_final.columns]
                    df_pdf_to_render = df_pdf_final[pdf_table_cols_exist].copy()
                    if 'date' in df_pdf_to_render.columns: df_pdf_to_render['date'] = df_pdf_to_render['date'].dt.strftime('%Y-%m-%d')
                    html_table_content = df_pdf_to_render.to_html(index=False, classes="dataframe", border=0)

                html_full = f"<head><meta charset='utf-8'><title>Data Table Report</title><style>body{{font-family:Arial,sans-serif;margin:20px}}h1,h2{{text-align:center;color:#333;page-break-after:avoid}}table{{border-collapse:collapse;width:100%;margin-top:15px;font-size:0.8em;page-break-inside:auto}}tr{{page-break-inside:avoid;page-break-after:auto}}th,td{{border:1px solid #ddd;padding:6px;text-align:left;word-wrap:break-word}}th{{background-color:#f2f2f2}}.dataframe tbody tr:nth-of-type(even){{background-color:#f9f9f9}}@media print{{*{{-webkit-print-color-adjust:exact !important;color-adjust:exact !important;print-color-adjust:exact !important}}body{{background-color:white !important}}}}</style></head><body>"
                html_full += f"<h1>{pdf_title_suffix} Report</h1><h2>Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}</h2>"
                if not is_purely_missing_check: html_full += f"<p><strong>Total Records:</strong> {len(df_pdf_final if not is_purely_complaints_check else df_pdf_to_render)}</p>"
                html_full += html_table_content + "</body></html>"
                pdf_bytes = generate_pdf(html_full, wk_path=wk_path)
                if pdf_bytes: st.session_state.pdf_dashboard_primary_data = pdf_bytes; st.sidebar.success(f"{pdf_title_suffix} PDF (Primary) ready.")
                else: st.session_state.pop('pdf_dashboard_primary_data', None)
    if 'pdf_dashboard_primary_data' in st.session_state and st.session_state.pdf_dashboard_primary_data:
        pdf_dl_fn_suffix_tbl = "complaints_table" if is_purely_complaints_check else ("missing_perf_table" if is_purely_missing_check else "data_table")
        pdf_dl_label_tbl = "Complaints Table" if is_purely_complaints_check else ("Missing Perf. Table" if is_purely_missing_check else "Data Table")
        st.sidebar.download_button(f"Download {pdf_dl_label_tbl} PDF (Primary)", st.session_state.pdf_dashboard_primary_data, f"{pdf_dl_fn_suffix_tbl}_report_primary_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.pdf", "application/pdf", key="action_dl_dashboard_pdf_primary", on_click=lambda: st.session_state.pop('pdf_dashboard_primary_data', None))
else: st.sidebar.info("No primary period data to download.")

if enable_comparison and comparison_date_range_1 and comparison_date_range_2: # Comparison Downloads
    st.sidebar.markdown("Comparison Period Data (CSV):")
    if 'df_comp1' in locals() and not df_comp1.empty: # Use df_comp1, df_comp2 as defined in comparison logic
        try: csv_c1 = df_comp1.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'); st.sidebar.download_button(f"Download P1 ({comparison_date_range_1[0]:%b %d}-{comparison_date_range_1[1]:%b %d})", csv_c1, f"comp_p1_{comparison_date_range_1[0]:%Y%m%d}-{comparison_date_range_1[1]:%Y%m%d}.csv", "text/csv", key="dl_csv_comp1")
        except Exception as e: st.sidebar.error(f"P1 CSV Error: {e}")
    else: st.sidebar.caption(f"No data for P1 ({comparison_date_range_1[0]:%b %d}-{comparison_date_range_1[1]:%b %d})")
    if 'df_comp2' in locals() and not df_comp2.empty:
        try: csv_c2 = df_comp2.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'); st.sidebar.download_button(f"Download P2 ({comparison_date_range_2[0]:%b %d}-{comparison_date_range_2[1]:%b %d})", csv_c2, f"comp_p2_{comparison_date_range_2[0]:%Y%m%d}-{comparison_date_range_2[1]:%Y%m%d}.csv", "text/csv", key="dl_csv_comp2")
        except Exception as e: st.sidebar.error(f"P2 CSV Error: {e}")
    else: st.sidebar.caption(f"No data for P2 ({comparison_date_range_2[0]:%b %d}-{comparison_date_range_2[1]:%b %d})")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)")
