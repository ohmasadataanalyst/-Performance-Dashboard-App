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

# --- Helper function for normalizing project names ---
def normalize_project_name(name):
    if pd.isna(name):
        return ""
    return re.sub(r'\s+', ' ', str(name).lower().strip())

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
    "LB01": "Lubda Alaqeq Branch LB01", "LB02": "Alkhaleej Branch LB02",
    "QB01": "As Suwaidi Branch QB01", "QB02": "Al Nargis Branch QB02", "TW01": "Twesste B01 TW01",
    "FYJED B32": "FYJED B32"
}
BRANCH_SCHEMA_NORMALIZED = {str(k).strip().upper(): v for k, v in BRANCH_SCHEMA.items()}
for k_schema, v_schema in BRANCH_SCHEMA.items():
    normalized_v_schema_upper = v_schema.upper()
    if normalized_v_schema_upper not in BRANCH_SCHEMA_NORMALIZED:
        BRANCH_SCHEMA_NORMALIZED[normalized_v_schema_upper] = v_schema


PROJECT_FREQUENCIES_ORIGINAL = {
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
PROJECT_FREQUENCIES_NORMALIZED = {normalize_project_name(k): v for k, v in PROJECT_FREQUENCIES_ORIGINAL.items()}
ALL_DEFINED_PROJECT_NAMES_NORMALIZED = list(PROJECT_FREQUENCIES_NORMALIZED.keys())

DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS uploads (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT, file_type TEXT, category TEXT, submission_date TEXT, file BLOB)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id INTEGER, code TEXT, issues TEXT, branch TEXT, area_manager TEXT, date TEXT, report_type TEXT, shift TEXT, FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE)''')
conn.commit()

try:
    c.execute("PRAGMA table_info(uploads)")
    if 'submission_date' not in [col[1] for col in c.fetchall()]:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT"); conn.commit()
        if 'db_schema_updated_flag_uploads' not in st.session_state: st.session_state.db_schema_updated_flag_uploads = True
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not in st.session_state: st.session_state.db_critical_error_msg = f"Failed to update 'uploads' schema: {e}"
try:
    c.execute("PRAGMA table_info(issues)")
    if 'shift' not in [col[1] for col in c.fetchall()]:
        c.execute("ALTER TABLE issues ADD COLUMN shift TEXT"); conn.commit()
        if 'db_schema_updated_flag_issues' not in st.session_state: st.session_state.db_schema_updated_flag_issues = True
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not in st.session_state: st.session_state.db_critical_error_msg = f"Failed to update 'issues' schema: {e}"

db_admin = { "abdalziz alsalem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvpLxRumSduEte8MDAPkOnuXMdnW", "omar salah": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy", "omarsalah":b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy", "ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEn.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG", "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe", "mohamedhattab":b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe" }
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
MULTI_VALUE_COMPLAINT_COLS = ['Complaint Type', 'Quality Issue Detail', 'Order Error Detail']
TOP_N_GENERAL_ISSUES_COMPARISON = 15

COMPLAINT_CLOSURE_EXCEL_AM_COL_NAME = 'مدير المنطقة المسؤول'
COMPLAINT_CLOSURE_EXCEL_STATUS_COL_NAME = 'مدى الاجراء المتخذ'
COMPLAINT_CLOSURE_EXCEL_DATE_COL_NAME = 'date submitted'
CLOSURE_REPORT_TYPE_NAME = 'اغلاق الشكاوي'

CLOSURE_STATUS_ORDER = [
    'غير صحيح', 'غير مكتمل', 'لايوجد اجراء اداري',
    'لايوجد اجراء اداري, لايوجد اجراء تشغيلي', 'لايوجد اجراء تشغيلي', 'مكتمل'
]
CLOSURE_COMPLETED_STATUS = 'مكتمل'
CLOSURE_STATUS_COLORS = {
    'مكتمل': '#4CAF50',
    'لايوجد اجراء تشغيلي': '#2196F3',
    'لايوجد اجراء اداري, لايوجد اجراء تشغيلي': '#9C27B0',
    'لايوجد اجراء اداري': '#FFC107',
    'غير مكتمل': '#FF9800',
    'غير صحيح': '#F44336'
}


if 'db_critical_error_msg' in st.session_state: st.error(f"DB Startup Error: {st.session_state.db_critical_error_msg}"); del st.session_state.db_critical_error_msg
if 'db_schema_updated_flag_uploads' in st.session_state and st.session_state.db_schema_updated_flag_uploads: st.toast("DB 'uploads' schema updated.", icon="ℹ️"); st.session_state.db_schema_updated_flag_uploads = False
if 'db_schema_updated_flag_issues' in st.session_state and st.session_state.db_schema_updated_flag_issues: st.toast("DB 'issues' schema updated.", icon="ℹ️"); st.session_state.db_schema_updated_flag_issues = False

LOGO_PATH = "company_logo.png"

def check_login():
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None
    if not st.session_state.authenticated:
        c1, c2 = st.columns([1,5]);
        with c1:
            try: st.image(LOGO_PATH, width=100)
            except: pass
        with c2: st.title("📊 Login - Performance Dashboard")
        st.subheader("Please log in")
        with st.form("login_form"):
            un = st.text_input("Full Name:", key="auth_username_login").strip()
            pw = st.text_input("Password:", type="password", key="auth_password_login")
            sub = st.form_submit_button("Login")
            if sub:
                un_low = un.lower()
                admin_hpw = db_admin.get(un_low) or db_admin.get(un_low.replace(" ", ""))
                if admin_hpw and bcrypt.checkpw(pw.encode('utf-8'), admin_hpw): st.session_state.authenticated, st.session_state.user_name, st.session_state.user_role = True, un, 'admin'; st.rerun()
                elif un_low in view_only and pw: st.session_state.authenticated, st.session_state.user_name, st.session_state.user_role = True, un, 'view_only'; st.rerun()
                elif un_low in view_only and not pw: st.error("Password needed for view-only.")
                elif un or pw: st.error("Invalid credentials.")
                else: st.info("Enter credentials.")
        return False
    return True

if not check_login(): st.stop()

c1_mt, c2_mt = st.columns([1, 5])
with c1_mt:
    try: st.image(LOGO_PATH, width=100)
    except Exception as e: st.error(f"Logo error: {e}")
with c2_mt: st.title("📊 Classic Dashboard for Performance")


st.sidebar.success(f"Logged in: {st.session_state.get('user_name', 'N/A').title()} ({st.session_state.get('user_role', 'N/A')})")
if st.sidebar.button("Logout", key="logout_button_main"): st.session_state.authenticated, st.session_state.user_name, st.session_state.user_role = False, None, None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.session_state.get('user_name', 'Unknown User')

def generate_pdf(html, wk_path=None):
    if not wk_path or wk_path == "not found": st.error("wkhtmltopdf path needed."); return None
    try:
        import pdfkit
        conf = pdfkit.configuration(wkhtmltopdf=wk_path)
        opts = {'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8", 'load-error-handling': 'ignore', 'load-media-error-handling': 'ignore', 'disable-smart-shrinking': None, 'zoom': '0.85'}
        return pdfkit.from_string(html, False, configuration=conf, options=opts)
    except Exception as e: st.error(f"PDF error: {e}"); return None

st.sidebar.header("🔍 Filters & Options")

if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("Set params, select Excel, date range, then upload.")
    sel_cat_admin = st.sidebar.selectbox("Category for upload", options=all_categories, key="admin_category_select")
    _current_admin_category_val = st.session_state.get("admin_category_select", all_categories[0] if all_categories else None)
    valid_ft_admin = category_file_types.get(_current_admin_category_val, [])
    sel_ft_admin = st.sidebar.selectbox("File type for upload", options=valid_ft_admin, key="admin_file_type_select", disabled=(not valid_ft_admin), help="Options change based on category.")
    st.sidebar.markdown("**Filter Excel Data by Date Range for this Import:**")
    imp_from_dt_val = st.sidebar.date_input("Import Data From Date:", value=date.today() - timedelta(days=7), key="import_from_date_upload")
    imp_to_dt_val = st.sidebar.date_input("Import Data To Date:", value=date.today(), key="import_to_date_upload")
    up_file = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    up_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if up_btn:
        st.sidebar.info(f"--- Upload: Cat='{st.session_state.get('admin_category_select')}', FileType='{st.session_state.get('admin_file_type_select')}' ---")

        final_cat_val = st.session_state.admin_category_select
        final_ft_val = st.session_state.admin_file_type_select
        imp_from = st.session_state.import_from_date_upload
        imp_to = st.session_state.import_to_date_upload
        req_ft = bool(category_file_types.get(final_cat_val, []))

        if req_ft and not final_ft_val: st.sidebar.error(f"File type needed for '{final_cat_val}'. Select and retry."); st.stop()
        if not up_file: st.sidebar.error("Select Excel file."); st.stop()
        if not imp_from or not imp_to: st.sidebar.error("Select import date range."); st.stop()
        if imp_from > imp_to: st.sidebar.error("Import 'From Date' > 'To Date'."); st.stop()
        if not req_ft: final_ft_val = None

        file_data = up_file.getvalue()
        timestamp_now = datetime.now().isoformat()
        up_sub_date_str = imp_from.isoformat()

        try:
            c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?', (up_file.name, current_user, final_ft_val, final_cat_val, up_sub_date_str))
            if c.fetchone()[0] > 0: st.sidebar.warning(f"Duplicate upload batch for '{up_file.name}' seems to exist. Processing.")

            df_excel = pd.read_excel(io.BytesIO(file_data), header=0)
            df_excel.columns = [str(col).strip().lower().replace('\n', ' ').replace('\r', '') for col in df_excel.columns]

            EXCEL_CODE_COL = 'code'; STD_EXCEL_ISSUES_COL = 'issues'; STD_EXCEL_BRANCH_COL = 'branch'
            STD_EXCEL_AM_COL = 'area manager'; STD_EXCEL_DATE_COL = 'date'
            CCTV_VIOLATION_COL = 'choose the violation - اختر المخالفه'; CCTV_SHIFT_COL = 'choose the shift - اختر الشفت'
            CCTV_DATE_COL = 'date submitted'; CCTV_BRANCH_COL = 'branch'; CCTV_AM_COL = 'area manager'
            COMP_BRANCH_COL = 'branch'; COMP_TYPE_COL = 'نوع الشكوى'; COMP_PROD_COL = 'الشكوى على اي منتج؟'
            COMP_QUAL_COL = 'فى حاله كانت الشكوى جوده برجاء تحديد نوع الشكوى'; COMP_ORDER_ERR_COL = 'فى حاله خطاء فى الطلب برجاء تحديد نوع الشكوى'
            COMP_DATE_COL = 'date'
            MISSING_PROJECT_COL = 'project'; MISSING_BRANCH_COL = 'branch'; MISSING_AM_COL = 'area manager'; MISSING_DATE_COL = 'date';

            req_cols_up = []
            date_col_excel = ''

            norm_cat = str(final_cat_val).lower().strip()
            norm_ft = str(final_ft_val).lower().strip() if final_ft_val else ""

            if norm_cat == 'cctv':
                req_cols_up = [EXCEL_CODE_COL, CCTV_VIOLATION_COL, CCTV_SHIFT_COL, CCTV_DATE_COL, CCTV_BRANCH_COL, CCTV_AM_COL]; date_col_excel = CCTV_DATE_COL
            elif norm_cat == 'complaints':
                if norm_ft == 'performance': req_cols_up = [COMP_BRANCH_COL, EXCEL_CODE_COL, COMP_TYPE_COL, COMP_PROD_COL, COMP_QUAL_COL, COMP_ORDER_ERR_COL, COMP_DATE_COL]; date_col_excel = COMP_DATE_COL
                elif norm_ft == CLOSURE_REPORT_TYPE_NAME.lower():
                    req_cols_up = [EXCEL_CODE_COL, STD_EXCEL_BRANCH_COL, COMPLAINT_CLOSURE_EXCEL_AM_COL_NAME.lower(), COMPLAINT_CLOSURE_EXCEL_STATUS_COL_NAME.lower(), COMPLAINT_CLOSURE_EXCEL_DATE_COL_NAME.lower()]
                    date_col_excel = COMPLAINT_CLOSURE_EXCEL_DATE_COL_NAME.lower()
                else: st.sidebar.error(f"Invalid file type '{final_ft_val}' for 'complaints'."); st.stop()
            elif norm_cat == 'missing':
                if norm_ft == 'performance':
                    req_cols_up = [MISSING_PROJECT_COL, EXCEL_CODE_COL, MISSING_BRANCH_COL, MISSING_AM_COL, MISSING_DATE_COL]; date_col_excel = MISSING_DATE_COL
                else: st.sidebar.error(f"Invalid file type '{final_ft_val}' for 'missing'."); st.stop()
            elif norm_cat == 'visits':
                req_cols_up = [EXCEL_CODE_COL, STD_EXCEL_BRANCH_COL, STD_EXCEL_AM_COL, STD_EXCEL_ISSUES_COL, STD_EXCEL_DATE_COL]; date_col_excel = STD_EXCEL_DATE_COL
            else:
                req_cols_up = [EXCEL_CODE_COL, STD_EXCEL_ISSUES_COL, STD_EXCEL_BRANCH_COL, STD_EXCEL_AM_COL, STD_EXCEL_DATE_COL]; date_col_excel = STD_EXCEL_DATE_COL

            missing_cols = [col for col in req_cols_up if col not in df_excel.columns]
            if missing_cols:
                missing_cols_str = ", ".join(missing_cols)
                st.sidebar.error(f"Excel for '{final_cat_val}/{final_ft_val or 'N/A'}' missing columns: {missing_cols_str}. Aborted.")
                st.sidebar.info(f"Excel columns found: {list(df_excel.columns)}")
                st.sidebar.info(f"Expected columns: {req_cols_up}"); st.stop()

            if not date_col_excel or date_col_excel not in df_excel.columns: st.sidebar.error(f"Date column '{date_col_excel}' not found or not defined."); st.stop()

            df_excel['parsed_date'] = pd.to_datetime(df_excel[date_col_excel], errors='coerce')
            original_row_count = len(df_excel)
            df_excel.dropna(subset=['parsed_date'], inplace=True)
            rows_dropped_na_date = original_row_count - len(df_excel)
            if rows_dropped_na_date > 0:
                st.sidebar.warning(f"Dropped {rows_dropped_na_date} rows due to unparseable dates in '{date_col_excel}'.")

            if df_excel.empty: st.sidebar.error("No valid data after attempting to parse dates."); st.stop()

            df_to_imp = df_excel[(df_excel['parsed_date'].dt.date >= imp_from) & (df_excel['parsed_date'].dt.date <= imp_to)].copy()

            if df_to_imp.empty:
                st.sidebar.error(f"No rows found within the selected import date range ({imp_from.strftime('%Y-%m-%d')} to {imp_to.strftime('%Y-%m-%d')}).")
                min_excel_dt_after_parse = df_excel['parsed_date'].min()
                max_excel_dt_after_parse = df_excel['parsed_date'].max()
                st.sidebar.info(f"Date range in (parsed) Excel: {min_excel_dt_after_parse.strftime('%Y-%m-%d') if pd.notna(min_excel_dt_after_parse) else 'N/A'} to {max_excel_dt_after_parse.strftime('%Y-%m-%d') if pd.notna(max_excel_dt_after_parse) else 'N/A'}")
                st.stop()

            c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)', (up_file.name, current_user, timestamp_now, final_ft_val, final_cat_val, up_sub_date_str, sqlite3.Binary(file_data)))
            up_id = c.lastrowid
            unmapped_branches = set(); inserted_count = 0

            for _, row_data in df_to_imp.iterrows():
                issue_dt_str = row_data['parsed_date'].strftime('%Y-%m-%d')
                iss_val, am_val_row, shift_val_row = "N/A", "N/A", None
                excel_branch_str = "Unknown Branch"; code_from_excel_col_direct = ""

                if norm_cat == 'complaints' and norm_ft == 'performance':
                    excel_branch_str = str(row_data.get(COMP_BRANCH_COL.lower(), "Unk Comp Branch"))
                    code_from_excel_col_direct = str(row_data.get(EXCEL_CODE_COL.lower(), "")).strip().upper()
                    am_val_row = "N/A - Complaints Performance"
                    details_list = [f"Type: {str(row_data.get(COMP_TYPE_COL.lower())).strip()}" if pd.notna(row_data.get(COMP_TYPE_COL.lower())) else None,
                                    f"Product: {str(row_data.get(COMP_PROD_COL.lower())).strip()}" if pd.notna(row_data.get(COMP_PROD_COL.lower())) else None,
                                    f"Quality Detail: {str(row_data.get(COMP_QUAL_COL.lower())).strip()}" if pd.notna(row_data.get(COMP_QUAL_COL.lower())) else None,
                                    f"Order Error: {str(row_data.get(COMP_ORDER_ERR_COL.lower())).strip()}" if pd.notna(row_data.get(COMP_ORDER_ERR_COL.lower())) else None]
                    iss_val = "; ".join(filter(None, details_list)) or "No specific complaint details"
                elif norm_cat == 'complaints' and norm_ft == CLOSURE_REPORT_TYPE_NAME.lower():
                    excel_branch_str = str(row_data.get(STD_EXCEL_BRANCH_COL.lower(), "Unk Closure Branch"))
                    code_from_excel_col_direct = str(row_data.get(EXCEL_CODE_COL.lower(), "")).strip().upper()
                    am_val_row = str(row_data.get(COMPLAINT_CLOSURE_EXCEL_AM_COL_NAME.lower(), "N/A"))
                    iss_val = str(row_data.get(COMPLAINT_CLOSURE_EXCEL_STATUS_COL_NAME.lower(), "N/A"))
                elif norm_cat == 'cctv':
                    excel_branch_str = str(row_data.get(CCTV_BRANCH_COL.lower(), "Unk CCTV Branch"))
                    code_from_excel_col_direct = str(row_data.get(EXCEL_CODE_COL.lower(), "")).strip().upper()
                    am_val_row = str(row_data.get(CCTV_AM_COL.lower(), "N/A"))
                    iss_val = str(row_data.get(CCTV_VIOLATION_COL.lower(), "N/A"))
                    shift_val_row = str(row_data.get(CCTV_SHIFT_COL.lower())) if pd.notna(row_data.get(CCTV_SHIFT_COL.lower())) else None
                elif norm_cat == 'missing' and norm_ft == 'performance':
                    excel_branch_str = str(row_data.get(MISSING_BRANCH_COL.lower(), "Unk Missing Branch")).strip()
                    code_from_excel_col_direct = str(row_data.get(EXCEL_CODE_COL.lower(), "")).strip().upper()
                    iss_val = normalize_project_name(row_data.get(MISSING_PROJECT_COL.lower(), "Unk Project"))
                    am_val_row = str(row_data.get(MISSING_AM_COL.lower(), "N/A")).strip()
                elif norm_cat == 'visits':
                    excel_branch_str = str(row_data.get(STD_EXCEL_BRANCH_COL.lower(), "Unk Visit Branch"))
                    code_from_excel_col_direct = str(row_data.get(EXCEL_CODE_COL.lower(), "")).strip().upper()
                    am_val_row = str(row_data.get(STD_EXCEL_AM_COL.lower(), "N/A - Visits"))
                    iss_val = str(row_data.get(STD_EXCEL_ISSUES_COL.lower(), "Visit Logged"))
                else:
                    excel_branch_str = str(row_data.get(STD_EXCEL_BRANCH_COL.lower(), "Unk Std Branch"))
                    code_from_excel_col_direct = str(row_data.get(EXCEL_CODE_COL.lower(), "")).strip().upper()
                    am_val_row = str(row_data.get(STD_EXCEL_AM_COL.lower(), "N/A"))
                    iss_val_raw = row_data.get(STD_EXCEL_ISSUES_COL.lower(), "N/A")
                    if norm_cat == 'operation-training':
                        iss_val = normalize_project_name(iss_val_raw)
                    else:
                        iss_val = str(iss_val_raw)

                std_branch_name = "Unknown Branch"; db_code_val = ""
                norm_excel_branch_name_str = excel_branch_str.strip().upper()

                extracted_code_from_branch_name_match = re.search(r'\b([A-Z0-9]{2,5})\b(?![A-Z0-9])', norm_excel_branch_name_str)
                extracted_code_from_branch_name = extracted_code_from_branch_name_match.group(1).upper() if extracted_code_from_branch_name_match else None

                if code_from_excel_col_direct and code_from_excel_col_direct in BRANCH_SCHEMA_NORMALIZED:
                    std_branch_name = BRANCH_SCHEMA_NORMALIZED[code_from_excel_col_direct]
                    db_code_val = code_from_excel_col_direct
                elif extracted_code_from_branch_name and extracted_code_from_branch_name in BRANCH_SCHEMA_NORMALIZED:
                    std_branch_name = BRANCH_SCHEMA_NORMALIZED[extracted_code_from_branch_name]
                    db_code_val = extracted_code_from_branch_name
                else:
                    match_found_by_full_name = False
                    for sc_code, sc_name in BRANCH_SCHEMA_NORMALIZED.items():
                        if norm_excel_branch_name_str == sc_name.upper():
                            std_branch_name = sc_name
                            db_code_val = sc_code
                            match_found_by_full_name = True
                            break
                    if not match_found_by_full_name:
                        if norm_excel_branch_name_str in BRANCH_SCHEMA_NORMALIZED:
                            std_branch_name = BRANCH_SCHEMA_NORMALIZED[norm_excel_branch_name_str]
                            db_code_val = norm_excel_branch_name_str
                            match_found_by_full_name = True

                    if not match_found_by_full_name:
                        std_branch_name = excel_branch_str
                        unmapped_code_attempt = code_from_excel_col_direct or extracted_code_from_branch_name or "N/A"
                        db_code_val = code_from_excel_col_direct or extracted_code_from_branch_name or ""
                        unmapped_branches.add(f"{excel_branch_str} (Code: {unmapped_code_attempt})")

                if not db_code_val and std_branch_name != "Unknown Branch" and std_branch_name != excel_branch_str:
                    for schema_key, schema_val_name in BRANCH_SCHEMA_NORMALIZED.items():
                        if std_branch_name.upper() == schema_val_name.upper():
                            db_code_val = schema_key
                            break

                db_code_val = db_code_val or ""

                c.execute('''INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type, shift) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (up_id, db_code_val, iss_val, std_branch_name, am_val_row, issue_dt_str, final_ft_val, shift_val_row))
                inserted_count += 1

            conn.commit()
            st.sidebar.success(f"Successfully imported {inserted_count} issues from '{up_file.name}'.")
            if unmapped_branches: st.sidebar.warning(f"Unmapped branches ({len(unmapped_branches)}): {', '.join(sorted(list(unmapped_branches)))}. Review schema or data.")
        except Exception as e: conn.rollback(); st.sidebar.error(f"Upload error: {e}. Rolled back."); st.exception(e)
        finally: st.rerun()

    st.sidebar.subheader("Manage Submissions")
    df_uploads_del = pd.read_sql('SELECT id, filename, category, file_type, submission_date FROM uploads ORDER BY submission_date DESC, id DESC', conn)
    del_opts_disp = [f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) SubDate: {r['submission_date'] or 'N/A'}" for i,r in df_uploads_del.iterrows()]
    del_choice = st.sidebar.selectbox("🗑️ Delete Batch:", ['Select to Delete'] + del_opts_disp, key="del_batch_sel")
    if del_choice != 'Select to Delete':
        del_id = int(del_choice.split(' - ')[0])
        if st.sidebar.button(f"Confirm Del Batch #{del_id}", key=f"conf_del_{del_id}", type="primary"):
            try: c.execute('DELETE FROM uploads WHERE id=?', (del_id,)); conn.commit(); st.sidebar.success(f"Deleted {del_id}."); st.rerun()
            except Exception as e: conn.rollback(); st.sidebar.error(f"Delete failed: {e}")

    st.sidebar.subheader("Database Management")
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as fp: db_bytes = fp.read()
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.sidebar.download_button("Download DB Backup", db_bytes, f"issues_backup_{ts_str}.db", "application/vnd.sqlite3", key="dl_db_direct")

default_wk_path = shutil.which('wkhtmltopdf')
wk_path_value = default_wk_path if default_wk_path else 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path (for PDF generation):", value=wk_path_value)


df_uploads_raw_main = pd.read_sql('SELECT id, filename, category, file_type, submission_date FROM uploads ORDER BY submission_date DESC, id DESC', conn)
scope_opts_main = ['All uploads'] + [f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) SubDate: {r['submission_date'] or 'N/A'}" for i,r in df_uploads_raw_main.iterrows()]
sel_display = st.sidebar.selectbox("Analyze Upload Batch:", scope_opts_main, key="sel_up_scope_main")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

df_all_issues = pd.read_sql('SELECT i.*, u.category as upload_category, u.id as upload_id_col FROM issues i JOIN uploads u ON u.id = i.upload_id', conn, parse_dates=['date'])
if df_all_issues.empty: st.warning("No issues data in DB."); st.stop()

min_overall_date = df_all_issues['date'].min().date() if not df_all_issues['date'].isnull().all() else date.today()
max_overall_date = df_all_issues['date'].max().date() if not df_all_issues['date'].isnull().all() else date.today()
if min_overall_date > max_overall_date: max_overall_date = min_overall_date

primary_date_range_val = st.sidebar.date_input("Primary Date Range (Issue Dates):", value=[min_overall_date, max_overall_date], min_value=min_overall_date, max_value=max_overall_date, key="primary_date_range_filter")
primary_date_range = [min_overall_date, max_overall_date]
if primary_date_range_val and len(primary_date_range_val) == 2:
    primary_date_range = [primary_date_range_val[0], primary_date_range_val[1]] if primary_date_range_val[0] <= primary_date_range_val[1] else [primary_date_range_val[1], primary_date_range_val[0]]
elif primary_date_range_val: st.sidebar.warning("Invalid primary date range, defaulting.")

branch_opts = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist()); sel_branch = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")
cat_opts = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist()); sel_cat = st.sidebar.multiselect("Category (from Upload Batch):", cat_opts, default=['All'], key="category_filter")
am_opts = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist()); sel_am = st.sidebar.multiselect("Area Manager:", am_opts, default=['All'], key="area_manager_filter")
unique_report_types = df_all_issues['report_type'].astype(str).unique()
filtered_report_types = sorted([rt for rt in unique_report_types if rt.lower() not in ['none', 'nan', '']])
file_type_filter_opts = ['All'] + filtered_report_types
sel_ft = st.sidebar.multiselect("File Type (from Upload Batch):", file_type_filter_opts, default=['All'], key="file_type_filter")

st.sidebar.subheader("📊 Period Comparison")
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox")
comparison_date_range_1, comparison_date_range_2 = None, None
if enable_comparison:
    st.sidebar.markdown("Comparison Period 1:")
    safe_p1_end = min(min_overall_date + timedelta(days=6), max_overall_date)
    comp_dr1_val = st.sidebar.date_input("Start & End (P1):", value=[min_overall_date, safe_p1_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period1_filter")
    if comp_dr1_val and len(comp_dr1_val) == 2 and comp_dr1_val[0] <= comp_dr1_val[1]: comparison_date_range_1 = comp_dr1_val
    else: st.sidebar.warning("P1: Invalid range."); comparison_date_range_1 = None
    if comparison_date_range_1:
        st.sidebar.markdown("Comparison Period 2:")
        def_p2_start = min(comparison_date_range_1[1] + timedelta(days=1), max_overall_date)
        def_p2_end = min(def_p2_start + timedelta(days=6), max_overall_date)
        comp_dr2_val = st.sidebar.date_input("Start & End (P2):", value=[def_p2_start, def_p2_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period2_filter")
        if comp_dr2_val and len(comp_dr2_val) == 2 and comp_dr2_val[0] <= comp_dr2_val[1]: comparison_date_range_2 = comp_dr2_val
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
            if include_na_types:
                df_filtered = pd.concat([df_filtered_specific_types, df_filtered[is_na_report_type]]).drop_duplicates().reset_index(drop=True)
            else:
                na_like_mask = df_filtered['report_type'].isnull() | df_filtered['report_type'].astype(str).str.lower().isin(['none', 'nan', ''])
                df_filtered = df_filtered_specific_types[~df_filtered_specific_types['report_type'].fillna('').astype(str).str.lower().isin(['none', 'nan', ''])].reset_index(drop=True)

    return df_filtered

df_temp_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)
df_primary_period = df_temp_filtered.copy()
if primary_date_range and len(primary_date_range) == 2:
    start_date_filt, end_date_filt = primary_date_range[0], primary_date_range[1]
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']):
        df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= start_date_filt) & (df_primary_period['date'].dt.date <= end_date_filt)]
    else:
        df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)
else:
    df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)

st.subheader(f"Filtered Data for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total records found in primary period: {len(df_primary_period)}")

COMPLAINTS_COLOR_SEQUENCE = px.colors.qualitative.Vivid

def create_bar_chart(df_source, group_col, title_suffix="", chart_title=None, color_sequence=None, barmode='group', sort_ascending=False, sort_values_by='count', color_discrete_map=None, y_axis_title='count', text_auto=False):
    final_title = chart_title if chart_title else f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col not in df_source.columns or df_source.empty: return None

    df_valid_data = df_source.copy()
    df_valid_data.dropna(subset=[group_col], inplace=True)
    df_valid_data[group_col] = df_valid_data[group_col].astype(str).str.strip()
    df_valid_data = df_valid_data[df_valid_data[group_col] != '']
    df_valid_data = df_valid_data[~df_valid_data[group_col].str.lower().isin(['nan', 'none', '<na>'])]

    fig = None
    if not df_valid_data.empty:
        if 'period_label' in df_valid_data.columns:
            data = df_valid_data.groupby([group_col, 'period_label']).size().reset_index(name='count')
            data = data.sort_values(by=[group_col, 'period_label'], ascending=[True, True])
            if not data.empty:
                fig = px.bar(data, x=group_col, y='count', color='period_label', barmode=barmode, title=final_title, template="plotly_white", color_discrete_sequence=color_sequence, color_discrete_map=color_discrete_map, text_auto=text_auto)
        else:
            if group_col in df_source.columns and sort_values_by in df_source.columns and group_col != sort_values_by:
                 data_to_plot = df_source.copy()
                 if pd.api.types.is_string_dtype(data_to_plot[sort_values_by]):
                     try:
                         data_to_plot[sort_values_by] = data_to_plot[sort_values_by].str.rstrip('%').astype(float)
                     except:
                         pass
                 data_to_plot[group_col] = data_to_plot[group_col].astype(str)
                 fig = px.bar(data_to_plot, x=group_col, y=sort_values_by, title=final_title, template="plotly_white", color_discrete_sequence=color_sequence, color_discrete_map=color_discrete_map, text_auto=text_auto)
                 if pd.api.types.is_numeric_dtype(data_to_plot[sort_values_by]):
                    ordered_categories = data_to_plot.sort_values(by=sort_values_by, ascending=sort_ascending)[group_col].tolist()
                    fig.update_xaxes(categoryorder='array', categoryarray=ordered_categories)
            else:
                data = df_valid_data.groupby(group_col).size().reset_index(name='count')
                data = data.sort_values(by='count', ascending=sort_ascending)
                if not data.empty:
                    fig = px.bar(data, x=group_col, y='count', title=final_title, template="plotly_white", color_discrete_sequence=color_sequence, color_discrete_map=color_discrete_map, text_auto=text_auto)
    if fig: fig.update_layout(yaxis_title=y_axis_title)
    return fig


def create_pie_chart(df_source, group_col, title_suffix="", chart_title=None, color_sequence=None, color_discrete_map=None):
    final_title = chart_title if chart_title else f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col not in df_source.columns or df_source.empty: return None

    df_valid_data = df_source.copy()
    df_valid_data.dropna(subset=[group_col], inplace=True)
    df_valid_data[group_col] = df_valid_data[group_col].astype(str).str.strip()
    df_valid_data = df_valid_data[df_valid_data[group_col] != '']
    df_valid_data = df_valid_data[~df_valid_data[group_col].str.lower().isin(['nan', 'none', '<na>'])]

    if not df_valid_data.empty:
        data = df_valid_data.groupby(group_col).size().reset_index(name='count')
        if not data.empty:
            return px.pie(data, names=group_col, values='count', title=final_title, hole=0.3, template="plotly_white", color_discrete_sequence=color_sequence, color_discrete_map=color_discrete_map)
    return None

def parse_complaint_details(issue_string):
    details = {'Type': [], 'Product': None, 'Quality Detail': [], 'Order Error': []}
    if not isinstance(issue_string, str): return pd.Series(details)
    def _get_value(pattern, text, is_multi_value=False):
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.group(1):
            value_str = match.group(1).strip()
            if value_str:
                return [s.strip() for s in value_str.split(',') if s.strip()] if is_multi_value else value_str
        return [] if is_multi_value else None
    details['Type'] = _get_value(r"Type:\s*(.*?)(?:;|$)", issue_string, is_multi_value=True)
    details['Product'] = _get_value(r"Product:\s*(.*?)(?:;|$)", issue_string, is_multi_value=False)
    details['Quality Detail'] = _get_value(r"Quality Detail:\s*(.*?)(?:;|$)", issue_string, is_multi_value=True)
    details['Order Error'] = _get_value(r"Order Error:\s*(.*?)(?:;|$)", issue_string, is_multi_value=True)
    return pd.Series(details)

def display_general_dashboard(df_data, figs_container):
    if df_data.empty: st.info("No data available for general performance analysis with current filters."); return figs_container
    chart_cols = st.columns(2)
    with chart_cols[0]:
        figs_container['Branch_Issues'] = create_bar_chart(df_data, 'branch', '(Primary)')
        if figs_container.get('Branch_Issues'): st.plotly_chart(figs_container['Branch_Issues'], use_container_width=True)
        else: st.caption("No data for Branch chart.")

        df_report_type_viz = df_data.copy()
        if 'upload_category' in df_report_type_viz.columns and 'report_type' in df_report_type_viz.columns:
            condition = (df_report_type_viz['report_type'].astype(str).str.lower() == 'issues') & \
                        (df_report_type_viz['upload_category'].astype(str).str.lower() == 'cctv')
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
        trend_data_primary['date'] = pd.to_datetime(trend_data_primary['date'])
        trend_data_primary = trend_data_primary.sort_values('date')
        if not trend_data_primary.empty:
            window_size = min(7, len(trend_data_primary)); window_size = max(2,window_size)
            trend_data_primary[f'{window_size}-Day MA'] = trend_data_primary['daily_issues'].rolling(window=window_size, center=True, min_periods=1).mean().round(1)

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=trend_data_primary['date'], y=trend_data_primary['daily_issues'],
                name='Daily Issues', marker_color='lightblue',
                hovertemplate="<b>%{x|%A, %b %d}</b><br>Issues: %{y}<extra></extra>"
            ))
            fig_trend.add_trace(go.Scatter(
                x=trend_data_primary['date'], y=trend_data_primary[f'{window_size}-Day MA'],
                name=f'{window_size}-Day Moving Avg.', mode='lines+markers',
                line=dict(color='royalblue', width=2), marker=dict(size=5),
                hovertemplate="<b>%{x|%A, %b %d}</b><br>Moving Avg: %{y:.1f}<extra></extra>"
            ))
            fig_trend.update_layout(
                title_text='Issues Trend (Primary Period - Based on Issue Dates)',
                xaxis_title='Date', yaxis_title='Number of Issues',
                template="plotly_white", hovermode="x unified", legend_title_text='Metric'
            )
            figs_container['Trend'] = fig_trend
            if figs_container.get('Trend'): st.plotly_chart(figs_container['Trend'], use_container_width=True)
        else: st.caption("No data for trend analysis.")

    if len(df_data) < 50 or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.subheader("Detailed Records (Primary Period - Filtered)")
        display_columns = ['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']
        if 'shift' in df_data.columns and df_data['shift'].notna().any(): display_columns.append('shift')

        df_display_primary = df_data[[col for col in display_columns if col in df_data.columns]].copy()

        if 'upload_category' in df_display_primary.columns and 'report_type' in df_display_primary.columns:
            condition_table = (df_display_primary['report_type'].astype(str).str.lower() == 'issues') & \
                              (df_display_primary['upload_category'].astype(str).str.lower() == 'cctv')
            df_display_primary.loc[condition_table, 'report_type'] = 'CCTV issues'

        if 'date' in df_display_primary.columns and pd.api.types.is_datetime64_any_dtype(df_display_primary['date']):
            df_display_primary['date'] = df_display_primary['date'].dt.strftime('%Y-%m-%d')
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
            else: st.info("No non-empty issue descriptions for 'Top Issues' (Primary).")
        else: st.info("No non-empty issue descriptions for 'Top Issues' (Primary).")
    else: st.info("Issue descriptions column ('issues') not available or empty.")
    return figs_container

def display_complaints_performance_dashboard(df_complaints_raw, figs_container):
    if df_complaints_raw.empty: st.info("No complaints data for performance with current filters."); return figs_container

    parsed_details = df_complaints_raw['issues'].apply(parse_complaint_details)
    df_complaints = pd.concat([df_complaints_raw.reset_index(drop=True).drop(columns=['issues'], errors='ignore'), parsed_details.reset_index(drop=True)], axis=1)
    df_complaints.rename(columns={'Type': 'Complaint Type', 'Product': 'Product Complained About',
                                'Quality Detail': 'Quality Issue Detail', 'Order Error': 'Order Error Detail'}, inplace=True)

    for col_name in MULTI_VALUE_COMPLAINT_COLS:
        if col_name in df_complaints.columns:
            def _sanitize_and_split_elements(entry_list_or_str):
                if not isinstance(entry_list_or_str, list):
                    if isinstance(entry_list_or_str, str): entry_list_or_str = [entry_list_or_str]
                    else: return []

                final_elements = []
                for element in entry_list_or_str:
                    if isinstance(element, str):
                        final_elements.extend([s.strip() for s in element.split(',') if s.strip()])
                    elif element is not None :
                        final_elements.append(str(element).strip())
                return final_elements
            df_complaints[col_name] = df_complaints[col_name].apply(_sanitize_and_split_elements)

    col1, col2 = st.columns(2)
    with col1:
        df_type_chart_data = df_complaints.explode('Complaint Type').dropna(subset=['Complaint Type'])
        df_type_chart_data = df_type_chart_data[df_type_chart_data['Complaint Type'] != '']
        figs_container['Complaint_Type'] = create_bar_chart(df_type_chart_data, 'Complaint Type', chart_title="Complaints by Type", color_sequence=COMPLAINTS_COLOR_SEQUENCE, barmode='stack')
        if figs_container.get('Complaint_Type'): st.plotly_chart(figs_container['Complaint_Type'], use_container_width=True)
        else: st.caption("No data for Complaint Type chart.")

        df_product_chart_source = df_complaints[df_complaints['Product Complained About'].notna() & (df_complaints['Product Complained About'] != '') & (df_complaints['Product Complained About'].str.lower() != 'لا علاقة لها بالمنتج')].copy()
        if not df_product_chart_source.empty:
            figs_container['Product_Complained_About'] = create_bar_chart(df_product_chart_source, 'Product Complained About', chart_title="Complaints by Product (Specific Products)", color_sequence=COMPLAINTS_COLOR_SEQUENCE, barmode='stack')
            if figs_container.get('Product_Complained_About'): st.plotly_chart(figs_container['Product_Complained_About'], use_container_width=True)
            else: st.caption("No data for Product chart (filtered).")
        else: st.info("No complaints on specific products (excluding 'لا علاقة لها بالمنتج').")

    with col2:
        df_exploded_types_for_quality = df_complaints.explode('Complaint Type').dropna(subset=['Complaint Type'])
        df_exploded_types_for_quality = df_exploded_types_for_quality[df_exploded_types_for_quality['Complaint Type'] != '']
        df_quality_issues_source = df_exploded_types_for_quality[df_exploded_types_for_quality['Complaint Type'] == 'جوده'].copy()
        if not df_quality_issues_source.empty:
            df_quality_detail_chart_data = df_quality_issues_source.explode('Quality Issue Detail').dropna(subset=['Quality Issue Detail'])
            df_quality_detail_chart_data = df_quality_detail_chart_data[df_quality_detail_chart_data['Quality Issue Detail'] != '']
            figs_container['Quality_Issue_Detail'] = create_bar_chart(df_quality_detail_chart_data, 'Quality Issue Detail', chart_title="Quality Issue Details (for 'جوده' complaints)", color_sequence=COMPLAINTS_COLOR_SEQUENCE, barmode='stack')
            if figs_container.get('Quality_Issue_Detail'): st.plotly_chart(figs_container['Quality_Issue_Detail'], use_container_width=True)
            else: st.caption("No specific quality details for 'جوده' complaints.")
        else: st.caption("No 'جوده' (Quality) type complaints to detail.")

        df_exploded_types_for_order_error = df_complaints.explode('Complaint Type').dropna(subset=['Complaint Type'])
        df_exploded_types_for_order_error = df_exploded_types_for_order_error[df_exploded_types_for_order_error['Complaint Type'] != '']
        df_order_errors_source = df_exploded_types_for_order_error[df_exploded_types_for_order_error['Complaint Type'] == 'خطاء فى الطلب'].copy()
        if not df_order_errors_source.empty:
            df_order_error_detail_chart_data = df_order_errors_source.explode('Order Error Detail').dropna(subset=['Order Error Detail'])
            df_order_error_detail_chart_data = df_order_error_detail_chart_data[df_order_error_detail_chart_data['Order Error Detail'] != '']
            figs_container['Order_Error_Detail'] = create_bar_chart(df_order_error_detail_chart_data, 'Order Error Detail', chart_title="Order Error Details (for 'خطاء فى الطلب' complaints)", color_sequence=COMPLAINTS_COLOR_SEQUENCE, barmode='stack')
            if figs_container.get('Order_Error_Detail'): st.plotly_chart(figs_container['Order_Error_Detail'], use_container_width=True)
            else: st.caption("No specific order error details for 'خطاء فى الطلب' complaints.")
        else: st.caption("No 'خطاء فى الطلب' (Order Error) type complaints to detail.")

    st.subheader("Complaints by Branch")
    figs_container['Complaints_by_Branch'] = create_bar_chart(df_complaints, 'branch', chart_title="Total Complaints per Branch", color_sequence=COMPLAINTS_COLOR_SEQUENCE, barmode='stack')
    if figs_container.get('Complaints_by_Branch'): st.plotly_chart(figs_container['Complaints_by_Branch'], use_container_width=True)
    else: st.caption("No data for Complaints by Branch chart.")

    if 'date' in df_complaints.columns and pd.api.types.is_datetime64_any_dtype(df_complaints['date']) and not df_complaints['date'].isnull().all():
        trend_data_complaints = df_complaints.groupby(df_complaints['date'].dt.date).size().reset_index(name='daily_complaints')
        trend_data_complaints['date'] = pd.to_datetime(trend_data_complaints['date'])
        trend_data_complaints = trend_data_complaints.sort_values('date')
        if not trend_data_complaints.empty:
            fig_complaints_trend = px.line(trend_data_complaints, x='date', y='daily_complaints', title='Daily Complaints Trend', markers=True, color_discrete_sequence=COMPLAINTS_COLOR_SEQUENCE)
            fig_complaints_trend.update_layout(template="plotly_white")
            figs_container['Complaints_Trend'] = fig_complaints_trend
            if figs_container.get('Complaints_Trend'): st.plotly_chart(figs_container['Complaints_Trend'], use_container_width=True)
        else: st.caption("No data for daily complaints trend.")

    st.subheader("Detailed Complaints Data (Primary Period - Parsed)")
    display_cols_complaints_options = ['date', 'branch', 'code', 'Complaint Type', 'Product Complained About', 'Quality Issue Detail', 'Order Error Detail']
    display_cols_complaints_final = [col for col in display_cols_complaints_options if col in df_complaints.columns]
    df_display_complaints = df_complaints[display_cols_complaints_final].copy()
    if 'date' in df_display_complaints.columns and pd.api.types.is_datetime64_any_dtype(df_display_complaints['date']):
        df_display_complaints['date'] = df_display_complaints['date'].dt.strftime('%Y-%m-%d')

    for col in MULTI_VALUE_COMPLAINT_COLS:
        if col in df_display_complaints.columns:
            df_display_complaints[col] = df_display_complaints[col].apply(lambda x: ', '.join(x) if isinstance(x, list) and x else (x if not isinstance(x,list) else ''))
    st.dataframe(df_display_complaints.reset_index(drop=True), use_container_width=True)
    return figs_container

def get_expected_task_count(project_name_norm, start_date_obj, end_date_obj):
    if project_name_norm not in PROJECT_FREQUENCIES_NORMALIZED:
        return 0
    config = PROJECT_FREQUENCIES_NORMALIZED[project_name_norm]
    expected_count = 0
    if start_date_obj > end_date_obj: return 0

    current_date = start_date_obj
    while current_date <= end_date_obj:
        if config["type"] == "daily":
            expected_count += 1
        elif config["type"] == "weekly" and current_date.weekday() == config["weekday"]:
            expected_count += 1
        current_date += timedelta(days=1)
    return expected_count

def display_missing_performance_dashboard(df_missing_raw_period_data, figs_container, date_range_for_calc, dashboard_title_suffix=""):
    if df_missing_raw_period_data.empty and not list(BRANCH_SCHEMA_NORMALIZED.values()):
        st.info(f"No 'missing' task data for analysis {dashboard_title_suffix}."); return figs_container, pd.DataFrame()

    start_date_calc, end_date_calc = date_range_for_calc[0], date_range_for_calc[1]
    results = []
    all_branches_to_calculate_for = sorted(list(BRANCH_SCHEMA_NORMALIZED.values()))

    df_missing_data_for_calc = df_missing_raw_period_data.copy()
    if 'issues' in df_missing_data_for_calc.columns:
        df_missing_data_for_calc['issues_normalized_for_calc'] = df_missing_data_for_calc['issues'].apply(normalize_project_name)
    else:
        df_missing_data_for_calc['issues_normalized_for_calc'] = ""


    for branch_name in all_branches_to_calculate_for:
        total_expected_for_branch = 0
        total_missed_for_branch = 0

        df_branch_missed_tasks = df_missing_data_for_calc[df_missing_data_for_calc['branch'] == branch_name]

        for project_name_norm in ALL_DEFINED_PROJECT_NAMES_NORMALIZED:
            expected_for_project = get_expected_task_count(project_name_norm, start_date_calc, end_date_calc)
            if expected_for_project == 0: continue

            total_expected_for_branch += expected_for_project

            missed_count_for_project = 0
            if not df_branch_missed_tasks.empty:
                 missed_count_for_project = len(df_branch_missed_tasks[df_branch_missed_tasks['issues_normalized_for_calc'] == project_name_norm])

            total_missed_for_branch += missed_count_for_project

        done_count = total_expected_for_branch - total_missed_for_branch
        done_rate = (done_count / total_expected_for_branch * 100) if total_expected_for_branch > 0 else 100.0
        missing_rate_calc = (total_missed_for_branch / total_expected_for_branch * 100) if total_expected_for_branch > 0 else 0.0

        results.append({
            "branch": branch_name,
            "done rate": f"{done_rate:.1f}%",
            "missing rate": f"{missing_rate_calc:.0f}%",
            "_done_rate_numeric": done_rate,
            "_missing_rate_numeric": missing_rate_calc
        })

    df_results = pd.DataFrame(results)
    if df_results.empty: st.info(f"No missing performance data to display {dashboard_title_suffix}."); return figs_container, pd.DataFrame()

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

    def style_row(row):
        bg_color, text_color = get_color(row['_done_rate_numeric'])
        return pd.Series({
            'done rate': f'background-color: {bg_color}; color: {text_color}; text-align: right;',
            'missing rate': f'background-color: {bg_color}; color: {text_color}; text-align: right;'
        })

    st.subheader(f"Missing Tasks Performance by Branch {dashboard_title_suffix}")

    html_table_styler = df_results_sorted.style \
        .apply(style_row, axis=1) \
        .set_properties(**{'text-align': 'left', 'min-width': '150px', 'font-weight': 'bold'}, subset=['branch']) \
        .set_table_styles([{'selector': 'th', 'props': 'background-color: #E8E8E8; text-align: center; font-weight: bold; padding: 5px;'},
                           {'selector': 'td', 'props': 'padding: 5px; border: 1px solid #ddd;'},
                           {'selector': 'thead th:first-child', 'props': 'text-align: left;'}]) \
        .hide(axis='index').set_table_attributes('class="dataframe styled-missing-table"')

    html_table_output = html_table_styler.to_html(columns=['branch', 'done rate', 'missing rate'])
    html_table_output = html_table_output.replace("<th>branch</th>", "<th>Branch <small>↕</small></th>", 1) \
                                       .replace("<th>done rate</th>", "<th>Done Rate <small>↕</small></th>", 1) \
                                       .replace("<th>missing rate</th>", "<th>Missing Rate <small>↕</small></th>", 1)
    st.markdown(html_table_output, unsafe_allow_html=True)

    figs_container[f'missing_perf_table_df{dashboard_title_suffix.replace(" ", "_")}'] = df_results_sorted

    csv_sum = df_results_sorted[['branch', 'done rate', 'missing rate']].to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"Download Missing Summary (CSV) {dashboard_title_suffix}", csv_sum, f"missing_perf_summary{dashboard_title_suffix.replace(' ', '_')}.csv", "text/csv", key=f"dl_csv_miss_sum{dashboard_title_suffix.replace(' ', '_')}")

    return figs_container, df_results_sorted

def _prepare_closure_summary_df(df, group_by_col):
    # This function must be defined before display_complaint_closure_dashboard or passed to it
    # For simplicity, keeping it global or defined just before its first use.
    summary = df.groupby([group_by_col, 'Status']).size().unstack(fill_value=0)
    summary = summary.reindex(columns=CLOSURE_STATUS_ORDER, fill_value=0)
    summary['المجموع'] = summary.sum(axis=1)
    summary[CLOSURE_COMPLETED_STATUS] = summary.get(CLOSURE_COMPLETED_STATUS, 0)
    summary['نسبة الاكتمال'] = (summary[CLOSURE_COMPLETED_STATUS] / summary['المجموع'] * 100).fillna(0).round(1)
    
    display_df = pd.DataFrame(index=summary.index)
    for status_col in CLOSURE_STATUS_ORDER:
        if status_col in summary.columns:
            display_df[status_col] = summary.apply(
                lambda row: f"{int(row[status_col])} ({((row[status_col] / row['المجموع'] * 100) if row['المجموع'] > 0 else 0.0):.1f}%)", axis=1
            )
        else:
            display_df[status_col] = "0 (0.0%)"
    display_df['المجموع'] = summary['المجموع'].astype(int)
    display_df['نسبة الاكتمال (%)'] = summary['نسبة الاكتمال'] 
    return summary, display_df

def display_complaint_closure_dashboard(df_closure_data, figs_container, period_name="Primary Period"):
    if df_closure_data.empty:
        st.info(f"No data for Complaint Closure Analysis for {period_name}.")
        return figs_container, None, None 

    df_closure_data = df_closure_data.rename(columns={'issues': 'Status'})

    st.header(f"تحليل اغلاق الشكاوي ({period_name})")
    tab_managers, tab_branches = st.tabs(["📊 حسب المديرين", "🏢 حسب الفروع"])

    df_managers_raw_summary, df_managers_display = _prepare_closure_summary_df(df_closure_data, 'area_manager')
    with tab_managers:
        st.subheader("إحصائيات حسب المديرين")
        df_managers_display_final = df_managers_display.copy()
        df_managers_display_final['نسبة الاكتمال (%)'] = df_managers_display_final['نسبة الاكتمال (%)'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_managers_display_final, use_container_width=True)
        
        if not df_managers_raw_summary.empty:
            df_manager_chart_data = df_managers_raw_summary[CLOSURE_STATUS_ORDER].copy()
            fig_managers = px.bar(df_manager_chart_data,
                                  barmode='stack',
                                  title="اغلاق الشكاوي حسب المدير",
                                  color_discrete_map=CLOSURE_STATUS_COLORS,
                                  text_auto=True)
            fig_managers.update_layout(xaxis_title="مدير المنطقة", yaxis_title="عدد الشكاوى")
            fig_managers.update_traces(textposition='inside')
            st.plotly_chart(fig_managers, use_container_width=True)
            figs_container['closure_managers_chart'] = fig_managers
        else:
            st.caption("No data for manager chart.")

    df_branches_raw_summary, df_branches_display = _prepare_closure_summary_df(df_closure_data, 'branch')
    with tab_branches:
        st.subheader("إحصائيات حسب الفروع")
        df_branches_display_final = df_branches_display.copy()
        df_branches_display_final['نسبة الاكتمال (%)'] = df_branches_display_final['نسبة الاكتمال (%)'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_branches_display_final.sort_values("المجموع", ascending=False), use_container_width=True)

        if not df_branches_raw_summary.empty:
            top_n_branches = 15
            df_branch_chart_data = df_branches_raw_summary.sort_values("المجموع", ascending=False).head(top_n_branches)
            df_branch_chart_data = df_branch_chart_data[CLOSURE_STATUS_ORDER].copy()
            
            fig_branches = px.bar(df_branch_chart_data,
                                  barmode='stack',
                                  orientation='h',
                                  title=f"اغلاق الشكاوي حسب الفروع (أعلى {top_n_branches})",
                                  color_discrete_map=CLOSURE_STATUS_COLORS,
                                  text_auto=True)
            fig_branches.update_layout(yaxis_title="الفرع", xaxis_title="عدد الشكاوى", yaxis={'categoryorder':'total ascending'})
            fig_branches.update_traces(textposition='inside')
            st.plotly_chart(fig_branches, use_container_width=True)
            figs_container['closure_branches_chart'] = fig_branches
        else:
            st.caption("No data for branch chart.")

    st.subheader("الاجمالي")
    total_complaints_overall = df_closure_data.shape[0]
    total_completed_overall = df_closure_data[df_closure_data['Status'] == CLOSURE_COMPLETED_STATUS].shape[0]
    completion_percentage_overall = (total_completed_overall / total_complaints_overall * 100) if total_complaints_overall > 0 else 0

    summary_cols = st.columns(3)
    summary_cols[0].metric("إجمالي الشكاوى", total_complaints_overall)
    summary_cols[1].metric("إجمالي الشكاوى المكتملة", total_completed_overall)
    summary_cols[2].metric("نسبة الاكتمال الإجمالية", f"{completion_percentage_overall:.1f}%")

    st.write("---")
    st.write("إحصائيات حسب الحالة:")
    status_counts_overall = df_closure_data['Status'].value_counts().reindex(CLOSURE_STATUS_ORDER, fill_value=0)
    for status, count in status_counts_overall.items():
        percentage = (count / total_complaints_overall * 100) if total_complaints_overall > 0 else 0
        st.markdown(f"- **{status}:** {count} ({percentage:.1f}%)")
    
    figs_container['closure_overall_summary_df'] = status_counts_overall.to_frame(name='count')

    st.subheader("الفروع مع نسبة اكتمال أقل من 50%")
    if not df_branches_raw_summary.empty:
        df_low_completion_branches = df_branches_raw_summary[df_branches_raw_summary['نسبة الاكتمال'] < 50].copy()
        df_low_completion_branches.sort_values('نسبة الاكتمال', ascending=True, inplace=True)

        if not df_low_completion_branches.empty:
            # Use the _prepare_closure_summary_df to get the display version for low completion branches
            # Filter the original df_closure_data for only these branches before passing to the summary function
            df_low_comp_data_filtered = df_closure_data[df_closure_data['branch'].isin(df_low_completion_branches.index)]
            _, df_low_comp_display = _prepare_closure_summary_df(df_low_comp_data_filtered, 'branch')
            
            df_low_comp_display_final = df_low_comp_display.copy()
            df_low_comp_display_final['نسبة الاكتمال (%)'] = df_low_comp_display_final['نسبة الاكتمال (%)'].apply(lambda x: f"{x:.1f}%")

            df_low_comp_display_final.index.name = "الفرع"
            st.dataframe(df_low_comp_display_final.reset_index(), use_container_width=True)
            
            df_low_comp_chart_data = df_low_completion_branches[CLOSURE_STATUS_ORDER].copy()
            fig_low_completion = px.bar(df_low_comp_chart_data,
                                         barmode='stack',
                                         orientation='h',
                                         title="تفاصيل حالات الفروع ذات الاكتمال المنخفض",
                                         color_discrete_map=CLOSURE_STATUS_COLORS,
                                         text_auto=True)
            fig_low_completion.update_layout(yaxis_title="الفرع", xaxis_title="عدد الشكاوى", yaxis={'categoryorder':'total ascending'})
            fig_low_completion.update_traces(textposition='inside')
            st.plotly_chart(fig_low_completion, use_container_width=True)
            figs_container['closure_low_completion_chart'] = fig_low_completion
            figs_container['closure_low_completion_table_df'] = df_low_completion_branches

            st.markdown("---")
            st.subheader("ملخص الفروع ذات نسبة الاكتمال المنخفضة (أقل من 50%)")
            num_low_comp_branches = len(df_low_completion_branches)
            total_complaints_low_comp = df_low_completion_branches['المجموع'].sum()
            total_completed_low_comp = df_low_completion_branches[CLOSURE_COMPLETED_STATUS].sum()
            completion_perc_low_comp = (total_completed_low_comp / total_complaints_low_comp * 100) if total_complaints_low_comp > 0 else 0
            
            st.markdown(f"- إجمالي عدد الفروع ذات نسبة اكتمال أقل من 50%: **{num_low_comp_branches}** فرعاً")
            st.markdown(f"- إجمالي عدد الشكاوى في هذه الفروع: **{total_complaints_low_comp}** شكوى")
            st.markdown(f"- إجمالي عدد الشكاوى المكتملة في هذه الفروع: **{total_completed_low_comp}** شكوى ({completion_perc_low_comp:.1f}%)")
            
            non_completed_sum_low_comp = df_low_completion_branches[[s for s in CLOSURE_STATUS_ORDER if s != CLOSURE_COMPLETED_STATUS]].sum()
            total_non_completed_low_comp = non_completed_sum_low_comp.sum()
            
            if total_non_completed_low_comp > 0:
                st.markdown(f"أبرز الأسباب لعدم الاكتمال (من إجمالي **{total_non_completed_low_comp}** شكوى غير مكتملة أو ذات تصنيف آخر في هذه الفروع):")
                with st.container():
                    ul_items = ""
                    for status, count in non_completed_sum_low_comp.items():
                        if count > 0:
                            percentage = (count / total_non_completed_low_comp * 100)
                            ul_items += f"<li>{status}: {int(count)} ({percentage:.1f}%)</li>"
                    st.markdown(f"<ul>{ul_items}</ul>", unsafe_allow_html=True)
        else:
            st.info("لا توجد فروع حاليًا بنسبة اكتمال أقل من 50%.")
    else:
        st.info("لا يمكن تحليل الفروع ذات الاكتمال المنخفض لعدم توفر بيانات الفروع.")
        
    return figs_container, df_managers_raw_summary, df_branches_raw_summary


# --- Main Dashboard Logic ---
figs_primary = {}
figs_complaints_primary = {}
figs_missing_primary = {}
figs_complaint_closure_primary = {}
df_missing_perf_results_primary = pd.DataFrame()
df_closure_managers_summary_primary = None 
df_closure_branches_summary_primary = None 

if not df_primary_period.empty:
    is_purely_complaints_perf = ((df_primary_period['upload_category'].astype(str).str.lower() == 'complaints').all() and \
                                 (df_primary_period['report_type'].astype(str).str.lower() == 'performance').all() and \
                                 df_primary_period['upload_category'].nunique() == 1 and \
                                 df_primary_period['report_type'].nunique() == 1)

    is_purely_missing_perf = ((df_primary_period['upload_category'].astype(str).str.lower() == 'missing').all() and \
                              (df_primary_period['report_type'].astype(str).str.lower() == 'performance').all() and \
                              df_primary_period['upload_category'].nunique() == 1 and \
                              df_primary_period['report_type'].nunique() == 1)

    is_purely_complaint_closure = ((df_primary_period['upload_category'].astype(str).str.lower() == 'complaints').all() and \
                                   (df_primary_period['report_type'].astype(str) == CLOSURE_REPORT_TYPE_NAME).all() and \
                                   df_primary_period['upload_category'].nunique() == 1 and \
                                   df_primary_period['report_type'].nunique() == 1)


    if is_purely_complaint_closure:
        figs_complaint_closure_primary, df_closure_managers_summary_primary, df_closure_branches_summary_primary = display_complaint_closure_dashboard(df_primary_period.copy(), figs_complaint_closure_primary, "Primary Period")
    elif is_purely_complaints_perf:
        st.subheader("Complaints Performance Dashboard (Primary Period)")
        figs_complaints_primary = display_complaints_performance_dashboard(df_primary_period.copy(), figs_complaints_primary)
    elif is_purely_missing_perf:
        figs_missing_primary, df_missing_perf_results_primary = display_missing_performance_dashboard(
            df_primary_period.copy(), figs_missing_primary, primary_date_range, "(Primary Period)"
        )
    else:
        st.subheader("General Performance Analysis (Primary Period)")
        figs_primary = display_general_dashboard(df_primary_period.copy(), figs_primary)

        df_complaints_subset_in_primary = df_primary_period[
            (df_primary_period['upload_category'].astype(str).str.lower() == 'complaints') &
            (df_primary_period['report_type'].astype(str).str.lower() == 'performance')
        ].copy()
        if not df_complaints_subset_in_primary.empty:
            st.markdown("---"); st.subheader("Complaints Analysis (Subset of Primary Period)")
            temp_figs_subset_complaints = display_complaints_performance_dashboard(df_complaints_subset_in_primary, {})
            if figs_primary is not None and temp_figs_subset_complaints:
                 for key, fig_val in temp_figs_subset_complaints.items():
                     figs_primary[f"Subset_Complaints_{key}"] = fig_val

        df_missing_subset_in_primary = df_primary_period[
            (df_primary_period['upload_category'].astype(str).str.lower() == 'missing') &
            (df_primary_period['report_type'].astype(str).str.lower() == 'performance')
        ].copy()
        if not df_missing_subset_in_primary.empty:
            st.markdown("---");
            temp_figs_subset_missing, df_missing_subset_results = display_missing_performance_dashboard(
                df_missing_subset_in_primary, {}, primary_date_range, "(Subset of Primary)"
            )
            if figs_primary is not None and temp_figs_subset_missing:
                for key, data_val in temp_figs_subset_missing.items():
                    figs_primary[f"Subset_Missing_{key}"] = data_val

        df_complaint_closure_subset_in_primary = df_primary_period[
            (df_primary_period['upload_category'].astype(str).str.lower() == 'complaints') &
            (df_primary_period['report_type'].astype(str) == CLOSURE_REPORT_TYPE_NAME)
        ].copy()
        if not df_complaint_closure_subset_in_primary.empty:
            st.markdown("---");
            temp_figs_subset_closure, _, _ = display_complaint_closure_dashboard(df_complaint_closure_subset_in_primary, {}, "Subset of Primary") 
            if figs_primary is not None and temp_figs_subset_closure:
                for key, fig_val_closure in temp_figs_subset_closure.items():
                    figs_primary[f"Subset_ComplaintClosure_{key}"] = fig_val_closure


    st.markdown("---")
    if not is_purely_complaint_closure:
        if st.button("🏆 Show Branch Rankings (Current Filters)", key="show_rankings_button_main_display"):
            if not df_primary_period.empty and 'branch' in df_primary_period.columns:
                st.subheader(f"Branch Performance Ranking (Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d})")

                if is_purely_missing_perf and not df_missing_perf_results_primary.empty:
                    st.markdown("_Based on 'Missing Rate'. Lower is better._")
                    ranked_missing_df = df_missing_perf_results_primary.sort_values(by='_missing_rate_numeric', ascending=True).copy()
                    ranked_missing_df['Rank'] = ranked_missing_df['_missing_rate_numeric'].rank(method='min', ascending=True).astype(int)
                    st.dataframe(ranked_missing_df[['Rank', 'branch', 'done rate', 'missing rate']].reset_index(drop=True), use_container_width=True)

                    if len(ranked_missing_df) > 1:
                        rank_chart_cols = st.columns(2)
                        top_n = min(10, len(ranked_missing_df))
                        with rank_chart_cols[0]:
                            fig_top = create_bar_chart(ranked_missing_df.head(top_n), 'branch', chart_title=f"Top {top_n} (Lowest Missing Rate)", sort_values_by='_missing_rate_numeric', sort_ascending=True)
                            if fig_top: st.plotly_chart(fig_top, use_container_width=True)
                        with rank_chart_cols[1]:
                            fig_bot = create_bar_chart(ranked_missing_df.tail(top_n).sort_values('_missing_rate_numeric',ascending=False), 'branch', chart_title=f"Bottom {top_n} (Highest Missing Rate)", sort_values_by='_missing_rate_numeric', sort_ascending=False)
                            if fig_bot: st.plotly_chart(fig_bot, use_container_width=True)
                else: 
                    st.markdown("_Based on total count of issues/complaints. Lower count is better._")
                    branch_counts_df = df_primary_period.groupby('branch').size().reset_index(name='Total Issues/Complaints').sort_values(by='Total Issues/Complaints', ascending=True)
                    branch_counts_df['Rank'] = branch_counts_df['Total Issues/Complaints'].rank(method='min', ascending=True).astype(int)
                    st.dataframe(branch_counts_df[['Rank', 'branch', 'Total Issues/Complaints']].reset_index(drop=True), use_container_width=True)

                    if len(branch_counts_df) > 1:
                        rank_chart_cols = st.columns(2)
                        top_n = min(10, len(branch_counts_df))
                        with rank_chart_cols[0]:
                            fig_top = create_bar_chart(branch_counts_df.head(top_n), 'branch', chart_title=f"Top {top_n} (Best - Fewest Issues)", sort_values_by='Total Issues/Complaints', sort_ascending=True)
                            if fig_top: st.plotly_chart(fig_top, use_container_width=True)
                        with rank_chart_cols[1]:
                            fig_bot = create_bar_chart(branch_counts_df.tail(top_n).sort_values('Total Issues/Complaints',ascending=False), 'branch', chart_title=f"Bottom {top_n} (Needs Improvement - Most Issues)", sort_values_by='Total Issues/Complaints', sort_ascending=False)
                            if fig_bot: st.plotly_chart(fig_bot, use_container_width=True)
            else: st.info("No data or branch information available for rankings with current filters.")
    elif is_purely_complaint_closure:
         st.info(f"Branch ranking by issue count is not applicable for '{CLOSURE_REPORT_TYPE_NAME}' analysis. Completion rates are shown in the specific dashboard.")
else:
    st.info("No data matches the current filter criteria for the primary period.")

# --- Period Comparison Logic ---
if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.markdown("---"); st.header("📊 Period Comparison Results")

    df_comp_base_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)

    df_comp1 = df_comp_base_filtered[(df_comp_base_filtered['date'].dt.date >= comparison_date_range_1[0]) & (df_comp_base_filtered['date'].dt.date <= comparison_date_range_1[1])].copy()
    df_comp2 = df_comp_base_filtered[(df_comp_base_filtered['date'].dt.date >= comparison_date_range_2[0]) & (df_comp_base_filtered['date'].dt.date <= comparison_date_range_2[1])].copy()

    p1_lab = f"P1 ({comparison_date_range_1[0]:%b %d}-{comparison_date_range_1[1]:%b %d})"
    p2_lab = f"P2 ({comparison_date_range_2[0]:%b %d}-{comparison_date_range_2[1]:%b %d})"

    if df_comp1.empty and df_comp2.empty: st.info("No data for comparison in either period with the selected filters.")
    else:
        # 1. Missing Tasks Comparison
        df_comp1_miss_data = df_comp1[(df_comp1['upload_category'].astype(str).str.lower() == 'missing') & (df_comp1['report_type'].astype(str).str.lower() == 'performance')].copy()
        df_comp2_miss_data = df_comp2[(df_comp2['upload_category'].astype(str).str.lower() == 'missing') & (df_comp2['report_type'].astype(str).str.lower() == 'performance')].copy()

        if not df_comp1_miss_data.empty or not df_comp2_miss_data.empty:
            st.subheader("Missing Tasks Performance Comparison")
            _, df_miss_res_c1 = display_missing_performance_dashboard(df_comp1_miss_data, {}, comparison_date_range_1, f"({p1_lab})")
            st.markdown("---")
            _, df_miss_res_c2 = display_missing_performance_dashboard(df_comp2_miss_data, {}, comparison_date_range_2, f"({p2_lab})")

            if not df_miss_res_c1.empty and not df_miss_res_c2.empty:
                df_miss_comp_chart_data = pd.merge(
                    df_miss_res_c1[['branch', '_done_rate_numeric']].rename(columns={'_done_rate_numeric': p1_lab}),
                    df_miss_res_c2[['branch', '_done_rate_numeric']].rename(columns={'_done_rate_numeric': p2_lab}),
                    on='branch', how='outer'
                ).fillna(0)
                df_miss_comp_chart_melted = df_miss_comp_chart_data.melt(id_vars='branch', var_name='Period', value_name='Done Rate (%)')

                if not df_miss_comp_chart_melted.empty:
                    fig_m_comp = px.bar(df_miss_comp_chart_melted, x='branch', y='Done Rate (%)', color='Period', barmode='group', title='Missing Tasks: Done Rate Comparison by Branch')
                    fig_m_comp.update_layout(yaxis_ticksuffix="%")
                    st.plotly_chart(fig_m_comp, use_container_width=True)
            st.markdown("---")

        # 2. Complaints Performance Comparison ('performance' type)
        df_comp1_complaints_data = df_comp1[(df_comp1['upload_category'].astype(str).str.lower() == 'complaints') & (df_comp1['report_type'].astype(str).str.lower() == 'performance')].copy()
        df_comp2_complaints_data = df_comp2[(df_comp2['upload_category'].astype(str).str.lower() == 'complaints') & (df_comp2['report_type'].astype(str).str.lower() == 'performance')].copy()

        if not df_comp1_complaints_data.empty or not df_comp2_complaints_data.empty:
            st.subheader("Complaints Performance Comparison ('performance' type)")

            def _prepare_complaints_df_for_comp(df_raw, period_label):
                if df_raw.empty: return pd.DataFrame()
                parsed = df_raw['issues'].apply(parse_complaint_details)
                df_p = pd.concat([df_raw.reset_index(drop=True).drop(columns=['issues'], errors='ignore'), parsed.reset_index(drop=True)], axis=1)
                df_p.rename(columns={'Type': 'Complaint Type', 'Product': 'Product Complained About', 'Quality Detail': 'Quality Issue Detail', 'Order Error': 'Order Error Detail'}, inplace=True)
                df_p['period_label'] = period_label
                for col_name_comp in MULTI_VALUE_COMPLAINT_COLS:
                    if col_name_comp in df_p.columns:
                        df_p[col_name_comp] = df_p[col_name_comp].apply(
                            lambda x_list: [str(item).strip() for item in x_list if item and str(item).strip()] if isinstance(x_list, list) else []
                        )
                return df_p

            df_c1_parsed_comp = _prepare_complaints_df_for_comp(df_comp1_complaints_data, p1_lab)
            df_c2_parsed_comp = _prepare_complaints_df_for_comp(df_comp2_complaints_data, p2_lab)

            dfs_to_concat_complaints_comp = [df for df in [df_c1_parsed_comp, df_c2_parsed_comp] if not df.empty]
            if dfs_to_concat_complaints_comp:
                df_combined_complaints_comp = pd.concat(dfs_to_concat_complaints_comp, ignore_index=True)
                if not df_combined_complaints_comp.empty:
                    st.markdown("##### Total Complaint Counts by Period")
                    total_c1 = len(df_c1_parsed_comp); total_c2 = len(df_c2_parsed_comp)
                    delta_c = total_c2 - total_c1
                    cc1_metric, cc2_metric = st.columns(2)
                    with cc1_metric: st.metric(f"Total Complaints ({p1_lab})", total_c1)
                    with cc2_metric: st.metric(f"Total Complaints ({p2_lab})", total_c2, delta=f"{delta_c:+}" if delta_c!=0 else None, delta_color="inverse" if delta_c < 0 else "normal")

                    comp_chart_cols_row1_c1, comp_chart_cols_row1_c2 = st.columns(2)
                    with comp_chart_cols_row1_c1:
                        fig_branch_cc = create_bar_chart(df_combined_complaints_comp, 'branch', chart_title='Complaints by Branch Comparison', color_sequence=COMPLAINTS_COLOR_SEQUENCE, barmode='group')
                        if fig_branch_cc: st.plotly_chart(fig_branch_cc, use_container_width=True)
                        else: st.caption("No data for Branch Comparison (Complaints).")

                    with comp_chart_cols_row1_c2:
                        if 'Complaint Type' in df_combined_complaints_comp.columns:
                            df_type_c_exploded = df_combined_complaints_comp.explode('Complaint Type').dropna(subset=['Complaint Type'])
                            df_type_c_exploded = df_type_c_exploded[df_type_c_exploded['Complaint Type'] != '']
                            if not df_type_c_exploded.empty:
                                fig_type_cc = create_bar_chart(df_type_c_exploded, 'Complaint Type', chart_title='Complaint Types Comparison', color_sequence=COMPLAINTS_COLOR_SEQUENCE, barmode='group')
                                if fig_type_cc: st.plotly_chart(fig_type_cc, use_container_width=True)
                            else: st.caption("No data for Complaint Type Comparison.")
                        else: st.caption("Complaint Type column not available for comparison.")
            st.markdown("---")

        # 3. Complaint Closure Comparison ('اغلاق الشكاوي' type)
        df_comp1_closure_data = df_comp1[(df_comp1['upload_category'].astype(str).str.lower() == 'complaints') & (df_comp1['report_type'] == CLOSURE_REPORT_TYPE_NAME)].copy()
        df_comp2_closure_data = df_comp2[(df_comp2['upload_category'].astype(str).str.lower() == 'complaints') & (df_comp2['report_type'] == CLOSURE_REPORT_TYPE_NAME)].copy()

        if not df_comp1_closure_data.empty or not df_comp2_closure_data.empty:
            st.subheader(f"Complaints Closure Comparison ('{CLOSURE_REPORT_TYPE_NAME}' type)")

            df_c1_closure_parsed = df_comp1_closure_data.rename(columns={'issues': 'Status'})
            df_c1_closure_parsed['period_label'] = p1_lab
            df_c2_closure_parsed = df_comp2_closure_data.rename(columns={'issues': 'Status'})
            df_c2_closure_parsed['period_label'] = p2_lab

            dfs_to_concat_closure_comp = [df for df in [df_c1_closure_parsed, df_c2_closure_parsed] if not df.empty]
            if dfs_to_concat_closure_comp:
                df_combined_closure_comp = pd.concat(dfs_to_concat_closure_comp, ignore_index=True)
                if not df_combined_closure_comp.empty:
                    st.markdown("##### Total Closure Records by Period")
                    total_cl1 = len(df_c1_closure_parsed); total_cl2 = len(df_c2_closure_parsed)
                    delta_cl = total_cl2 - total_cl1
                    cl1_metric, cl2_metric = st.columns(2)
                    with cl1_metric: st.metric(f"Total Records ({p1_lab})", total_cl1)
                    with cl2_metric: st.metric(f"Total Records ({p2_lab})", total_cl2, delta=f"{delta_cl:+}" if delta_cl!=0 else None, delta_color="inverse" if delta_cl < 0 else "normal")

                    closure_comp_chart_cols_c1, closure_comp_chart_cols_c2 = st.columns(2)
                    with closure_comp_chart_cols_c1:
                        fig_branch_cl_comp = create_bar_chart(df_combined_closure_comp, 'branch', chart_title='Closure Records by Branch Comparison', barmode='group')
                        if fig_branch_cl_comp: st.plotly_chart(fig_branch_cl_comp, use_container_width=True)
                        else: st.caption("No data for Branch Comparison (Closure).")

                    with closure_comp_chart_cols_c2:
                        fig_status_cl_comp = create_bar_chart(df_combined_closure_comp, 'Status', chart_title='Closure Status Comparison', barmode='group', color_discrete_map=CLOSURE_STATUS_COLORS)
                        if fig_status_cl_comp: st.plotly_chart(fig_status_cl_comp, use_container_width=True)
                        else: st.caption("No data for Status Comparison (Closure).")
            st.markdown("---")

        # 4. General Issues Comparison
        df_comp1_gen_issues = df_comp1[
            ~(((df_comp1['upload_category'].astype(str).str.lower() == 'complaints') & (df_comp1['report_type'].astype(str).str.lower() == 'performance'))) &
            ~(((df_comp1['upload_category'].astype(str).str.lower() == 'missing') & (df_comp1['report_type'].astype(str).str.lower() == 'performance'))) &
            ~(((df_comp1['upload_category'].astype(str).str.lower() == 'complaints') & (df_comp1['report_type'] == CLOSURE_REPORT_TYPE_NAME)))
        ].copy()
        df_comp2_gen_issues = df_comp2[
            ~(((df_comp2['upload_category'].astype(str).str.lower() == 'complaints') & (df_comp2['report_type'].astype(str).str.lower() == 'performance'))) &
            ~(((df_comp2['upload_category'].astype(str).str.lower() == 'missing') & (df_comp2['report_type'].astype(str).str.lower() == 'performance'))) &
            ~(((df_comp2['upload_category'].astype(str).str.lower() == 'complaints') & (df_comp2['report_type'] == CLOSURE_REPORT_TYPE_NAME)))
        ].copy()


        if not df_comp1_gen_issues.empty or not df_comp2_gen_issues.empty:
            st.subheader("General Issues Comparison")
            st.markdown("_(Excluding Complaints Performance, Missing Performance, and Complaint Closure data shown above)_")

            if not df_comp1_gen_issues.empty: df_comp1_gen_issues['period_label'] = p1_lab
            if not df_comp2_gen_issues.empty: df_comp2_gen_issues['period_label'] = p2_lab

            dfs_to_concat_gen = [df for df in [df_comp1_gen_issues, df_comp2_gen_issues] if not df.empty]
            if dfs_to_concat_gen:
                df_combined_gen_issues = pd.concat(dfs_to_concat_gen, ignore_index=True)
                if not df_combined_gen_issues.empty:
                    st.markdown("##### Total General Issue Counts by Period")
                    total_g1 = len(df_comp1_gen_issues); total_g2 = len(df_comp2_gen_issues)
                    delta_g = total_g2 - total_g1
                    gc1_metric, gc2_metric = st.columns(2)
                    with gc1_metric: st.metric(f"Total General Issues ({p1_lab})", total_g1)
                    with gc2_metric: st.metric(f"Total General Issues ({p2_lab})", total_g2, delta=f"{delta_g:+}" if delta_g!=0 else None, delta_color="inverse" if delta_g < 0 else "normal")

                    gen_chart_cols_c1, gen_chart_cols_c2 = st.columns(2)
                    with gen_chart_cols_c1:
                        fig_branch_gen_comp = create_bar_chart(df_combined_gen_issues, 'branch', chart_title='General Issues by Branch Comparison', barmode='group')
                        if fig_branch_gen_comp: st.plotly_chart(fig_branch_gen_comp, use_container_width=True)
                        else: st.caption("No data for Branch Comparison (General Issues).")
                    with gen_chart_cols_c2:
                        fig_cat_gen_comp = create_bar_chart(df_combined_gen_issues, 'upload_category', chart_title='General Issues by Category Comparison', barmode='group')
                        if fig_cat_gen_comp: st.plotly_chart(fig_cat_gen_comp, use_container_width=True)
                        else: st.caption("No data for Category Comparison (General Issues).")

                    if 'issues' in df_combined_gen_issues.columns:
                        df_combined_gen_issues['issues'] = df_combined_gen_issues['issues'].astype(str).fillna("N/A_issue")
                        df_top_issues_comp_data = df_combined_gen_issues.groupby(['issues', 'period_label']).size().reset_index(name='count')
                        overall_top_issues_list = df_combined_gen_issues['issues'].value_counts().nlargest(TOP_N_GENERAL_ISSUES_COMPARISON).index.tolist()
                        df_top_issues_comp_filtered = df_top_issues_comp_data[df_top_issues_comp_data['issues'].isin(overall_top_issues_list)].copy()

                        if not df_top_issues_comp_filtered.empty:
                            pivot_df = df_top_issues_comp_filtered.pivot_table(index='issues', columns='period_label', values='count', fill_value=0).reset_index()
                            if pivot_df.empty:
                                st.caption(f"Pivot table for Top {TOP_N_GENERAL_ISSUES_COMPARISON} General Issues resulted in no data.")
                            else:
                                if p1_lab not in pivot_df.columns: pivot_df[p1_lab] = 0
                                if p2_lab not in pivot_df.columns: pivot_df[p2_lab] = 0
                                df_top_issues_for_chart = pivot_df.melt(id_vars='issues', value_vars=[p1_lab, p2_lab], var_name='period_label', value_name='count')
                                df_top_issues_for_chart = df_top_issues_for_chart.sort_values(by=['issues', 'period_label'])
                                fig_top_issues_comp = px.bar(df_top_issues_for_chart, x='issues', y='count', color='period_label', barmode='group', title=f'Top {TOP_N_GENERAL_ISSUES_COMPARISON} General Issues Comparison')
                                fig_top_issues_comp.update_xaxes(categoryorder='total descending')
                                if fig_top_issues_comp: st.plotly_chart(fig_top_issues_comp, use_container_width=True)
                                else: st.caption(f"Could not generate Top {TOP_N_GENERAL_ISSUES_COMPARISON} General Issues Comparison chart.")
                        else:
                            st.caption(f"Not enough distinct data for Top {TOP_N_GENERAL_ISSUES_COMPARISON} General Issues Comparison.")
                    else:
                        st.caption("Issues column not available for Top N General Issues Comparison.")


# --- Download Section ---
st.sidebar.subheader("Downloads")
is_primary_data_purely_complaints_check = False
is_primary_data_purely_missing_check = False
is_primary_data_purely_complaint_closure_check = False

if 'df_primary_period' in locals() and not df_primary_period.empty:
    is_purely_complaints_check = ((df_primary_period['upload_category'].astype(str).str.lower() == 'complaints').all() and \
                                 (df_primary_period['report_type'].astype(str).str.lower() == 'performance').all() and \
                                 df_primary_period['upload_category'].nunique() == 1 and \
                                 df_primary_period['report_type'].nunique() == 1)
    is_purely_missing_check = ((df_primary_period['upload_category'].astype(str).str.lower() == 'missing').all() and \
                              (df_primary_period['report_type'].astype(str).str.lower() == 'performance').all() and \
                              df_primary_period['upload_category'].nunique() == 1 and \
                              df_primary_period['report_type'].nunique() == 1)
    is_primary_data_purely_complaint_closure_check = ((df_primary_period['upload_category'].astype(str).str.lower() == 'complaints').all() and \
                                   (df_primary_period['report_type'].astype(str) == CLOSURE_REPORT_TYPE_NAME).all() and \
                                   df_primary_period['upload_category'].nunique() == 1 and \
                                   df_primary_period['report_type'].nunique() == 1)

    is_complaints_subset_displayed_check = not is_purely_complaints_check and not is_purely_missing_check and not is_primary_data_purely_complaint_closure_check and \
                                      not df_primary_period[(df_primary_period['upload_category'].astype(str).str.lower() == 'complaints') & (df_primary_period['report_type'].astype(str).str.lower() == 'performance')].empty
    is_missing_subset_displayed_check = not is_purely_complaints_check and not is_purely_missing_check and not is_primary_data_purely_complaint_closure_check and \
                                     not df_primary_period[(df_primary_period['upload_category'].astype(str).str.lower() == 'missing') & (df_primary_period['report_type'].astype(str).str.lower() == 'performance')].empty
    is_complaint_closure_subset_displayed_check = not is_purely_complaints_check and not is_purely_missing_check and not is_primary_data_purely_complaint_closure_check and \
                                     not df_primary_period[(df_primary_period['upload_category'].astype(str).str.lower() == 'complaints') & (df_primary_period['report_type'] == CLOSURE_REPORT_TYPE_NAME)].empty


    st.sidebar.markdown("Primary Period Data:")
    try:
        csv_data_primary = df_primary_period.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.sidebar.download_button("Download Primary (Raw CSV)", csv_data_primary, f"primary_data_raw_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.csv", "text/csv", key="download_csv_primary")
    except Exception as e: st.sidebar.error(f"Primary CSV Error: {e}")

    try:
        output_excel = io.BytesIO()
        df_primary_excel_export = df_primary_period.copy()
        excel_file_suffix = "data"
        excel_download_ready = False 

        if is_primary_data_purely_complaints_check:
            excel_file_suffix = "complaints_data_parsed"
            parsed_details_excel = df_primary_excel_export['issues'].apply(parse_complaint_details)
            df_primary_excel_export = pd.concat([df_primary_excel_export.reset_index(drop=True).drop(columns=['issues'], errors='ignore'), parsed_details_excel.reset_index(drop=True)], axis=1)
            df_primary_excel_export.rename(columns={'Type': 'Complaint Type', 'Product': 'Product Complained About', 'Quality Detail': 'Quality Issue Detail', 'Order Error': 'Order Error Detail'}, inplace=True)
            for col_name_excel in MULTI_VALUE_COMPLAINT_COLS:
                if col_name_excel in df_primary_excel_export.columns:
                    df_primary_excel_export[col_name_excel] = df_primary_excel_export[col_name_excel].apply(lambda x_list: ', '.join(map(str,x_list)) if isinstance(x_list, list) else x_list)
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_primary_excel_export.to_excel(writer, index=False, sheet_name='PrimaryComplaintsParsed')
            excel_data = output_excel.getvalue()
            excel_download_ready = True

        elif is_primary_data_purely_missing_check and not df_missing_perf_results_primary.empty:
            excel_file_suffix = "missing_perf_summary"
            df_primary_excel_export = df_missing_perf_results_primary[['branch', 'done rate', 'missing rate']].copy()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_primary_excel_export.to_excel(writer, index=False, sheet_name='MissingPerfSummary')
            excel_data = output_excel.getvalue()
            excel_download_ready = True

        elif is_primary_data_purely_complaint_closure_check:
            excel_file_suffix = "complaint_closure" 
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_primary_period.rename(columns={'issues': 'Status'}).to_excel(writer, index=False, sheet_name='Closure_Details')
                if df_closure_managers_summary_primary is not None:
                     _prepare_closure_summary_df(df_primary_period.rename(columns={'issues':'Status'}), 'area_manager')[1].reset_index().to_excel(writer, index=False, sheet_name='Manager_Summary_Closure')
                if df_closure_branches_summary_primary is not None:
                    _prepare_closure_summary_df(df_primary_period.rename(columns={'issues':'Status'}), 'branch')[1].reset_index().to_excel(writer, index=False, sheet_name='Branch_Summary_Closure')
            excel_data = output_excel.getvalue()
            excel_download_ready = True
        else: 
            excel_file_suffix = "general_data"
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_primary_excel_export.to_excel(writer, index=False, sheet_name='PrimaryGeneralData')
            excel_data = output_excel.getvalue()
            excel_download_ready = True

        if excel_download_ready:
            st.sidebar.download_button(
                label=f"Download Primary ({excel_file_suffix.replace('_',' ').title()}) (Excel)",
                data=excel_data,
                file_name=f"primary_{excel_file_suffix}_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_primary_{excel_file_suffix}_xlsx"
            )
    except Exception as e:
        st.sidebar.error(f"Primary Excel Error: {e}")


    active_pdf_visuals_type_key = "general_visuals"
    current_figs_for_pdf = figs_primary.copy()
    pdf_visual_button_label = "Prepare General Visuals PDF"

    if is_primary_data_purely_complaints_check:
        active_pdf_visuals_type_key = "complaints_visuals_primary"
        current_figs_for_pdf = figs_complaints_primary
        pdf_visual_button_label = "Prepare Complaints Perf. Visuals PDF"
    elif is_primary_data_purely_missing_check:
        active_pdf_visuals_type_key = "missing_visuals_primary"
        current_figs_for_pdf = {k: v for k, v in figs_missing_primary.items() if isinstance(v, go.Figure)}
        pdf_visual_button_label = "Prepare Missing Perf. Visuals PDF"
    elif is_primary_data_purely_complaint_closure_check:
        active_pdf_visuals_type_key = "complaint_closure_visuals_primary"
        current_figs_for_pdf = {k:v for k,v in figs_complaint_closure_primary.items() if isinstance(v,go.Figure)}
        pdf_visual_button_label = f"Prepare {CLOSURE_REPORT_TYPE_NAME} Visuals PDF"
    elif is_complaints_subset_displayed_check or is_missing_subset_displayed_check or is_complaint_closure_subset_displayed_check:
        pdf_visual_button_label = "Prepare Combined Visuals PDF"

    if st.sidebar.button(pdf_visual_button_label, key=f"prep_{active_pdf_visuals_type_key}_pdf"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        elif not current_figs_for_pdf or not any(isinstance(fig, go.Figure) for fig in current_figs_for_pdf.values()):
             st.sidebar.warning("No chart visuals to generate PDF for this selection.")
        else:
            with st.spinner("Generating Visuals PDF..."):
                html_content = f"<html><head><meta charset='utf-8'><title>Visuals Report</title><style>body{{font-family:Arial,sans-serif;margin:20px}}h1,h2{{text-align:center;color:#333;page-break-after:avoid}}img{{display:block;margin-left:auto;margin-right:auto;max-width:650px;height:auto;border:1px solid #ccc;padding:5px;margin-bottom:25px;page-break-inside:avoid}}@media print{{*{{-webkit-print-color-adjust:exact !important;color-adjust:exact !important;print-color-adjust:exact !important}}body{{background-color:white !important}}}}</style></head><body>"
                report_title_pdf = pdf_visual_button_label.replace("Prepare ", "").replace(" PDF", "")
                html_content += f"<h1>{report_title_pdf}</h1><h2>Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}</h2>"

                ordered_keys_for_pdf = []
                if active_pdf_visuals_type_key == "complaints_visuals_primary":
                    ordered_keys_for_pdf = ["Complaint_Type", "Product_Complained_About", "Quality_Issue_Detail", "Order_Error_Detail", "Complaints_by_Branch", "Complaints_Trend"]
                elif active_pdf_visuals_type_key == "missing_visuals_primary":
                    ordered_keys_for_pdf = [k for k,v in current_figs_for_pdf.items() if isinstance(v, go.Figure)]
                elif active_pdf_visuals_type_key == "complaint_closure_visuals_primary":
                    ordered_keys_for_pdf = ['closure_managers_chart', 'closure_branches_chart', 'closure_low_completion_chart']
                else:
                    gen_order = ["Branch_Issues", "Area_Manager", "Report_Type", "Category", "Shift_Values", "Trend"]
                    sub_compl_order = [f"Subset_Complaints_{k}" for k in ["Complaint_Type", "Product_Complained_About", "Quality_Issue_Detail", "Order_Error_Detail", "Complaints_by_Branch", "Complaints_Trend"]]
                    sub_miss_order = [k for k in current_figs_for_pdf if k.startswith("Subset_Missing_") and isinstance(current_figs_for_pdf.get(k), go.Figure)]
                    sub_closure_order = [k for k in current_figs_for_pdf if k.startswith("Subset_ComplaintClosure_") and isinstance(current_figs_for_pdf.get(k), go.Figure)]

                    ordered_keys_for_pdf.extend([k for k in gen_order if k in current_figs_for_pdf and isinstance(current_figs_for_pdf.get(k), go.Figure)])
                    ordered_keys_for_pdf.extend([k for k in sub_compl_order if k in current_figs_for_pdf and isinstance(current_figs_for_pdf.get(k), go.Figure)])
                    ordered_keys_for_pdf.extend(sub_miss_order)
                    ordered_keys_for_pdf.extend(sub_closure_order)


                has_charts_to_render = False
                for title_key in ordered_keys_for_pdf:
                    fig_obj_cand = current_figs_for_pdf.get(title_key)
                    if fig_obj_cand and isinstance(fig_obj_cand, go.Figure):
                        has_charts_to_render = True
                        try:
                            img_bytes = fig_obj_cand.to_image(format='png', engine='kaleido', scale=1.2, width=700, height=450)
                            b64_img = base64.b64encode(img_bytes).decode()
                            chart_title_actual = fig_obj_cand.layout.title.text if fig_obj_cand.layout.title else title_key.replace("_"," ")
                            html_content += f"<h2>{chart_title_actual}</h2><img src='data:image/png;base64,{b64_img}' alt='{chart_title_actual}'/>"
                        except Exception as img_e:
                            st.sidebar.warning(f"Could not render chart '{title_key}' to image: {img_e}")

                if not has_charts_to_render: st.sidebar.warning("No chart figures were successfully rendered for PDF.")
                else:
                    html_content += "</body></html>"
                    pdf_bytes = generate_pdf(html_content, wk_path=wk_path)
                    if pdf_bytes: st.session_state[f'pdf_data_visuals_{active_pdf_visuals_type_key}'] = pdf_bytes; st.sidebar.success("Visuals PDF ready.")
                    else: st.session_state.pop(f'pdf_data_visuals_{active_pdf_visuals_type_key}', None)

    if f'pdf_data_visuals_{active_pdf_visuals_type_key}' in st.session_state and st.session_state[f'pdf_data_visuals_{active_pdf_visuals_type_key}']:
        dl_fn_prefix_vis = active_pdf_visuals_type_key.replace("_primary","").replace("_visuals","").replace("_or_","/")
        st.sidebar.download_button(f"Download {pdf_visual_button_label.replace('Prepare ','')}", st.session_state[f'pdf_data_visuals_{active_pdf_visuals_type_key}'], f"{dl_fn_prefix_vis}_visuals_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.pdf", "application/pdf", key=f"action_dl_visuals_{active_pdf_visuals_type_key}_pdf", on_click=lambda: st.session_state.pop(f'pdf_data_visuals_{active_pdf_visuals_type_key}', None))

    if st.sidebar.button("Prepare Data Table PDF (Primary)", key="prep_dashboard_table_pdf_primary"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        else:
            with st.spinner("Generating Data Table PDF..."):
                df_pdf_final_table = df_primary_period.copy()
                pdf_table_title_suffix = "Data"; html_table_content_for_pdf = ""
                pdf_table_cols_display = ['date','branch','report_type','upload_category','issues','area_manager','code']

                if is_primary_data_purely_complaints_check:
                    pdf_table_title_suffix = "Complaints Performance Data"
                    parsed_pdf_complaints = df_pdf_final_table['issues'].apply(parse_complaint_details)
                    df_pdf_final_table = pd.concat([df_pdf_final_table.reset_index(drop=True).drop(columns=['issues'],errors='ignore'), parsed_pdf_complaints.reset_index(drop=True)],axis=1)
                    df_pdf_final_table.rename(columns={'Type':'Complaint Type','Product':'Product Complained About','Quality Detail':'Quality Issue Detail','Order Error':'Order Error Detail'},inplace=True)
                    pdf_table_cols_display = ['date','branch','code','Complaint Type','Product Complained About','Quality Issue Detail','Order Error Detail']
                    for col_pdf_multi in MULTI_VALUE_COMPLAINT_COLS:
                        if col_pdf_multi in df_pdf_final_table.columns:
                            df_pdf_final_table[col_pdf_multi] = df_pdf_final_table[col_pdf_multi].apply(lambda x_list: ', '.join(map(str,x_list)) if isinstance(x_list, list) else x_list)

                elif is_primary_data_purely_missing_check and not df_missing_perf_results_primary.empty:
                    pdf_table_title_suffix = "Missing Performance Summary"
                    df_styled_missing_pdf = df_missing_perf_results_primary[['branch', 'done rate', 'missing rate', '_done_rate_numeric']].copy()
                    def get_color_for_pdf_local(val):
                        if val == 100.0: return ('#2ca02c', 'white');
                        if val >= 99.0: return ('#90EE90', 'black')
                        elif val >= 98.0: return ('#ADFF2F', 'black');
                        elif val >= 96.0: return ('#FFFF99', 'black')
                        elif val >= 93.0: return ('#FFD700', 'black');
                        elif val >= 90.0: return ('#FFA500', 'black')
                        elif val >= 85.0: return ('#FF7F50', 'white');
                        else: return ('#FF6347', 'white')
                    def style_row_for_pdf_local(row_series):
                        bg_color_l, text_color_l = get_color_for_pdf_local(row_series['_done_rate_numeric'])
                        return pd.Series({'done rate': f'background-color: {bg_color_l}; color: {text_color_l}; text-align: right;',
                                          'missing rate': f'background-color: {bg_color_l}; color: {text_color_l}; text-align: right;'})
                    html_table_content_for_pdf = df_styled_missing_pdf.style.apply(style_row_for_pdf_local, axis=1) \
                        .set_properties(**{'text-align': 'left', 'min-width': '150px', 'font-weight': 'bold'}, subset=['branch']) \
                        .set_table_styles([{'selector': 'th', 'props': 'background-color: #E8E8E8; text-align: center; font-weight: bold; padding: 5px;'},
                                           {'selector': 'td', 'props': 'padding: 5px; border: 1px solid #ddd;'},
                                           {'selector': 'thead th:first-child', 'props': 'text-align: left;'}]) \
                        .hide(axis='index').to_html(columns=['branch', 'done rate', 'missing rate'])

                elif is_primary_data_purely_complaint_closure_check:
                    pdf_table_title_suffix = f"{CLOSURE_REPORT_TYPE_NAME} Data"
                    html_table_content_for_pdf = f"<h2>Summary by Managers</h2>"

                    if df_closure_managers_summary_primary is not None:
                        _, manager_disp_df_pdf = _prepare_closure_summary_df(df_pdf_final_table.rename(columns={'issues':'Status'}), 'area_manager')
                        manager_disp_df_pdf['نسبة الاكتمال (%)'] = manager_disp_df_pdf['نسبة الاكتمال (%)'].apply(lambda x: f"{x:.1f}%")
                        html_table_content_for_pdf += manager_disp_df_pdf.reset_index().to_html(index=False, classes="dataframe", border=0)
                    else: html_table_content_for_pdf += "<p>No manager summary data.</p>"


                    html_table_content_for_pdf += f"<h2>Summary by Branches</h2>"
                    if df_closure_branches_summary_primary is not None:
                        _, branch_disp_df_pdf = _prepare_closure_summary_df(df_pdf_final_table.rename(columns={'issues':'Status'}), 'branch')
                        branch_disp_df_pdf['نسبة الاكتمال (%)'] = branch_disp_df_pdf['نسبة الاكتمال (%)'].apply(lambda x: f"{x:.1f}%")
                        html_table_content_for_pdf += branch_disp_df_pdf.sort_values("المجموع", ascending=False).reset_index().to_html(index=False, classes="dataframe", border=0)
                    else: html_table_content_for_pdf += "<p>No branch summary data.</p>"


                    if 'closure_low_completion_table_df' in figs_complaint_closure_primary:
                        low_comp_df_pdf_raw = figs_complaint_closure_primary['closure_low_completion_table_df']
                        df_low_comp_data_filtered_pdf = df_pdf_final_table[df_pdf_final_table['branch'].isin(low_comp_df_pdf_raw.index)].rename(columns={'issues':'Status'})
                        _, df_low_comp_display_pdf = _prepare_closure_summary_df(df_low_comp_data_filtered_pdf, 'branch')
                        
                        df_low_comp_display_pdf['نسبة الاكتمال (%)'] = df_low_comp_display_pdf['نسبة الاكتمال (%)'].apply(lambda x: f"{x:.1f}%")
                        df_low_comp_display_pdf.index.name = "الفرع"

                        html_table_content_for_pdf += f"<h2>Branches with &lt; 50% Completion</h2>"
                        html_table_content_for_pdf += df_low_comp_display_pdf.reset_index().to_html(index=False, classes="dataframe", border=0)
                else:
                    if 'shift' in df_pdf_final_table.columns and df_pdf_final_table['shift'].notna().any(): pdf_table_cols_display.append('shift')
                    if 'upload_category' in df_pdf_final_table.columns and 'report_type' in df_pdf_final_table.columns:
                        cond_pdf_table = (df_pdf_final_table['report_type'].astype(str).str.lower()=='issues') & (df_pdf_final_table['upload_category'].astype(str).str.lower()=='cctv')
                        df_pdf_final_table.loc[cond_pdf_table,'report_type'] = 'CCTV issues'

                if not html_table_content_for_pdf:
                    pdf_table_cols_exist_final = [col for col in pdf_table_cols_display if col in df_pdf_final_table.columns]
                    df_pdf_to_render_final = df_pdf_final_table[pdf_table_cols_exist_final].copy()
                    if 'date' in df_pdf_to_render_final.columns and pd.api.types.is_datetime64_any_dtype(df_pdf_to_render_final['date']):
                        df_pdf_to_render_final['date'] = df_pdf_to_render_final['date'].dt.strftime('%Y-%m-%d')
                    html_table_content_for_pdf = df_pdf_to_render_final.to_html(index=False, classes="dataframe", border=0)

                html_full_for_table_pdf = f"<head><meta charset='utf-8'><title>Data Table Report</title><style>body{{font-family:Arial,sans-serif;margin:20px}}h1,h2{{text-align:center;color:#333;page-break-after:avoid}}table{{border-collapse:collapse;width:100%;margin-top:15px;font-size:0.8em;page-break-inside:auto}}tr{{page-break-inside:avoid;page-break-after:auto}}th,td{{border:1px solid #ddd;padding:6px;text-align:left;word-wrap:break-word}}th{{background-color:#f2f2f2}}.dataframe tbody tr:nth-of-type(even){{background-color:#f9f9f9}}@media print{{*{{-webkit-print-color-adjust:exact !important;color-adjust:exact !important;print-color-adjust:exact !important}}body{{background-color:white !important}}}}ul{{list-style-type:disc;padding-left:20px}}</style></head><body>"
                html_full_for_table_pdf += f"<h1>{pdf_table_title_suffix} Report</h1><h2>Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}</h2>"

                record_count_text = ""
                if is_primary_data_purely_missing_check and not df_missing_perf_results_primary.empty:
                    record_count_text = f"<p><strong>Branch Count in Summary:</strong> {len(df_missing_perf_results_primary)}</p>"
                elif is_primary_data_purely_complaint_closure_check:
                    closure_summary_df_for_pdf = figs_complaint_closure_primary.get('closure_overall_summary_df')
                    if closure_summary_df_for_pdf is not None:
                        total_records_closure = closure_summary_df_for_pdf['count'].sum()
                        record_count_text = f"<p><strong>Total Records in Closure Summary:</strong> {total_records_closure}</p>"
                        record_count_text += "<ul>"
                        for status_pdf, row_pdf in closure_summary_df_for_pdf.iterrows():
                            percentage_pdf = (row_pdf['count'] / total_records_closure * 100) if total_records_closure > 0 else 0
                            record_count_text += f"<li>{status_pdf}: {row_pdf['count']} ({percentage_pdf:.1f}%)</li>"
                        record_count_text += "</ul>"
                elif not df_pdf_final_table.empty:
                     record_count_text = f"<p><strong>Total Records in Table:</strong> {len(df_pdf_final_table)}</p>"
                html_full_for_table_pdf += record_count_text
                html_full_for_table_pdf += html_table_content_for_pdf + "</body></html>"

                pdf_bytes_table = generate_pdf(html_full_for_table_pdf, wk_path=wk_path)
                if pdf_bytes_table: st.session_state.pdf_dashboard_primary_table_data = pdf_bytes_table; st.sidebar.success(f"{pdf_table_title_suffix} PDF (Primary) ready.")
                else: st.session_state.pop('pdf_dashboard_primary_table_data', None)

    if 'pdf_dashboard_primary_table_data' in st.session_state and st.session_state.pdf_dashboard_primary_table_data:
        pdf_dl_fn_suffix_tbl_final = "data_table"
        pdf_dl_label_tbl_final = "Data Table"
        if is_primary_data_purely_complaints_check: pdf_dl_fn_suffix_tbl_final, pdf_dl_label_tbl_final = "complaints_table", "Complaints Perf. Table"
        elif is_primary_data_purely_missing_check: pdf_dl_fn_suffix_tbl_final, pdf_dl_label_tbl_final = "missing_perf_table", "Missing Perf. Table"
        elif is_primary_data_purely_complaint_closure_check: pdf_dl_fn_suffix_tbl_final, pdf_dl_label_tbl_final = "complaint_closure_table", f"{CLOSURE_REPORT_TYPE_NAME} Table"

        st.sidebar.download_button(f"Download {pdf_dl_label_tbl_final} PDF (Primary)", st.session_state.pdf_dashboard_primary_table_data, f"{pdf_dl_fn_suffix_tbl_final}_report_primary_{primary_date_range[0]:%Y%m%d}-{primary_date_range[1]:%Y%m%d}.pdf", "application/pdf", key="action_dl_dashboard_table_pdf_primary", on_click=lambda: st.session_state.pop('pdf_dashboard_primary_table_data', None))
else: st.sidebar.info("No primary period data to download.")


if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.sidebar.markdown("Comparison Period Data (CSV):")
    if 'df_comp1' in locals() and not df_comp1.empty:
        try:
            csv_c1_data = df_comp1.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.sidebar.download_button(f"Download P1 ({comparison_date_range_1[0]:%b %d}-{comparison_date_range_1[1]:%b %d}) Data (CSV)", csv_c1_data, f"comparison_period1_data_{comparison_date_range_1[0]:%Y%m%d}-{comparison_date_range_1[1]:%Y%m%d}.csv", "text/csv", key="download_csv_comp1_data")
        except Exception as e: st.sidebar.error(f"P1 CSV Data Error: {e}")
    else: st.sidebar.caption(f"No data for P1 ({comparison_date_range_1[0]:%b %d}-{comparison_date_range_1[1]:%b %d})")

    if 'df_comp2' in locals() and not df_comp2.empty:
        try:
            csv_c2_data = df_comp2.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.sidebar.download_button(f"Download P2 ({comparison_date_range_2[0]:%b %d}-{comparison_date_range_2[1]:%b %d}) Data (CSV)", csv_c2_data, f"comparison_period2_data_{comparison_date_range_2[0]:%Y%m%d}-{comparison_date_range_2[1]:%Y%m%d}.csv", "text/csv", key="download_csv_comp2_data")
        except Exception as e: st.sidebar.error(f"P2 CSV Data Error: {e}")
    else: st.sidebar.caption(f"No data for P2 ({comparison_date_range_2[0]:%b %d}-{comparison_date_range_2[1]:%b %d})")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)")
