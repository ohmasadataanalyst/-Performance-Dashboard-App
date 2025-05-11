import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
import shutil
import base64
from datetime import datetime, date, timedelta

# Streamlit config MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- Database setup ---
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Create uploads table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    uploader TEXT,
    timestamp TEXT,
    file_type TEXT,
    category TEXT,
    submission_date TEXT, -- User-specified effective date
    file BLOB
)''')
# Create issues table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    upload_id INTEGER,
    code TEXT,
    issues TEXT,
    branch TEXT,
    area_manager TEXT,
    date TEXT,            -- This will store the effective_report_date
    report_type TEXT,
    FOREIGN KEY(upload_id) REFERENCES uploads(id)
)''')
conn.commit()

# Add submission_date column to uploads if it doesn't exist (idempotent)
c.execute("PRAGMA table_info(uploads)")
existing_columns = [column[1] for column in c.fetchall()]
if 'submission_date' not in existing_columns:
    try:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        if 'db_schema_updated_flag' not in st.session_state:
            st.session_state.db_schema_updated_flag = True
    except sqlite3.OperationalError as e:
        st.session_state.db_critical_error_msg = f"Failed to update 'uploads' table schema: {e}"

# Credentials
db_admin = {
    "abdalziz alsalem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvpLxRumSduEte8MDAPkOnuXMdnW",
    "omar salah": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy",
    "ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEn.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG",
    "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe"
}
view_only = ["mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"]

# --- Show critical DB error from setup if any ---
if 'db_critical_error_msg' in st.session_state:
    st.error(f"DB Startup Error: {st.session_state.db_critical_error_msg}")
    del st.session_state.db_critical_error_msg
# --- Show DB schema update toast if flag is set ---
if 'db_schema_updated_flag' in st.session_state and st.session_state.db_schema_updated_flag:
    st.toast("DB 'uploads' table schema updated.", icon="ℹ️")
    st.session_state.db_schema_updated_flag = False

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
                    st.session_state.authenticated = True; st.session_state.user_name = username; st.session_state.user_role = 'admin'; st.rerun()
                elif username in view_only and password:
                    st.session_state.authenticated = True; st.session_state.user_name = username; st.session_state.user_role = 'view_only'; st.rerun()
                elif username in view_only and not password: st.error("Password cannot be empty for view-only users.")
                elif username or password: st.error("Invalid username or password.")
                else: st.info("Please enter your credentials.")
        return False
    return True
if not check_login(): st.stop()

# --- User is Authenticated, Proceed with App ---
st.title("📊 Classic Dashboard for Performance")
user_name_display = st.session_state.get('user_name', "N/A").title()
user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main"):
    st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.session_state.get('user_name', 'Unknown User')

# PDF generator
def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path or wk_path == "not found": st.error("wkhtmltopdf path not set."); return None
    try:
        import pdfkit; config = pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8",'load-error-handling': 'ignore','load-media-error-handling': 'ignore'}
        pdfkit.from_string(html, fname, configuration=config, options=options);
        with open(fname, 'rb') as f: return f.read()
    except Exception as e: st.error(f"PDF error: {e}"); return None

# Sidebar: controls
st.sidebar.header("🔍 Filters & Options")

# Upload control for admins
if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("Set parameters below, choose Excel file, then click 'Upload Data'.")
    file_type_upload = st.sidebar.selectbox("File type for upload", ["opening", "closing", "handover", "meal training"], key="upload_file_type")
    category_upload = st.sidebar.selectbox("Category for upload", ['operation-training', 'CCTV', 'complaints', 'missing', 'visits', 'meal training'], key="upload_category")
    
    effective_report_date = st.sidebar.date_input(
        "**Effective Date of Report:**", 
        value=date.today(), 
        key="effective_report_date_upload",
        help="Select the date this report should be attributed to. All issues from the uploaded file will use this date."
    )

    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    if upload_btn: 
        if up and effective_report_date: 
            data = up.getvalue()
            ts = datetime.now().isoformat() 
            effective_date_str = effective_report_date.isoformat() 

            c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type=? AND category=? AND submission_date=?',
                      (up.name, current_user, file_type_upload, category_upload, effective_date_str))
            
            if c.fetchone()[0] == 0:
                c.execute(
                    'INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (up.name, current_user, ts, file_type_upload, category_upload, effective_date_str, sqlite3.Binary(data))
                )
                uid = c.lastrowid
                try:
                    df_up = pd.read_excel(io.BytesIO(data))
                    df_up.columns = [col.strip().lower() for col in df_up.columns]
                    
                    required_cols = ['code', 'issues', 'branch', 'area manager', 'date'] 
                    missing_cols = [col for col in required_cols if col not in df_up.columns]

                    if missing_cols:
                        st.sidebar.error(f"Excel missing columns: {', '.join(missing_cols)}. Upload aborted.")
                        c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                        conn.commit()
                    else:
                        df_up['excel_date_validated'] = pd.to_datetime(df_up['date'], dayfirst=True, errors='coerce')
                        original_len = len(df_up)
                        df_up.dropna(subset=['excel_date_validated'], inplace=True)
                        
                        rows_dropped = original_len - len(df_up)
                        if rows_dropped > 0:
                            st.sidebar.warning(f"{rows_dropped} rows dropped from Excel due to invalid date format in its 'date' column.")

                        if df_up.empty:
                            st.sidebar.error("No valid data rows in Excel after 'date' column validation. Upload aborted.")
                            c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                            conn.commit()
                        else:
                            for _, row in df_up.iterrows():
                                c.execute('INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                        (uid, row['code'], row['issues'], row['branch'], row['area manager'],
                                         effective_date_str, 
                                         file_type_upload))
                            conn.commit()
                            st.sidebar.success(f"Uploaded '{up.name}' ({len(df_up)} records) with Effective Report Date: {effective_report_date.strftime('%Y-%m-%d')}")
                            st.rerun() 
                except Exception as e:
                    st.sidebar.error(f"Error processing Excel file '{up.name}': {e}. Upload rolled back.")
                    c.execute('DELETE FROM uploads WHERE id=?', (uid,)) 
                    conn.commit()
            else:
                st.sidebar.warning(f"A file named '{up.name}' by '{current_user}' of type '{file_type_upload}' in category '{category_upload}' for effective date '{effective_date_str}' has already been uploaded.")
        else:
            if not up:
                st.sidebar.error("Please select an Excel file to upload.")


# wkhtmltopdf path
default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk)

# Load uploads for selection
df_uploads_raw = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A"
df_uploads_raw['display_submission_date'] = df_uploads_raw['submission_date'].apply(format_display_date)

# Scope selection
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [f"{r['id']} - {r['filename']} ({r['file_type']}) Eff.Date: {r['display_submission_date']}" for i,r in df_uploads_raw.iterrows()]
sel_display = st.sidebar.selectbox("Select upload to analyze:", scope_opts, key="select_upload_scope")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

# Admin: delete submission
if is_admin:
    st.sidebar.subheader("Manage Submissions")
    delete_opts_list = []
    if not df_uploads_raw.empty:
        delete_opts_list = [f"{row['id']} - {row['filename']} (Eff.Date: {row['display_submission_date']})" for index, row in df_uploads_raw.iterrows()]
    delete_opts = ['Select ID to Delete'] + delete_opts_list
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission:", delete_opts, key="delete_submission_id")
    if del_choice_display != 'Select ID to Delete':
        del_id_val = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id_val}", key=f"confirm_del_btn_{del_id_val}", type="primary"):
            c.execute('DELETE FROM issues WHERE upload_id=?', (del_id_val,))
            c.execute('DELETE FROM uploads WHERE id=?', (del_id_val,))
            conn.commit()
            st.sidebar.success(f"Deleted submission {del_id_val} and its associated issues.")
            st.rerun()

# Fetch ALL data initially
df_all_issues = pd.read_sql(
    'SELECT i.*, u.category as upload_category, u.file_type as master_file_type, u.id as upload_id_col FROM issues i JOIN uploads u ON u.id = i.upload_id', # Added u.id as upload_id_col
    conn, parse_dates=['date']
)

if df_all_issues.empty:
    st.warning("No data found in the database. Please upload data.")
    st.stop()

# --- DASHBOARD FILTERS ---
st.sidebar.subheader("Dashboard Filters")
min_overall_date = df_all_issues['date'].min().date() if pd.notna(df_all_issues['date'].min()) else date.today()
max_overall_date = df_all_issues['date'].max().date() if pd.notna(df_all_issues['date'].max()) else date.today()

primary_date_range = st.sidebar.date_input(
    "Primary Date Range (Effective Report Date):",
    value=[min_overall_date, max_overall_date] if min_overall_date <= max_overall_date else [max_overall_date, min_overall_date],
    min_value=min_overall_date, max_value=max_overall_date, key="primary_date_range_filter"
)
if not primary_date_range or len(primary_date_range) != 2: primary_date_range = [min_overall_date, max_overall_date]

branch_opts = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist())
sel_branch = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")
cat_opts = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist())
sel_cat = st.sidebar.multiselect("Category:", cat_opts, default=['All'], key="category_filter")
am_opts = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist())
sel_am = st.sidebar.multiselect("Area Manager:", am_opts, default=['All'], key="area_manager_filter")
file_type_filter_opts = ['All'] + sorted(df_all_issues['report_type'].astype(str).unique().tolist())
sel_ft = st.sidebar.multiselect("File Type (Report Type):", file_type_filter_opts, default=['All'], key="file_type_filter")

# --- Period Comparison ---
st.sidebar.subheader("📊 Period Comparison")
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox")
comparison_date_range_1, comparison_date_range_2 = None, None
if enable_comparison:
    st.sidebar.markdown("**Comparison Period 1:**")
    default_p1_end = min_overall_date + timedelta(days=6) if (min_overall_date + timedelta(days=6)) <= max_overall_date else max_overall_date
    comparison_date_range_1 = st.sidebar.date_input("Start & End Date (Period 1):", value=[min_overall_date, default_p1_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period1_filter")
    
    st.sidebar.markdown("**Comparison Period 2:**")
    default_p2_start = comparison_date_range_1[1] + timedelta(days=1) if comparison_date_range_1 and (comparison_date_range_1[1] + timedelta(days=1)) <= max_overall_date else min_overall_date
    if default_p2_start > max_overall_date : default_p2_start = max_overall_date - timedelta(days=6) if (max_overall_date - timedelta(days=6)) >= min_overall_date else min_overall_date
    default_p2_end = default_p2_start + timedelta(days=6)
    if default_p2_end > max_overall_date: default_p2_end = max_overall_date
    if default_p2_start > default_p2_end : default_p2_start = default_p2_end # Ensure start is not after end

    comparison_date_range_2 = st.sidebar.date_input("Start & End Date (Period 2):", value=[default_p2_start, default_p2_end], min_value=min_overall_date, max_value=max_overall_date, key="comparison_period2_filter")
    if not comparison_date_range_1 or len(comparison_date_range_1) != 2: comparison_date_range_1 = None
    if not comparison_date_range_2 or len(comparison_date_range_2) != 2: comparison_date_range_2 = None

# Function to apply general filters
def apply_general_filters(df_input, sel_upload_id_val, selected_branches, selected_categories, selected_managers, selected_file_types):
    df_filtered = df_input.copy()
    if sel_upload_id_val:
        df_filtered = df_filtered[df_filtered['upload_id_col'] == sel_upload_id_val]
    if 'All' not in selected_branches: df_filtered = df_filtered[df_filtered['branch'].isin(selected_branches)]
    if 'All' not in selected_categories: df_filtered = df_filtered[df_filtered['upload_category'].isin(selected_categories)]
    if 'All' not in selected_managers: df_filtered = df_filtered[df_filtered['area_manager'].isin(selected_managers)]
    if 'All' not in selected_file_types: df_filtered = df_filtered[df_filtered['report_type'].isin(selected_file_types)]
    return df_filtered

df_temp_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)

# Filter for Primary Period
df_primary_period = df_temp_filtered.copy()
if primary_date_range and len(primary_date_range) == 2:
    start_date, end_date = primary_date_range[0], primary_date_range[1]
    df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= start_date) & (df_primary_period['date'].dt.date <= end_date)]
else:
    df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns) # Empty if no valid range

# --- Dashboard Display ---
st.subheader(f"Filtered Issues for Primary Period: {primary_date_range[0].strftime('%Y-%m-%d')} to {primary_date_range[1].strftime('%Y-%m-%d')}")
st.write(f"Total issues found in primary period: {len(df_primary_period)}")

def create_bar_chart(df_source, group_col, title):
    # (Chart function from previous correct version)
    if group_col in df_source.columns and not df_source[group_col].isnull().all():
        data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count').sort_values('count', ascending=False)
        if not data.empty: return px.bar(data, x=group_col, y='count', title=title, template="plotly_white")
    return None
def create_pie_chart(df_source, group_col, title):
    # (Chart function from previous correct version)
    if group_col in df_source.columns and not df_source[group_col].isnull().all():
        data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count')
        if not data.empty: return px.pie(data, names=group_col, values='count', title=title, hole=0.3, template="plotly_white")
    return None

if df_primary_period.empty:
    st.info("No data matches the current filter criteria for the primary period.")
else:
    figs_primary = {}
    col1, col2 = st.columns(2)
    with col1:
        figs_primary['Branch'] = create_bar_chart(df_primary_period, 'branch', 'Issues by Branch (Primary)')
        if figs_primary['Branch']: st.plotly_chart(figs_primary['Branch'], use_container_width=True)
        figs_primary['Report Type'] = create_bar_chart(df_primary_period, 'report_type', 'Issues by Report Type (Primary)')
        if figs_primary['Report Type']: st.plotly_chart(figs_primary['Report Type'], use_container_width=True)
    with col2:
        figs_primary['Area Manager'] = create_pie_chart(df_primary_period, 'area_manager', 'Issues by Area Manager (Primary)')
        if figs_primary['Area Manager']: st.plotly_chart(figs_primary['Area Manager'], use_container_width=True)
        figs_primary['Category'] = create_bar_chart(df_primary_period, 'upload_category', 'Issues by Upload Category (Primary)')
        if figs_primary['Category']: st.plotly_chart(figs_primary['Category'], use_container_width=True)
    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']) and not df_primary_period['date'].isnull().all():
        trend_data = df_primary_period.groupby(df_primary_period['date'].dt.date).size().reset_index(name='count').sort_values('date')
        if not trend_data.empty:
            figs_primary['Trend'] = px.line(trend_data, x='date', y='count', title='Issues Trend (Primary Period)', markers=True, template="plotly_white")
            st.plotly_chart(figs_primary['Trend'], use_container_width=True)
    if len(df_primary_period) < 50 or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.subheader("Detailed Records (Primary Period - Filtered)")
        # (Display logic for detailed records)
    st.subheader("Top Issues (Primary Period - Filtered)")
    # (Display logic for top issues)

# --- Period Comparison Display ---
if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.markdown("---"); st.header("📊 Period Comparison Results")
    df_comp1 = df_temp_filtered.copy()
    start_c1, end_c1 = comparison_date_range_1[0], comparison_date_range_1[1]
    df_comp1 = df_comp1[(df_comp1['date'].dt.date >= start_c1) & (df_comp1['date'].dt.date <= end_c1)]
    df_comp2 = df_temp_filtered.copy()
    start_c2, end_c2 = comparison_date_range_2[0], comparison_date_range_2[1]
    df_comp2 = df_comp2[(df_comp2['date'].dt.date >= start_c2) & (df_comp2['date'].dt.date <= end_c2)]

    st.subheader(f"Period 1: {start_c1:%Y-%m-%d} to {end_c1:%Y-%m-%d} (Total: {len(df_comp1)} issues)")
    st.subheader(f"Period 2: {start_c2:%Y-%m-%d} to {end_c2:%Y-%m-%d} (Total: {len(df_comp2)} issues)")

    if df_comp1.empty and df_comp2.empty:
        st.warning("No data for either comparison period with current filters.")
    else:
        col_comp1, col_comp2 = st.columns(2)
        with col_comp1:
            st.metric(label=f"Total Issues (P1)", value=len(df_comp1))
            if not df_comp1.empty: st.dataframe(df_comp1['issues'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue', 'issues':'Count'}), height=200, use_container_width=True)
        with col_comp2:
            delta_val = len(df_comp2) - len(df_comp1)
            st.metric(label=f"Total Issues (P2)", value=len(df_comp2), delta=f"{delta_val:+}" if delta_val !=0 else "0")
            if not df_comp2.empty: st.dataframe(df_comp2['issues'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue', 'issues':'Count'}), height=200, use_container_width=True)
        
        if not df_comp1.empty or not df_comp2.empty:
            df_comp1['period_label'] = f"P1: {start_c1:%d %b} - {end_c1:%d %b}"
            df_comp2['period_label'] = f"P2: {start_c2:%d %b} - {end_c2:%d %b}"
            df_combined_branch = pd.concat([df_comp1, df_comp2])
            if not df_combined_branch.empty:
                branch_comp_data = df_combined_branch.groupby(['branch', 'period_label']).size().reset_index(name='count')
                if not branch_comp_data.empty:
                    fig_branch_comp = px.bar(branch_comp_data, x='branch', y='count', color='period_label', barmode='group', title='Issues by Branch (Comparison)')
                    st.plotly_chart(fig_branch_comp, use_container_width=True)
            
            trend_c1 = df_comp1.groupby(df_comp1['date'].dt.normalize()).size().reset_index(name='count').rename(columns={'date':'time', 'count':'P1 Issues'})
            trend_c2 = df_comp2.groupby(df_comp2['date'].dt.normalize()).size().reset_index(name='count').rename(columns={'date':'time', 'count':'P2 Issues'})

            if not trend_c1.empty or not trend_c2.empty:
                df_trend_merged = pd.DataFrame()
                if not trend_c1.empty: df_trend_merged = trend_c1
                if not trend_c2.empty:
                    if not df_trend_merged.empty:
                        df_trend_merged = pd.merge(df_trend_merged, trend_c2, on='time', how='outer')
                    else:
                        df_trend_merged = trend_c2
                
                df_trend_merged = df_trend_merged.fillna(0).sort_values('time')
                fig_trend_comp = px.line(df_trend_merged, x='time', y=[col for col in ['P1 Issues', 'P2 Issues'] if col in df_trend_merged.columns],
                                         title='Daily Issues Trend Comparison', markers=True)
                fig_trend_comp.update_layout(legend_title_text='Period')
                st.plotly_chart(fig_trend_comp, use_container_width=True)

# --- Downloads ---
st.sidebar.subheader("Downloads")
# (Download logic for primary period, can be expanded for comparison data)
if not df_primary_period.empty:
    st.sidebar.download_button("CSV (Primary Period)", df_primary_period.to_csv(index=False).encode('utf-8'), "primary_period_issues.csv", "text/csv")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH}")
