import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import sqlite3
import io
import shutil
import base64
from datetime import datetime

# Database setup
DB_PATH = 'issues.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    uploader TEXT,
    timestamp TEXT,
    file_type TEXT,
    category TEXT,
    file BLOB
)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (
    upload_id INTEGER,
    code TEXT,
    issues TEXT,
    branch TEXT,
    area_manager TEXT,
    date TEXT,
    report_type TEXT,
    FOREIGN KEY(upload_id) REFERENCES uploads(id)
)''')
conn.commit()

# Credentials
db_admin = {
    "abdalziz alsalem": b"$2b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvpLxRumSduEte8MDAPkOnuXMdnW",
    "omar salah": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01ecj1cEShMAZGYbFCE3JdGagfaWomy",
    "ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGkEn.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG",
    "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgY8zEwgY/bYIqe"
}
view_only = ["mohamed emad", "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"]

# Streamlit config
st.set_page_config(page_title="Performance Dashboard", layout="wide")
st.title("📊 classic Dashboard for performance")

# Authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None # 'admin' or 'view_only'

if not st.session_state.authenticated:
    user_input = st.text_input("Enter your full name:").strip().lower()
    pwd_input = st.text_input("Enter your password:", type="password")
    
    if st.button("Login"):
        if user_input in db_admin and bcrypt.checkpw(pwd_input.encode(), db_admin[user_input]):
            st.session_state.authenticated = True
            st.session_state.user_role = 'admin'
            st.session_state.user_name = user_input
            st.rerun()
        elif user_input in view_only: # For view_only, password check might be simpler or different
            # Assuming view_only users might not need a bcrypt password for this example
            # Or you can extend db_admin-like structure for them if they have passwords
            # For now, let's assume a placeholder password or simple check
            # This part needs secure password handling for view_only users if passwords are required
            # For simplicity, if they are in view_only list and provide any password, let's allow.
            # IMPORTANT: This is a simplified view-only auth. Implement proper password checks if needed.
            if pwd_input: # Basic check: password field is not empty
                st.session_state.authenticated = True
                st.session_state.user_role = 'view_only'
                st.session_state.user_name = user_input
                st.rerun()
            else:
                st.error("Password cannot be empty for view-only users.")
        else:
            st.error("Invalid credentials.")
    else:
        st.info("Enter credentials to proceed.")
        st.stop()
else: # Authenticated
    st.sidebar.success(f"Logged in as: {st.session_state.user_name.title()} ({st.session_state.user_role})")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


is_admin = st.session_state.user_role == 'admin'
current_user = st.session_state.user_name


# PDF generator
def generate_pdf(html, fname='report.pdf', wk_path=None):
    if not wk_path:
        st.error("wkhtmltopdf path not set. Please provide the path in the sidebar.")
        return None
    try:
        import pdfkit
        config = pdfkit.configuration(wkhtmltopdf=wk_path)
        
        # --- MODIFIED OPTIONS for unpatched wkhtmltopdf ---
        options = {
            'enable-local-file-access': None,
            # 'print-media-type': None,       # Removed - unsupported by unpatched Qt
            'background': None,             # Keep, might work or be ignored, generally safe
            # 'no-grayscale': None,           # Removed - unknown argument
            'images': None,
            'encoding': "UTF-8",
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
            'disable-smart-shrinking': None, # This might also be unsupported, test
            'zoom': 0.8,
            'page-size': 'A4',
        }
        # If you still want to try forcing color (and it defaults to it anyway if --grayscale isn't used)
        # you might not need any specific color option.
        # If it still comes out grayscale, your wkhtmltopdf might default to it for some reason
        # or the content itself is styled that way.

        pdfkit.from_string(html, fname, configuration=config, options=options)
        with open(fname, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"wkhtmltopdf not found at the specified path: {wk_path}. Please ensure it's installed and the path is correct.")
        return None
    except Exception as e:
        st.error(f"PDF generation error: {e}") # This will show the wkhtmltopdf error output
        return None
# Sidebar: controls
st.sidebar.header("🔍 Filters & Options")

# Upload control for admins
if is_admin:
    st.sidebar.subheader("Admin Controls")
    file_type_upload = st.sidebar.selectbox("File type for upload", ["opening", "closing", "handover", "meal training"], key="upload_file_type")
    category_upload = st.sidebar.selectbox("Category for upload", ['operation-training', 'CCTV', 'complaints', 'missing', 'visits', 'meal training'], key="upload_category")
    up = st.sidebar.file_uploader("Upload Excel", type=["xlsx"], key="excel_uploader")
    upload_btn = st.sidebar.button("Upload Data", key="upload_data_button")
    if up and upload_btn:
        data = up.getvalue()
        ts = datetime.now().isoformat()
        c.execute('SELECT COUNT(*) FROM uploads WHERE filename=? AND uploader=? AND file_type=? AND category=?',
                  (up.name, current_user, file_type_upload, category_upload))
        if c.fetchone()[0] == 0:
            c.execute(
                'INSERT INTO uploads (filename, uploader, timestamp, file_type, category, file) VALUES (?, ?, ?, ?, ?, ?)',
                (up.name, current_user, ts, file_type_upload, category_upload, sqlite3.Binary(data))
            )
            uid = c.lastrowid
            df_up = pd.read_excel(io.BytesIO(data))
            df_up.columns = [col.strip().lower() for col in df_up.columns] # Ensure column names are lower and stripped
            
            # Validate required columns
            required_cols = ['code', 'issues', 'branch', 'area manager', 'date']
            missing_cols = [col for col in required_cols if col not in df_up.columns]
            if missing_cols:
                st.sidebar.error(f"Excel sheet is missing required columns: {', '.join(missing_cols)}")
            else:
                try:
                    df_up['date'] = pd.to_datetime(df_up['date'], dayfirst=True, errors='coerce')
                    # Drop rows where date parsing failed
                    original_len = len(df_up)
                    df_up.dropna(subset=['date'], inplace=True)
                    if len(df_up) < original_len:
                        st.sidebar.warning(f"{original_len - len(df_up)} rows dropped due to invalid date format.")

                    for _, row in df_up.iterrows():
                        c.execute('INSERT INTO issues VALUES (?, ?, ?, ?, ?, ?, ?)',
                                (uid, row['code'], row['issues'], row['branch'], row['area manager'], row['date'].isoformat(), file_type_upload))
                    conn.commit()
                    st.sidebar.success(f"Uploaded {up.name} ({len(df_up)} records)")
                except Exception as e:
                    st.sidebar.error(f"Error processing Excel file: {e}")
        else:
            st.sidebar.warning("This file (based on name, uploader, type, category) has already been uploaded.")

# wkhtmltopdf path
default_wk = shutil.which('wkhtmltopdf') or ''
wk_path = st.sidebar.text_input("wkhtmltopdf path:", default_wk, help="Path to wkhtmltopdf executable. Required for PDF downloads.")

# Load uploads for selection and deletion
df_uploads = pd.read_sql('SELECT id, filename, uploader, timestamp, file_type, category FROM uploads ORDER BY timestamp DESC', conn)

# Scope selection
st.sidebar.subheader("Data Scope")
scope_opts = ['All uploads'] + [f"{row['id']} - {row['filename']} ({row['file_type']})" for index, row in df_uploads.iterrows()]
sel_display = st.sidebar.selectbox("Select upload to analyze:", scope_opts, key="select_upload_scope")
sel_id = None
if sel_display != 'All uploads':
    sel_id = int(sel_display.split(' - ')[0])


# Admin: delete submission
if is_admin:
    st.sidebar.subheader("Manage Submissions")
    delete_opts = ['Select ID to Delete'] + [f"{row['id']} - {row['filename']}" for index, row in df_uploads.iterrows()]
    del_choice_display = st.sidebar.selectbox("🗑️ Delete Submission:", delete_opts, key="delete_submission_id")
    if del_choice_display != 'Select ID to Delete':
        del_id = int(del_choice_display.split(' - ')[0])
        if st.sidebar.button(f"Confirm Delete Submission #{del_id}", key=f"confirm_del_{del_id}", type="primary"):
            c.execute('DELETE FROM issues WHERE upload_id=?', (del_id,))
            c.execute('DELETE FROM uploads WHERE id=?', (del_id,))
            conn.commit()
            st.sidebar.success(f"Deleted submission {del_id} and its associated issues.")
            try:
                st.rerun()
            except AttributeError: # Fallback for very old Streamlit versions
                st.experimental_rerun()


# Fetch data for dashboard
sql = 'SELECT i.*, u.category as upload_category, u.file_type as master_file_type FROM issues i JOIN uploads u ON u.id = i.upload_id'
params = []
if sel_id:
    sql += ' WHERE i.upload_id = ?'
    params.append(sel_id)
df = pd.read_sql(sql, conn, params=params, parse_dates=['date'])

if df.empty:
    st.warning("No data to display for the selected scope. Please upload data or broaden filters.")
    st.stop()

# Filters
st.sidebar.subheader("Dashboard Filters")
min_date = df['date'].min().date() if not df.empty else datetime.today().date()
max_date = df['date'].max().date() if not df.empty else datetime.today().date()

date_range = st.sidebar.date_input("Date range:", [min_date, max_date], min_value=min_date, max_value=max_date, key="date_range_filter")
if not date_range or len(date_range) != 2: # Ensure date_range is valid
    date_range = [min_date, max_date]


branch_opts = ['All'] + sorted(df['branch'].unique().tolist())
sel_br = st.sidebar.multiselect("Branch:", branch_opts, default=['All'], key="branch_filter")

cat_opts = ['All'] + sorted(df['upload_category'].unique().tolist()) # Use 'upload_category' from join
sel_cat = st.sidebar.multiselect("Category:", cat_opts, default=['All'], key="category_filter")

# NEW: Filter by File Type (derived from issues.report_type which is set during upload)
file_type_filter_opts = ['All'] + sorted(df['report_type'].unique().tolist())
sel_ft = st.sidebar.multiselect("File Type (Report Type):", file_type_filter_opts, default=['All'], key="file_type_filter")


# Apply filters
df_f = df.copy()
if date_range and len(date_range) == 2:
    df_f = df_f[(df_f['date'].dt.date >= date_range[0]) & (df_f['date'].dt.date <= date_range[1])]

if 'All' not in sel_br:
    df_f = df_f[df_f['branch'].isin(sel_br)]
if 'All' not in sel_cat:
    df_f = df_f[df_f['upload_category'].isin(sel_cat)]
if 'All' not in sel_ft:
    df_f = df_f[df_f['report_type'].isin(sel_ft)]


# Dashboard
st.subheader(f"Filtered Issues from {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}")
st.write(f"Total issues found: {len(df_f)}")

if df_f.empty:
    st.info("No data matches the current filter criteria.")
    st.stop()

# Charts
figs = {}
if not df_f.empty:
    col1, col2 = st.columns(2)
    with col1:
        if 'branch' in df_f.columns and not df_f['branch'].empty:
            figs['Branch'] = px.bar(df_f.groupby('branch').size().reset_index(name='count').sort_values('count', ascending=False), 
                                    x='branch', y='count', title='Issues by Branch')
            st.plotly_chart(figs['Branch'], use_container_width=True)
        
        if 'report_type' in df_f.columns and not df_f['report_type'].empty:
            figs['Report Type'] = px.bar(df_f.groupby('report_type').size().reset_index(name='count').sort_values('count', ascending=False), 
                                        x='report_type', y='count', title='Issues by Report Type')
            st.plotly_chart(figs['Report Type'], use_container_width=True)

    with col2:
        if 'area_manager' in df_f.columns and not df_f['area_manager'].empty:
            figs['Area Manager'] = px.pie(df_f.groupby('area_manager').size().reset_index(name='count'), 
                                        names='area_manager', values='count', title='Issues by Area Manager')
            st.plotly_chart(figs['Area Manager'], use_container_width=True)

        if 'upload_category' in df_f.columns and not df_f['upload_category'].empty:
            figs['Category'] = px.bar(df_f.groupby('upload_category').size().reset_index(name='count').sort_values('count', ascending=False), 
                                    x='upload_category', y='count', title='Issues by Upload Category')
            st.plotly_chart(figs['Category'], use_container_width=True)

    # Trend Chart
    if 'date' in df_f.columns and not df_f['date'].empty:
        trend_data = df_f.groupby(df_f['date'].dt.date).size().reset_index(name='count')
        figs['Trend'] = px.line(trend_data, x='date', y='count', title='Issues Trend Over Time', markers=True)
        st.plotly_chart(figs['Trend'], use_container_width=True)

# Detailed records (optional, or if few records)
if len(df_f) < 50 or (date_range and date_range[0] == date_range[1]): # Show if single day or few records
    st.subheader("Detailed Records (Filtered)")
    st.dataframe(df_f[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager', 'code']])

# Top issues
st.subheader("Top Issues (Filtered)")
if 'issues' in df_f.columns and not df_f['issues'].empty:
    st.dataframe(df_f['issues'].value_counts().head(20).rename_axis('Issue Description').reset_index(name='Frequency'))


# Downloads
st.sidebar.subheader("Downloads")
csv_data = df_f.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("Download Filtered Data as CSV", csv_data, "filtered_issues.csv", "text/csv", key="download_csv")

if st.sidebar.button("Prepare Visuals PDF", key="prep_visuals_pdf"):
    if not wk_path or wk_path == "not found":
        st.sidebar.error("wkhtmltopdf path not set or invalid. Cannot generate PDF.")
    elif not figs:
        st.sidebar.warning("No visuals to include in the PDF.")
    else:
        html = '<html><head><meta charset="utf-8"><title>Visuals Report</title></head><body>'
        html += f"<h1>Visuals Report ({date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')})</h1>"
        for title, fig in figs.items():
            try:
                img_bytes = fig.to_image(format='png', engine='kaleido') # Ensure kaleido is installed
                b64_img = base64.b64encode(img_bytes).decode()
                html += f"<h2>{title}</h2><img src='data:image/png;base64,{b64_img}' style='max-width: 95%; height: auto; display: block; margin-left: auto; margin-right: auto; border: 1px solid #ccc; padding: 5px;'/><br/>"
            except Exception as e:
                st.sidebar.warning(f"Could not convert figure '{title}' to image: {e}. Ensure 'kaleido' is installed (`pip install kaleido`).")
        html += '</body></html>'
        
        pdf_content = generate_pdf(html, fname='visuals_report.pdf', wk_path=wk_path)
        if pdf_content:
            st.session_state.pdf_visuals_data = pdf_content
            st.sidebar.success("Visuals PDF is ready.")
        else:
            if 'pdf_visuals_data' in st.session_state:
                del st.session_state.pdf_visuals_data # Clear stale data if generation failed
            # Error message already shown by generate_pdf

if 'pdf_visuals_data' in st.session_state and st.session_state.pdf_visuals_data:
    st.sidebar.download_button(
        label="Download Visuals PDF Now",
        data=st.session_state.pdf_visuals_data,
        file_name="visuals_report.pdf",
        mime="application/pdf",
        key="action_download_visuals_pdf"
    )

if st.sidebar.button("Prepare Full Dashboard PDF", key="prep_dashboard_pdf"):
    if not wk_path or wk_path == "not found":
        st.sidebar.error("wkhtmltopdf path not set or invalid. Cannot generate PDF.")
    elif df_f.empty:
        st.sidebar.warning("No data to include in the Dashboard PDF.")
    else:
        html_full = f"<h1>Dashboard Report ({date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')})</h1>"
        html_full += df_f.to_html(index=False, classes="dataframe", border=0) # Basic styling
        
        # (Optional) Add visuals to this PDF as well, similar to visuals_pdf
        # For brevity, I'm keeping it to just the table data here.
        # You could iterate through `figs` and add them as base64 images like in the visuals PDF.

        pdf_full_content = generate_pdf(html_full, fname='dashboard_report.pdf', wk_path=wk_path)
        if pdf_full_content:
            st.session_state.pdf_dashboard_data = pdf_full_content
            st.sidebar.success("Dashboard PDF is ready.")
        else:
            if 'pdf_dashboard_data' in st.session_state:
                del st.session_state.pdf_dashboard_data

if 'pdf_dashboard_data' in st.session_state and st.session_state.pdf_dashboard_data:
    st.sidebar.download_button(
        label="Download Dashboard PDF Now",
        data=st.session_state.pdf_dashboard_data,
        file_name="dashboard_report.pdf",
        mime="application/pdf",
        key="action_download_dashboard_pdf"
    )

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH}")
