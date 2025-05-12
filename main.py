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

# Streamlit config MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- Database setup (assuming correct as before) ---
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
# ... (table creation and schema check logic remains the same) ...
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
    file_type TEXT, category TEXT, submission_date TEXT, file BLOB
)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    upload_id INTEGER, code TEXT, issues TEXT, branch TEXT, area_manager TEXT,
    date TEXT, report_type TEXT, FOREIGN KEY(upload_id) REFERENCES uploads(id)
)''')
conn.commit()
c.execute("PRAGMA table_info(uploads)")
if 'submission_date' not in [col[1] for col in c.fetchall()]:
    try:
        c.execute("ALTER TABLE uploads ADD COLUMN submission_date TEXT")
        conn.commit()
        if 'db_schema_updated_flag' not in st.session_state: st.session_state.db_schema_updated_flag = True
    except sqlite3.OperationalError as e:
        st.session_state.db_critical_error_msg = f"Failed to update 'uploads' schema: {e}"


# Credentials (assuming correct as before)
db_admin = { # Your admin users
    "abdalziz alsalem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvpLxRumSduEte8MDAPkOnuXMdnW",
    # ... other admins
}
view_only = ["mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"] # Your view-only users

# --- NEW: Define Category-File Type Mapping ---
category_file_types = {
    'operation-training': ['opening', 'closing', 'handover', 'store arranging', 'tempreature of heaters', 'defrost', 'clean AC'],
    'CCTV': ['issues', 'submission time'],
    'complaints': ['performance', 'اغلاق الشكاوي'], # Handles Arabic text
    'missing': ['performance'],
    'visits': [], # No specific types for 'visits' as requested
    'meal training': ['performance', 'missing types']
}
# List of all categories available for selection
all_categories = list(category_file_types.keys())


# --- Show errors/toasts (assuming correct as before) ---
if 'db_critical_error_msg' in st.session_state: # ... (error handling)
    st.error(f"DB Startup Error: {st.session_state.db_critical_error_msg}")
    del st.session_state.db_critical_error_msg
if 'db_schema_updated_flag' in st.session_state and st.session_state.db_schema_updated_flag: # ... (toast)
    st.toast("DB 'uploads' table schema updated.", icon="ℹ️")
    st.session_state.db_schema_updated_flag = False

# --- Authentication Function (assuming correct as before) ---
def check_login(): # ... (check_login logic)
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False; st.session_state.user_name=None; st.session_state.user_role=None
    if not st.session_state.authenticated:
        # Login page display logic...
        return False
    return True
if not check_login(): st.stop()

# --- Logo & Title Logic (assuming correct as before) ---
LOGO_PATH = "company_logo.png" # Make sure this path is correct
col1_main_title, col2_main_title = st.columns([1, 6]) 
with col1_main_title:
    try: st.image(LOGO_PATH, width=70) 
    except Exception: pass 
with col2_main_title:
    st.title("📊 Classic Dashboard for Performance")

# --- Sidebar login status (assuming correct as before) ---
user_name_display = st.session_state.get('user_name', "N/A").title()
user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main"): # ... (logout logic)
    st.session_state.authenticated=False; st.session_state.user_name=None; st.session_state.user_role=None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.session_state.get('user_name', 'Unknown User')

# --- PDF generator (assuming correct as before) ---
def generate_pdf(html, fname='report.pdf', wk_path=None): # ... (generate_pdf logic)
    pass # Placeholder

# ==============================================================
# --- MODIFIED Admin Controls SECTION ---
# ==============================================================
st.sidebar.header("🔍 Filters & Options")

if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("Set parameters below, choose Excel file, then click 'Upload Data'.")
    
    # 1. Category Selection
    selected_category = st.sidebar.selectbox(
        "Category for upload",
        options=all_categories, # Use the defined list
        key="admin_category_select" # Use a key to access state easily
    )
    
    # 2. Get Valid File Types based on Selected Category
    # Access the selected category value using its key from session state
    current_category = st.session_state.get("admin_category_select", all_categories[0]) # Default to first category if state not set yet
    valid_file_types = category_file_types.get(current_category, []) # Get list, default to empty list if category not found

    # 3. File Type Selection (Dynamic Options)
    selected_file_type = st.sidebar.selectbox(
        "File type for upload",
        options=valid_file_types, # Use the dynamic list based on category
        key="admin_file_type_select",
        # Disable the dropdown if the selected category has no valid file types
        disabled=(not valid_file_types),
        help="Options change based on the selected category. Select category first." if current_category == 'visits' else None # Example help text
    )
    
    # 4. Rest of the upload controls
    effective_report_date = st.sidebar.date_input(
        "**Effective Date of Report:**", 
        value=date.today(), 
        key="effective_report_date_upload",
        help="Select the date this report should be attributed to."
    )

    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")

    # 5. Upload Processing Logic (Uses selected_category and selected_file_type)
    if upload_btn: 
        # Use st.session_state to get the definitive values selected just before button press
        final_category = st.session_state.admin_category_select
        final_file_type = st.session_state.admin_file_type_select

        if not final_file_type and valid_file_types: # Check if a file type should have been selected
             st.sidebar.warning(f"Please select a file type for the '{final_category}' category.")
        elif not final_file_type and not valid_file_types: # Category has no types (e.g., visits)
             st.sidebar.info(f"Category '{final_category}' does not require a specific file type.")
             # Allow upload or handle as needed - for now, assume upload is ok but file_type is None/empty
             final_file_type = None # Or ""
        
        # Proceed with upload only if mandatory selections are made (and file is chosen)
        if up and effective_report_date and (final_file_type or not valid_file_types): 
            data = up.getvalue(); ts = datetime.now().isoformat(); effective_date_str = effective_report_date.isoformat() 
            
            c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type=? AND category=? AND submission_date=?',
                      (up.name, current_user, final_file_type, final_category, effective_date_str)) # Use final values
            
            if c.fetchone()[0] == 0:
                c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, category, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                          (up.name, current_user, ts, final_file_type, final_category, effective_date_str, sqlite3.Binary(data))) # Use final values
                uid = c.lastrowid
                try:
                    df_up = pd.read_excel(io.BytesIO(data)); df_up.columns = [col.strip().lower() for col in df_up.columns]
                    required_cols = ['code', 'issues', 'branch', 'area manager', 'date'] 
                    missing_cols = [col for col in required_cols if col not in df_up.columns]
                    if missing_cols:
                        st.sidebar.error(f"Excel missing: {', '.join(missing_cols)}. Aborted."); c.execute('DELETE FROM uploads WHERE id=?', (uid,)); conn.commit()
                    else:
                        df_up['excel_date_validated'] = pd.to_datetime(df_up['date'], dayfirst=True, errors='coerce')
                        original_len = len(df_up); df_up.dropna(subset=['excel_date_validated'], inplace=True)
                        if len(df_up) < original_len: st.sidebar.warning(f"{original_len - len(df_up)} rows dropped (invalid date).")
                        if df_up.empty:
                            st.sidebar.error("No valid data in Excel. Aborted."); c.execute('DELETE FROM uploads WHERE id=?', (uid,)); conn.commit()
                        else:
                            for _, row in df_up.iterrows():
                                # Important: Insert the file type selected in the UI into the issues table!
                                c.execute('INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                          (uid, row['code'], row['issues'], row['branch'], row['area manager'], effective_date_str, final_file_type)) # Use final_file_type
                            conn.commit(); st.sidebar.success(f"Uploaded '{up.name}' ({len(df_up)} recs) Eff.Date: {effective_date_str}"); st.rerun() 
                except Exception as e:
                    st.sidebar.error(f"Excel error '{up.name}': {e}. Rolled back."); c.execute('DELETE FROM uploads WHERE id=?', (uid,)); conn.commit()
            else: st.sidebar.warning(f"Duplicate file for date '{effective_date_str}' exists.")
        else:
            if not up: st.sidebar.error("Please select an Excel file.")
            # Other checks if needed

# ==============================================================
# --- End of MODIFIED Admin Controls SECTION ---
# ==============================================================


# --- wkhtmltopdf path (assuming correct) ---
default_wk = shutil.which('wkhtmltopdf') or 'not found'
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk)

# --- Data Scope Selection (assuming correct) ---
df_uploads_raw = pd.read_sql('SELECT id, filename, file_type, category, submission_date FROM uploads ORDER BY submission_date DESC, timestamp DESC', conn)
def format_display_date(d): return datetime.strptime(str(d),'%Y-%m-%d').strftime('%Y-%m-%d') if pd.notna(d) else "N/A"
df_uploads_raw['display_submission_date'] = df_uploads_raw['submission_date'].apply(format_display_date)
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [f"{r['id']} - {r['filename']} ({r['category']}/{r['file_type'] or 'N/A'}) Eff.Date: {r['display_submission_date']}" for i,r in df_uploads_raw.iterrows()]
sel_display = st.sidebar.selectbox("Select upload to analyze:", scope_opts, key="select_upload_scope")
sel_id = int(sel_display.split(' - ')[0]) if sel_display != 'All uploads' else None

# --- Manage Submissions (assuming correct) ---
if is_admin: # ... (delete logic)
    pass # Placeholder

# --- Fetch Data ---
df_all_issues = pd.read_sql('SELECT i.*, u.category as upload_category, u.id as upload_id_col FROM issues i JOIN uploads u ON u.id = i.upload_id', conn, parse_dates=['date'])
if df_all_issues.empty: st.warning("No data in database."); st.stop()

# --- Dashboard Filters (assuming correct) ---
st.sidebar.subheader("Dashboard Filters")
min_overall_date, max_overall_date = (d.date() if pd.notna(d) else date.today() for d in (df_all_issues['date'].min(), df_all_issues['date'].max()))
primary_date_range = st.sidebar.date_input("Primary Date Range:", value=[min_overall_date, max_overall_date], min_value=min_overall_date, max_value=max_overall_date, key="primary_date_range_filter")
if not primary_date_range or len(primary_date_range)!=2: primary_date_range = [min_overall_date, max_overall_date]
sel_branch = st.sidebar.multiselect("Branch:", ['All'] + sorted(df_all_issues['branch'].astype(str).unique().tolist()), default=['All'], key="branch_filter")
sel_cat = st.sidebar.multiselect("Category:", ['All'] + sorted(df_all_issues['upload_category'].astype(str).unique().tolist()), default=['All'], key="category_filter")
sel_am = st.sidebar.multiselect("Area Manager:", ['All'] + sorted(df_all_issues['area_manager'].astype(str).unique().tolist()), default=['All'], key="area_manager_filter")
sel_ft = st.sidebar.multiselect("File Type (Report Type):", ['All'] + sorted(df_all_issues['report_type'].astype(str).unique().tolist()), default=['All'], key="file_type_filter") # This now filters the 'issues' table

# --- Period Comparison Setup (assuming correct) ---
st.sidebar.subheader("📊 Period Comparison")
enable_comparison = st.sidebar.checkbox("Enable Period Comparison", key="enable_comparison_checkbox")
comparison_date_range_1, comparison_date_range_2 = None, None
if enable_comparison: # ... (comparison date selection logic)
    pass # Placeholder

# --- Apply Filters ---
def apply_general_filters(df_input, sel_upload_id_val, sel_br, sel_cat, sel_am, sel_ft): # Modified parameters
    df_filtered = df_input.copy()
    if sel_upload_id_val: df_filtered = df_filtered[df_filtered['upload_id_col'] == sel_upload_id_val]
    if 'All' not in sel_br: df_filtered = df_filtered[df_filtered['branch'].isin(sel_br)]
    if 'All' not in sel_cat: df_filtered = df_filtered[df_filtered['upload_category'].isin(sel_cat)] # Filter based on upload's category
    if 'All' not in sel_am: df_filtered = df_filtered[df_filtered['area_manager'].isin(sel_am)]
    # Note: Filtering by sel_ft here filters the 'report_type' stored in the 'issues' table,
    # which now directly comes from the UI selection during upload.
    if 'All' not in sel_ft: df_filtered = df_filtered[df_filtered['report_type'].isin(sel_ft)]
    return df_filtered

df_temp_filtered = apply_general_filters(df_all_issues, sel_id, sel_branch, sel_cat, sel_am, sel_ft) # Pass correct filter selections

# Filter for Primary Period (assuming correct)
df_primary_period = df_temp_filtered.copy()
if primary_date_range and len(primary_date_range) == 2:
    start_date, end_date = primary_date_range[0], primary_date_range[1]
    df_primary_period = df_primary_period[(df_primary_period['date'].dt.date >= start_date) & (df_primary_period['date'].dt.date <= end_date)]
else: df_primary_period = pd.DataFrame(columns=df_temp_filtered.columns)

# --- Dashboard Display ---
st.subheader(f"Filtered Issues for Primary Period: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d}")
st.write(f"Total issues found in primary period: {len(df_primary_period)}")

# Chart generation functions (assuming correct)
def create_bar_chart(df_source, group_col, title_suffix=""): pass # Placeholder
def create_pie_chart(df_source, group_col, title_suffix=""): pass # Placeholder

if df_primary_period.empty:
    st.info("No data matches the current filter criteria for the primary period.")
else:
    # --- Main dashboard charts, detailed records, top issues (assuming correct logic using enhanced trend chart) ---
    figs_primary = {}
    # ... (Chart generation including enhanced Trend) ...
    # ... (Detailed Records display) ...
    # ... (Top Issues display) ...
    pass # Placeholder for brevity


# --- Period Comparison Display (assuming correct logic using Period-Level Trend) ---
if enable_comparison and comparison_date_range_1 and comparison_date_range_2:
    st.markdown("---"); st.header("📊 Period Comparison Results")
    # ... (Calculation and display logic for comparison metrics, branch comparison, and period-level trend) ...
    pass # Placeholder for brevity


# --- Downloads Section (assuming correct as per last fix) ---
st.sidebar.subheader("Downloads")
# ... (All download buttons and logic for primary CSV/PDFs and optional comparison CSVs) ...
pass # Placeholder for brevity


# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH}")
