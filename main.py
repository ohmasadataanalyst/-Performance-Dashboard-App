import streamlit as st
import pandas as pd
import plotly.express.")
else:
    figs_primary = {}
    col1_charts, col2_charts = st.columns(2)
    with col1_charts:
        figs_primary['Branch'] = create_bar_chart الرمال", # From CCTV sample, maps to MURUH B19
    "B06": "Ald as px
import plotly.graph_objects as go 
import bcrypt
import sqlite3
import io
import(df_primary_period, 'branch', '(Primary)')
        if figs_primary['Branch']: st.plotly_araiah - الدرعية", # From CCTV sample, maps to DARUH B06
    "B10 shutil
import base64
from datetime import datetime, date, timedelta
import os 

# Streamlit config": "Alshifa - الشفاء", # From CCTV sample, maps to SHRUH B10
    chart(figs_primary['Branch'], use_container_width=True)
        figs_primary['Report Type MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="Performance Dashboard","QB02": "Shawarma Garatis Alnargis B02 -  B02 شاورما ق'] = create_bar_chart(df_primary_period, 'report_type', '(Primary)')
         layout="wide")

# --- Database setup ---
DB_PATH = 'issues.db' 
conn =if figs_primary['Report Type']: st.plotly_chart(figs_primary['Report Type'], use_containerراطيس النرجس", # From CCTV sample
    "B08": "Alsweedi - السويدي", # sqlite3.connect(DB_PATH, check_same_thread=False, timeout=20) 
_width=True)
    with col2_charts:
        figs_primary['Area Manager'] = create From CCTV sample, maps to SWRUH B08
    "B03": "Gurnatah -c = conn.cursor()

def initialize_database_schema(cursor, connection):
    # st.write("DEBUG: Initializing/Verifying database schema...") # Can be noisy
    cursor.execute('''CREATE TABLE IF NOT EXISTS uploads_pie_chart(df_primary_period, 'area_manager', '(Primary)')
        if figs_primary['Area Manager']: st.plotly_chart(figs_primary['Area Manager'], use_container_width= غرناطة", # From CCTV sample, maps to GHRUH B03
    "B30": "Al Qadisiyyah branch - فرع القادسية", # From CCTV sample, maps to QADRUH B3 (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, uploader TEXT, timestamp TEXT,
        file_True)
        figs_primary['Category'] = create_bar_chart(df_primary_period, '0
    "B24": "Alsafa Jeddah - الصفا جدة", # From CCTV sample, mapstype TEXT, category TEXT, submission_date TEXT, file BLOB
    )''')
    connection.commit to SFJED B24
    "B21": "Alkharj - الخرج",# From CCTV sample,upload_category', '(Primary)') 
        if figs_primary['Category']: st.plotly_chart(figs() 
    required_uploads_columns = {
        "submission_date": "TEXT", "category": "_primary['Category'], use_container_width=True)
    
    if 'date' in df_ maps to KRRUH B21
    "B04": "Alnaseem Riyadh- النسيم الرياض", #TEXT", "file_type": "TEXT",
        "uploader": "TEXT", "timestamp": "TEXT"primary_period.columns and pd.api.types.is_datetime64_any_dtype(df_primary_period['date']) and not df_primary_period['date'].isnull().all():
        trend_ From CCTV sample, maps to NSRUH B04
    "B25": "Al Rawdha Al Hofuf - الروضة الهفوف", # From CCTV sample, maps to RWAHS B25
    "B
    }
    cursor.execute("PRAGMA table_info(uploads)")
    existing_uploads_cols = {col[1]: col[2] for col in cursor.fetchall()}
    for col_name, col_data_primary = df_primary_period.groupby(df_primary_period['date'].dt.date).type in required_uploads_columns.items():
        if col_name not in existing_uploads_cols:
            try:
                cursor.execute(f"ALTER TABLE uploads ADD COLUMN {col_name} {col18": "Takhasussi Riyadh - التخصصي الرياض",# From CCTV sample, maps to TKRUH B18
    "B17": "Alqairawan - القيروان",# From CCTV sample, maps to QRRUH B17
    "B16": "Albadeah - البديعة", # From CCTV sample,size().reset_index(name='daily_issues')
        trend_data_primary['date'] = pd.to_datetime(trend_data_primary['date']); trend_data_primary = trend_data_primary.sort_values('date')
        if not trend_data_primary.empty:
            window_size = min(7, len(trend_data_primary)); window_size = max(2,window_size) 
            trend_data_primary[f'{window_size}-Day MA'] = trend_data_primary['daily_issues'].rolling(window=window_size, center=True, min_periods=1).mean()._type}")
                connection.commit()
                st.toast(f"Added column '{col_name}' to 'uploads' table.", icon="🔧")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower(): raise 
    cursor.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id INTEGER, 
        code TEXT, issues TEXT, branch TEXT, area_manager TEXT, date TEXT, report_type TEXT, 
        FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE 
    )''')
    connection.commit()
    cursor.execute('''CREATE TABLE IF maps to BDRUH B16
    "B01": "Nuzhah - النزهة", # From CCTV sample, maps to NURUH B01
    "B32": "Alfayha branch - فرع الفيحاء",# From CCTV sample, maps to FAYJED B32
    "B23": "Al Sulimaniyah Al Hofuf - السلمانية الهفوف",# From CCTV sample, maps to SLAHS B23
    "B09": "Alaziziah - العزيزية",# From CCTV sample, maps to AZRUround(1)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=trend_data_primary['date'], y=trend_data_primary['daily_issues'], name='Daily Issues', marker_color='lightblue', hovertemplate="<b>%{x|%A, %b %d NOT EXISTS cctv_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT, upload_id INTEGER, 
        code TEXT, violation TEXT, shift TEXT, date_submitted TEXT, 
        branch_name TEXT, area_managerH B09
    "B28": "Almarwah branch - فرع المروة",# From CCTV sample, maps to MAJED B28
    "B14": "Alrabea}</b><br>Issues: %{y}<extra></extra>"))
            fig_trend.add_trace(go.Scatter(x=trend_data_primary['date'], y=trend_data_primary[ TEXT, report_type TEXT,
        FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE - الربيع",# From CCTV sample, maps to RBRUH B14
    "B11":f'{window_size}-Day MA'], name=f'{window_size}-Day Moving Avg.', mode='lines 
    )''')
    connection.commit()
    # st.toast("Database schema initialized/verified successfully.", icon "Alnargis - النرجس",# From CCTV sample, maps to NRRUH B11
    "+markers', line=dict(color='royalblue', width=2), marker=dict(size=5), hover="✅") # Can be noisy

try:
    initialize_database_schema(c, conn)
except Exception asB05": "Alrawabi - الروابي",# From CCTV sample, maps to RAWRUH B0template="<b>%{x|%A, %b %d}</b><br>Moving Avg: %{y e_schema:
    st.error(f"CRITICAL ERROR during database schema initialization: {e_schema5
    "B31": "Anas Ibn Malik - انس ابن مالك",# From CCTV sample,:.1f}<extra></extra>"))
            fig_trend.update_layout(title_text='Issues maps to ANRUH B31
    "B22": "Obhur Branch - فرع ابحر}")
    st.stop()

db_admin = {
    "abdalziz alsalem": b"$2 Trend (Primary Period - Based on Issue Dates)', xaxis_title='Date', yaxis_title='Number of Issues', template="plotly_white", hovermode="x unified", legend_title_text='Metric')
            figs_primary['",# From CCTV sample, maps to OBJED B22
    "B12": "Twuaiq - طويق",# From CCTV sample, maps to TWRUH B12
    "B3b$12$VzSUGELJcT7DaBWoGuJi8OLK7mvTrend'] = fig_trend 
            st.plotly_chart(figs_primary['Trend'], use_container4": "Al Urubah Branch - فرع العروبة",# From CCTV sample, maps to URURUH B3pLxRumSduEte8MDAPkOnuXMdnW",
    "omar salah": b"$2b$12$9VB3YRZRVe2RLxjO8FD3C.01_width=True)
    
    if len(df_primary_period) < 50 or (ecj1cEShMAZGYbFCE3JdGagfaWomy",
    "4
    "B07": "Wadi Laban Riyadh - وادي لبن الرياض", # From CCTVprimary_date_range and primary_date_range[0] == primary_date_range[1]):
        st.ahmed khaled": b"$2b$12$wUMnrBOqsXlMLvFGk Sample, maps to LBRUH B07
    "TW01": "Twesste"
}

LOGO_subheader("Detailed Records (Primary Period - Filtered)")
        df_display_primary = df_primary_period[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_manager',En.b.xsK7Cl49iBCoLQHaUnTaPixjE7ByHEG 'code']].copy()
        if 'date' in df_display_primary.columns and pd.api.PATH = "company_logo.png" 
# ... (check_login function - no changes) ...
def",
    "mohamed hattab": b"$2b$12$X5hWO55U9Y0RobP9Mk7t3eW3AK.6uNajas8SkuxgYtypes.is_datetime64_any_dtype(df_display_primary['date']): 
            df_display_primary['date'] = df_display_primary['date'].dt.strftime('%Y-%m-% check_login(): # Condensed
    if 'authenticated' not in st.session_state: st.session_state.authenticated8zEwgY/bYIqe"
}
view_only = ["mohamed emad",d') 
        st.dataframe(df_display_primary, use_container_width=True)
 = False; st.session_state.user_name = None; st.session_state.user_role = None
    if not st.session_state.authenticated:
        col1_lgn, col2 "mohamed houider", "sujan podel", "ali ismail", "islam mostafa"]
category_file_types = {
    'operation-training': ['opening', 'closing', 'handover', '    
    st.subheader("Top Issues (Primary Period - Filtered)")
    if 'issues' in df_primary_period.columns and not df_primary_period['issues'].isnull().all():
        top_issues_primary_lgn = st.columns([2,6]);
        with col1_lgn:
            try: st.image(LOGO_PATH, width=120) 
            except Exception: pass 
        withstore arranging', 'tempreature of heaters', 'defrost', 'clean AC'],
    'CCTV': ['issues', 'submission time'], 
    'complaints': ['performance', 'اغلاق الشكاوي'], 
 = df_primary_period['issues'].astype(str).value_counts().head(20).rename_axis('Issue Description').reset_index(name='Frequency')
        if not top_issues_primary.empty col2_lgn: st.title("📊 Login - Dashboard")
        st.subheader("Please log in to continue")
        with st.form("login_form"):
            username = st.text_input("Full Name:", key="auth    'missing': ['performance'],
    'visits': [], 
    'meal training': ['performance', 'missing types']
}
all_categories = list(category_file_types.keys())

BRANCH_CODE_MAP = {
    "NURUH B01": "Nuzhah - النزهة", ": st.dataframe(top_issues_primary, use_container_width=True)

if enable_comparison_val and comparison_date_range_1 and comparison_date_range_2: # Use comparison_date__username_login_widget").strip().lower(); password = st.text_input("Password:", type="password", key="KHRUH B02": "Alkaleej - الخليج", "GHRUH B03": "Gurnatah - غرناطة",
    "NSRUH B04": "Alnaseem Riyadh-range_1/2 from enable_comparison block
    st.markdown("---"); st.header("📊 Period Comparison Resultsauth_password_login_widget") 
            if st.form_submit_button("Login"):
                if username in db_admin and bcrypt.checkpw(password.encode(), db_admin[username]): st. النسيم الرياض", "RAWRUH B05": "Alrawabi - الروابي", "DARUH B06 (Based on Issue Dates)")
    df_comp1 = pd.DataFrame(columns=df_temp_filtered.columns); df_comp2 = pd.DataFrame(columns=df_temp_filtered.columns)
    session_state.authenticated = True; st.session_state.user_name = username; st.session_state.user_role = 'admin'; st.rerun()
                elif username in view_only and password: st.session": "Aldaraiah - الدرعية",
    "LBRUH B07": "Wadi Laban Riyadh - وادي لبن الرياض", "SWRUH B08": "Alsweedi - السويديstart_c1_disp, end_c1_disp, start_c2_disp, end_c_state.authenticated = True; st.session_state.user_name = username; st.session_state.user_role = 'view_only'; st.rerun()
                elif username in view_only and", "AZRUH B09": "Alaziziah - العزيزية",
    "SHRUH B10": "Alshifa - الشفاء", "NRRUH B11": "Alnargis - النرج2_disp = "N/A", "N/A", "N/A", "N/A"

    if comparison_date_range_1 and len(comparison_date_range_1) == 2:
        start_c1_dt_obj, end_c1_dt_obj = comparison_date not password: st.error("Password required for view-only.")
                elif username or password: st.error("Invalidس", "TWRUH B12": "Twuaiq - طويق",
    "AQRUH B13": "Al Aqiq - العقيق", "RBRUH B14": "Al_range_1[0], comparison_date_range_1[1]
        if 'date' in df_temp_filtered.columns and pd.api.types.is_datetime64_any_dtype( credentials.")
                else: st.info("Enter credentials.")
        return False
    return True
if not check_loginrabea - الربيع", "NDRUH B15": "Nad Al Hamar", 
    df_temp_filtered['date']): 
            df_comp1 = df_temp_filtered[(df_temp_filtered['date'].dt.date >= start_c1_dt_obj) & (df_temp(): st.stop()

# ... (Main title and sidebar login status - no changes) ...
col1_main"BDRUH B16": "Albadeah - البديعة", "QRRUH B17": "Alqairawan - القيروان", "TKRUH B18": "Takhasussi Riyadh - التخصص_filtered['date'].dt.date <= end_c1_dt_obj)].copy()
        start__title, col2_main_title = st.columns([2, 6]); # Main dashboard title
with col1_main_title:
    try: st.image(LOGO_PATH, width=120ي الرياض",
    "MURUH B19": "Alremal - الرمال", "KRRc1_disp, end_c1_disp = start_c1_dt_obj.strftime('%Y-%m-%d'), end_c1_dt_obj.strftime('%Y-%m-%d')
    )
    except Exception: pass
with col2_main_title: st.title("📊 Classic Dashboard for Performance")
user_name_display = st.session_state.get('user_name', "N/UH B21": "Alkharj - الخرج", "OBJED B22": "Obhur Branch - فرع ابحر",
    "SLAHS B23": "Al Sulimaniyah Al Hofuf -
    if comparison_date_range_2 and len(comparison_date_range_2) == 2A").title(); user_role_display = st.session_state.get('user_role', "N السلمانية الهفوف", "SFJED B24": "Alsafa Jeddah - الصفا جدة",:
        start_c2_dt_obj, end_c2_dt_obj = comparison_date_range/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({
    "RWAHS B25": "Al Rawdha Al Hofuf - الروضة الهف_2[0], comparison_date_range_2[1]
        if 'date' in df_user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main_widget"):وف", "HAJED B26": "Al Hamadaniyyah  - الحمدانية",
    "temp_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_ st.session_state.authenticated = False; st.session_state.user_name = None; st.session_stateSARUH B27": "Alsaadah branch - فرع السعادة", "MAJED B28": "Altemp_filtered['date']): 
            df_comp2 = df_temp_filtered[(df_temp_.user_role = None; st.rerun()
is_admin = st.session_state.getmarwah branch - فرع المروة",
    "EVENT B29": "Event Location B29filtered['date'].dt.date >= start_c2_dt_obj) & (df_temp_filtered('user_role') == 'admin'; current_user = st.session_state.get('user_name", "QADRUH B30": "Al Qadisiyyah branch - فرع القادسية",
    "['date'].dt.date <= end_c2_dt_obj)].copy()
        start_c2_disp, end_c2_disp = start_c2_dt_obj.strftime('%Y-%m', 'Unknown User')

# ... (generate_pdf function - no changes) ...
def generate_pdf(html, fname='report.pdf', wk_path=None): # Condensed
    if not wk_path orANRUH B31": "Anas Ibn Malik - انس ابن مالك", "FAYJED B-%d'), end_c2_dt_obj.strftime('%Y-%m-%d')

    if not df_comp1.empty or not df_comp2.empty:
        if comparison_date_range_ wk_path == "not found": st.error("wkhtmltopdf path not set."); return None
    32": "Alfayha branch - فرع الفيحاء",
    "HIRJED B331: st.subheader(f"Period 1: {start_c1_disp} to {end_c1try:
        import pdfkit; config = pdfkit.configuration(wkhtmltopdf=wk_path); options": "Hira Jeddah", "URURUH B34": "Al Urubah Branch - فرع العروبة",
    "LB01": "Lubda - لبدة", "LB02": "Alkhaleej Branch_disp} (Total: {len(df_comp1)} issues)")
        if comparison_date_range = {'enable-local-file-access': None, 'images': None, 'encoding': "UTF-8 LB02", 
    "QB01": "Shawarma Garatis As Suwaidi - شاورما قراطيس السويدي",
    "QB02": "Shawarma Garatis Alnargis_2: st.subheader(f"Period 2: {start_c2_disp} to {end",'load-error-handling': 'ignore','load-media-error-handling': 'ignore'}
        pdf B02 -  B02 شاورما قراطيس النرجس",
    "TW01_c2_disp} (Total: {len(df_comp2)} issues)")
        
        colkit.from_string(html, fname, configuration=config, options=options);
        with open(fname, 'rb') as f: return f.read()
    except Exception as e: st.error(f"PDF error": "Twesste",
    "B01": "Nuzhah - النزهة", "B02":_comp1_disp_metrics, col_comp2_disp_metrics = st.columns(2)
        with col_comp1_disp_metrics:
            st.metric(label=f"Total Issues (P: {e}"); return None

st.sidebar.header("🔍 Filters & Options")

if is_admin:
    st "Alkaleej - الخليج", "B03": "Gurnatah - غرناطة", "B1)", value=len(df_comp1))
            if not df_comp1.empty: st..sidebar.subheader("Admin Controls")
    st.sidebar.markdown("Set parameters, select Excel, specify import date range,04": "Alnaseem Riyadh- النسيم الرياض",
    "B05": "Alrawabi - الdataframe(df_comp1['issues'].value_counts().nlargest(5).reset_index().rename( then upload.")
    selected_category_val = st.sidebar.selectbox("Category for upload", options=allروابي", "B06": "Aldaraiah - الدرعية", "B07": "Wadi Laban Riyadhcolumns={'index':'Issue', 'issues':'Count'}), height=220, use_container_width=True_categories, key="admin_category_select_widget")
    valid_file_types = category_file_types - وادي لبن الرياض",
    "B08": "Alsweedi - السويدي", ")
        with col_comp2_disp_metrics:
            delta_val = len(df_comp.get(selected_category_val, [])
    selected_file_type_val = st.sidebar.B09": "Alaziziah - العزيزية", "B10": "Alshifa - الشفاء",
2) - len(df_comp1); st.metric(label=f"Total Issues (P2)",selectbox("File type for upload", options=valid_file_types, key="admin_file_type_select    "B11": "Alnargis - النرجس", "B12": "Twu value=len(df_comp2), delta=f"{delta_val:+}" if delta_val !=0_widget", disabled=(not valid_file_types), help="Options change based on category.")
    st.sidebar.markdownaiq - طويق", "B14": "Alrabea - الربيع",
    "B1 else None)
            if not df_comp2.empty: st.dataframe(df_comp2['issues("**Filter Excel Data by Date Range for this Import:**")
    import_from_date_widget_val = st.sidebar6": "Albadeah - البديعة", "B17": "Alqairawan - القير'].value_counts().nlargest(5).reset_index().rename(columns={'index':'Issue', 'issues':'Count'}), height=220, use_container_width=True)
        
        if not df.date_input("Import Data From Date:", value=date.today() - timedelta(days=7), keyوان", "B18": "Takhasussi Riyadh - التخصصي الرياض",
    "B19_comp1.empty or not df_comp2.empty:
            df_comp1_labeled = df="import_from_date_upload_widget")
    import_to_date_widget_val = st": "Alremal - الرمال", "B21": "Alkharj - الخرج", "B22_comp1.copy(); df_comp2_labeled = df_comp2.copy()
            if comparison.sidebar.date_input("Import Data To Date:", value=date.today(), key="import_to_": "Obhur Branch - فرع ابحر",
    "B23": "Al Sulimaniyah Al_date_range_1: df_comp1_labeled['period_label'] = f"P1: {comparison_date_upload_widget")
    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader_widget")
    upload_btn = st.sidebar.button(" Hofuf - السلمانية الهفوف", "B24": "Alsafa Jeddah - الصفا جدة",date_range_1[0]:%d%b}-{comparison_date_range_1[1]:%dUpload Data", key="upload_data_button_widget")

    if upload_btn: 
        final
    "B25": "Al Rawdha Al Hofuf - الروضة الهفوف", "%b}"
            if comparison_date_range_2: df_comp2_labeled['period_label_category = selected_category_val; final_file_type = selected_file_type_val
        B26": "Al Hamadaniyyah  - الحمدانية",
    "B27": "Al'] = f"P2: {comparison_date_range_2[0]:%d%b}-{comparisonimp_from_dt = import_from_date_widget_val; imp_to_dt = import_saadah branch - فرع السعادة", "B28": "Almarwah branch - فرع المرو_date_range_2[1]:%d%b}"
            dfs_to_concat = []; 
            ifto_date_widget_val 
        requires_file_type = bool(category_file_types.ة",
    "B30": "Al Qadisiyyah branch - فرع القادسية", "B31 not df_comp1_labeled.empty and 'period_label' in df_comp1_labeled.columns : dfs_get(final_category, []))

        if requires_file_type and not final_file_type: st.sidebar": "Anas Ibn Malik - انس ابن مالك",
    "B32": "Alfayha branchto_concat.append(df_comp1_labeled)
            if not df_comp2_labeled..warning(f"Please select a file type for '{final_category}'.")
        elif not up: st - فرع الفيحاء", "B34": "Al Urubah Branch - فرع العروبة"empty and 'period_label' in df_comp2_labeled.columns : dfs_to_concat.append
    # ** COMPLETE THIS MAP WITH ALL YOUR CODES (UPPERCASE) AND FULL NAMES **
}

LOGO_PATH.sidebar.error("Please select an Excel file.")
        elif not imp_from_dt or not imp_(df_comp2_labeled)
            if dfs_to_concat:
                df_combined_branch = "company_logo.png" 

def check_login():
    if 'authenticated' not in st.session_to_dt: st.sidebar.error("Please select both Import From and To Dates.")
        elif imp_ = pd.concat(dfs_to_concat)
                if not df_combined_branch.empty:
state:
        st.session_state.authenticated = False; st.session_state.user_name =from_dt > imp_to_dt: st.sidebar.error("Import From Date cannot be after Import To                    branch_comp_data = df_combined_branch.groupby(['branch', 'period_label']).size(). None; st.session_state.user_role = None
    if not st.session_state.authenticated Date.")
        else: 
            if not requires_file_type: final_file_type = None 
            excel_data_bytes = up.getvalue(); ts_now = datetime.now()
            upload_submissionreset_index(name='count')
                    if not branch_comp_data.empty:
                        fig_:
        col1_lgn, col2_lgn = st.columns([2,6]);
_date_for_uploads_table = imp_from_dt 
            
            upload_id_forbranch_comp = px.bar(branch_comp_data, x='branch', y='count', color='period_label', barmode='group', title='Issues by Branch (Comparison)')
                        st.plotly_chart(fig        with col1_lgn:
            try: st.image(LOGO_PATH, width=12_op = None 
            try:
                with conn: 
                    c.execute('SELECT id FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                              (up.name_branch_comp, use_container_width=True)
            
            st.markdown("#### Period-0) 
            except Exception: pass 
        with col2_lgn: st.title("📊 Login - Dashboard")
        st.subheader("Please log in to continue")
        with st.form("login, current_user, final_file_type, final_category, upload_submission_date_for_uploads_table.isoformat()))
                    existing_upload = c.fetchone()
                    if existing_upload: Level Trend (Average Daily Issues)")
            period_summary_data = []
            if comparison_date_range_1 and not df_comp1.empty and 'date' in df_comp1.columns and pd._form"):
            username = st.text_input("Full Name:", key="auth_username_login_widget").strip().lower() 
            password = st.text_input("Password:", type="password", key
                        st.sidebar.warning(f"DUPLICATE: Upload batch (ID: {existing_upload[0api.types.is_datetime64_any_dtype(df_comp1['date']): 
                avg_issues_p1 = df_comp1.groupby(df_comp1['date'].dt.date="auth_password_login_widget") 
            submitted = st.form_submit_button("Login")]}) already exists. No action taken.")
                    else:
                        st.sidebar.info(f"Attempting to process new).size().mean(); period_summary_data.append({'Period': f"Period 1 ({comparison_date_range_1[0]:%b %d} - {comparison_date_range_1[1]:%b
            if submitted:
                if username in db_admin and bcrypt.checkpw(password.encode(), db_admin[username]):
                    st.session_state.authenticated = True; st.session_state.user upload: {up.name}")
                        df_excel_full = pd.read_excel(io.Bytes %d})", 'StartDate': pd.to_datetime(comparison_date_range_1[0]), 'AverageDailyIssues': round(avg_issues_p1, 2)})
            if comparison_date_range_name = username; st.session_state.user_role = 'admin'; st.rerun()
                elif username in view_only and password: 
                    st.session_state.authenticated = True; stIO(excel_data_bytes))
                        df_excel_full.columns = [col.strip().lower() for col in df_excel_full.columns]
                        st.sidebar.text("DEBUG: Excel columns_2 and not df_comp2.empty and 'date' in df_comp2.columns and pd.api.types.is_datetime64_any_dtype(df_comp2['date']): 
                .session_state.user_name = username; st.session_state.user_role = 'view_ found: " + str(list(df_excel_full.columns)))

                        df_to_import = pd.DataFrame()
                        issues_prepared_count = 0

                        if final_category == 'CCTV':avg_issues_p2 = df_comp2.groupby(df_comp2['date'].dt.dateonly'; st.rerun()
                elif username in view_only and not password: st.error("Password cannot be empty for view-only users.")
                elif username or password: st.error("Invalid username or password.")
                else: st.info("Please enter your credentials.")
        return False
    return True
if
                            st.sidebar.info("--- CCTV Processing Started ---")
                            cctv_req_cols =).size().mean(); period_summary_data.append({'Period': f"Period 2 ({comparison_date_range_2[0]:%b %d} - {comparison_date_range_2[1]: not check_login(): st.stop()

col1_main_title, col2_main_title = st.columns ['code', 'choose the violation - اختر المخالفه', 'date submitted', 'area manager']
                            missing_cctv_cols = [col for col in cctv_req_cols if col not in df_excel%b %d})", 'StartDate': pd.to_datetime(comparison_date_range_2[0([2, 6]) 
with col1_main_title:
    try: st.image(LOGO_PATH, width=120)
    except FileNotFoundError: st.error(f"Logo image_full.columns]
                            if missing_cctv_cols: raise ValueError(f"CCTV Excel]), 'AverageDailyIssues': round(avg_issues_p2, 2)})
            
            if len(period_summary_data) >= 1:
                df_period_trend = pd.DataFrame(period not found: {LOGO_PATH}") 
    except Exception as e: st.error(f"Error loading logo: {e}")
with col2_main_title: st.title("📊 Classic Dashboard for Performance") missing: {', '.join(missing_cctv_cols)}.")
                            
                            st.sidebar.info(f"Required CCTV columns found: {cctv_req_cols}")
                            if 'date submitted'_summary_data).sort_values('StartDate')
                if len(df_period_trend) == 1: fig_period_level_trend = px.bar(df_period_trend, x='Period', y='AverageDailyIssues', text='AverageDailyIssues', title='Avg Daily Issues by Period'); fig_period_

user_name_display = st.session_state.get('user_name', "N/A").title() in df_excel_full.columns: st.sidebar.info(f"Raw 'date submitted' head:\n{df_excel_full['date submitted'].head().to_string()}")
                            else: st.sidebar.error("'level_trend.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                
user_role_display = st.session_state.get('user_role', "N/A")
st.sidebar.success(f"Logged in as: {user_name_display} ({user_role_display})")
if st.sidebar.button("Logout", key="logout_button_main_widget"):date submitted' column NOT FOUND."); raise ValueError("'date submitted' column not found in CCTV Excel.")

                            df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full['date submitted'], errorselse: fig_period_level_trend = px.line(df_period_trend, x='Period', y='AverageDailyIssues', markers=True, text='AverageDailyIssues', title='Trend of Avg Daily Issues Across
    st.session_state.authenticated = False; st.session_state.user_name = None; st.session_state.user_role = None; st.rerun()
is_admin = st.session_state.get('user_role') == 'admin'
current_user = st.session_state.get='coerce', dayfirst=False) 
                            st.sidebar.info(f"Parsed 'parsed_date' head (NaT if failed):\n{df_excel_full['parsed_date'].head().to_string Periods'); fig_period_level_trend.update_traces(texttemplate='%{text:.2f}', textposition='top center')
                fig_period_level_trend.update_layout(xaxis_title="Comparison Period", yaxis_title="Avg. Daily Issues", template="plotly_white"); st.plotly_chart(('user_name', 'Unknown User')

def generate_pdf(html, fname='report.pdf', wk()}")
                            st.sidebar.info(f"NaNs in parsed_date after to_datetime: {df_excel_full['parsed_date'].isnull().sum()}")
                            
                            original_len = len(df_excel_full); df_excel_full.dropna(subset=['parsed_date'], inplace=True)
                            if len(dffig_period_level_trend, use_container_width=True)
            else: st.info("_path=None):
    if not wk_path or wk_path == "not found": st.error("wkhtmltopdf path not set."); return None
    try:
        import pdfkit; config = pdfkit.configuration(wkhtmltopdf=wk_path)
        options = {'enable-local-file-access':_excel_full) < original_len: st.sidebar.warning(f"{original_len - len(df_excel_full)} CCTV rows dropped (invalid 'date submitted').")
                            if df_excel_fullNot enough data for period-level trend (ensure selected periods have data with valid dates).")
    else: st.warning("No data found for either comparison period with the current general filters.")

st.sidebar.subheader("Downloads")
if 'df_primary_period' in locals() and not df_primary_period.empty:
    csv_data_primary = df_primary_period.to_csv(index=False).encode('utf-8 None, 'images': None, 'encoding': "UTF-8",'load-error-handling': 'ignore','load-media-error-handling': 'ignore'}
        pdfkit.from_string(html, fname,.empty: raise ValueError("No valid CCTV data rows after date parsing.")
                            st.sidebar.info(f"Rows after NaT drop: {len(df_excel_full)}")
                            st.sidebar.info(')
    st.sidebar.download_button("Download Primary Period Data as CSV", csv_data_primary, "primary_period_issues.csv", "text/csv", key="download_csv_primary_widget") configuration=config, options=options);
        with open(fname, 'rb') as f: return f.read()
    except Exception as e: st.error(f"PDF error: {e}"); return None

f"Importing from: {imp_from_dt:%Y-%m-%d} to {imp_to
    if st.sidebar.button("Prepare Visuals PDF (Primary Period)", key="prep_visuals_pdf_primary_widget"):
        if not wk_path or wk_path == "not found": st.sidebar.errorst.sidebar.header("🔍 Filters & Options")

if is_admin:
    st.sidebar.subheader("Admin Controls")
    st.sidebar.markdown("Set parameters, select Excel, specify import date range, then upload.")_dt:%Y-%m-%d}")
                                
                            df_to_import = df_excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()
                            st.sidebar.info("wkhtmltopdf path not set.")
        elif 'figs_primary' not in locals() or not figs_primary or not any(figs_primary.values()): st.sidebar.warning("No visuals for primary period.")
        
    selected_category_val = st.sidebar.selectbox("Category for upload", options=all_categories, key="admin_category_select_widget")
    valid_file_types = category_file_types.get(selected_category_val, [])
    selected_file_type_val = st.sidebar.selectbox(f"Rows in df_to_import (after date range filter): {len(df_to_importelse:
            html_content = "<html><head><meta charset='utf-8'><title>Visuals Report (Primary)</title><style>body{font-family:sans-serif;} h1,h2{text-align:center;} img{display:block;margin-left:auto;margin-right:auto;("File type for upload", options=valid_file_types, key="admin_file_type_select_widget", disabled=(not valid_file_types), help="Options change based on category.")
    st.sidebar)}")
                        
                        else: # Standard Processing
                            st.sidebar.info("--- Standard Processing Started ---")
                            required_cols = ['code', 'issues', 'branch', 'area manager', 'date']
                            missing_cols = [col for col in required_cols if col not in df_excel_full.columns]
                            if missing_max-width:95%;height:auto;border:1px solid #ccc;padding:5px;margin-bottom:20px;} @media print {* {-webkit-print-color-adjust:exact !.markdown("**Filter Excel Data by Date Range for this Import:**")
    import_from_date_widget_val = st.sidebar.date_input("Import Data From Date:", value=date.today() - timedelta(cols: raise ValueError(f"Standard Excel missing: {', '.join(missing_cols)}.")
                            stimportant; color-adjust:exact !important; print-color-adjust:exact !important;} body { background-color:white !important;}}</style></head><body>"
            html_content += f"<h1>Visualdays=7), key="import_from_date_upload_widget")
    import_to_date_widget_val = st.sidebar.date_input("Import Data To Date:", value=date.today(), key.sidebar.info(f"Required Standard columns found: {required_cols}")
                            if 'date' in df_excel_full.columns: st.sidebar.info(f"Raw 'date' head:\n{df_excel_fulls Report (Primary: {primary_date_range[0]:%Y-%m-%d} to {primary_date_range[1]:%Y-%m-%d})</h1>"; chart_titles_in_order =="import_to_date_upload_widget")
    up = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"], key="excel_uploader_widget")
    upload_btn = st['date'].head().to_string()}")
                            else: st.sidebar.error("'date' column NOT FOUND."); raise ValueError("'date' column not found in Standard Excel.")
                            
                            df_excel_full['parsed_date'] ["Branch", "Area Manager", "Report Type", "Category", "Trend"]
            for title in chart_titles_in_order:
                if figs_primary.get(title): 
                    fig_obj = figs_.sidebar.button("Upload Data", key="upload_data_button_widget")

    if upload_btn: 
        final_category = selected_category_val; final_file_type = selected_file_ = pd.to_datetime(df_excel_full['date'], dayfirst=True, errors='coerce')
                            st.sidebar.info(f"Parsed 'parsed_date' head (NaT if failed):\n{df_excel_full['parsed_date'].head().to_string()}")
                            st.sidebar.info(f"primary[title]; 
                    try: img_bytes = fig_obj.to_image(format='png', engine='kaleido', scale=2); b64_img = base64.b64encodetype_val
        imp_from_dt = import_from_date_widget_val; imp_to_dt = import_to_date_widget_val 
        requires_file_type = bool(category_file_types.get(final_category, []))

        if requires_file_type and not finalNaNs in parsed_date after to_datetime: {df_excel_full['parsed_date'].isnull().(img_bytes).decode(); html_content += f"<h2>{title}</h2><img src='data:image/png;base64,{b64_img}' alt='{title}'/>"
                    except Exception as e_file_type: st.sidebar.warning(f"Please select a file type for '{final_category}'.")
        elif not up: st.sidebar.error("Please select an Excel file.")
        elif not impsum()}")

                            original_len = len(df_excel_full); df_excel_full.dropna(subset=['parsed_date'], inplace=True)
                            if len(df_excel_full) < original_len: st.sidebar.warning(f"{original_len - len(df_excel_full)} rows dropped (invalid date_fig: st.sidebar.warning(f"Fig '{title}' to image error: {e_fig}.")
            html_content += "</body></html>"; pdf_bytes = generate_pdf(html_content, fname='_from_dt or not imp_to_dt: st.sidebar.error("Please select both Import From and To Dates.")
        elif imp_from_dt > imp_to_dt: st.sidebar.error("Import From Date cannot be after Import To Date.")
        else: 
            if not requires_file_type).")
                            if df_excel_full.empty: raise ValueError("No valid data rows in Excel after date parsing.")
                            st.sidebar.info(f"Rows after NaT drop: {len(df_excel_fullvisuals_report_primary.pdf', wk_path=wk_path)
            if pdf_bytes: st.session_state.pdf_visuals_primary_data = pdf_bytes; st.sidebar.success("Visuals PDF (Primary) ready.")
            else:
                if 'pdf_visuals_primary_: final_file_type = None 
            excel_data_bytes = up.getvalue(); ts_now = datetime)}")
                            st.sidebar.info(f"Importing from: {imp_from_dt:%Y-%m-%d} to {imp_to_dt:%Y-%m-%d}")

                            df_to_import = dfdata' in st.session_state: del st.session_state.pdf_visuals_primary_data
    if 'pdf_visuals_primary_data' in st.session_state and st.session_.now()
            upload_submission_date_for_uploads_table = imp_from_dt 
            
            upload_id_for_op = None 
            try:
                with conn: 
                    c._excel_full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copystate.pdf_visuals_primary_data:
        st.sidebar.download_button(label="Download Visuals PDF (Primary) Now", data=st.session_state.pdf_visuals_primary_dataexecute('SELECT id FROM uploads WHERE filename=? AND uploader=? AND file_type IS ? AND category=? AND submission_date=?',
                              (up.name, current_user, final_file_type, final_category, upload_submission_date_for_uploads_table.isoformat()))
                    existing_upload = c.fetchone()
                    if existing()
                            st.sidebar.info(f"Rows in df_to_import (after date range filter): {len(df_to_import)}")

                        # --- Common Insertion Logic ---
                        if not df_to_, file_name="visuals_report_primary.pdf", mime="application/pdf", key="action_dl_visuals_pdf_primary_widget")
    if st.sidebar.button("Prepare Full Dashboard PDF (_upload: 
                        st.sidebar.warning(f"DUPLICATE: Upload batch (ID: {existingimport.empty:
                            st.sidebar.info(f"DEBUG: Preparing to insert {len(df_to_import)} rows into DB.")
                            c.execute('INSERT INTO uploads (filename, uploader, timestamp, file_type, categoryPrimary Period)", key="prep_dashboard_pdf_primary_widget"):
        if not wk_path or wk_upload[0]}) already exists. No action taken.")
                    else:
                        st.sidebar.info(f, submission_date, file) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                      (up.name, current_user_path == "not found": st.sidebar.error("wkhtmltopdf path not set.")
        else:
"Attempting to process new upload: {up.name}")
                        df_excel_full = pd.read_excel(io.BytesIO(excel_data_bytes))
                        df_excel_full.columns = [col, ts_now.isoformat(), final_file_type, final_category, upload_submission_date_for            html_full = "<head><meta charset='utf-8'><style>body{font-family:sans-serif;} table{border-collapse:collapse;width:100%;} th,td{border:.strip().lower() for col in df_excel_full.columns]
                        st.sidebar.text("_uploads_table.isoformat(), sqlite3.Binary(excel_data_bytes)))
                            upload_id_for_op = c.lastrowid 
                            st.sidebar.info(f"DEBUG: Inserted into 'uploads1px solid #ddd;padding:8px;text-align:left;} th{background-color:#f2f2f2;}</style></head>"
            html_full += f"<h1>Dashboard Report (Primary: {primary_date_range[0]:%Y-%m-%d} to {primary_date_rangeDEBUG: Excel columns found: " + str(list(df_excel_full.columns)))

                        df_to_import = pd.DataFrame()
                        issues_prepared_count = 0
                        cctv_issues_to_insert_tuples = []
                        standard_issues_to_insert_tuples = []


                        if final_' table, ID: {upload_id_for_op}")

                            if final_category == 'CCTV':
                               [1]:%Y-%m-%d})</h1>"
            df_pdf_view = df_primary_period[['date', 'branch', 'report_type', 'upload_category', 'issues', 'area_managercategory == 'CCTV':
                            st.sidebar.info("DEBUG: Processing as CCTV category.")
                            c cctv_issues_to_insert_tuples = []
                                for _, row_data in df_to_import.iterrows():
                                    violation = row_data['choose the violation - اختر المخالفه']
                                    shift =', 'code']].copy()
            if 'date' in df_pdf_view.columns and pd.apictv_req_cols = ['code', 'choose the violation - اختر المخالفه', 'date submitted', 'branch', 'area manager']
                            missing_cctv_cols = [col for col in cct row_data.get('choose the shift - اختر الشفت', None) 
                                    branch_code_excel = str(row_data['code']).strip().upper()
                                    branch_name_from_map =.types.is_datetime64_any_dtype(df_pdf_view['date']): df_pdf_view['date'] = df_pdf_view['date'].dt.strftime('%Y-%m-%d')
            html_full += df_pdf_view.to_html(index=False, classes="dataframe",v_req_cols if col not in df_excel_full.columns]
                            if missing_cctv_cols: raise ValueError(f"CCTV Excel missing required columns: {', '.join(missing_cct BRANCH_CODE_MAP.get(branch_code_excel)
                                    if branch_name_from_map: branch_name_final = branch_name_from_map.strip()
                                    else:  border=0)
            pdf_full_bytes = generate_pdf(html_full, fname='dashboard_report_primary.pdf', wk_path=wk_path)
            if pdf_full_bytes: stv_cols)}")
                            
                            st.sidebar.text("DEBUG: CCTV required columns found.")
                            df_excel_full['parsed_date'] = pd.to_datetime(df_excel_full['date submitted'], errors='coerce', day
                                        branch_name_final = str(row_data.get('branch', branch_code_excel)).strip()
                                        st.sidebar.warning(f"CCTV Code '{branch_code_excel}' not.session_state.pdf_dashboard_primary_data = pdf_full_bytes; st.sidebar.success("Dashboard PDF (Primary) ready.")
            else:
                if 'pdf_dashboard_primary_data' in st.session_state: del st.session_state.pdf_dashboard_primary_data
    iffirst=False)
                            st.sidebar.text(f"DEBUG: CCTV Parsed 'parsed_date' head: {df_excel_full['parsed_date'].head().to_list()}")
                            st.sidebar.text(f in BRANCH_CODE_MAP. Using '{branch_name_final}'.")
                                    cctv_issues_to_insert_tuples.append((upload_id_for_op, branch_code_excel, violation, shift, row 'pdf_dashboard_primary_data' in st.session_state and st.session_state.pdf_dashboard_primary_data:
        st.sidebar.download_button(label="Download Dashboard PDF (Primary)"DEBUG: NaNs in parsed_date after to_datetime: {df_excel_full['parsed_date'].isnull().sum()}")
                            
                            original_len = len(df_excel_full); df_excel_full._data['parsed_date'].strftime('%Y-%m-%d'), branch_name_final, row_data['area manager'], final_file_type))
                                if cctv_issues_to_insert_tuples:
 Now", data=st.session_state.pdf_dashboard_primary_data, file_name="dashboard_report_primary.pdf", mime="application/pdf", key="action_dl_dashboard_pdf_primary_dropna(subset=['parsed_date'], inplace=True)
                            if len(df_excel_full) < original_len: st.sidebar.warning(f"{original_len - len(df_excel_full)}                                    c.executemany('''INSERT INTO cctv_issues (upload_id, code, violation, shift, date_submitted, branch_name, area_manager, report_type) 
                                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', cctv_issues_to_insert_tuples)
                               widget")
else: st.sidebar.info("No primary period data to download.")

if enable_comparison_ CCTV rows dropped (invalid 'date submitted').")
                            if df_excel_full.empty: raise ValueError("No valid CCTV data rows after date parsing.")
                            
                            st.sidebar.text(f"DEBUG: Rows after Na     issues_prepared_count = len(cctv_issues_to_insert_tuples)
                                    val and comparison_date_range_1 and comparison_date_range_2:
    df_comp1_exists = 'df_comp1' in locals() and not df_comp1.empty; df_compT drop: {len(df_excel_full)}")
                            df_to_import = df_excel_st.sidebar.info(f"DEBUG: Executed insert for {issues_prepared_count} CCTV issues.")
                            else: # Standard issues
                                standard_issues_to_insert_tuples = []
                                for _, row_data in df_2_exists = 'df_comp2' in locals() and not df_comp2.empty
    start_c1_str = comparison_date_range_1[0].strftime('%Y%m%d')full[(df_excel_full['parsed_date'].dt.date >= imp_from_dt) & (df_excel_full['parsed_date'].dt.date <= imp_to_dt)].copy()
                            to_import.iterrows():
                                    standard_issues_to_insert_tuples.append((upload_id_for_op, row_data['code'], row_data['issues'], str(row_data['branch']).strip if df_comp1_exists and comparison_date_range_1 and len(comparison_date_range_1)==2 else "P1"
    end_c1_str = comparison_date_range_1[1].strftime('%Y%m%d') if df_comp1_exists and comparison_date_rangest.sidebar.text(f"DEBUG: Rows for import (CCTV): {len(df_to_import)}")

                            if not df_to_import.empty:
                                for _, row in df_to_import.iterrows():
                                    violation = str(row['choose the violation - اختر المخالفه'])
                                    shift(), row_data['area manager'], row_data['parsed_date'].strftime('%Y-%m-%d'), final_file_type))
                                if standard_issues_to_insert_tuples:
                                    c.exec_1 and len(comparison_date_range_1)==2 else ""
    start_c2_str = comparison_date_range_2[0].strftime('%Y%m%d') if df_comp2 = str(row.get('choose the shift - اختر الشفت', '')) 
                                    branch_code_excelutemany('''INSERT INTO issues (upload_id, code, issues, branch, area_manager, date, report_type) 
                                                     VALUES (?, ?, ?, ?, ?, ?, ?)''', standard_issues_to_insert_tuples_exists and comparison_date_range_2 and len(comparison_date_range_2)==2 else " = str(row['code']).strip().upper()
                                    excel_branch_name = str(row['branch']).strip()
                                    branch_name_final = BRANCH_CODE_MAP.get(branch_code_excel, excel_branch_name)
                                    cctv_issues_to_insert_tuples.append)
                                    issues_prepared_count = len(standard_issues_to_insert_tuples)
                               P2"
    end_c2_str = comparison_date_range_2[1].strftime('%Y%m%d') if df_comp2_exists and comparison_date_range_2 and len(comparison_date_range_2)==2 else ""
    if df_comp1_exists: st.sidebar((branch_code_excel, violation, shift if shift else None, row['parsed_date'].strftime('%Y-%m-%d'), branch_name_final, str(row['area manager']), final_file_type))
                        else     st.sidebar.info(f"DEBUG: Executed insert for {issues_prepared_count} Standard issues.")
                            
                            # conn.commit() # Implicitly committed by 'with conn:' if no exceptions
                            st.sidebar.success(f"Imported {issues_prepared_count} issues from '{up.name}'.")
                            st.rer.download_button(f"CSV (Comp P1: {comparison_date_range_1[0]:: 
                            st.sidebar.info("DEBUG: Processing as Standard category.")
                            required_cols = ['code',un()
                        else: # df_to_import was empty
                             st.sidebar.info(f"No issues%b%d}-{comparison_date_range_1[1]:%b%d})", df_comp1.to_csv(index=False).encode('utf-8'), f"comp_p1_{start_c1_str}-{end_c1_str}.csv", "text/csv", key="dl_csv_comp 'issues', 'branch', 'area manager', 'date']
                            missing_cols = [col for col in found within the import date range in '{up.name}'. No data imported, and no 'uploads' entry created for1_widget")
    if df_comp2_exists: st.sidebar.download_button(f"CSV (Comp P2: {comparison_date_range_2[0]:%b%d}-{comparison_date_range required_cols if col not in df_excel_full.columns]
                            if missing_cols: raise ValueError(f"Standard Excel missing: {', '.join(missing_cols)}.")
                            
                            df_excel_full[' this attempt.")
            
            except ValueError as ve: 
                 st.sidebar.error(f"Data_2[1]:%b%d})", df_comp2.to_csv(index=False).encode('utf-8'), f"comp_p2_{start_c2_str}-{end_c2parsed_date'] = pd.to_datetime(df_excel_full['date'], dayfirst=True, errors='coerce')
                            original_len = len(df_excel_full); df_excel_full.dropna(subset Error: {ve} Upload process halted. Transaction (if started) rolled back.")
            except sqlite3.Error as e_sql: 
                st.sidebar.error(f"DB error during upload: {e_sql}. Transaction implicitly rolled back.")
            except Exception as e_general: 
                st.sidebar.error(f"_str}.csv", "text/csv", key="dl_csv_comp2_widget")

st.sidebar.markdown("---")
st.sidebar.caption(f"Database: {DB_PATH} (Local SQLite)")

=['parsed_date'], inplace=True)
                            if len(df_excel_full) < original_len```
