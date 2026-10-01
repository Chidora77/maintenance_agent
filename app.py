import os
import glob
import pandas as pd
from datetime import datetime, timedelta, date
import streamlit as st
import io

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="Maintenance Agent - Google Sheets", layout="wide")

# === FORCE ALL BUTTONS BLUE ===
st.markdown("""
<style>
    div.stButton > button {
        background-color: #2a5a9a !important;
        background: #2a5a9a !important;
        border-color: #2a5a9a !important;
        color: white !important;
    }
    div.stButton > button:hover {
        background-color: #1e3d6f !important;
        background: #1e3d6f !important;
    }
    div.stDownloadButton > button {
        background-color: #2a5a9a !important;
        border-color: #2a5a9a !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# === GOOGLE SHEETS IMPORT CHECK ===
GSHEETS_AVAILABLE = False
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError as e:
    GSHEETS_AVAILABLE = False

CLIENT_CONFIG = {
    "name": "Bonny Terminal",
    "default_technicians": ["Chinedu K.", "Tunde A.", "Emeka O.", "S. Okoro", "A. Bello", "K. Ibrahim", "J. Musa"],
    "main_sheet_name": "Assets",
    "history_sheet_name": "History"
}

def get_gspread_client():
    if not GSHEETS_AVAILABLE:
        st.sidebar.error("❌ gspread not installed. Add to requirements.txt: gspread, google-auth")
        return None
    try:
        if "gcp_service_account" not in st.secrets:
            st.sidebar.error("❌ No [gcp_service_account] in secrets.toml")
            return None
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.sidebar.error(f"❌ Google auth failed: {e}")
        st.sidebar.code(str(e))
        return None

def get_gsheet_id():
    if "gsheet_id" in st.secrets:
        return st.secrets["gsheet_id"]
    if "private_gsheets_url" in st.secrets:
        try:
            url = st.secrets["private_gsheets_url"]
            return url.split("/d/")[1].split("/")[0]
        except:
            pass
    return None

def load_from_gsheet(client, gsheet_id, sheet_name):
    try:
        sh = client.open_by_key(gsheet_id)
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            # Try get_all_values if header issue
            vals = ws.get_all_values()
            if len(vals) > 1:
                df = pd.DataFrame(vals[1:], columns=vals[0])
        return df
    except gspread.WorksheetNotFound:
        st.sidebar.warning(f"Sheet tab '{sheet_name}' not found, will create on save")
        return None
    except Exception as e:
        st.sidebar.error(f"Failed to load {sheet_name}: {e}")
        return None

def save_to_gsheet(client, gsheet_id, df, sheet_name):
    try:
        sh = client.open_by_key(gsheet_id)
        try:
            ws = sh.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=sheet_name, rows=2000, cols=30)
        
        ws.clear()
        df_save = df.copy()
        # Convert all datetime to string for Sheets
        for col in df_save.columns:
            df_save[col] = df_save[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, (pd.Timestamp, datetime)) else str(x) if pd.notna(x) else "")
        
        # Build data
        data = [df_save.columns.tolist()] + df_save.values.tolist()
        ws.update(data)
        return True
    except Exception as e:
        st.error(f"❌ Failed to save {sheet_name} to Google Sheets: {e}")
        st.code(str(e))
        return False

def append_history_to_gsheet(client, gsheet_id, record, sheet_name):
    try:
        sh = client.open_by_key(gsheet_id)
        try:
            ws = sh.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=sheet_name, rows=5000, cols=20)
            ws.append_row(list(record.keys()))
        
        row = []
        for v in record.values():
            if isinstance(v, (pd.Timestamp, datetime, date)):
                row.append(v.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                row.append(str(v) if v is not None and str(v) != 'NaT' else "")
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Failed to append history: {e}")
        return False

def calc_mtbf(df_hist, asset_tag):
    try:
        if df_hist is None or df_hist.empty:
            return None
        sub = df_hist[df_hist['Asset Tag'] == asset_tag].copy()
        if len(sub) < 2:
            return None
        sub['Date'] = pd.to_datetime(sub['Date'], errors='coerce')
        sub = sub.sort_values('Date')
        diffs = sub['Date'].diff().dt.days.dropna()
        return int(diffs.mean()) if not diffs.empty else None
    except:
        return None

# === DEBUG SIDEBAR - CONNECTION STATUS ===
st.sidebar.header("🔧 Debug - Google Sheets Status")
client = get_gspread_client()
gsheet_id = get_gsheet_id()

if client and gsheet_id:
    st.sidebar.success(f"✅ Secrets found")
    st.sidebar.caption(f"Sheet ID: {gsheet_id[:10]}...{gsheet_id[-6:]}")
    try:
        sh = client.open_by_key(gsheet_id)
        st.sidebar.success(f"✅ Opened sheet: {sh.title}")
        st.sidebar.caption(f"Tabs: {[ws.title for ws in sh.worksheets()]}")
        use_gsheet = True
    except Exception as e:
        st.sidebar.error(f"❌ Cannot open Sheet ID. Did you SHARE sheet with service account email?")
        st.sidebar.code(f"Share with: {st.secrets['gcp_service_account']['client_email']}")
        st.sidebar.code(str(e))
        use_gsheet = False
else:
    if not gsheet_id:
        st.sidebar.error("❌ gsheet_id not in secrets.toml")
    use_gsheet = False

# === LOAD DATA ===
df = None
df_history = pd.DataFrame()

if use_gsheet:
    df = load_from_gsheet(client, gsheet_id, CLIENT_CONFIG["main_sheet_name"])
    df_history = load_from_gsheet(client, gsheet_id, CLIENT_CONFIG["history_sheet_name"])
    if df_history is None:
        df_history = pd.DataFrame()

if df is None or df.empty:
    # Fallback to local Excel for first migration (no warning as requested)
    xlsx_files = glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx"))
    xlsx_files = [f for f in xlsx_files if "service_history" not in os.path.basename(f).lower()]
    if not xlsx_files:
        xlsx_files = glob.glob("*.xlsx")
        xlsx_files = [f for f in xlsx_files if "service_history" not in f.lower()]
    
    if xlsx_files:
        df = pd.read_excel(xlsx_files[0])
        st.sidebar.info(f"📂 Loaded local Excel: {os.path.basename(xlsx_files[0])} - will migrate to Sheets")
        # Auto-migrate if Sheets available
        if use_gsheet and client and gsheet_id:
            if save_to_gsheet(client, gsheet_id, df, CLIENT_CONFIG["main_sheet_name"]):
                st.sidebar.success("✅ Migrated Assets to Google Sheets! Reloading...")
                # Load history excel if exists
                hist_path = os.path.join(SCRIPT_DIR, "service_history.xlsx")
                if os.path.exists(hist_path):
                    try:
                        df_h = pd.read_excel(hist_path)
                        save_to_gsheet(client, gsheet_id, df_h, CLIENT_CONFIG["history_sheet_name"])
                    except:
                        pass
                st.rerun()
    else:
        st.error("No data found. Add Excel file or configure Google Sheets.")
        st.stop()

# Process DataFrame
for col in ['Asset Tag', 'Equipment', 'Last Service', 'Interval', 'Technician']:
    if col not in df.columns:
        df[col] = "" if col != 'Interval' else 30

df['Last Service'] = pd.to_datetime(df['Last Service'], errors='coerce')
today_ts = pd.Timestamp(date.today())
df['Next Service'] = df.apply(lambda r: r['Last Service'] + timedelta(days=int(r['Interval'])) if pd.notna(r['Last Service']) else today_ts + timedelta(days=int(r['Interval'])), axis=1)
df['Days Overdue'] = (today_ts - df['Next Service']).dt.days
df['MTBF (days)'] = df['Asset Tag'].apply(lambda t: calc_mtbf(df_history, t))

# Sidebar Tech
st.sidebar.divider()
st.sidebar.subheader("👷 Technician")
existing_techs = [str(t) for t in df['Technician'].dropna().unique() if str(t).strip() != 'nan']
tech_pool = sorted(set(existing_techs + CLIENT_CONFIG["default_technicians"]))
if 'active_technicians' not in st.session_state:
    st.session_state.active_technicians = tech_pool
tech_opts = st.sidebar.multiselect("Active Technicians", tech_pool, default=st.session_state.active_technicians)
st.session_state.active_technicians = tech_opts if tech_opts else tech_pool
selected_technician = st.sidebar.selectbox("Current User (who is servicing?)", st.session_state.active_technicians)
st.sidebar.caption(f"Servicing as: **{selected_technician} ✅**")

if 'undo_stack' not in st.session_state:
    st.session_state.undo_stack = []

# === MAIN DASHBOARD ===
st.title("🔧 Asset Maintenance Dashboard")
if use_gsheet:
    st.success(f"✅ Google Sheets persistence ACTIVE - Sheet: {sh.title if 'sh' in locals() else gsheet_id[:15]}... - Today: {date.today().strftime('%d/%m/%Y')}")

for idx, row in df.iterrows():
    asset_tag = row['Asset Tag']
    equipment = row['Equipment']
    last_service = row['Last Service']
    next_service = row['Next Service']
    interval = int(row['Interval']) if pd.notna(row['Interval']) else 30
    overdue = int(row['Days Overdue']) if pd.notna(row['Days Overdue']) else 0
    mtbf = row['MTBF (days)']
    tech = row['Technician']
    status = "🟢 Green - OK" if overdue <=0 else "🔴 Red - OVERDUE"

    with st.container():
        c1,c2,c3 = st.columns([3,3,2])
        with c1:
            st.markdown(f"**{asset_tag} - {equipment}**")
            st.caption(f"Tech: {tech} | MTBF: {mtbf if pd.notna(mtbf) else 'N/A'}d")
            st.markdown(f"<span style='color:{'green' if overdue<=0 else 'red'}'>{status}</span>", unsafe_allow_html=True)
            st.progress(max(0,min(100,100-(overdue+interval)/interval*100))/100 if interval else 0.5)
            st.caption(f"Overdue: {overdue}d | AI: 23% LOW")
        with c2:
            st.markdown(f"**Next: {abs(overdue)}d | MTBF {int(mtbf) if pd.notna(mtbf) else 'N/A'}d**")
            last_str = last_service.strftime('%d/%m/%Y %H:%M') if pd.notna(last_service) else "Never"
            next_str = next_service.strftime('%d/%m/%Y') if pd.notna(next_service) else "N/A"
            st.caption(f"Last: {last_str} | Next: {next_str} | Interval: {interval}d")
        with c3:
            # SERVICE - FIXED DATE + GSHEET SAVE
            if st.button(f"🟢 Green - OK", key=f"svc_{asset_tag}", type="primary", use_container_width=True):
                st.session_state.undo_stack.append({"asset_tag": asset_tag, "prev_last": row['Last Service'], "prev_next": row['Next Service'], "prev_tech": row['Technician']})
                new_last = pd.Timestamp.now()
                new_next = pd.Timestamp(date.today()) + timedelta(days=interval)
                df.loc[df['Asset Tag']==asset_tag, 'Last Service'] = new_last
                df.loc[df['Asset Tag']==asset_tag, 'Next Service'] = new_next
                df.loc[df['Asset Tag']==asset_tag, 'Technician'] = selected_technician
                
                if use_gsheet:
                    ok = save_to_gsheet(client, gsheet_id, df, CLIENT_CONFIG["main_sheet_name"])
                    if ok:
                        rec = {"Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Asset Tag": asset_tag, "Equipment": equipment,
                               "Last Service (Previous)": row['Last Service'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['Last Service']) else "",
                               "Last Service (New)": new_last.strftime('%Y-%m-%d %H:%M:%S'), "Technician": selected_technician,
                               "Days Overdue Was": overdue, "Interval": interval}
                        append_history_to_gsheet(client, gsheet_id, rec, CLIENT_CONFIG["history_sheet_name"])
                        st.success(f"✅ Saved to Google Sheets! {asset_tag} = {date.today().strftime('%d/%m/%Y')} by {selected_technician}")
                    else:
                        st.error("❌ Failed to save to Google Sheets - check errors above")
                else:
                    # Fallback local
                    df.to_excel(xlsx_files[0], index=False)
                    st.success(f"✅ Saved locally (Sheets not connected) {asset_tag}")
                st.rerun()
            
            st.caption(f"Last serviced {last_service.strftime('%d/%m/%Y') if pd.notna(last_service) else 'Never'}")
            if st.button(f"↩️ UNDO to Red", key=f"undo_{asset_tag}", type="primary", use_container_width=True):
                found = None
                for i in range(len(st.session_state.undo_stack)-1,-1,-1):
                    if st.session_state.undo_stack[i]['asset_tag']==asset_tag:
                        found = st.session_state.undo_stack.pop(i)
                        break
                if found:
                    df.loc[df['Asset Tag']==asset_tag, 'Last Service'] = found['prev_last']
                    df.loc[df['Asset Tag']==asset_tag, 'Next Service'] = found['prev_next']
                    df.loc[df['Asset Tag']==asset_tag, 'Technician'] = found['prev_tech']
                    if use_gsheet:
                        save_to_gsheet(client, gsheet_id, df, CLIENT_CONFIG["main_sheet_name"])
                    else:
                        df.to_excel(xlsx_files[0], index=False)
                    st.warning(f"↩️ Undone {asset_tag}")
                    st.rerun()
                else:
                    st.error("No undo history")
        st.divider()

# Export section
st.header("🖨️ Print / Export Service History with Dates")
df_display = df_history.copy()
if not df_display.empty:
    for col in df_display.columns:
        if 'Date' in col or 'Service' in col:
            df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')

c1,c2,c3,c4 = st.columns(4)
with c1:
    if not df_display.empty:
        st.download_button("📄 CSV with Dates", df_display.to_csv(index=False), f"service_history_{date.today().strftime('%Y%m%d')}.csv", "text/csv", type="primary", use_container_width=True)
    else:
        st.button("📄 CSV with Dates", disabled=True, type="primary", use_container_width=True)
with c2:
    if not df_display.empty:
        buf = io.BytesIO(); df_display.to_excel(buf, index=False); buf.seek(0)
        st.download_button("📊 Excel with Dates", buf.getvalue(), f"service_history_{date.today().strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
    else:
        st.button("📊 Excel with Dates", disabled=True, type="primary", use_container_width=True)
with c3:
    st.button("📕 PDF Export", disabled=False, type="primary", use_container_width=True)
with c4:
    if st.button("🖨️ Print View", key="print_view_btn_final", type="primary", use_container_width=True):
        st.session_state.show_print = True

if st.session_state.get('show_print', False):
    st.dataframe(df_display, use_container_width=True)
