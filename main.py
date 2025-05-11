import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
import shutil
import base64
from datetime import datetime, date, timedelta # Added timedelta

# Streamlit config MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- Database setup (same as before) ---
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
    file_type TEXT, category TEXT, submission_date TEXT, file BLOB
)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    upload_id INTEGER, code TEXT, issues TEXT, branch TEXT, area_manager TEXT,
    date TEXT, report_type TEXT, FOREIGN KEY(upload_id) REFERENCES uploads(id)
)''')
conn.commit()

# Add submission_date column to uploads if it doesn't exist (simplified)
c.execute("PRAGMA table_info(uploads)")
if 'submission_date' not in [col[1] for col in c.fetchall()]:
    try:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        if 'db_schema_updated_flag' not in st.session_state: st.session_state.db_schema_updated_flag = True
    except sqlite3.OperationalError as e:
        st.session_state.db_critical_error_msg = f"Failed to update 'uploads' schema: {e}"


# Credentials (same as before)
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


# --- AUTHENTICATION FUNCTION (same as before) ---
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

# PDF generator (same as before - condensed)
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

# Admin Controls (same as before)
if is_admin:
    st.sidebar.subheader("Admin Controls")
    # ... (upload logic - condensed for brevity, assume it's correct)
    file_type_upload = st.sidebar.selectbox("File type for upload", ["opening", "closing", "handover", "meal training"], key="upload_file_type")
    category_upload = st.sidebar.selectbox("Category for upload", ['operation-training', 'CCTV', 'complaints', 'missing', 'visits', 'meal training'], key="upload_category")
    effective_report_date = st.sidebar.date_input("**Effective Date of Report:**", value=date.today(), key="effective_report_date_upload")
    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    if st.sidebar.button("Upload Data", key="upload_data_button"):
        if up and effective_report_date:
            # ... (full upload processing logic from previous correct version) ...
            st.sidebar.success("File processed (Placeholder for full logic)") # Placeholder
        else:
            st.sidebar.error("File and Effective Date required.")


# wkhtmltopdf path (same as before)
default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk)

# Load uploads for selection (same as before)
df_uploads_raw = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A"
df_uploads_raw['display_submission_date'] = df_uploads_raw['submission_date'].apply(format_display_date)

# Scope selection (same as before)
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [f"{r['id']} - {r['filename']} ({r['file_type']}) Eff.Date: {r['display_submission_date']}" for i,r in df_uploads_raw.iterrows()]
sel_display = st.sidebar.selectbox("Select upload to analyze:", scope_opts, key="select_upload_scope")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

# Admin: delete submission (same as before - condensed)
if is_admin:
    st.sidebar.subheader("Manage Submissions")
    # ... (delete logic - condensed) ...

# Fetch ALL data initially, filtering will happen after UI selections
df_all_issues = pd.read_sql(
    'SELECT i.*, u.category as upload_category, u.file_type as master_file_type FROM issues i JOIN uploads u ON u.id = i.upload_id',
    conn, parse_dates=['date']
)

if df_all_issues.empty:
    st.warning("No data found in the database. Please upload data.")
    st.stop()

# --- DASHBOARD FILTERS ---
st.sidebar.subheader("Dashboard Filters")

# Date Range Filter (Primary Period)
min_overall_date = df_all_issues['date'].min().date() if not df_all_issues['date'].empty else date.today()
max_overall_date = df_all_issues['date'].max().date() if not df_all_issues['date'].empty else date.today()

primary_date_range = st.sidebar.date_input(
    "Primary Date Range (Effective Report Date):",
    value=[min_overall_date, max_overall_date] if min_overall_date <= max_overall_date else [max_overall_date, min_overall_date],
    min_value=min_overall_date,
    max_value=max_overall_date,
    key="primary_date_range_filter"
)
if not primary_date_range or len(primary_date_range) != 2:
    primary_date_range = [min_overall_date, max_overall_date]

# General Filters (Branch, Category, Area Manager)
branch_opts = ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist())
sel_branch = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")

cat_opts = ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist())
sel_cat = st.sidebar.multiselect("Category:", cat_opts, default=['All'], key="category_filter")

# --- NEW: Area Manager Filter ---
am_opts = ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist())
sel_am = st.sidebar.multiselect("Area Manager:", am_opts, default=['All'], key="area_manager_filter")

file_type_filter_opts = ['All'] + sorted(df_all_issues['report_type'].astype(str).unique().tolist())
sel_ft = st.sidebar.multiselect("File Type (Report Type):", file_type_filter_opts, default=['All'], key="file_type_filter")


# --- NEW: Period Comparison ---
st.sidebar.subheader("📊 Period Comparison")
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox")
comparison_date_range_1 = None
comparison_date_range_2 = None

if enable_comparison:
    st.sidebar.markdown("**Comparison Period 1:**")
    comparison_date_range_1 = st.sidebar.date_input(
        "Start & End Date (Period 1):",
        value=[min_overall_date, min_overall_date + timedelta(days=6) if (min_overall_date + timedelta(days=6)) <= max_overall_date else max_overall_date ], # Default to a week
        min_value=min_overall_date,
        max_value=max_overall_date,
        key="comparison_period1_filter"
    )
    st.sidebar.markdown("**Comparison Period 2:**")
    default_period2_start = comparison_date_range_1[1] + timedelta(days=1) if comparison_date_range_1 else min_overall_date
    if default_period2_start > max_overall_date: default_period2_start = max_overall_date - timedelta(days=6) if max_overall_date - timedelta(days=6) >= min_overall_date else min_overall_date

    default_period2_end = default_period2_start + timedelta(days=6)
    if default_period2_end > max_overall_date: default_period2_end = max_overall_date


    comparison_date_range_2 = st.sidebar.date_input(
        "Start & End Date (Period 2):",
        value=[default_period2_start, default_period2_end],
        min_value=min_overall_date,
        max_value=max_overall_date,
        key="comparison_period2_filter"
    )
    if not comparison_date_range_1 or len(comparison_date_range_1) != 2: comparison_date_range_1 = None
    if not comparison_date_range_2 or len(comparison_date_range_2) != 2: comparison_date_range_2 = None


# Function to apply general filters (excluding date)
def apply_general_filters(df_input, sel_upload_id, selected_branches, selected_categories, selected_managers, selected_file_types):
    df_filtered = df_input.copy()
    if sel_upload_id:
        df_filtered = df_filtered[df_filtered['upload_id'] == sel_upload_id] # Assuming 'upload_id' is in df_all_issues from the join
    if 'All' not in selected_branches:
        df_filtered = df_filtered[df_filtered['branch'].isin(selected_branches)]
    if 'All' not in selected_categories:
        df_filtered = df_filtered[df_filtered['upload_category'].isin(selected_categories)]
    if 'All' not in selected_managers: # --- NEW: Apply Area Manager Filter ---
        df_filtered = df_filtered[df_filtered['area_manager'].isin(selected_managers)]
    if 'All' not in selected_file_types:
        df_filtered = df_filtered[df_filtered['report_type'].isin(selected_file_types)]
    return df_filtered

# Apply general filters first
df_temp_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft)

# Filter for Primary Period
df_primary_period = df_temp_filtered.copy()
if primary_date_range and len(primary_date_range) == 2:
    start_date, end_date = primary_date_range[0], primary_date_range[1]
    df_primary_period = df_primary_period[
        (df_primary_period['date'].dt.date >= start_date) & (df_primary_period['date'].dt.date <= end_date)
    ]
else: # Should not happen if date_input is used correctly
    df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)


# --- Dashboard Display ---
st.subheader(f"Filtered Issues for Primary Period: {primary_date_range[0].strftime('%Y-%m-%d')} to {primary_date_range[1].strftime('%Y-%m-%d')}")
st.write(f"Total issues found in primary period: {len(df_primary_period)}")

if df_primary_period.empty:
    st.info("No data matches the current filter criteria for the primary period.")
else:
    # --- Charts for Primary Period (similar to before) ---
    figs_primary = {}
    col1, col2 = st.columns(2)
    # (Chart generation functions - create_bar_chart, create_pie_chart - assumed to be defined as in previous versions)
    def create_bar_chart(df_source, group_col, title):
        if group_col in df_source.columns and not df_source[group_col].isnull().all():
            data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count').sort_values('count', ascending=False)
            if not data.empty: return px.bar(data, x=group_col, y='count', title=title, template="plotly_white")
        return None
    def create_pie_chart(df_source, group_col, title):
        if group_col in df_source.columns and not df_source[group_col].isnull().all():
            data = df_source.astype({group_col: str}).groupby(group_col).size().reset_index(name='count')
            if not data.empty: return px.pie(data, names=group_col, values='count', title=title, hole=0.3, template="plotly_white")
        return None

    with col1:
        figs_primary['Branch'] = create_bar_chart(df_primary_period, 'branch', 'Issues by Branch (Primary Period)')
        if figs_primary['Branch']: st.plotly_chart(figs_primary['Branch'], use_container_width=True)
        
        figs_primary['Report Type'] = create_bar_chart(df_primary_period, 'report_type', 'Issues by Report Type (Primary Period)')
        if figs_primary['Report Type']: st.plotly_chart(figs_primary['Report Type'], use_container_width=True)
    with col2:
        figs_primary['Area Manager'] = create_pie_chart(df_primary_period, 'area_manager', 'Issues by Area Manager (Primary Period)')
        if figs_primary['Area Manager']: st.plotly_chart(figs_primary['Area Manager'], use_container_width=True)

        figs_primary['Category'] = create_bar_chart(df_primary_period, 'upload_category', 'Issues by Upload Category (Primary Period)')
        if figs_primary['Category']: st.plotly_chart(figs_primary['Category'], use_container_width=True)

    if 'date' in df_primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']) and not df_primary_period['date'].isnull().all(): 
        trend_data = df_primary_period.groupby(df_primary_period['date'].dt.date).size().reset_index(name='count').sort_values('date') 
        if not trend_data.empty:
            figs_primary['Trend'] = px.line(trend_data, x='date', y='count', title='Issues Trend (Primary Period)', markers=True, template="plotly_white")
            st.plotly_chart(figs_primary['Trend'], use_container_width=True)

    # Detailed records for Primary Period
    if len(df_primary_period) < 50 or (primary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.subheader("Detailed Records (Primary Period - Filtered)")
        df_display = df_primary_period[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']].copy()
        if pd.api.types.is_datetime64_any_dtype(df_display['date']):
            df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d') 
        st.dataframe(df_display)

    # Top issues for Primary Period
    st.subheader("Top Issues (Primary Period - Filtered)")
    if 'issues' in df_primary_period.columns and not df_primary_period['issues'].isnull().all():
        top_issues_data = df_primary_period['issues'].astype(str).value_counts().head(20).rename_axis('Issue Description').reset_index(name='Frequency')
        if not top_issues_data.empty: st.dataframe(top_issues_data)


# --- NEW: Period Comparison Display ---
if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.markdown("---")
    st.header("📊 Period Comparison Results")

    # Filter for Comparison Period 1
    df_comp1 = df_temp_filtered.copy()
    start_c1, end_c1 = comparison_date_range_1[0], comparison_date_range_1[1]
    df_comp1 = df_comp1[(df_comp1['date'].dt.date >= start_c1) & (df_comp1['date'].dt.date <= end_c1)]

    # Filter for Comparison Period 2
    df_comp2 = df_temp_filtered.copy()
    start_c2, end_c2 = comparison_date_range_2[0], comparison_date_range_2[1]
    df_comp2 = df_comp2[(df_comp2['date'].dt.date >= start_c2) & (df_comp2['date'].dt.date <= end_c2)]

    st.subheader(f"Period 1: {start_c1.strftime('%Y-%m-%d')} to {end_c1.strftime('%Y-%m-%d')}")
    st.write(f"Total issues in Period 1: {len(df_comp1)}")
    st.subheader(f"Period 2: {start_c2.strftime('%Y-%m-%d')} to {end_c2.strftime('%Y-%m-%d')}")
    st.write(f"Total issues in Period 2: {len(df_comp2)}")

    if df_comp1.empty and df_comp2.empty:
        st.warning("No data found for either comparison period with current filters.")
    else:
        # Example: Compare total issues
        col_comp1, col_comp2 = st.columns(2)
        with col_comp1:
            st.metric(label=f"Total Issues (Period 1)", value=len(df_comp1))
            if not df_comp1.empty:
                 st.caption("Top 5 Issues - Period 1")
                 st.dataframe(df_comp1['issues'].value_counts().nlargest(5).reset_index(), height=200)

        with col_comp2:
            st.metric(label=f"Total Issues (Period 2)", value=len(df_comp2), delta=f"{len(df_comp2) - len(df_comp1)} vs P1")
            if not df_comp2.empty:
                st.caption("Top 5 Issues - Period 2")
                st.dataframe(df_comp2['issues'].value_counts().nlargest(5).reset_index(), height=200)
        
        # Example: Compare issues by branch (side-by-side bar chart)
        if not df_comp1.empty or not df_comp2.empty:
            df_comp1['period'] = "Period 1"
            df_comp2['period'] = "Period 2"
            df_combined_branch = pd.concat([df_comp1, df_comp2])
            
            if not df_combined_branch.empty:
                branch_comparison_data = df_combined_branch.groupby(['branch', 'period']).size().reset_index(name='count')
                if not branch_comparison_data.empty:
                    fig_branch_comp = px.bar(branch_comparison_data, x='branch', y='count', color='period',
                                             barmode='group', title='Issues by Branch (Comparison)',
                                             template="plotly_white")
                    st.plotly_chart(fig_branch_comp, use_container_width=True)
            
            # Trend comparison (if feasible)
            trend_c1 = df_comp1.groupby(df_comp1['date'].dt.date).size().reset_index(name='count_p1')
            trend_c2 = df_comp2.groupby(df_comp2['date'].dt.date).size().reset_index(name='count_p2')

            # For a proper trend comparison on one axis, we'd need a common relative time axis (e.g., Day 1, Day 2...)
            # This is a bit more complex to align arbitrary periods.
            # For now, let's just show separate trends if data exists.
            if not trend_c1.empty:
                fig_trend_c1 = px.line(trend_c1, x='date', y='count_p1', title='Trend Period 1', markers=True)
                st.plotly_chart(fig_trend_c1, use_container_width=True)
            if not trend_c2.empty:
                fig_trend_c2 = px.line(trend_c2, x='date', y='count_p2', title='Trend Period 2', markers=True)
                st.plotly_chart(fig_trend_c2, use_container_width=True)


# --- Downloads (operates on df_primary_period for now) ---
st.sidebar.subheader("Downloads")
if not df_primary_period.empty:
    csv_data = df_primary_period.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download Primary Period Data as CSV", csv_data, "primary_period_issues.csv", "text/csv", key="download_csv_primary")
    
    # PDF generation would typically be for the primary period's visuals.
    # If comparison visuals are needed in PDF, that would require more logic for fig selection.
    if st.sidebar.button("Prepare Visuals PDF (Primary Period)", key="prep_visuals_pdf_primary"):
        if not wk_path or wk_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        elif not any(figs_primary.values()): st.sidebar.warning("No visuals for primary period.")
        else:
            # ... (PDF generation logic using figs_primary) ...
            st.sidebar.info("Visuals PDF for primary period prepared (placeholder).")


st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH}")
