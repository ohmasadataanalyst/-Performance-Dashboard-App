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
    'CCTV': ['issues', 'submission time'], 'complaints': ['performance', 'اغلاق الشكاوي'],
    'missing': ['performance'], 'visits': [], 'meal training': ['performance', 'missing types']
}
all_categories = list(category_file_types.keys())
MULTI_VALUE_COMPLAINT_COLS = ['Complaint Type', 'Quality Issue Detail', 'Order Error Detail']

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

            df_excel = pd.read_excel(io.BytesIO(file_data))
            df_excel.columns = [str(col).strip().lower().replace('\n', ' ').replace('\r', '') for col in df_excel.columns]

            EXCEL_CODE_COL = 'code'; STD_EXCEL_ISSUES_COL = 'issues'; STD_EXCEL_BRANCH_COL = 'branch'
            STD_EXCEL_AM_COL = 'area manager'; STD_EXCEL_DATE_COL = 'date'
            CCTV_VIOLATION_COL = 'choose the violation - اختر المخالفه'; CCTV_SHIFT_COL = 'choose the shift - اختر الشفت'
            CCTV_DATE_COL = 'date submitted'; CCTV_BRANCH_COL = 'branch'; CCTV_AM_COL = 'area manager'
            COMP_BRANCH_COL = 'branch'; COMP_TYPE_COL = 'نوع الشكوى'; COMP_PROD_COL = 'الشكوى على اي منتج؟'
            COMP_QUAL_COL = 'فى حاله كانت الشكوى جوده برجاء تحديد نوع الشكوى'; COMP_ORDER_ERR_COL = 'فى حاله خطاء فى الطلب برجاء تحديد نوع الشكوى'
            COMP_DATE_COL = 'date'
            MISSING_PROJECT_COL = 'project'; MISSING_BRANCH_COL = 'branch'; MISSING_AM_COL = 'area manager'; MISSING_DATE_COL = 'date'
            
            req_cols_up = []
            date_col_excel = ''
            
            norm_cat = str(final_cat_val).lower().strip()
            norm_ft = str(final_ft_val).lower().strip() if final_ft_val else ""
            
            if norm_cat == 'cctv':
                req_cols_up = [EXCEL_CODE_COL, CCTV_VIOLATION_COL, CCTV_SHIFT_COL, CCTV_DATE_COL, CCTV_BRANCH_COL, CCTV_AM_COL]; date_col_excel = CCTV_DATE_COL
            elif norm_cat == 'complaints':
                if norm_ft == 'performance': req_cols_up = [COMP_BRANCH_COL, EXCEL_CODE_COL, COMP_TYPE_COL, COMP_PROD_COL, COMP_QUAL_COL, COMP_ORDER_ERR_COL, COMP_DATE_COL]; date_col_excel = COMP_DATE_COL
                elif norm_ft == 'اغلاق الشكاوي': st.sidebar.error("Schema for 'complaints / اغلاق الشكاوي' not implemented."); st.stop()
                else: st.sidebar.error(f"Invalid file type '{final_ft_val}' for 'complaints'."); st.stop()
            elif norm_cat == 'missing':
                if norm_ft == 'performance':
                    req_cols_up = [MISSING_PROJECT_COL, MISSING_BRANCH_COL, MISSING_AM_COL, MISSING_DATE_COL]; date_col_excel = MISSING_DATE_COL
                else: st.sidebar.error(f"Invalid file type '{final_ft_val}' for 'missing'."); st.stop()
            elif norm_cat == 'visits':
                req_cols_up = [EXCEL_CODE_COL, STD_EXCEL_BRANCH_COL, STD_EXCEL_AM_COL, STD_EXCEL_ISSUES_COL, STD_EXCEL_DATE_COL]; date_col_excel = STD_EXCEL_DATE_COL
            else: 
                req_cols_up = [EXCEL_CODE_COL, STD_EXCEL_ISSUES_COL, STD_EXCEL_BRANCH_COL, STD_EXCEL_AM_COL, STD_EXCEL_DATE_COL]; date_col_excel = STD_EXCEL_DATE_COL

            missing_cols = [col for col in req_cols_up if col not in df_excel.columns]
            if missing_cols:
                st.sidebar.error(f"Excel for '{final_cat_val}/{final_ft_val or 'N/A'}' missing columns: {', '.join(missing_cols)}. Aborted.")
                st.sidebar.info(f"Normalized Excel columns: {list(df_excel.columns)}")
                st.sidebar.info(f"Expected: {req_cols_up}"); st.stop()

            if not date_col_excel or date_col_excel not in df_excel.columns: st.sidebar.error(f"Date column '{date_col_excel}' not found or not defined."); st.stop()
            
            df_excel['parsed_date'] = pd.to_datetime(df_excel[date_col_excel], errors='coerce')
            original_row_count = len(df_excel)
            df_excel.dropna(subset=['parsed_date'], inplace=True)
            rows_dropped_na_date = original_row_count - len(df_excel)
            if rows_dropped_na_date > 0:
                st.sidebar.warning(f"Dropped {rows_dropped_na_date} rows due to unparseable dates in '{date_col_excel}'.")

            if df_excel.empty: st.sidebar.error("No valid data after attempting to parse dates (all dates might be invalid or unparseable)."); st.stop()

            df_to_imp = df_excel[(df_excel['parsed_date'].dt.date >= imp_from) & (df_excel['parsed_date'].dt.date <= imp_to)].copy()
            
            if df_to_imp.empty: 
                st.sidebar.error(f"No rows found within the selected import date range ({imp_from.strftime('%Y-%m-%d')} to {imp_to.strftime('%Y-%m-%d')}). Please check Excel dates and your import range selection.")
                min_excel_dt_after_parse = df_excel['parsed_date'].min()
                max_excel_dt_after_parse = df_excel['parsed_date'].max()
                st.sidebar.info(f"Date range in (validly parsed) Excel data: {min_excel_dt_after_parse.strftime('%Y-%m-%d') if pd.notna(min_excel_dt_after_parse) else 'N/A'} to {max_excel_dt_after_parse.strftime('%Y-%m-%d') if pd.notna(max_excel_dt_after_parse) else 'N/A'}")
                st.stop()

            c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)', (up_file.name, current_user, timestamp_now, final_ft_val, final_cat_val, up_sub_date_str, sqlite3.Binary(file_data)))
            up_id = c.lastrowid
            unmapped_branches = set(); inserted_count = 0

            for _, row_data in df_to_imp.iterrows():
                issue_dt_str = row_data['parsed_date'].strftime('%Y-%m-%d')
                iss_val, am_val_row, shift_val_row = "N/A", "N/A", None
                excel_branch_str = "Unknown Branch"; code_from_excel_col = ""

                if norm_cat == 'complaints' and norm_ft == 'performance':
                    excel_branch_str = str(row_data.get(COMP_BRANCH_COL, "Unk Comp Branch"))
                    code_from_excel_col = str(row_data.get(EXCEL_CODE_COL, "")).strip()
                    am_val_row = "N/A - Complaints"
                    details_list = [f"Type: {str(row_data.get(COMP_TYPE_COL)).strip()}" if pd.notna(row_data.get(COMP_TYPE_COL)) else None,
                                    f"Product: {str(row_data.get(COMP_PROD_COL)).strip()}" if pd.notna(row_data.get(COMP_PROD_COL)) else None,
                                    f"Quality Detail: {str(row_data.get(COMP_QUAL_COL)).strip()}" if pd.notna(row_data.get(COMP_QUAL_COL)) else None,
                                    f"Order Error: {str(row_data.get(COMP_ORDER_ERR_COL)).strip()}" if pd.notna(row_data.get(COMP_ORDER_ERR_COL)) else None]
                    iss_val = "; ".join(filter(None, details_list)) or "No specific complaint details"
                elif norm_cat == 'cctv':
                    excel_branch_str = str(row_data.get(CCTV_BRANCH_COL, "Unk CCTV Branch"))
                    code_from_excel_col = str(row_data.get(EXCEL_CODE_COL, "")).strip()
                    am_val_row = str(row_data.get(CCTV_AM_COL, "N/A"))
                    iss_val = str(row_data.get(CCTV_VIOLATION_COL, "N/A"))
                    shift_val_row = str(row_data.get(CCTV_SHIFT_COL)) if pd.notna(row_data.get(CCTV_SHIFT_COL)) else None
                elif norm_cat == 'missing' and norm_ft == 'performance':
                    excel_branch_str = str(row_data.get(MISSING_BRANCH_COL, "Unk Missing Branch")).strip()
                    iss_val = str(row_data.get(MISSING_PROJECT_COL, "Unk Project")).strip() 
                    am_val_row = str(row_data.get(MISSING_AM_COL, "N/A")).strip()
                elif norm_cat == 'visits': 
                    excel_branch_str = str(row_data.get(STD_EXCEL_BRANCH_COL, "Unk Visit Branch"))
                    code_from_excel_col = str(row_data.get(EXCEL_CODE_COL, "")).strip()
                    am_val_row = str(row_data.get(STD_EXCEL_AM_COL, "N/A - Visits"))
                    iss_val = str(row_data.get(STD_EXCEL_ISSUES_COL, "Visit Logged"))
                else: 
                    excel_branch_str = str(row_data.get(STD_EXCEL_BRANCH_COL, "Unk Std Branch"))
                    code_from_excel_col = str(row_data.get(EXCEL_CODE_COL, "")).strip()
                    am_val_row = str(row_data.get(STD_EXCEL_AM_COL, "N/A"))
                    iss_val = str(row_data.get(STD_EXCEL_ISSUES_COL, "N/A"))

                std_branch_name = "Unknown Branch"; db_code_val = ""
                norm_excel_branch_str = excel_branch_str.strip().upper()
                extracted_code_match = re.search(r'\b([A-Z0-9]{2,5})\b(?![A-Z0-9])', norm_excel_branch_str)
                extracted_code = extracted_code_match.group(1).upper() if extracted_code_match else None

                if extracted_code and extracted_code in BRANCH_SCHEMA_NORMALIZED:
                    std_branch_name = BRANCH_SCHEMA_NORMALIZED[extracted_code]; db_code_val = extracted_code
                elif code_from_excel_col and code_from_excel_col.upper() in BRANCH_SCHEMA_NORMALIZED:
                    std_branch_name = BRANCH_SCHEMA_NORMALIZED[code_from_excel_col.upper()]; db_code_val = code_from_excel_col.upper()
                else:
                    match_found = False
                    for sc_code, sc_name in BRANCH_SCHEMA_NORMALIZED.items():
                        if norm_excel_branch_str == sc_name.upper():
                            std_branch_name = sc_name; db_code_val = sc_code; match_found = True; break
                    if not match_found:
                        std_branch_name = excel_branch_str; db_code_val = code_from_excel_col
                        unmapped_branches.add(f"{excel_branch_str} (Code: {db_code_val or 'N/A'})")
                if not db_code_val and standardized_branch_name != "Unknown Branch" and standardized_branch_name.upper() != excel_branch_str.upper() :
                    for sc_c, sc_n in BRANCH_SCHEMA_NORMALIZED.items():
                        if standardized_branch_name.upper() == sc_n.upper(): db_code_val = sc_c; break
                db_code_val = db_code_val or ""
                
                c.execute('INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type, shift) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                          (up_id, db_code_val, iss_val, std_branch_name, am_val_row, issue_dt_str, final_ft_val, shift_val_row))
                inserted_count += 1
            
            conn.commit()
            st.sidebar.success(f"Successfully imported {inserted_count} issues from '{up_file.name}'.")
            if unmapped_branches: st.sidebar.warning(f"Unmapped branches: {', '.join(sorted(list(unmapped_branches)))}. Review schema or data.")
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

default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk)

df_uploads_main_scope = pd.read_sql('SELECT id, filename, category, file_type, submission_date FROM uploads ORDER BY submission_date DESC, id DESC', conn)
scope_opts_main = ['All uploads'] + [f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) SubDate: {r['submission_date'] or 'N/A'}" for i,r in df_uploads_main_scope.iterrows()]
sel_disp_scope = st.sidebar.selectbox("Analyze Upload Batch:", scope_opts_main, key="sel_up_scope_main")
sel_id_scope = int(sel_disp_scope.split(' - ')[0]) if sel_disp_scope != 'All uploads' else None

df_all_issues = pd.read_sql('SELECT i.*, u.category as upload_category, u.id as upload_id_col FROM issues i JOIN uploads u ON u.id = i.upload_id', conn, parse_dates=['date'])
if df_all_issues.empty: st.warning("No issues data in DB."); st.stop()

min_dt_overall = df_all_issues['date'].min().date() if not df_all_issues['date'].isnull().all() else date.today()
max_dt_overall = df_all_issues['date'].max().date() if not df_all_issues['date'].isnull().all() else date.today()
if min_dt_overall > max_dt_overall: max_dt_overall = min_dt_overall

primary_date_range_selected = st.sidebar.date_input("Primary Date Range (Issue Dates):", value=[min_dt_overall, max_dt_overall], min_value=min_dt_overall, max_value=max_dt_overall, key="primary_date_range_filter_main")
if primary_date_range_selected and len(primary_date_range_selected) == 2:
    primary_date_range = [primary_date_range_selected[0], primary_date_range_selected[1]] if primary_date_range_selected[0] <= primary_date_range_selected[1] else [primary_date_range_selected[1], primary_date_range_selected[0]]
else: primary_date_range = [min_dt_overall, max_dt_overall]

branch_opts_main = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist())
sel_branch_main = st.sidebar.multiselect("Branch:", branch_opts_main, default=['All'], key="branch_filter_main")
cat_opts_main = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist())
sel_cat_main = st.sidebar.multiselect("Category (from Upload Batch):", cat_opts_main, default=['All'], key="category_filter_main")
am_opts_main = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist())
sel_am_main = st.sidebar.multiselect("Area Manager:", am_opts_main, default=['All'], key="area_manager_filter_main")
unique_ft_main = df_all_issues['report_type'].astype(str).unique()
filtered_ft_main = sorted([rt for rt in unique_ft_main if rt.lower() not in ['none', 'nan', '']])
ft_filter_opts_main = ['All'] + filtered_ft_main
sel_ft_main = st.sidebar.multiselect("File Type (from Upload Batch):", ft_filter_opts_main, default=['All'], key="file_type_filter_main")

st.sidebar.subheader("📊 Period Comparison")
enable_comp_main = st.sidebar.checkbox("Enable Period Comparison", key="enable_comp_checkbox_main")
comp_date_range_1, comp_date_range_2 = None, None
if enable_comp_main:
    st.sidebar.markdown("Comparison Period 1:")
    safe_p1_end = min(min_dt_overall + timedelta(days=6), max_dt_overall)
    comp_dr1_val = st.sidebar.date_input("Start & End (P1):", value=[min_dt_overall, safe_p1_end], min_value=min_dt_overall, max_value=max_dt_overall, key="comp_p1_filt")
    if comp_dr1_val and len(comp_dr1_val) == 2 and comp_dr1_val[0] <= comp_dr1_val[1]: comp_date_range_1 = comp_dr1_val
    else: st.sidebar.warning("P1: Invalid range."); comp_date_range_1 = None
    if comp_date_range_1:
        st.sidebar.markdown("Comparison Period 2:")
        def_p2_start = min(comp_date_range_1[1] + timedelta(days=1), max_dt_overall)
        def_p2_end = min(def_p2_start + timedelta(days=6), max_dt_overall)
        comp_dr2_val = st.sidebar.date_input("Start & End (P2):", value=[def_p2_start, def_p2_end], min_value=min_dt_overall, max_value=max_dt_overall, key="comp_p2_filt")
        if comp_dr2_val and len(comp_dr2_val) == 2 and comp_dr2_val[0] <= comp_dr2_val[1]: comp_date_range_2 = comp_dr2_val
        else: st.sidebar.warning("P2: Invalid range."); comp_date_range_2 = None
    else: comp_date_range_2 = None

df_primary_period_filtered = apply_general_filters(df_all_issues, sel_id_scope, sel_branch_main, sel_cat_main, sel_am_main, sel_ft_main)
if primary_date_range and len(primary_date_range) == 2:
    df_primary_period_filtered = df_primary_period_filtered[(df_primary_period_filtered['date'].dt.date >= primary_date_range[0]) & (df_primary_period_filtered['date'].dt.date <= primary_date_range[1])]
else: df_primary_period_filtered = pd.DataFrame(columns=df_all_issues.columns)

st.subheader(f"Filtered Data for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total records in primary period: {len(df_primary_period_filtered)}")

figs_primary_main, figs_complaints_primary_main, figs_missing_primary_main = {}, {}, {}
df_missing_perf_results_primary_main = pd.DataFrame()

if not df_primary_period_filtered.empty:
    is_purely_complaints_main = ((df_primary_period_filtered['upload_category'] == 'complaints').all() and 
                                (df_primary_period_filtered['report_type'] == 'performance').all() and 
                                df_primary_period_filtered['upload_category'].nunique() == 1 and 
                                df_primary_period_filtered['report_type'].nunique() == 1)
    is_purely_missing_main = ((df_primary_period_filtered['upload_category'] == 'missing').all() and 
                             (df_primary_period_filtered['report_type'] == 'performance').all() and 
                             df_primary_period_filtered['upload_category'].nunique() == 1 and 
                             df_primary_period_filtered['report_type'].nunique() == 1)

    if is_purely_complaints_main:
        st.subheader("Complaints Performance Dashboard (Primary Period)")
        figs_complaints_primary_main = display_complaints_performance_dashboard(df_primary_period_filtered.copy(), figs_complaints_primary_main)
    elif is_purely_missing_main:
        figs_missing_primary_main, df_missing_perf_results_primary_main = display_missing_performance_dashboard(df_primary_period_filtered.copy(), figs_missing_primary_main, primary_date_range, "(Primary Period)")
    else:
        st.subheader("General Performance Analysis (Primary Period)")
        figs_primary_main = display_general_dashboard(df_primary_period_filtered.copy(), figs_primary_main)
        
        df_compl_subset_main = df_primary_period_filtered[(df_primary_period_filtered['upload_category'] == 'complaints') & (df_primary_period_filtered['report_type'] == 'performance')].copy()
        if not df_compl_subset_main.empty:
            st.markdown("---"); st.subheader("Complaints Analysis (Subset of Primary Period)")
            temp_figs_compl_sub_main = display_complaints_performance_dashboard(df_compl_subset_main, {})
            for k, v in temp_figs_compl_sub_main.items(): figs_primary_main[f"Subset_Complaints_{k}"] = v
        
        df_miss_subset_main = df_primary_period_filtered[(df_primary_period_filtered['upload_category'] == 'missing') & (df_primary_period_filtered['report_type'] == 'performance')].copy()
        if not df_miss_subset_main.empty:
            st.markdown("---"); st.subheader("Missing Tasks Analysis (Subset of Primary Period)")
            temp_figs_miss_sub_main, _ = display_missing_performance_dashboard(df_miss_subset_main, {}, primary_date_range, "(Subset of Primary)")
            for k, v in temp_figs_miss_sub_main.items(): figs_primary_main[f"Subset_Missing_{k}"] = v
    
    st.markdown("---")
    if st.button("🏆 Show Branch Rankings (Current Filters)", key="show_rankings_button_main"):
        if not df_primary_period_filtered.empty and 'branch' in df_primary_period_filtered.columns:
            st.subheader(f"Branch Performance Ranking (Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d})")
            if is_purely_missing_main and not df_missing_perf_results_primary_main.empty:
                st.markdown("_Based on 'Missing Rate'. Lower is better._")
                ranked_miss_df_main = df_missing_perf_results_primary_main.sort_values(by='_missing_rate_numeric', ascending=True).copy()
                ranked_miss_df_main['Rank'] = ranked_miss_df_main['_missing_rate_numeric'].rank(method='min', ascending=True).astype(int)
                st.dataframe(ranked_miss_df_main[['Rank', 'branch', 'done rate', 'missing rate']].reset_index(drop=True), use_container_width=True)
                if len(ranked_miss_df_main) > 1:
                    rank_cols = st.columns(2); top_n = min(10, len(ranked_miss_df_main))
                    with rank_cols[0]: fig_top = create_bar_chart(ranked_miss_df_main.head(top_n), 'branch', chart_title=f"Top {top_n} (Lowest Missing)", sort_values_by='_missing_rate_numeric', sort_ascending=True); st.plotly_chart(fig_top, use_container_width=True) if fig_top else None
                    with rank_cols[1]: fig_bot = create_bar_chart(ranked_miss_df_main.tail(top_n).sort_values('_missing_rate_numeric',ascending=False), 'branch', chart_title=f"Bottom {top_n} (Highest Missing)", sort_values_by='_missing_rate_numeric', sort_ascending=False); st.plotly_chart(fig_bot, use_container_width=True) if fig_bot else None
            else:
                st.markdown("_Based on total count of issues/complaints. Lower count is better._")
                branch_counts_main = df_primary_period_filtered.groupby('branch').size().reset_index(name='Total Issues/Complaints').sort_values(by='Total Issues/Complaints', ascending=True)
                branch_counts_main['Rank'] = branch_counts_main['Total Issues/Complaints'].rank(method='min', ascending=True).astype(int)
                st.dataframe(branch_counts_main[['Rank', 'branch', 'Total Issues/Complaints']].reset_index(drop=True), use_container_width=True)
                if len(branch_counts_main) > 1:
                    rank_cols = st.columns(2); top_n = min(10, len(branch_counts_main))
                    with rank_cols[0]: fig_top = create_bar_chart(branch_counts_main.head(top_n), 'branch', chart_title=f"Top {top_n} (Best)", sort_values_by='Total Issues/Complaints', sort_ascending=True); st.plotly_chart(fig_top, use_container_width=True) if fig_top else None
                    with rank_cols[1]: fig_bot = create_bar_chart(branch_counts_main.tail(top_n).sort_values('Total Issues/Complaints',ascending=False), 'branch', chart_title=f"Bottom {top_n} (Needs Improvement)", sort_values_by='Total Issues/Complaints', sort_ascending=False); st.plotly_chart(fig_bot, use_container_width=True) if fig_bot else None
        else: st.info("No data or branch info for rankings with current filters.")
else:
    st.info("No data matches the current filter criteria for the primary period.")

if enable_comp_main and comp_date_range_1 and comp_date_range_2: # Period Comparison Display
    st.markdown("---"); st.header("📊 Period Comparison Results")
    df_comp1_all_main = apply_general_filters(df_all_issues, sel_id_scope, sel_branch_main, sel_cat_main, sel_am_main, sel_ft_main)
    df_comp1_main = df_comp1_all_main[(df_comp1_all_main['date'].dt.date >= comp_date_range_1[0]) & (df_comp1_all_main['date'].dt.date <= comp_date_range_1[1])].copy()
    df_comp2_all_main = apply_general_filters(df_all_issues, sel_id_scope, sel_branch_main, sel_cat_main, sel_am_main, sel_ft_main)
    df_comp2_main = df_comp2_all_main[(df_comp2_all_main['date'].dt.date >= comp_date_range_2[0]) & (df_comp2_all_main['date'].dt.date <= comp_date_range_2[1])].copy()
    p1_lab, p2_lab = f"P1 ({comp_date_range_1[0]:%b %d}-{comp_date_range_1[1]:%b %d})", f"P2 ({comp_date_range_2[0]:%b %d}-{comp_date_range_2[1]:%b %d})"
    if df_comp1_main.empty and df_comp2_main.empty: st.info("No data for comparison in either period.")
    else:
        df_comp1_miss_data = df_comp1_main[(df_comp1_main['upload_category'] == 'missing') & (df_comp1_main['report_type'] == 'performance')].copy()
        df_comp2_miss_data = df_comp2_main[(df_comp2_main['upload_category'] == 'missing') & (df_comp2_main['report_type'] == 'performance')].copy()
        if not df_comp1_miss_data.empty or not df_comp2_miss_data.empty:
            st.subheader("Missing Tasks Performance Comparison")
            _, df_miss_res_c1 = display_missing_performance_dashboard(df_comp1_miss_data, {}, comp_date_range_1, f"({p1_lab})")
            st.markdown("---"); _, df_miss_res_c2 = display_missing_performance_dashboard(df_comp2_miss_data, {}, comp_date_range_2, f"({p2_lab})")
            if not df_miss_res_c1.empty and not df_miss_res_c2.empty:
                df_miss_comp_chart = pd.merge(df_miss_res_c1[['branch', '_done_rate_numeric']].rename(columns={'_done_rate_numeric': p1_lab}), df_miss_res_c2[['branch', '_done_rate_numeric']].rename(columns={'_done_rate_numeric': p2_lab}), on='branch', how='outer').fillna(0).melt(id_vars='branch', var_name='Period', value_name='Done Rate (%)')
                if not df_miss_comp_chart.empty: fig_m_comp = px.bar(df_miss_comp_chart, x='branch', y='Done Rate (%)', color='Period', barmode='group', title='Missing Tasks: Done Rate Comparison'); fig_m_comp.update_layout(yaxis_ticksuffix="%"); st.plotly_chart(fig_m_comp, use_container_width=True)
            st.markdown("---")
        st.info("Full Period Comparison for Complaints and General Issues is extensive and needs adaptation from previous full logic here.")

st.sidebar.subheader("Downloads")
st.info("Full Downloads section logic is extensive and needs adaptation from previous full logic here.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)")

def display_missing_performance_dashboard(df_missing_raw_period_data, figs_container, date_range_for_calc, dashboard_title_suffix=""):
    if df_missing_raw_period_data.empty and not list(BRANCH_SCHEMA_NORMALIZED.values()):
        st.info(f"No 'missing' task data for performance analysis {dashboard_title_suffix}.")
        return figs_container, pd.DataFrame()

    start_date_calc, end_date_calc = date_range_for_calc[0], date_range_for_calc[1]
    results = []
    all_branches_to_calculate_for = sorted(list(BRANCH_SCHEMA_NORMALIZED.values()))

    for branch_name in all_branches_to_calculate_for:
        total_expected_for_branch, total_missed_for_branch = 0, 0
        if 'issues' not in df_missing_raw_period_data.columns or 'branch' not in df_missing_raw_period_data.columns:
            pass 
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

    df_results = pd.DataFrame(results) # df_results now contains raw calculated data
    if df_results.empty: 
        st.info(f"No missing performance data to display {dashboard_title_suffix}.")
        return figs_container, pd.DataFrame()
        
    df_results_sorted = df_results.sort_values(by="_done_rate_numeric", ascending=False)

    def get_color_for_done_rate(done_rate_numeric): 
        if done_rate_numeric == 100.0: return ('#2ca02c', 'white') 
        if done_rate_numeric >= 99.0: return ('#90EE90', 'black') 
        elif done_rate_numeric >= 98.0: return ('#ADFF2F', 'black') 
        elif done_rate_numeric >= 96.0: return ('#FFFF99', 'black') 
        elif done_rate_numeric >= 93.0: return ('#FFD700', 'black') 
        elif done_rate_numeric >= 90.0: return ('#FFA500', 'black') 
        elif done_rate_numeric >= 85.0: return ('#FF7F50', 'white') 
        else: return ('#FF6347', 'white') 

    def apply_styling_to_row_missing(row):
        bg_color, text_color = get_color_for_done_rate(row['_done_rate_numeric'])
        return [f'background-color: {bg_color}; color: {text_color}; text-align: right;'] * 2

    st.subheader(f"Missing Tasks Performance by Branch {dashboard_title_suffix}")
    
    # df_for_styling now correctly uses df_results_sorted
    df_for_styling = df_results_sorted[['branch', 'done rate', 'missing rate', '_done_rate_numeric']].copy()

    html_table = df_for_styling.style \
        .apply(apply_styling_to_row_missing, axis=1, subset=['done rate', 'missing rate']) \
        .set_properties(**{'text-align': 'left', 'min-width': '150px', 'font-weight': 'bold'}, subset=['branch']) \
        .set_properties(**{'text-align': 'right'}, subset=['done rate', 'missing rate']) \
        .set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#E8E8E8'), ('text-align', 'center'), ('font-weight', 'bold'), ('padding', '5px')]},
            {'selector': 'td', 'props': [('padding', '5px'), ('border', '1px solid #ddd')]},
            {'selector': 'thead th:first-child', 'props': [('text-align', 'left')]} 
        ]) \
        .hide(axis='index') \
        .set_table_attributes('class="dataframe styled-missing-table"')
    
    html_table_output = html_table.to_html(columns=['branch', 'done rate', 'missing rate'])
    
    html_table_output = html_table_output.replace("<th>branch</th>", "<th>Branch <small>↕</small></th>", 1) 
    html_table_output = html_table_output.replace("<th>done rate</th>", "<th>Done Rate <small>↕</small></th>", 1)
    html_table_output = html_table_output.replace("<th>missing rate</th>", "<th>Missing Rate <small>↕</small></th>", 1)

    st.markdown(html_table_output, unsafe_allow_html=True)
    
    figs_container[f'missing_performance_table_df{dashboard_title_suffix.replace(" ", "_")}'] = df_results_sorted 
    
    csv_missing_summary = df_results_sorted[['branch', 'done rate', 'missing rate']].to_csv(index=False).encode('utf-8-sig')
    st.download_button(f"Download Missing Summary (CSV) {dashboard_title_suffix}", csv_missing_summary, f"missing_performance{dashboard_title_suffix.replace(' ', '_')}.csv", "text/csv", key=f"download_csv_missing_summary{dashboard_title_suffix.replace(' ', '_')}")
    
    return figs_container, df_results_sorted
