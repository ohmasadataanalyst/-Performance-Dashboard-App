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
import os # For os.path.exists and os.path.basename

# Streamlit config MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- Database setup ---
DB_PATH = 'issues.db' # This will be created in your CWD if it doesn't exist
conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10) 
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
    file_type TEXT, category TEXT, 
    submission_date TEXT, 
    file BLOB
)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Good to have a PK on issues
    upload_id INTEGER, code TEXT, issues TEXT, branch TEXT, area_manager TEXT,
    date TEXT, 
    report_type TEXT, 
    FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE -- Added ON DELETE CASCADE
)''')
conn.commit()

# Check and add submission_date column if missing from uploads
# This is a one-time migration attempt
try:
    c.execute("PRAGMA table_info(uploads)")
    existing_columns = [column[1] for column in c.fetchall()]
    if 'submission_date' not in existing_columns:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        if 'db_schema_updated_flag' not in st.session_state:
            st.session_state.db_schema_updated_flag = True
except sqlite3.OperationalError as e:
    # This might happen if the column was added but the flag wasn't set, or other DB issues
    if "duplicate column name" not in str(e).lower() and 'db_critical_error_msg' not in st.session_state :
        st.session_state.db_critical_error_msg = f"Failed to update 'uploads' table schema: {e}"


# Credentials
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
    st.error(f"DB Startup Error: {st.session_state.db_critical_error_msg}")
    del st.session_state.db_critical_error_msg
if 'db_schema_updated_flag' in st.session_state and st.session_state.db_schema_updated_flag:
    st.toast("DB 'uploads' table schema updated.", icon="ℹ️")
    st.session_state.db_schema_updated_flag = False

LOGO_PATH = "company_logo.png" 

def check_login():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None
    if not st.session_state.authenticated:
        col1_login_title, col2_login_title = st.columns([2, 6])
        with col1_login_title:
            try: st.image(LOGO_PATH, width=120) 
            except Exception: pass 
        with col2_login_title: st.title("📊 Login - Dashboard")
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

col1_title, col2_title = st.columns([2, 6])
with col1_title:
    try: st.image(LOGO_PATH, width=120)
    except FileNotFoundError: st.error(f"Logo image not found at {LOGO_PATH}. Please check the path.") 
    except Exception as e: st.error(f"Error loading logo: {e}")
with col2_title: st.title("📊 Classic Dashboard for Performance")

user_name_display = st.session_state.get('user_name', "N/A").title()
user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main"):
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
    selected_category = st.sidebar.selectbox("Category for upload", options=all_categories, key="admin_category_select")
    valid_file_types = category_file_types.get(st.session_state.get("admin_category_select", all_categories[0]), [])
    selected_file_type = st.sidebar.selectbox("File type for upload", options=valid_file_types, key="admin_file_type_select",
                                            disabled=(not valid_file_types), help="Options change based on category.")
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
        
        if requires_file_type and not final_file_type: st.sidebar.warning(f"Please select a file type for '{final_category}'.")
        elif not up: st.sidebar.error("Please select an Excel file.")
        elif not imp_from_dt or not imp_to_dt: st.sidebar.error("Please select both Import From and To Dates.")
        elif imp_from_dt > imp_to_dt: st.sidebar.error("Import From Date cannot be after Import To Date.")
        else: 
            if not requires_file_type: final_file_type = None 
            data = up.getvalue(); ts = datetime.now().isoformat()
            upload_submission_date_str = imp_from_dt.isoformat() 
            try:
                c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                          (up.name, current_user, final_file_type, final_category, upload_submission_date_str))
                if c.fetchone()[0] > 0:
                    st.sidebar.warning(f"Upload batch for '{up.name}' (type: '{final_file_type}', cat: '{final_category}') with import start date '{upload_submission_date_str}' seems duplicate.")
                else:
                    df_excel_full = pd.read_excel(io.BytesIO(data))
                    df_excel_full.columns = [col.strip().lower() for col in df_excel_full.columns]
                    required_cols = ['code', 'issues', 'branch', 'area manager', 'date'] 
                    missing_cols = [col for col in required_cols if col not in df_excel_full.columns]
                    if missing_cols: st.sidebar.error(f"Excel missing: {', '.join(missing_cols)}. Aborted.")
                    else:
                        df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full['date'], dayfirst=True, errors='coerce')
                        original_excel_rows = len(df_excel_full); df_excel_full.dropna(subset=['parsed_date'], inplace=True) 
                        if len(df_excel_full) < original_excel_rows: st.sidebar.warning(f"{original_excel_rows - len(df_excel_full)} Excel rows dropped (invalid date).")
                        if df_excel_full.empty: st.sidebar.error("No valid data rows in Excel. Aborted.")
                        else:
                            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()
                            if df_to_import.empty: st.sidebar.info(f"No rows in '{up.name}' for import range: {imp_from_dt:%Y-%m-%d} to {imp_to_dt:%Y-%m-%d}.")
                            else:
                                c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                          (up.name, current_user, ts, final_file_type, final_category, upload_submission_date_str, sqlite3.Binary(data)))
                                upload_id = c.lastrowid 
                                for _, row in df_to_import.iterrows():
                                    issue_date_str = row['parsed_date'].strftime('%Y-%m-%d')
                                    c.execute('INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                              (upload_id, row['code'], row['issues'], row['branch'], row['area manager'], issue_date_str, final_file_type)) 
                                conn.commit(); st.sidebar.success(f"Imported {len(df_to_import)} issues from '{up.name}'."); st.rerun()
            except sqlite3.Error as e_sql: conn.rollback(); st.sidebar.error(f"DB error: {e_sql}. Rolled back.")
            except Exception as e_general: conn.rollback(); st.sidebar.error(f"Error processing '{up.name}': {e_general}. Rolled back.")

    st.sidebar.subheader("Manage Submissions")
    df_uploads_raw_for_delete = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn) # Fresh read
    df_uploads_raw_for_delete['display_submission_date_fmt'] = df_uploads_raw_for_delete['submission_date'].apply(lambda d: datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A")
    delete_opts_list = [(f"{row['id']} - {row['filename']} ({row['category']}/{row['file_type'] or 'N/A'}) Imp.From: {row['display_submission_date_fmt']}") for index, row in df_uploads_raw_for_delete.iterrows()]
    delete_opts = ['Select ID to Delete'] + delete_opts_list
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission Batch:", delete_opts, key="delete_submission_id_select")
    if del_choice_display != 'Select ID to Delete':
        del_id_val = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id_val}", key=f"confirm_del_btn_{del_id_val}", type="primary"):
            try:
                # ON DELETE CASCADE in issues table definition handles deleting related issues
                c.execute('DELETE FROM uploads WHERE id=?', (del_id_val,))
                conn.commit()
                st.sidebar.success(f"Deleted submission batch {del_id_val}."); st.rerun()
            except sqlite3.Error as e:
                conn.rollback()
                st.sidebar.error(f"Failed to delete submission: {e}")
    
    # --- NEW: Database Backup Download Section ---
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
    current_timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_db_filename = f"issues_backup_{current_timestamp_str}.db"

    # Prepare data for download button (this needs to be outside the 'if' for the actual download)
    db_file_data_for_download = None
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as fp:
            db_file_data_for_download = fp.read()

    if db_file_data_for_download:
        st.sidebar.download_button(
            label="Download Database Backup",
            data=db_file_data_for_download,
            file_name=backup_db_filename,
            mime="application/vnd.sqlite3",
            key="download_db_backup_final_button", # Unique key
            help=f"Downloads the current state of '{DB_PATH}'. Rename to '{os.path.basename(DB_PATH)}' before committing to Git."
        )
    else:
        st.sidebar.warning(f"'{DB_PATH}' not found or empty. Cannot offer download.")
    # --- END: Database Backup Download Section ---


default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk)

df_uploads_raw_main = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A"
df_uploads_raw_main['display_submission_date_fmt'] = df_uploads_raw_main['submission_date'].apply(format_display_date)

st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [(f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) Imp.From: {r['display_submission_date_fmt']}") for i,r in df_uploads_raw_main.iterrows()]
sel_display = st.sidebar.selectbox("Select upload batch to analyze:", scope_opts, key="select_upload_scope_main")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None


df_all_issues = pd.read_sql('SELECT i.*, u.category as upload_category, u.id as upload_id_col FROM issues i JOIN uploads u ON u.id = i.upload_id', conn, parse_dates=['date'])
if df_all_issues.empty: st.warning("No issues data in database. Please upload data."); st.stop()

st.sidebar.subheader("Dashboard Filters")
min_overall_date = df_all_issues['date'].min().date() if pd.notna(df_all_issues['date'].min()) else date.today()
max_overall_date = df_all_issues['date'].max().date() if pd.notna(df_all_issues['date'].max()) else date.today()
primary_date_range = st.sidebar.date_input("Primary Date Range (Issue Dates):", value=[min_overall_date, max_overall_date] if min_overall_date <= max_overall_date else [max_overall_date, min_overall_date], min_value=min_overall_date, max_value=max_overall_date, key="primary_date_range_filter")
if not primary_date_range or len(primary_date_range) != 2: primary_date_range = [min_overall_date, max_overall_date]
branch_opts = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist())
sel_branch = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")
cat_opts = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist()) 
sel_cat = st.sidebar.multiselect("Category (from Upload Batch):", cat_opts, default=['All'], key="category_filter")
am_opts = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist())
sel_am = st.sidebar.multiselect("Area Manager:", am_opts, default=['All'], key="area_manager_filter")
file_type_filter_opts = ['All'] + sorted(df_all_issues['report_type'].astype(str).unique().tolist()) 
sel_ft = st.sidebar.multiselect("File Type (from Upload Batch):", file_type_filter_opts, default=['All'], key="file_type_filter")

st.sidebar.subheader("📊 Period Comparison")
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox")
comparison_date_range_1, comparison_date_range_2 = None, None 
if enable_comparison:
    st.sidebar.markdown("**Comparison Period 1 (Issue Dates):**")
    safe_default_p1_end = min_overall_date + timedelta(days=6); safe_default_p1_end = min(safe_default_p1_end, max_overall_date); safe_default_p1_end = max(safe_default_p1_end, min_overall_date)
    comparison_date_range_1_val = st.sidebar.date_input("Start & End Date (Period 1):", value=[min_overall_date, safe_default_p1_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period1_filter")
    if comparison_date_range_1_val and len(comparison_date_range_1_val) == 2:
        comparison_date_range_1 = comparison_date_range_1_val 
        st.sidebar.markdown("**Comparison Period 2 (Issue Dates):**")
        default_p2_start = comparison_date_range_1[1] + timedelta(days=1); default_p2_start = min(default_p2_start, max_overall_date); default_p2_start = max(default_p2_start, min_overall_date)
        default_p2_end = default_p2_start + timedelta(days=6); default_p2_end = min(default_p2_end, max_overall_date); default_p2_end = max(default_p2_end, default_p2_start)
        comparison_date_range_2_val = st.sidebar.date_input("Start & End Date (Period 2):", value=[default_p2_start, default_p2_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period2_filter")
        if comparison_date_range_2_val and len(comparison_date_range_2_val) == 2: comparison_date_range_2 = comparison_date_range_2_val 
        else: comparison_date_range_2 = None 
    else: comparison_date_range_1 = None; comparison_date_range_2 = None 

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
if primary_date_range and len(primary_date_range) == 2:
    start_date_filt, end_date_filt = primary_date_range[0], primary_date_range[1]
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']): # Check before .dt
        df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= start_date_filt) & (df_primary_period['date'].dt.date <= end_date_filt)]
else: df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)
st.subheader(f"Filtered Issues for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total issues found in primary period: {len(df_primary_period)}")

def create_bar_chart(df_source, group_col, title_suffix=""):
    title = f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col in df_source.columns and not df_source[group_col].isnull().all():
        data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count').sort_values('count', ascending=False)
        if not data.empty: return px.bar(data, x=group_col, y='count', title=title, template="plotly_white")
    return None
def create_pie_chart(df_source, group_col, title_suffix=""):
    title = f"Issues by {group_col.replace('_',' ').title()} {title_suffix}"
    if group_col in df_source.columns and not df_source[group_col].isnull().all():
        data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count')
        if not data.empty: return px.pie(data, names=group_col, values='count', title=title, hole=0.3, template="plotly_white")
    return None

if df_primary_period.empty:
    st.info("No data matches the current filter criteria for the primary period.")
else:
    figs_primary = {}
    col1_charts, col2_charts = st.columns(2) # Renamed to avoid conflict
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
        trend_data_primary['date'] = pd.to_datetime(trend_data_primary['date']) 
        trend_data_primary = trend_data_primary.sort_values('date')
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
        if pd.api.types.is_datetime64_any_dtype(df_display_primary['date']):
            df_display_primary['date'] = df_display_primary['date'].dt.strftime('%Y-%m-%d') 
        st.dataframe(df_display_primary, use_container_width=True)

    st.subheader("Top Issues (Primary Period - Filtered)")
    if 'issues' in df_primary_period.columns and not df_primary_period['issues'].isnull().all():
        top_issues_primary = df_primary_period['issues'].astype(str).value_counts().head(20).rename_axis('Issue Description').reset_index(name='Frequency')
        if not top_issues_primary.empty: st.dataframe(top_issues_primary, use_container_width=True)

if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.markdown("---"); st.header("📊 Period Comparison Results (Based on Issue Dates)")
    df_comp1 = pd.DataFrame(columns=df_temp_filtered.columns) 
    df_comp2 = pd.DataFrame(columns=df_temp_filtered.columns)
    start_c1_disp, end_c1_disp, start_c2_disp, end_c2_disp = "N/A", "N/A", "N/A", "N/A"

    if comparison_date_range_1 and len(comparison_date_range_1) == 2:
        start_c1, end_c1 = comparison_date_range_1[0], comparison_date_range_1[1]
        if 'date' in df_temp_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_temp_filtered['date']):
            df_comp1 = df_temp_filtered[(df_temp_filtered['date'].dt.date >= start_c1) & (df_temp_filtered['date'].dt.date <= end_c1)].copy()
        start_c1_disp, end_c1_disp = start_c1.strftime('%Y-%m-%d'), end_c1.strftime('%Y-%m-%d')
    if comparison_date_range_2 and len(comparison_date_range_2) == 2:
        start_c2, end_c2 = comparison_date_range_2[0], comparison_date_range_2[1]
        if 'date' in df_temp_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_temp_filtered['date']):
            df_comp2 = df_temp_filtered[(df_temp_filtered['date'].dt.date >= start_c2) & (df_temp_filtered['date'].dt.date <= end_c2)].copy()
        start_c2_disp, end_c2_disp = start_c2.strftime('%Y-%m-%d'), end_c2.strftime('%Y-%m-%d')

    if not df_comp1.empty or not df_comp2.empty:
        if comparison_date_range_1: st.subheader(f"Period 1: {start_c1_disp} to {end_c1_disp} (Total: {len(df_comp1)} issues)")
        if comparison_date_range_2: st.subheader(f"Period 2: {start_c2_disp} to {end_c2_disp} (Total: {len(df_comp2)} issues)")
        col_comp1_disp, col_comp2_disp = st.columns(2) # Renamed
        with col_comp1_disp:
            st.metric(label=f"Total Issues (P1)", value=len(df_comp1))
            if not df_comp1.empty: st.dataframe(df_comp1['issues'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue', 'issues':'Count'}), height=220, use_container_width=True)
        with col_comp2_disp:
            delta_val = len(df_comp2) - len(df_comp1)
            st.metric(label=f"Total Issues (P2)", value=len(df_comp2), delta=f"{delta_val:+}" if delta_val !=0 else None)
            if not df_comp2.empty: st.dataframe(df_comp2['issues'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue', 'issues':'Count'}), height=220, use_container_width=True)
        if not df_comp1.empty or not df_comp2.empty:
            df_comp1_labeled = df_comp1.copy(); df_comp2_labeled = df_comp2.copy()
            if comparison_date_range_1: df_comp1_labeled['period_label'] = f"P1: {comparison_date_range_1[0]:%d%b}-{comparison_date_range_1[1]:%d%b}"
            if comparison_date_range_2: df_comp2_labeled['period_label'] = f"P2: {comparison_date_range_2[0]:%d%b}-{comparison_date_range_2[1]:%d%b}"
            dfs_to_concat = []
            if not df_comp1_labeled.empty and 'period_label' in df_comp1_labeled.columns : dfs_to_concat.append(df_comp1_labeled)
            if not df_comp2_labeled.empty and 'period_label' in df_comp2_labeled.columns : dfs_to_concat.append(df_comp2_labeled)
            if dfs_to_concat:
                df_combined_branch = pd.concat(dfs_to_concat)
                if not df_combined_branch.empty:
                    branch_comp_data = df_combined_branch.groupby(['branch', 'period_label']).size().reset_index(name='count')
                    if not branch_comp_data.empty:
                        fig_branch_comp = px.bar(branch_comp_data, x='branch', y='count', color='period_label', barmode='group', title='Issues by Branch (Comparison)')
                        st.plotly_chart(fig_branch_comp, use_container_width=True)
            st.markdown("#### Period-Level Trend (Average Daily Issues)")
            period_summary_data = []
            if comparison_date_range_1 and not df_comp1.empty:
                avg_issues_p1 = df_comp1.groupby(df_comp1['date'].dt.date).size().mean()
                period_summary_data.append({'Period': f"Period 1 ({comparison_date_range_1[0]:%b %d} - {comparison_date_range_1[1]:%b %d})", 'StartDate': pd.to_datetime(comparison_date_range_1[0]), 'AverageDailyIssues': round(avg_issues_p1, 2)})
            if comparison_date_range_2 and not df_comp2.empty:
                avg_issues_p2 = df_comp2.groupby(df_comp2['date'].dt.date).size().mean()
                period_summary_data.append({'Period': f"Period 2 ({comparison_date_range_2[0]:%b %d} - {comparison_date_range_2[1]:%b %d})", 'StartDate': pd.to_datetime(comparison_date_range_2[0]), 'AverageDailyIssues': round(avg_issues_p2, 2)})
            if len(period_summary_data) >= 1:
                df_period_trend = pd.DataFrame(period_summary_data).sort_values('StartDate')
                if len(df_period_trend) == 1:
                    fig_period_level_trend = px.bar(df_period_trend, x='Period', y='AverageDailyIssues', text='AverageDailyIssues', title='Avg Daily Issues by Period')
                    fig_period_level_trend.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                else:
                    fig_period_level_trend = px.line(df_period_trend, x='Period', y='AverageDailyIssues', markers=True, text='AverageDailyIssues', title='Trend of Avg Daily Issues Across Periods')
                    fig_period_level_trend.update_traces(texttemplate='%{text:.2f}', textposition='top center')
                fig_period_level_trend.update_layout(xaxis_title="Comparison Period", yaxis_title="Avg. Daily Issues", template="plotly_white")
                st.plotly_chart(fig_period_level_trend, use_container_width=True)
            else: st.info("Not enough data for period-level trend (ensure selected periods have data).")
    else: st.warning("No data found for either comparison period with the current general filters.")

st.sidebar.subheader("Downloads")
if 'df_primary_period' in locals() and not df_primary_period.empty: # Ensure df_primary_period is defined
    csv_data_primary = df_primary_period.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download Primary Period Data as CSV", csv_data_primary, "primary_period_issues.csv", "text/csv", key="download_csv_primary")
    if st.sidebar.button("Prepare Visuals PDF (Primary Period)", key="prep_visuals_pdf_primary"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        elif 'figs_primary' not in locals() or not figs_primary or not any(figs_primary.values()): st.sidebar.warning("No visuals generated for primary period.")
        else:
            html_content = "<html><head><meta charset='utf-8'><title>Visuals Report (Primary)</title><style>body{font-family:sans-serif;} h1,h2{text-align:center;} img{display:block;margin-left:auto;margin-right:auto;max-width:95%;height:auto;border:1px solid #ccc;padding:5px;margin-bottom:20px;} @media print {* {-webkit-print-color-adjust:exact !important; color-adjust:exact !important; print-color-adjust:exact !important;} body { background-color:white !important;}}</style></head><body>"
            html_content += f"<h1>Visuals Report (Primary: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d})</h1>"
            chart_titles_in_order = ["Branch", "Area Manager", "Report Type", "Category", "Trend"]
            for title in chart_titles_in_order:
                if figs_primary.get(title): 
                    fig_obj = figs_primary[title]
                    try:
                        img_bytes = fig_obj.to_image(format='png', engine='kaleido', scale=2); b64_img = base64.b64encode(img_bytes).decode()
                        html_content += f"<h2>{title}</h2><img src='data:image/png;base64,{b64_img}' alt='{title}'/>"
                    except Exception as e_fig: st.sidebar.warning(f"Fig '{title}' to image error: {e_fig}. Kaleido needed.")
            html_content += "</body></html>"
            pdf_bytes = generate_pdf(html_content, fname='visuals_report_primary.pdf', wk_path=wk_path)
            if pdf_bytes: st.session_state.pdf_visuals_primary_data = pdf_bytes; st.sidebar.success("Visuals PDF (Primary) ready.")
            else:
                if 'pdf_visuals_primary_data' in st.session_state: del st.session_state.pdf_visuals_primary_data
    if 'pdf_visuals_primary_data' in st.session_state and st.session_state.pdf_visuals_primary_data:
        st.sidebar.download_button(label="Download Visuals PDF (Primary) Now", data=st.session_state.pdf_visuals_primary_data, file_name="visuals_report_primary.pdf", mime="application/pdf", key="action_dl_visuals_pdf_primary")
    if st.sidebar.button("Prepare Full Dashboard PDF (Primary Period)", key="prep_dashboard_pdf_primary"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        else:
            html_full = "<head><meta charset='utf-8'><style>body{font-family:sans-serif;} table{border-collapse:collapse;width:100%;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background-color:#f2f2f2;}</style></head>"
            html_full += f"<h1>Dashboard Report (Primary: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d})</h1>"
            df_pdf_view = df_primary_period[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']].copy()
            if pd.api.types.is_datetime64_any_dtype(df_pdf_view['date']): df_pdf_view['date'] = df_pdf_view['date'].dt.strftime('%Y-%m-%d')
            html_full += df_pdf_view.to_html(index=False, classes="dataframe", border=0)
            pdf_full_bytes = generate_pdf(html_full, fname='dashboard_report_primary.pdf', wk_path=wk_path)
            if pdf_full_bytes: st.session_state.pdf_dashboard_primary_data = pdf_full_bytes; st.sidebar.success("Dashboard PDF (Primary) ready.")
            else:
                if 'pdf_dashboard_primary_data' in st.session_state: del st.session_state.pdf_dashboard_primary_data
    if 'pdf_dashboard_primary_data' in st.session_state and st.session_state.pdf_dashboard_primary_data:
        st.sidebar.download_button(label="Download Dashboard PDF (Primary) Now", data=st.session_state.pdf_dashboard_primary_data, file_name="dashboard_report_primary.pdf", mime="application/pdf", key="action_dl_dashboard_pdf_primary")
else: st.sidebar.info("No primary period data to download.")

if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    df_comp1_exists = 'df_comp1' in locals() and not df_comp1.empty
    df_comp2_exists = 'df_comp2' in locals() and not df_comp2.empty
    start_c1_str = comparison_date_range_1[0].strftime('%Y%m%d') if df_comp1_exists and comparison_date_range_1 else "P1"
    end_c1_str = comparison_date_range_1[1].strftime('%Y%m%d') if df_comp1_exists and comparison_date_range_1 else ""
    start_c2_str = comparison_date_range_2[0].strftime('%Y%m%d') if df_comp2_exists and comparison_date_range_2 else "P2"
    end_c2_str = comparison_date_range_2[1].strftime('%Y%m%d') if df_comp2_exists and comparison_date_range_2 else ""

    if df_comp1_exists:
        st.sidebar.download_button(f"CSV (Comp P1: {comparison_date_range_1[0]:%b%d}-{comparison_date_range_1[1]:%b%d})", df_comp1.to_csv(index=False).encode('utf-8'), f"comp_p1_{start_c1_str}-{end_c1_str}.csv", "text/csv", key="dl_csv_comp1")
    if df_comp2_exists:
        st.sidebar.download_button(f"CSV (Comp P2: {comparison_date_range_2[0]:%b%d}-{comparison_date_range_2[1]:%b%d})", df_comp2.to_csv(index=False).encode('utf-8'), f"comp_p2_{start_c2_str}-{end_c2_str}.csv", "text/csv", key="dl_csv_comp2")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)") # Updated caption
