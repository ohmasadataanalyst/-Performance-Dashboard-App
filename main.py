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
    file_type TEXT, category TEXT, submission_date TEXT, file BLOB
)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id INTEGER, code TEXT, issues TEXT,
    branch TEXT, area_manager TEXT, date TEXT, report_type TEXT, shift TEXT,
    FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE
)''')
conn.commit()

try:
    c.execute("PRAGMA table_info(uploads)")
    if 'submission_date' not in [col[1] for col in c.fetchall()]:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT"); conn.commit()
        if 'db_schema_updated_flag_uploads' not in st.session_state: st.session_state.db_schema_updated_flag_uploads = True
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not in st.session_state:
        st.session_state.db_critical_error_msg = f"Failed to update 'uploads' table schema: {e}"
try:
    c.execute("PRAGMA table_info(issues)")
    if 'shift' not in [col[1] for col in c.fetchall()]:
        c.execute("ALTER TABLE issues ADD COLUMN shift TEXT"); conn.commit()
        if 'db_schema_updated_flag_issues' not in st.session_state: st.session_state.db_schema_updated_flag_issues = True
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not in st.session_state:
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
    'missing': ['performance'], 'visits': [], 'meal training': ['performance', 'missing types']
}
all_categories = list(category_file_types.keys())

if 'db_critical_error_msg' in st.session_state: st.error(f"DB Startup Error: {st.session_state.db_critical_error_msg}"); del st.session_state.db_critical_error_msg
if 'db_schema_updated_flag_uploads' in st.session_state and st.session_state.db_schema_updated_flag_uploads: st.toast("DB 'uploads' table schema updated.", icon="ℹ️"); st.session_state.db_schema_updated_flag_uploads = False
if 'db_schema_updated_flag_issues' in st.session_state and st.session_state.db_schema_updated_flag_issues: st.toast("DB 'issues' table schema updated.", icon="ℹ️"); st.session_state.db_schema_updated_flag_issues = False

LOGO_PATH = "company_logo.png"

def check_login():
    if 'authenticated' not in st.session_state: st.session_state.update({'authenticated': False, 'user_name': None, 'user_role': None})
    if not st.session_state.authenticated:
        col1_lgn, col2_lgn = st.columns([2,6])
        with col1_lgn:
            try: st.image(LOGO_PATH, width=120)
            except Exception: pass
        with col2_lgn: st.title("📊 Login - Dashboard")
        st.subheader("Please log in to continue")
        with st.form("login_form"):
            username = st.text_input("Full Name:", key="auth_username_login").strip().lower()
            password = st.text_input("Password:", type="password", key="auth_password_login")
            submitted = st.form_submit_button("Login")
            if submitted:
                if username in db_admin and bcrypt.checkpw(password.encode(), db_admin[username]):
                    st.session_state.update({'authenticated': True, 'user_name': username, 'user_role': 'admin'}); st.rerun()
                elif username in view_only and password: # Any non-empty password for view-only
                    st.session_state.update({'authenticated': True, 'user_name': username, 'user_role': 'view_only'}); st.rerun()
                elif username in view_only and not password: st.error("Password cannot be empty for view-only users.")
                elif username or password: st.error("Invalid username or password.")
                else: st.info("Please enter your credentials.")
        return False
    return True

if not check_login(): st.stop()

col1_main_title, col2_main_title = st.columns([2, 6])
with col1_main_title:
    try: st.image(LOGO_PATH, width=120)
    except Exception as e: st.error(f"Error loading logo: {e}")
with col2_main_title: st.title("📊 Classic Dashboard for Performance")

st.sidebar.success(f"Logged in as: {st.session_state.get('user_name', 'N/A').title()} ({st.session_state.get('user_role', 'N/A')})")
if st.sidebar.button("Logout", key="logout_button_main"):
    st.session_state.update({'authenticated': False, 'user_name': None, 'user_role': None}); st.rerun()

is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.session_state.get('user_name', 'Unknown User')

def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path or wk_path == "not found": st.error("wkhtmltopdf path not set."); return None
    try:
        import pdfkit; config = pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8", 'load-error-handling': 'ignore', 'load-media-error-handling': 'ignore'}
        pdfkit.from_string(html, fname, configuration=config, options=options)
        with open(fname, 'rb') as f: return f.read()
    except Exception as e: st.error(f"PDF error: {e}"); return None

st.sidebar.header("🔍 Filters & Options")

if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("Set parameters, select Excel, specify import date range, then upload.")
    selected_category_admin = st.sidebar.selectbox("Category for upload", options=all_categories, key="admin_category_select")
    valid_file_types_admin = category_file_types.get(selected_category_admin, [])
    selected_file_type_admin = st.sidebar.selectbox("File type for upload", options=valid_file_types_admin, key="admin_file_type_select", disabled=(not valid_file_types_admin), help="Options change based on category.")
    st.sidebar.markdown("**Filter Excel Data by Date Range for this Import:**")
    import_from_date_val = st.sidebar.date_input("Import Data From Date:", value=date.today() - timedelta(days=7), key="import_from_date_upload")
    import_to_date_val = st.sidebar.date_input("Import Data To Date:", value=date.today(), key="import_to_date_upload")
    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if upload_btn:
        final_category = selected_category_admin
        final_file_type = selected_file_type_admin
        imp_from_dt = import_from_date_val
        imp_to_dt = import_to_date_val
        requires_file_type = bool(valid_file_types_admin)

        if requires_file_type and not final_file_type: st.sidebar.warning(f"Please select a file type for '{final_category}'.")
        elif not up: st.sidebar.error("Please select an Excel file.")
        elif not imp_from_dt or not imp_to_dt: st.sidebar.error("Please select both Import From and To Dates.")
        elif imp_from_dt > imp_to_dt: st.sidebar.error("Import From Date cannot be after Import To Date.")
        else:
            if not requires_file_type: final_file_type = None
            data = up.getvalue()
            ts = datetime.now().isoformat()
            upload_submission_date_str = imp_from_dt.isoformat()
            try:
                c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                          (up.name, current_user, final_file_type, final_category, upload_submission_date_str))
                if c.fetchone()[0] > 0:
                    st.sidebar.warning(f"Upload for '{up.name}' (Cat: {final_category}, Type: {final_file_type or 'N/A'}, Import From: {upload_submission_date_str}) seems duplicate.")
                else:
                    df_excel_full = pd.read_excel(io.BytesIO(data))
                    df_excel_full.columns = [col.strip().lower().replace('\n', ' ').replace('\r', '') for col in df_excel_full.columns]
                    
                    missing_cols_detected = []
                    date_column_in_excel, branch_column_in_excel = '', 'branch'
                    
                    if final_category == 'CCTV':
                        required_cols_cctv = ['code', 'choose the violation - اختر المخالفه', 'choose the shift - اختر الشفت', 'date submitted', 'branch', 'area manager']
                        missing_cols_detected.extend([col for col in required_cols_cctv if col not in df_excel_full.columns])
                        date_column_in_excel = 'date submitted'
                    else:
                        required_cols_std = ['code', 'issues', 'branch', 'area manager', 'date']
                        missing_cols_detected.extend([col for col in required_cols_std if col not in df_excel_full.columns])
                        date_column_in_excel = 'date'

                    if 'code' not in df_excel_full.columns: missing_cols_detected.append('code')
                    if branch_column_in_excel not in df_excel_full.columns: missing_cols_detected.append(branch_column_in_excel)
                    
                    unique_missing_cols = list(set(missing_cols_detected))
                    if unique_missing_cols:
                        st.sidebar.error(f"Excel for '{final_category}' is missing: {', '.join(unique_missing_cols)}. Aborted.")
                    else:
                        df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full[date_column_in_excel], dayfirst=True, errors='coerce')
                        original_rows = len(df_excel_full)
                        df_excel_full.dropna(subset=['parsed_date'], inplace=True)
                        if len(df_excel_full) < original_rows:
                            st.sidebar.warning(f"{original_rows - len(df_excel_full)} Excel rows dropped due to invalid/missing dates in '{date_column_in_excel}'.")
                        
                        if df_excel_full.empty: st.sidebar.error(f"No valid data rows left in Excel after date parsing. Aborted.")
                        else:
                            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()
                            if df_to_import.empty:
                                st.sidebar.info(f"No rows in '{up.name}' match import range ({imp_from_dt:%Y-%m-%d} to {imp_to_dt:%Y-%m-%d}).")
                            else:
                                c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                          (up.name, current_user, ts, final_file_type, final_category, upload_submission_date_str, sqlite3.Binary(data)))
                                upload_id = c.lastrowid
                                unmapped_codes = set()
                                for _, row in df_to_import.iterrows():
                                    code_val, branch_excel = str(row.get('code', "")), str(row.get(branch_column_in_excel, "Unknown"))
                                    norm_code = code_val.strip().upper()
                                    std_branch = BRANCH_SCHEMA_NORMALIZED.get(norm_code, branch_excel)
                                    if norm_code and norm_code not in BRANCH_SCHEMA_NORMALIZED: unmapped_codes.add(norm_code)
                                    
                                    issue_val = row['choose the violation - اختر المخالفه'] if final_category == 'CCTV' else row['issues']
                                    shift_val = row['choose the shift - اختر الشفت'] if final_category == 'CCTV' else None
                                    am_val = row['area manager']
                                    issue_date_str = row['parsed_date'].strftime('%Y-%m-%d')
                                    
                                    c.execute('''INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type, shift)
                                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                              (upload_id, code_val, issue_val, std_branch, am_val, issue_date_str, final_file_type, shift_val))
                                if unmapped_codes: st.sidebar.warning(f"Unmapped codes (original name used): {', '.join(sorted(list(unmapped_codes)))}.")
                                conn.commit(); st.sidebar.success(f"Imported {len(df_to_import)} issues from '{up.name}'."); st.rerun()
            except sqlite3.Error as e: conn.rollback(); st.sidebar.error(f"DB error: {e}. Rolled back.")
            except KeyError as e: conn.rollback(); st.sidebar.error(f"Column error: {e} not in Excel for '{final_category}'. Rolled back.")
            except Exception as e: conn.rollback(); st.sidebar.error(f"Error processing '{up.name}': {e}. Rolled back.")

    st.sidebar.subheader("Manage Submissions")
    df_uploads_del = pd.read_sql('SELECT id, filename, uploader, category, file_type, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
    df_uploads_del['display_date'] = df_uploads_del['submission_date'].apply(lambda d: datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A")
    del_opts = ['Select ID to Delete'] + [f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) Imp.From: {r['display_date']}" for _, r in df_uploads_del.iterrows()]
    del_choice = st.sidebar.selectbox("🗑️ Delete Submission Batch:", del_opts, key="delete_sub_select")
    if del_choice != 'Select ID to Delete':
        del_id = int(del_choice.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id}", key=f"confirm_del_btn_{del_id}", type="primary"):
            try: c.execute('DELETE FROM uploads WHERE id=?', (del_id,)); conn.commit(); st.sidebar.success(f"Deleted submission {del_id}."); st.rerun()
            except sqlite3.Error as e: conn.rollback(); st.sidebar.error(f"Failed to delete: {e}")

    st.sidebar.subheader("Database Management")
    st.sidebar.markdown("""**To persist data changes:** 1. Click "Download DB". 2. Rename to `issues.db`. 3. Replace in Git project. 4. Commit & push.""")
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as fp: db_bytes = fp.read()
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.sidebar.download_button(label="Download Database Backup", data=db_bytes, file_name=f"issues_backup_{ts_str}.db", mime="application/vnd.sqlite3", key="dl_db_btn")
    else: st.sidebar.warning(f"'{DB_PATH}' not found.")

default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk)

df_uploads_main = pd.read_sql('SELECT id, filename, category, file_type, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
df_uploads_main['display_date'] = df_uploads_main['submission_date'].apply(lambda d: datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A")
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) Imp.From: {r['display_date']}" for _, r in df_uploads_main.iterrows()]
sel_display_scope = st.sidebar.selectbox("Select upload batch to analyze:", scope_opts, key="select_upload_scope")
sel_upload_id = int(sel_display_scope.split(' - ')[0]) if sel_display_scope != 'All uploads' else None

df_all_issues = pd.read_sql('SELECT i.*, u.category as upload_category, u.id as upload_id_col FROM issues i JOIN uploads u ON u.id = i.upload_id', conn, parse_dates=['date'])
if df_all_issues.empty: st.warning("No issues data in database."); st.stop()

st.sidebar.subheader("Dashboard Filters")
min_date_overall, max_date_overall = (df_all_issues['date'].min().date() if pd.notna(df_all_issues['date'].min()) else date.today(),
                                      df_all_issues['date'].max().date() if pd.notna(df_all_issues['date'].max()) else date.today())
primary_date_range = st.sidebar.date_input("Primary Date Range (Issue Dates):",
                                           value=[min_date_overall, max_date_overall] if min_date_overall <= max_date_overall else [max_date_overall, min_date_overall],
                                           min_value=min_date_overall, max_value=max_date_overall, key="primary_date_filter")
if not primary_date_range or len(primary_date_range) != 2: primary_date_range = [min_date_overall, max_date_overall]

sel_branch = st.sidebar.multiselect("Branch:", ['All'] + sorted(df_all_issues['branch'].astype(str).unique()), default=['All'], key="branch_flt")
sel_cat = st.sidebar.multiselect("Category:", ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique()), default=['All'], key="cat_flt")
sel_am = st.sidebar.multiselect("Area Manager:", ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique()), default=['All'], key="am_flt")
sel_ft = st.sidebar.multiselect("File Type:", ['All'] + sorted(df_all_issues['report_type'].astype(str).unique()), default=['All'], key="ft_flt")

st.sidebar.subheader("📊 Period Comparison")
enable_comp = st.sidebar.checkbox("Enable Period Comparison", key="enable_comp_cb")
comp_range_1, comp_range_2 = None, None
if enable_comp:
    st.sidebar.markdown("**Comparison Period 1 (Issue Dates):**")
    def_p1_end = min(min_date_overall + timedelta(days=6), max_date_overall)
    def_p1_end = max(def_p1_end, min_date_overall)
    comp_range_1_val = st.sidebar.date_input("Start & End (P1):", value=[min_date_overall, def_p1_end], min_value=min_date_overall, max_value=max_date_overall, key="comp_p1_flt")
    if comp_range_1_val and len(comp_range_1_val) == 2:
        comp_range_1 = comp_range_1_val
        st.sidebar.markdown("**Comparison Period 2 (Issue Dates):**")
        def_p2_start = min(comp_range_1[1] + timedelta(days=1), max_date_overall)
        def_p2_start = max(def_p2_start, min_date_overall)
        def_p2_end = min(def_p2_start + timedelta(days=6), max_date_overall)
        def_p2_end = max(def_p2_end, def_p2_start)
        comp_range_2_val = st.sidebar.date_input("Start & End (P2):", value=[def_p2_start, def_p2_end], min_value=min_date_overall, max_value=max_date_overall, key="comp_p2_flt")
        if comp_range_2_val and len(comp_range_2_val) == 2: comp_range_2 = comp_range_2_val
        else: comp_range_2 = None
    else: comp_range_1, comp_range_2 = None, None

def apply_filters(df, up_id, branches, cats, ams, fts):
    df_f = df.copy()
    if up_id: df_f = df_f[df_f['upload_id_col'] == up_id]
    if 'All' not in branches: df_f = df_f[df_f['branch'].isin(branches)]
    if 'All' not in cats: df_f = df_f[df_f['upload_category'].isin(cats)]
    if 'All' not in ams: df_f = df_f[df_f['area_manager'].isin(ams)]
    if 'All' not in fts: df_f = df_f[df_f['report_type'].isin(fts)]
    return df_f

df_filtered_general = apply_filters(df_all_issues, sel_upload_id, sel_branch, sel_cat, sel_am, sel_ft)
df_primary_period = df_filtered_general.copy()
if primary_date_range and len(primary_date_range) == 2:
    s_date, e_date = primary_date_range[0], primary_date_range[1]
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']):
        df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= s_date) & (df_primary_period['date'].dt.date <= e_date)]
else:
    df_primary_period = pd.DataFrame(columns=df_filtered_general.columns) # Ensure empty with same columns

st.subheader(f"Filtered Issues for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total issues found in primary period: {len(df_primary_period)}")

def create_chart(df_src, col, chart_type='bar', title_sfx=""):
    title = f"Issues by {col.replace('_',' ').title()} {title_sfx}"
    if col not in df_src.columns or df_src[col].isnull().all(): return None
    data = df_src.astype({col: str}).groupby(col).size().reset_index(name='count')
    if data.empty: return None
    if chart_type == 'bar': return px.bar(data.sort_values('count', ascending=False), x=col, y='count', title=title, template="plotly_white")
    if chart_type == 'pie': return px.pie(data, names=col, values='count', title=title, hole=0.3, template="plotly_white")
    return None

if df_primary_period.empty:
    st.info("No data matches current filter criteria for the primary period.")
else:
    figs_primary = {}
    chart_cols = st.columns(2)
    with chart_cols[0]:
        figs_primary['Branch'] = create_chart(df_primary_period, 'branch', 'bar', '(Primary)')
        if figs_primary['Branch']: st.plotly_chart(figs_primary['Branch'], use_container_width=True)
        
        df_rt_viz = df_primary_period.copy()
        if 'upload_category' in df_rt_viz.columns and 'report_type' in df_rt_viz.columns:
            cond = (df_rt_viz['report_type'] == 'issues') & (df_rt_viz['upload_category'] == 'CCTV')
            df_rt_viz.loc[cond, 'report_type'] = 'CCTV issues'
        figs_primary['Report Type'] = create_chart(df_rt_viz, 'report_type', 'bar', '(Primary)')
        if figs_primary['Report Type']: st.plotly_chart(figs_primary['Report Type'], use_container_width=True)
    with chart_cols[1]:
        figs_primary['Area Manager'] = create_chart(df_primary_period, 'area_manager', 'pie', '(Primary)')
        if figs_primary['Area Manager']: st.plotly_chart(figs_primary['Area Manager'], use_container_width=True)
        figs_primary['Category'] = create_chart(df_primary_period, 'upload_category', 'bar', '(Primary)')
        if figs_primary['Category']: st.plotly_chart(figs_primary['Category'], use_container_width=True)

    if 'shift' in df_primary_period.columns and df_primary_period['shift'].notna().any():
        with st.container():
            figs_primary['Shift'] = create_chart(df_primary_period[df_primary_period['shift'].notna()], 'shift', 'bar', '(Primary - CCTV Shifts)')
            if figs_primary['Shift']: st.plotly_chart(figs_primary['Shift'], use_container_width=True)

    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']) and not df_primary_period['date'].isnull().all():
        trend_data = df_primary_period.groupby(df_primary_period['date'].dt.date).size().reset_index(name='issues')
        trend_data['date'] = pd.to_datetime(trend_data['date']); trend_data.sort_values('date', inplace=True)
        if not trend_data.empty:
            win = max(2, min(7, len(trend_data)))
            trend_data[f'{win}-Day MA'] = trend_data['issues'].rolling(window=win, center=True, min_periods=1).mean().round(1)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=trend_data['date'], y=trend_data['issues'], name='Daily Issues', marker_color='lightblue', hovertemplate="<b>%{x|%A, %b %d}</b><br>Issues: %{y}<extra></extra>"))
            fig_trend.add_trace(go.Scatter(x=trend_data['date'], y=trend_data[f'{win}-Day MA'], name=f'{win}-Day Moving Avg.', mode='lines+markers', line=dict(color='royalblue', width=2), marker=dict(size=5), hovertemplate="<b>%{x|%A, %b %d}</b><br>Moving Avg: %{y:.1f}<extra></extra>"))
            fig_trend.update_layout(title='Issues Trend (Primary Period)', xaxis_title='Date', yaxis_title='Number of Issues', template="plotly_white", hovermode="x unified")
            figs_primary['Trend'] = fig_trend; st.plotly_chart(figs_primary['Trend'], use_container_width=True)

    if len(df_primary_period) < 50 or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.subheader("Detailed Records (Primary Period - Filtered)")
        disp_cols = ['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']
        if 'shift' in df_primary_period.columns and df_primary_period['shift'].notna().any(): disp_cols.append('shift')
        
        df_disp = df_primary_period[disp_cols].copy()
        if 'upload_category' in df_disp.columns and 'report_type' in df_disp.columns:
            cond_tbl = (df_disp['report_type'] == 'issues') & (df_disp['upload_category'] == 'CCTV')
            df_disp.loc[cond_tbl, 'report_type'] = 'CCTV issues'
        if pd.api.types.is_datetime64_any_dtype(df_disp['date']): df_disp['date'] = df_disp['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_disp, use_container_width=True)

    st.subheader("Top Issues (Primary Period - Filtered)")
    if 'issues' in df_primary_period.columns and not df_primary_period['issues'].isnull().all():
        top_issues = df_primary_period['issues'].astype(str).value_counts().head(20).rename_axis('Issue/Violation').reset_index(name='Frequency')
        if not top_issues.empty: st.dataframe(top_issues, use_container_width=True)

if enable_comp and comp_range_1 and comp_range_2:
    st.markdown("---"); st.header("📊 Period Comparison Results (Based on Issue Dates)")
    # Placeholder for comparison logic:
    # For example, you would filter df_all_issues for comp_range_1 and comp_range_2
    # then generate similar charts or comparative statistics.
    # df_comp1 = apply_filters(df_all_issues, sel_upload_id, sel_branch, sel_cat, sel_am, sel_ft)
    # df_comp1 = df_comp1[(df_comp1['date'].dt.date >= comp_range_1[0]) & (df_comp1['date'].dt.date <= comp_range_1[1])]
    # df_comp2 = apply_filters(df_all_issues, sel_upload_id, sel_branch, sel_cat, sel_am, sel_ft)
    # df_comp2 = df_comp2[(df_comp2['date'].dt.date >= comp_range_2[0]) & (df_comp2['date'].dt.date <= comp_range_2[1])]
    # st.write(f"Period 1 ({comp_range_1[0]:%Y-%m-%d} to {comp_range_1[1]:%Y-%m-%d}): {len(df_comp1)} issues")
    # st.write(f"Period 2 ({comp_range_2[0]:%Y-%m-%d} to {comp_range_2[1]:%Y-%m-%d}): {len(df_comp2)} issues")
    st.info("Comparison logic is not fully implemented yet.") # Example message
    pass # Ensures the if-block is syntactically correct

st.sidebar.subheader("Downloads")
if 'df_primary_period' in locals() and not df_primary_period.empty:
    # Placeholder for download logic:
    try:
        csv_primary = df_primary_period.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="Download Primary Data (CSV)",
            data=csv_primary,
            file_name=f"primary_data_{primary_date_range[0]:%Y%m%d}_{primary_date_range[1]:%Y%m%d}.csv",
            mime="text/csv",
            key="download_primary_csv_btn"
        )
    except Exception as e:
        st.sidebar.error(f"Error preparing download: {e}")
    pass # Ensures the if-block is syntactically correct, even if download fails or is just this
else:
    st.sidebar.info("No primary data to download based on current filters.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)")
