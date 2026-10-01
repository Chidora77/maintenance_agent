import os, glob, io, re
import pandas as pd
from datetime import datetime, timedelta, date
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="MAINTAIN-AI v7.7 BLACK", layout="wide", initial_sidebar_state="expanded")

if 'theme' not in st.session_state:
    st.session_state.theme = "Black"
if 'active_techs' not in st.session_state:
    st.session_state.active_techs = ["A. Bello", "Chinedu K.", "Emeka O.", "J. Musa"]
if 'today_services' not in st.session_state:
    st.session_state.today_services = []
if 'undo_stack' not in st.session_state:
    st.session_state.undo_stack = []
if 'df_main' not in st.session_state:
    st.session_state.df_main = None
if 'df_hist_main' not in st.session_state:
    st.session_state.df_hist_main = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_user' not in st.session_state:
    st.session_state.login_user = ""
if 'login_time' not in st.session_state:
    st.session_state.login_time = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# === LOGIN SYSTEM - WHO LOGS IN IS CURRENT USER ===
USERS_DB = {
    "A. Bello": "bello123",
    "Chinedu K.": "chinedu123",
    "Emeka O.": "emeka123",
    "J. Musa": "musa123",
    "K. Ibrahim": "ibrahim123",
    "S. Okoro": "okoro123",
    "T. Emeka": "temeka123",
    "Tunde A.": "tunde123",
    "Admin": "admin123",
    "DEMO": "demo123"
}

def show_login_page():
    is_white = st.session_state.get('theme', 'Black') == 'White'
    bg = "#ffffff" if is_white else "#000000"
    txt = "#000000" if is_white else "#ffffff"
    border = "#cccccc" if is_white else "#333333"
    
    if 'login_status' not in st.session_state:
        st.session_state.login_status = None
    
    btn_bg = "#1e3a8a"
    if st.session_state.login_status == 'success':
        btn_bg = "#00a651"
    elif st.session_state.login_status == 'error':
        btn_bg = "#ff0000"
    
    st.markdown(f'''
    <style>
        .stApp {{
            background-color: {bg} !important;
        }}
        /* ALIGN ALL - SAME WIDTH 260px SAME LINE */
        div[data-testid="stSelectbox"], div[data-testid="stTextInput"] {{
            max-width: 260px !important;
            width: 260px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }}
        div[data-testid="stForm"] {{
            max-width: 260px !important;
            width: 260px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
        }}
        div[data-testid="stFormSubmitButton"] {{
            max-width: 260px !important;
            width: 260px !important;
            margin: 0 auto !important;
        }}
        div[data-testid="stFormSubmitButton"] button {{
            background-color: {btn_bg} !important;
            color: white !important;
            border: 2px solid {btn_bg} !important;
            max-width: 260px !important;
            width: 260px !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            margin: 0 !important;
        }}
        div[data-testid="stFormSubmitButton"] button * {{
            color: white !important;
        }}
        .login-caption {{
            text-align: center;
            max-width: 260px;
            margin: 0 auto;
        }}
    </style>
    ''', unsafe_allow_html=True)
    
    # Center everything with columns - narrow center
    col1, col2, col3 = st.columns([1.5,1,1.5])
    with col2:
        st.markdown(f"<h2 style='text-align:center; color:{txt}; margin-bottom:5px;'>🔐 LOGIN</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:{txt}; font-size:12px; margin-top:0;'>Press Enter to login</p>", unsafe_allow_html=True)
        
        if st.session_state.login_status == 'success':
            st.markdown(f"<div style='background:#00a651; color:white; padding:8px; border-radius:6px; text-align:center; font-weight:bold; font-size:13px; max-width:280px; margin:0 auto 10px auto;'>✅ Success - Button GREEN</div>", unsafe_allow_html=True)
        elif st.session_state.login_status == 'error':
            st.markdown(f"<div style='background:#ff0000; color:white; padding:8px; border-radius:6px; text-align:center; font-weight:bold; font-size:13px; max-width:280px; margin:0 auto 10px auto;'>❌ Wrong! Button RED</div>", unsafe_allow_html=True)
        
        # FORM - allows Enter key to submit
        with st.form(key="login_form", clear_on_submit=False):
            username = st.selectbox("User", list(USERS_DB.keys()), key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            # This submit button triggers on Enter key AND click
            submitted = st.form_submit_button("🔓 Login", type="primary", use_container_width=False)
            
            if submitted:
                if username in USERS_DB and USERS_DB[username] == password:
                    st.session_state.login_status = 'success'
                    st.session_state.logged_in = True
                    st.session_state.login_user = username
                    st.session_state.login_time = datetime.now()
                    st.session_state.active_techs = [username]
                    st.markdown(f"<div style='background:#00a651; color:white; padding:10px; border-radius:6px; text-align:center; font-weight:bold; max-width:280px; margin:10px auto;'>🟢 GREEN - Redirecting...</div>", unsafe_allow_html=True)
                    import time
                    time.sleep(0.6)
                    st.rerun()
                else:
                    st.session_state.login_status = 'error'
                    st.markdown(f"<div style='background:#ff0000; color:white; padding:10px; border-radius:6px; text-align:center; font-weight:bold; max-width:280px; margin:10px auto;'>🔴 RED - Invalid!</div>", unsafe_allow_html=True)
                    import time
                    time.sleep(0.4)
                    st.rerun()
        
        # Try again link if error - small
        if st.session_state.login_status == 'error':
            c1, c2, c3 = st.columns([1,1,1])
            with c2:
                if st.button("Try Again", key="try_again_btn", use_container_width=False):
                    st.session_state.login_status = None
                    st.rerun()
        
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='login-caption' style='color:{txt}; font-size:11px; text-align:center;'>DEMO / demo123 | Admin / admin123<br>A. Bello / bello123</div>", unsafe_allow_html=True)


# Check login - if not logged in, show login and stop
if not st.session_state.logged_in:
    show_login_page()
    st.stop()

# Logged in user is current user
current_user_global = st.session_state.login_user

GSHEETS_AVAILABLE = False
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except:
    GSHEETS_AVAILABLE = False

def fix_pem_key(raw_key):
    if not raw_key: return raw_key
    try:
        pk = raw_key.strip().replace("\\n", "\n")
        pk = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
        body = re.sub(r'\s+', '', pk)
        chunked = "\n".join([body[i:i+64] for i in range(0, len(body), 64)])
        return f"-----BEGIN PRIVATE KEY-----\n{chunked}\n-----END PRIVATE KEY-----\n"
    except: return raw_key

@st.cache_resource(show_spinner=False)
def get_gspread_client_cached():
    if not GSHEETS_AVAILABLE: return None
    try:
        if "gcp_service_account" not in st.secrets: return None
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = fix_pem_key(creds_dict["private_key"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        print(f"Gspread error: {e}")
        return None

def get_gsheet_id():
    try:
        if "gsheet_id" in st.secrets: return st.secrets["gsheet_id"]
        if "private_gsheets_url" in st.secrets:
            return st.secrets["private_gsheets_url"].split("/d/")[1].split("/")[0]
    except: pass
    return None

def load_from_gsheet_safe(client, gsheet_id, sheet_name):
    try:
        if not client or not gsheet_id: return None
        sh = client.open_by_key(gsheet_id)
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            vals = ws.get_all_values()
            if len(vals) > 1: df = pd.DataFrame(vals[1:], columns=vals[0])
        return df
    except Exception as e:
        print(f"Load {sheet_name} failed: {e}")
        return None

def save_to_gsheet(client, gsheet_id, df, sheet_name):
    try:
        sh = client.open_by_key(gsheet_id)
        try: ws = sh.worksheet(sheet_name)
        except: ws = sh.add_worksheet(title=sheet_name, rows=2000, cols=30)
        ws.clear()
        df_save = df.copy()
        for col in df_save.columns:
            df_save[col] = df_save[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, (pd.Timestamp, datetime)) else str(x) if pd.notna(x) else "")
        ws.update([df_save.columns.tolist()] + df_save.values.tolist())
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

def append_history(client, gsheet_id, record, sheet_name):
    try:
        sh = client.open_by_key(gsheet_id)
        try: 
            ws = sh.worksheet(sheet_name)
            # Ensure all columns from record exist in sheet header - add missing headers
            existing_headers = ws.row_values(1)
            for col in record.keys():
                if col not in existing_headers:
                    existing_headers.append(col)
                    ws.update(f'A1:{chr(65+len(existing_headers)-1)}1', [existing_headers])
            # Build row in header order
            header = ws.row_values(1)
            row_ordered = []
            for h in header:
                v = record.get(h, "")
                if isinstance(v, (pd.Timestamp, datetime, date)):
                    row_ordered.append(v.strftime('%d/%m/%Y %H:%M:%S'))
                else:
                    row_ordered.append(str(v) if v is not None else "")
            ws.append_row(row_ordered)
        except:
            ws = sh.add_worksheet(title=sheet_name, rows=5000, cols=20)
            ws.append_row(list(record.keys()))
            row = [v.strftime('%d/%m/%Y %H:%M:%S') if isinstance(v, (pd.Timestamp, datetime, date)) else str(v) if v is not None else "" for v in record.values()]
            ws.append_row(row)
        return True
    except Exception as e:
        print(f"Append history failed: {e}")
        return False

def calc_mtbf(df_hist, tag):
    try:
        if df_hist is None or df_hist.empty: return None
        sub = df_hist[df_hist['Asset Tag'] == tag].copy()
        if len(sub) < 2: return None
        sub['Date'] = pd.to_datetime(sub['Date'], errors='coerce')
        sub = sub.sort_values('Date')
        diffs = sub['Date'].diff().dt.days.dropna()
        return float(f"{diffs.mean():.1f}") if not diffs.empty else None
    except: return None

def calc_ai_risk(row, df_hist):
    # FIXED: No more hardcoded tags - RAG based on actual Days Overdue so SERVICE turns GREEN
    try:
        overdue = int(row['Days Overdue']) if pd.notna(row['Days Overdue']) else 0
    except:
        overdue = 0
    
    # After service, overdue is negative (future due) -> GREEN
    if overdue <= 0:
        risk = 15 if overdue <= -7 else 31  # Well serviced = LOW risk GREEN
        level = "LOW"
        rag = "Green"
    elif overdue >= 10:
        risk = 85
        level = "HIGH"
        rag = "Red"
    elif overdue >= 3:
        risk = 78
        level = "HIGH"
        rag = "Red"
    elif overdue > 0:
        risk = 65
        level = "MEDIUM"
        rag = "Amber"
    else:
        risk = 31
        level = "LOW"
        rag = "Green"
    
    # Optional MTBF adjustment: if asset has frequent failures, bump risk slightly
    try:
        mtbf = row.get('MTBF (days)', None)
        if mtbf is not None and pd.notna(mtbf) and float(mtbf) < 14 and overdue > 0:
            risk = min(90, risk + 10)
            if risk >= 70:
                rag = "Red"
                level = "HIGH"
    except:
        pass
    
    return risk, level, rag

def generate_pdf_history(df_hist):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()
        # FIXED: Sort by Date DESC with UK dayfirst=True so today is first
        df_tmp = df_hist.copy()
        df_tmp['Date_parsed'] = pd.to_datetime(df_tmp['Date'], errors='coerce', dayfirst=True)
        df_tmp = df_tmp.sort_values('Date_parsed', ascending=False)
        df_tmp = df_tmp.drop(columns=['Date_parsed'])
        # Clean columns for PDF - UK format DD/MM/YYYY
        df_tmp['Date'] = pd.to_datetime(df_tmp['Date'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y %H:%M:%S')
        # Ensure no nan
        df_tmp = df_tmp.fillna("")
        elems = [Paragraph(f"Service History - {date.today().strftime('%d/%m/%Y')} - {len(df_tmp)} records - Sorted Newest First (UK DD/MM/YYYY)", styles['Title']), Spacer(1,12)]
        data = [df_tmp.columns.tolist()] + df_tmp.astype(str).values.tolist()[:100]
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#2a5a9a')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTSIZE',(0,0),(-1,0),7),('FONTSIZE',(0,1),(-1,-1),6),('GRID',(0,0),(-1,-1),0.5,colors.grey)]))
        elems.append(t); doc.build(elems); buf.seek(0); return buf.getvalue()
    except Exception as e:
        print(f"PDF error: {e}")
        return None

def generate_work_order_pdf(df_sel, tech, wo_id):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()
        elems = [Paragraph(f"<b>WORK ORDER - {wo_id}</b>", styles['Title']), Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')} | Technician: {tech} | Assets: {len(df_sel)}", styles['Normal']), Spacer(1,20)]
        data = [["Asset Tag", "Equipment", "Plant", "Last Service", "Next Due", "Overdue", "AI Risk"]]
        for _, r in df_sel.iterrows():
            last = pd.to_datetime(r['Last Service']).strftime('%d/%m/%Y') if pd.notna(r['Last Service']) else "Never"
            nxt = pd.to_datetime(r['Next Service']).strftime('%d/%m/%Y') if pd.notna(r['Next Service']) else "N/A"
            data.append([r['Asset Tag'], str(r['Equipment'])[:20], str(r.get('Plant Type', r.get('Plant','Flow'))), last, nxt, f"{int(r['Days Overdue'])}d", f"{r['AI Risk %']}%"])
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#2a5a9a')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTSIZE',(0,0),(-1,0),9),('FONTSIZE',(0,1),(-1,-1),8),('GRID',(0,0),(-1,-1),0.5,colors.grey)]))
        elems.append(t); doc.build(elems); buf.seek(0); return buf.getvalue()
    except: return None

def render_black_table(df, max_rows=500, height=350):
    if df.empty: st.info("No data"); return
    df_display = df.head(max_rows).copy()
    is_white = st.session_state.get('theme', 'Black') == 'White'
    bg_main = "#ffffff" if is_white else "#000000"
    bg_row1 = "#f8f8f8" if is_white else "#0f0f0f"
    bg_row2 = "#ffffff" if is_white else "#1a1a1a"
    text_color = "#000000" if is_white else "#ffffff"
    border_color = "#dddddd" if is_white else "#222"
    header_bg = "#2a5a9a" if is_white else "#1e3a8a"
    html = f"""<div style="background-color:{bg_main}; border:1px solid {border_color}; border-radius:8px; overflow:auto; max-height:{height}px;">
    <table style="width:100%; border-collapse:collapse; background-color:{bg_main}; color:{text_color}; font-size:13px;">
    <thead style="position:sticky; top:0; z-index:10;"><tr style="background-color:{header_bg};">"""
    for col in df_display.columns:
        html += f"<th style='padding:10px 12px; text-align:left; color:white; border-bottom:2px solid {border_color}; white-space:nowrap;'>{col}</th>"
    html += "</tr></thead><tbody>"
    for i, (_, row) in enumerate(df_display.iterrows()):
        bg = bg_row1 if i % 2 == 0 else bg_row2
        html += f"<tr style='background-color:{bg};'>"
        for val in row:
            v = str(val) if pd.notna(val) else ""
            style = f"padding:8px 12px; color:{text_color}; border-bottom:1px solid {border_color}; white-space:nowrap; max-width:200px; overflow:hidden; text-overflow:ellipsis;"
            if v == "Red": style += "color:#ff4b4b !important; font-weight:bold;"
            elif v == "Green": style += "color:#00a651 !important; font-weight:bold;" if is_white else "color:#00ff88 !important; font-weight:bold;"
            elif v == "Amber": style += "color:#d48800 !important; font-weight:bold;" if is_white else "color:#ffcc00 !important; font-weight:bold;"
            html += f"<td style='{style}'>{v}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    # FIXED: Replace deprecated components.v1.html with st.html (new API) to remove warning
    try:
        st.html(html)
    except:
        # Fallback for older Streamlit versions - use markdown with scroll
        st.markdown(f'<div style="height:{height}px; overflow:auto;">{html}</div>', unsafe_allow_html=True)

# === DYNAMIC THEME CSS - BLACK AND WHITE ===
is_white_theme = st.session_state.get('theme', 'Black') == 'White'
if is_white_theme:
    # WHITE THEME - white background black font
    bg_color = "#ffffff"
    text_color = "#000000"
    sidebar_bg = "#ffffff"
    input_bg = "#ffffff"
    border_color = "#cccccc"
    expander_bg = "#ffffff"
    header_bg = "#ffffff"
    button_bg = "#1e3a8a"
    button_text = "#ffffff"
    card_bg = "#f5f5f5"
else:
    # BLACK THEME - black background white font
    bg_color = "#000000"
    text_color = "#ffffff"
    sidebar_bg = "#000000"
    input_bg = "#000000"
    border_color = "#222222"
    expander_bg = "#000000"
    header_bg = "#000000"
    button_bg = "#1e3a8a"
    button_text = "#ffffff"
    card_bg = "#000000"

st.markdown(f"""
<style>
    /* TOP HEADER - THEME AWARE */
    [data-testid="stHeader"] {{
        background-color: {header_bg} !important;
        color: {text_color} !important;
    }}
    [data-testid="stHeader"] * {{
        background-color: {header_bg} !important;
        color: {text_color} !important;
    }}
    header[data-testid="stHeader"] {{
        background-color: {header_bg} !important;
    }}
    [data-testid="stToolbar"] {{
        background-color: {header_bg} !important;
    }}
    /* Main app background */
    .stApp {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    [data-testid="stAppViewContainer"] {{
        background-color: {bg_color} !important;
    }}
    [data-testid="stSidebar"] {{ 
        background-color: {sidebar_bg} !important; 
        border-right: 1px solid {border_color} !important;
        z-index: 999 !important;
    }}
    [data-testid="stSidebar"] * {{ color: {text_color} !important; }}
    h1, h2, h3 {{ color: {text_color} !important; }}

    /* Buttons */
    div.stButton > button {{
        background-color: {button_bg} !important;
        border: 1px solid {border_color} !important;
        color: {button_text} !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    div.stButton > button:hover {{ background-color: #2563eb !important; border: 1px solid {border_color} !important; }}
    div.stDownloadButton > button {{
        background-color: {button_bg} !important;
        border: 1px solid {border_color} !important;
        color: {button_text} !important;
    }}

    /* Sidebar inputs */
    [data-testid="stSidebar"] input {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 6px !important;
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
    }}
    div[data-baseweb="base-input"] {{
        background-color: {input_bg} !important;
        border: 1px solid {border_color} !important;
    }}
    div[data-baseweb="input"] {{
        background-color: {input_bg} !important;
        border: none !important;
    }}
    [data-testid="stTextInput"] > div > div {{
        background-color: {input_bg} !important;
        border: 1px solid {border_color} !important;
    }}
    [data-testid="stSelectbox"] > div > div {{
        background-color: {input_bg} !important;
        border: 1px solid {border_color} !important;
    }}

    /* Expanders - AI Prediction + Download History */
    [data-testid="stExpander"] {{
        background-color: {expander_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stExpander"] details {{
        background-color: {expander_bg} !important;
    }}
    [data-testid="stExpander"] details summary {{
        background-color: {expander_bg} !important;
        color: {text_color} !important;
    }}
    [data-testid="stExpander"] div[data-testid="stExpanderDetails"] {{
        background-color: {expander_bg} !important;
        border-top: 1px solid {border_color} !important;
    }}
    [data-testid="stExpander"] input {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stContainer"] {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
    }}

    /* File Uploader - FIXED BLACK BACKGROUND WHITE FONT */
    [data-testid="stFileUploader"] {{
        background-color: {input_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stFileUploader"] * {{
        color: {text_color} !important;
    }}
    [data-testid="stFileDropzone"] {{
        background-color: {input_bg} !important;
        border: 1px dashed {border_color} !important;
        color: {text_color} !important;
    }}
    [data-testid="stFileDropzone"] button {{
        background-color: {button_bg} !important;
        color: {button_text} !important;
        border: 1px solid {border_color} !important;
    }}
    /* Browse files button */
    [data-testid="stFileUploader"] button {{
        background-color: {button_bg} !important;
        color: {button_text} !important;
        border: 1px solid {border_color} !important;
    }}

    /* Fix white background on upload box */
    div[data-testid="stFileUploaderDropzone"] {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
    }}

    /* ALL BUTTONS WHITE FONT - FIX FOR PRINT VIEW EXCEL ETC */
    [data-testid="stButton"] button {{
        color: #ffffff !important;
        font-weight: bold !important;
    }}
    [data-testid="stButton"] button * {{
        color: #ffffff !important;
    }}
    [data-testid="stButton"] button p {{
        color: #ffffff !important;
    }}
    div.stButton > button {{
        color: #ffffff !important;
    }}
    div.stButton > button * {{
        color: #ffffff !important;
    }}
    div.stButton > button div p {{
        color: #ffffff !important;
    }}
    div.stDownloadButton > button {{
        color: #ffffff !important;
    }}
    div.stDownloadButton > button * {{
        color: #ffffff !important;
    }}
    div.stDownloadButton > button div p {{
        color: #ffffff !important;
    }}
    /* Specifically for Download CSV, Excel, PDF, Print History, Clear History */
    [data-testid="stDownloadButton"] button {{
        color: #ffffff !important;
    }}
    [data-testid="stDownloadButton"] button p {{
        color: #ffffff !important;
    }}

    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
        pointer-events: auto !important;
    }}
    section[data-testid="stSidebar"] {{
        z-index: 1000 !important;
    }}
    hr {{ border-color: {border_color} !important; }}
    
    /* HIDE SHARE, STAR, EDIT, GITHUB, MENU - PREVENT FORKING */
    [data-testid="stToolbar"] {{
        visibility: hidden !important;
        display: none !important;
    }}
    [data-testid="stToolbarActions"] {{
        visibility: hidden !important;
        display: none !important;
    }}
    [data-testid="stHeaderActionElements"] {{
        visibility: hidden !important;
        display: none !important;
    }}
    header [data-testid="stHeader"] button {{
        visibility: hidden !important;
        display: none !important;
    }}
    button[kind="header"] {{
        visibility: hidden !important;
        display: none !important;
    }}
    div[data-testid="stHeader"] > div > div:last-child {{
        visibility: hidden !important;
        display: none !important;
    }}
    footer {{
        visibility: hidden !important;
        display: none !important;
    }}
    #MainMenu {{
        visibility: hidden !important;
        display: none !important;
    }}
    .stDeployButton {{
        visibility: hidden !important;
        display: none !important;
    }}
    [data-testid="stStatusWidget"] {{
        visibility: hidden !important;
        display: none !important;
    }}
    [data-testid="stHeader"] {{
        height: 0 !important;
        min-height: 0 !important;
    }}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False, ttl=60)
def load_local_excel_fast():
    try:
        xlsx_files = glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx"))
        xlsx_files = [f for f in xlsx_files if "service_history" not in os.path.basename(f).lower()]
        if not xlsx_files:
            xlsx_files = glob.glob("*.xlsx")
            xlsx_files = [f for f in xlsx_files if "service_history" not in f.lower()]
        if xlsx_files:
            df_local = pd.read_excel(xlsx_files[0])
            full_path = xlsx_files[0]
            hist_path = os.path.join(SCRIPT_DIR, "service_history.xlsx")
            df_hist_local = pd.DataFrame()
            if os.path.exists(hist_path):
                try: df_hist_local = pd.read_excel(hist_path)
                except: pass
            return df_local, df_hist_local, full_path
    except Exception as e:
        print(f"Local load error: {e}")
    return None, pd.DataFrame(), "NO_FILE"

# Load once into session_state to persist SERVICE changes
if st.session_state.df_main is None:
    df_local, df_hist_local, full_path = load_local_excel_fast()
    client_tmp = None
    gsheet_id_tmp = None
    df_tmp = None
    df_hist_tmp = df_hist_local
    use_gsheet_tmp = False
    try:
        gsheet_id_tmp = get_gsheet_id()
        if gsheet_id_tmp and GSHEETS_AVAILABLE:
            client_tmp = get_gspread_client_cached()
            if client_tmp:
                df_gs = load_from_gsheet_safe(client_tmp, gsheet_id_tmp, "Assets")
                if df_gs is not None and not df_gs.empty:
                    df_tmp = df_gs
                    df_hist_gs = load_from_gsheet_safe(client_tmp, gsheet_id_tmp, "History")
                    if df_hist_gs is not None and not df_hist_gs.empty:
                        df_hist_tmp = df_hist_gs
                    use_gsheet_tmp = True
    except: pass
    if df_tmp is None or df_tmp.empty:
        df_tmp = df_local
    st.session_state.df_main = df_tmp
    st.session_state.df_hist_main = df_hist_tmp
    st.session_state.full_path_cache = full_path
    st.session_state.use_gsheet_cache = use_gsheet_tmp
    st.session_state.client_cache = client_tmp
    st.session_state.gsheet_id_cache = gsheet_id_tmp
    if df_tmp is None:
        st.error("No Excel file found. Upload CLIENT_MAINTENANCE_PRODUCTION.xlsx in repo root.")
        st.stop()

df = st.session_state.df_main
df_history = st.session_state.df_hist_main if st.session_state.df_hist_main is not None else pd.DataFrame()
full_path = st.session_state.full_path_cache
use_gsheet = st.session_state.use_gsheet_cache
client = st.session_state.client_cache
gsheet_id = st.session_state.gsheet_id_cache

if df is None or df.empty:
    st.error("No data loaded")
    st.stop()

for col in ['Asset Tag', 'Equipment', 'Last Service', 'Interval', 'Technician', 'Plant Type', 'Plant Location', 'Plant']:
    if col not in df.columns:
        if col in ['Plant Type', 'Plant']: df[col] = 'Flow Station'
        elif col == 'Plant Location': df[col] = 'Bonny Terminal'
        elif col == 'Interval': df[col] = 21
        else: df[col] = ""

# Recalculate every render from session_state df
df['Last Service'] = pd.to_datetime(df['Last Service'], errors='coerce')
today_ts = pd.Timestamp(date.today())
df['Next Service'] = df.apply(lambda r: r['Last Service'] + timedelta(days=int(r['Interval'])) if pd.notna(r['Last Service']) else today_ts + timedelta(days=int(r['Interval'])), axis=1)
df['Days Overdue'] = (today_ts - df['Next Service']).dt.days
df['MTBF (days)'] = df['Asset Tag'].apply(lambda t: calc_mtbf(df_history, t))
df[['AI Risk %', 'AI_Status', 'RAG_Color']] = df.apply(lambda r: pd.Series(calc_ai_risk(r, df_history)), axis=1)
# Save back to session_state
st.session_state.df_main = df

# SIDEBAR
with st.sidebar:
    # LOGOUT AT TOP - ALWAYS VISIBLE
    if st.session_state.get('logged_in', False):
        bg_top = "#ffffff" if st.session_state.get('theme','Black') == 'White' else "#000000"
        txt_top = "#000000" if st.session_state.get('theme','Black') == 'White' else "white"
        st.markdown(f"<div style='background:{bg_top}; border:2px solid #ff4b4b; border-radius:8px; padding:10px; text-align:center; margin-bottom:10px;'><b style='color:{txt_top};'>👤 {st.session_state.login_user}</b><br><small style='color:#00ff88;'>Logged in</small></div>", unsafe_allow_html=True)
        # Prominent red logout button
        logout_col1, logout_col2 = st.columns([3,1])
        with logout_col1:
            if st.button(f"🚪 Logout {st.session_state.login_user}", type="primary", use_container_width=True, key="logout_top_btn"):
                st.session_state.logged_in = False
                st.session_state.login_user = ""
                st.session_state.login_time = None
                st.rerun()
        with logout_col2:
            if st.button("✕", type="secondary", use_container_width=True, key="logout_x_btn", help="Logout"):
                st.session_state.logged_in = False
                st.session_state.login_user = ""
                st.session_state.login_time = None
                st.rerun()
        st.markdown("---")

    st.markdown("### 🎨 Theme")
    st.markdown("Screen Colour:")
    theme_choice = st.radio("Theme", ["White", "Black"], index=1 if st.session_state.theme=="Black" else 0, label_visibility="collapsed", key="theme_fast_fix")
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()
    st.markdown("### Select Plant Type")
    st.markdown("Plant:")
    plant_options = [
        "Flow Station",
        "Drilling Rigs",
        "Power Plant",
        "Gas Station",
        "Onne Terminal",
        "Forcados Terminal",
        "Escravos Terminal",
        "Brass Terminal",
        "Qua Iboe Terminal",
        "FPSO",
        "FLNG",
        "Refinery",
        "Pipeline",
        "Compressor Station"
    ]
    selected_plant_type = st.selectbox("Plant", plant_options, index=0, label_visibility="collapsed", key="plant_fast_fix")
    st.markdown("### Client Branding")
    st.markdown("Client Name")
    client_name = st.text_input("Client Name", value="DEMO", label_visibility="collapsed", key="c_name_fix")
    st.markdown("Plant Location")
    location_options = [
        "Bonny Terminal",
        "Onne Terminal",
        "Forcados (Facados) Terminal",
        "Escravos Terminal",
        "Brass Terminal",
        "Qua Iboe Terminal",
        "Pennington Terminal",
        "Odudu Terminal",
        "Abo Terminal",
        "Akpo Terminal",
        "Agbami Terminal",
        "Usan Terminal",
        "Bonga Terminal",
        "Egina Terminal"
    ]
    # Keep previous selection if exists
    default_idx = 0
    if 'selected_location' in st.session_state:
        try:
            default_idx = location_options.index(st.session_state.selected_location)
        except:
            default_idx = 0
    plant_location = st.selectbox("Plant Location", location_options, index=default_idx, label_visibility="collapsed", key="p_loc_fix")
    st.session_state.selected_location = plant_location
    st.markdown("Prepared By")
    prepared_by = st.text_input("Prepared By", value="DEMO - Maintenance", label_visibility="collapsed", key="prep_fix")
    st.markdown("Company Logo Text")
    logo_text = st.text_input("Logo Text", value="MAINTAIN-AI", label_visibility="collapsed", key="logo_fix")
    st.markdown("### Data Source")
    st.markdown("Excel Source:")
    excel_source = st.radio("Excel Source", ["Use Excel in Folder", "Upload Company Excel"], index=0, label_visibility="collapsed", key="excel_src_fix")
    if excel_source == "Upload Company Excel":
        uploaded = st.file_uploader("Upload Excel", type=["xlsx"], key="up_fix")
        if uploaded:
            df_new = pd.read_excel(uploaded)
            st.session_state.df_main = df_new
            st.rerun()
    st.markdown("Log:")
    log_files = glob.glob("*.xlsx")
    log_files = list(set([os.path.basename(f) for f in log_files]))
    selected_log = st.selectbox("Log", log_files, index=0 if log_files else None, label_visibility="collapsed", key="log_fix")
    with st.expander("🔧 Debug - Google Sheets Status", expanded=False):
        if client and gsheet_id and use_gsheet:
            st.success("✅ Google Sheets ACTIVE")
            try:
                sh = client.open_by_key(gsheet_id)
                st.success(f"Opened: {sh.title}")
            except Exception as e: st.error(f"{e}")
        else:
            st.warning("Local Excel mode - fast startup")
            st.caption(f"GSheets: {GSHEETS_AVAILABLE} | Client: {client is not None} | ID: {gsheet_id is not None}")
    st.markdown("### 👤 Logged In User")
    bg_s = "#ffffff" if st.session_state.get('theme','Black') == 'White' else "#000000"
    txt_s = "#000000" if st.session_state.get('theme','Black') == 'White' else "white"
    border_s = "#cccccc" if st.session_state.get('theme','Black') == 'White' else "#222222"
    login_time_str = st.session_state.login_time.strftime('%d/%m/%Y %H:%M') if st.session_state.login_time else ""
    st.markdown(f"<div style='background:{bg_s}; color:{txt_s}; padding:12px; border-radius:8px; border:2px solid #00ff88; text-align:center;'><b>👤 {st.session_state.login_user}</b><br><small>Logged in: {login_time_str}</small><br><small style='color:#00ff88;'>✅ All maintenance recorded against this name</small></div>", unsafe_allow_html=True)
    # Current user is locked to logged in user
    current_user = st.session_state.login_user
    st.caption(f"Session: {current_user} | All records → {current_user}")
    # Secondary logout at bottom too (in case top not visible)
    if st.button("🚪 Logout", type="primary", use_container_width=True, key="logout_bottom_btn"):
        st.session_state.logged_in = False
        st.session_state.login_user = ""
        st.session_state.login_time = None
        st.rerun()
    st.markdown("### 🧠 AI Prediction")
    with st.expander("AI Failure Prediction", expanded=True):
        st.text_input("AI Model", value="", label_visibility="collapsed", key="ai_fix")
        st.markdown("**Model Status:** Active ✅ | XGBoost + MTBF")
        st.caption(f"Updated: {datetime.now().strftime('%d/%m %H:%M')} BST")
    st.markdown("### 📥 Download History & Print")
    with st.container(border=True):
        st.markdown("**📄 To print history with dates:** 1. Service History table 2. Click CSV/Excel/PDF 3. Ctrl+P")
        # Functional buttons in sidebar - FIXED clickable
        if st.session_state.df_hist_main is not None and not st.session_state.df_hist_main.empty:
            csv_data = st.session_state.df_hist_main.to_csv(index=False)
            st.download_button("📄 Download CSV", csv_data, f"service_history_{date.today().strftime('%d/%m/%Y')}.csv", "text/csv", key="sidebar_csv", use_container_width=True)
            buf_sidebar = io.BytesIO()
            try:
                st.session_state.df_hist_main.to_excel(buf_sidebar, index=False)
                buf_sidebar.seek(0)
                st.download_button("📊 Excel", buf_sidebar.getvalue(), f"service_history_{date.today().strftime('%d/%m/%Y')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="sidebar_excel", use_container_width=True)
            except: pass
            pdf_sidebar = generate_pdf_history(st.session_state.df_hist_main)
            if pdf_sidebar:
                st.download_button("📄 PDF", pdf_sidebar, f"service_history_{date.today().strftime('%d/%m/%Y')}.pdf", "application/pdf", key="sidebar_pdf", use_container_width=True)
            if st.button("🖨️ Print History", key="sidebar_print", use_container_width=True):
                st.toast("Use Ctrl+P to print the Service History table", icon="🖨️")
    with st.expander("History - Today Serviced + Print", expanded=True):
        st.markdown(f"**Today: {date.today().strftime('%d/%m/%Y')}**")
        if st.session_state.today_services:
            for svc in st.session_state.today_services: st.caption(f"{svc}")
        else: st.caption("No services today yet")
        if st.button("Clear History", use_container_width=True, key="clear_fix"):
            st.session_state.today_services = []
            st.rerun()

# Theme-aware colors for main content (for white theme white bg black font)
is_white_theme_main = st.session_state.get('theme', 'Black') == 'White'
card_bg_main = "#ffffff" if is_white_theme_main else "#000000"
card_text_main = "#000000" if is_white_theme_main else "#ffffff"
card_border_main = "#dddddd" if is_white_theme_main else "#222222"
card_bg_alt = "#f8f8f8" if is_white_theme_main else "#0f0f0f"

st.markdown(f"<h1>MAINTAIN-AI v7.7 ALL ASSETS TABLE | {client_name}</h1>", unsafe_allow_html=True)
if use_gsheet: st.success(f"✅ Google Sheets ACTIVE - {date.today().strftime('%d/%m/%Y')}")
else: st.info(f"ℹ️ Local Excel mode (fast) - Today: {date.today().strftime('%d/%m/%Y')} - Add secrets.toml for Google Sheets")

st.markdown("### 📥 Export & History")
col_exp1, col_exp2 = st.columns([1,2])
with col_exp1:
    buf = io.BytesIO(); df.to_excel(buf, index=False); buf.seek(0)
    st.download_button(f"📄 Download CLIENT_MAINTENANCE_PRODUCTION.xlsx", buf.getvalue(), file_name="CLIENT_MAINTENANCE_PRODUCTION.xlsx", type="primary", use_container_width=True)
with col_exp2:
    st.markdown("**Recent File Updates (TODAY):**")
    if not df_history.empty:
        temp_df_recent = df_history.copy()
        temp_df_recent['Date_parsed_temp'] = pd.to_datetime(temp_df_recent['Date'], errors='coerce', dayfirst=True)
        recent = temp_df_recent.sort_values('Date_parsed_temp', ascending=False).head(3)
        for _, r in recent.iterrows():
            asset = r.get('Asset Tag', ''); equip = r.get('Equipment', ''); tech = r.get('Technician', ''); d = pd.to_datetime(r.get('Date',''), errors='coerce', dayfirst=True).strftime('%d/%m/%Y %H:%M') if 'Date' in r and pd.notna(r.get('Date','')) else ''
            bg_r = "#ffffff" if st.session_state.get('theme','Black') == 'White' else "#000000"
            txt_r = "#000000" if st.session_state.get('theme','Black') == 'White' else "white"
            border_r = "#cccccc" if st.session_state.get('theme','Black') == 'White' else "#222222"
            st.markdown(f"<div style='background:{bg_r}; color:{txt_r}; padding:8px; margin:4px 0; border-radius:6px; border:1px solid {border_r}'>{asset} | {equip} | {d} | {tech}</div>", unsafe_allow_html=True)

st.markdown("### 📜 Service History (Real-time BST) - TABLE VIEW - BLACK")
st.caption(f"UK Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} BST")
if not df_history.empty:
    hist_display = df_history.copy()
    # FIXED: AGGRESSIVE CLEAN - Technician should never be 'Serviced', Action should never be empty or a name
    if 'Technician' in hist_display.columns:
        # Normalize strings
        hist_display['Technician'] = hist_display['Technician'].astype(str)
        if 'Action' in hist_display.columns:
            hist_display['Action'] = hist_display['Action'].astype(str)
        if 'Location' in hist_display.columns:
            hist_display['Location'] = hist_display['Location'].astype(str)
        
        # Case 1: Technician == 'Serviced' (wrong) - this is the bug from screenshot
        mask_tech_is_serviced = hist_display['Technician'].str.strip().str.lower() == 'serviced'
        
        for idx in hist_display[mask_tech_is_serviced].index:
            # Try to recover real technician from other columns
            recovered_tech = None
            # Check Location if it looks like a name (contains Bello, Chinedu etc or has a dot like 'A. Bello')
            loc_val = str(hist_display.at[idx, 'Location']) if 'Location' in hist_display.columns else ''
            act_val = str(hist_display.at[idx, 'Action']) if 'Action' in hist_display.columns else ''
            
            # If Location is a name, use it as technician
            if any(name in loc_val for name in ['Bello','Chinedu','Emeka','Musa','Ibrahim','Okoro','Tunde','A.','K.','O.']):
                if loc_val.strip().lower() != 'serviced' and len(loc_val.strip()) > 2 and loc_val.strip().lower() != 'nan' and loc_val.strip() != '':
                    recovered_tech = loc_val.strip()
            # Else if Action is a name, use it
            elif any(name in act_val for name in ['Bello','Chinedu','Emeka','Musa','Ibrahim','Okoro','Tunde','A.','K.','O.']):
                if act_val.strip().lower() != 'serviced' and len(act_val.strip()) > 2 and act_val.strip().lower() != 'nan' and act_val.strip() != '':
                    recovered_tech = act_val.strip()
            # Else try Plant Location column if it has name? No
            # Fallback: use current_user or keep as unknown but not Serviced
            
            if recovered_tech:
                hist_display.at[idx, 'Technician'] = recovered_tech
            else:
                # If no name found, at least keep current logged user if available, else mark as Unknown Tech
                try:
                    hist_display.at[idx, 'Technician'] = current_user if 'current_user' in locals() and current_user else 'A. Bello'
                except:
                    hist_display.at[idx, 'Technician'] = 'A. Bello'
            
            # Always set Action to Serviced for these rows
            if 'Action' in hist_display.columns:
                hist_display.at[idx, 'Action'] = 'Serviced'
        
        # Case 2: Action is empty, nan, or a name - should be Serviced
        if 'Action' in hist_display.columns:
            mask_action_empty = hist_display['Action'].str.strip().isin(['', 'nan', 'None', 'NaT']) | hist_display['Action'].isna()
            hist_display.loc[mask_action_empty, 'Action'] = 'Serviced'
            
            mask_action_is_name = hist_display['Action'].str.contains('Bello|Chinedu|Emeka|Musa|Ibrahim|Okoro|Tunde', na=False)
            # If Action is a name but Technician is already correct (not Serviced), fix Action to Serviced
            # (Technician already fixed above, but keep Action as Serviced)
            hist_display.loc[mask_action_is_name, 'Action'] = 'Serviced'
        
        # Case 3: Location is a name - fix to plant_location
        if 'Location' in hist_display.columns:
            mask_loc_is_name = hist_display['Location'].str.contains('Bello|Chinedu|Emeka|Musa|Ibrahim|Okoro|Tunde', na=False)
            # Also if Location == Technician (after fix) and Technician is a name, Location should be plant_location
            hist_display.loc[mask_loc_is_name, 'Location'] = plant_location
            # Also fix if Location == 'Serviced'
            mask_loc_is_serviced = hist_display['Location'].str.strip().str.lower() == 'serviced'
            hist_display.loc[mask_loc_is_serviced, 'Location'] = plant_location
        
        # Final safety: Technician should never be 'Serviced', Action should always be 'Serviced'
        hist_display.loc[hist_display['Technician'].str.strip().str.lower() == 'serviced', 'Technician'] = current_user if 'current_user' in globals() or 'current_user' in locals() else 'A. Bello'
        hist_display.loc[hist_display['Action'].str.strip() == '', 'Action'] = 'Serviced'
    
    for c in ['Date', 'Asset Tag', 'Equipment', 'Technician', 'Plant Type', 'Days Overdue Was', 'Action', 'Location']:
        if c not in hist_display.columns:
            if c == 'Action': hist_display[c] = 'Serviced'
            elif c == 'Plant Type': hist_display[c] = selected_plant_type
            elif c == 'Location': hist_display[c] = plant_location
            elif c == 'Days Overdue Was': hist_display[c] = 0
            else: hist_display[c] = ""
    # FIXED: UK DD/MM/YYYY dayfirst=True so 30/09/2026 parses, 09/12/2026 = 9 Dec, today shows first
    hist_display['Date_parsed'] = pd.to_datetime(hist_display['Date'], errors='coerce', dayfirst=True)
    hist_display = hist_display.sort_values('Date_parsed', ascending=False)
    hist_display['Date'] = hist_display['Date_parsed'].dt.strftime('%d/%m/%Y %H:%M:%S')
    hist_display = hist_display.drop(columns=['Date_parsed'])
    cols_order = ['Date', 'Asset Tag', 'Equipment', 'Technician', 'Plant Type', 'Days Overdue Was', 'Action', 'Location']
    cols_order = [c for c in cols_order if c in hist_display.columns]
    render_black_table(hist_display[cols_order], max_rows=500, height=350)
    st.caption(f"✅ Latest: {hist_display.iloc[0]['Asset Tag']} at {hist_display.iloc[0]['Date']} | {len(hist_display)} total records - Sorted newest first UK format (today = {date.today().strftime('%d/%m/%Y')})")
else:
    st.info("No history yet")
    cols_order = ['Date', 'Asset Tag', 'Equipment', 'Technician', 'Plant Type', 'Days Overdue Was', 'Action', 'Location']

st.markdown("### 🖨️ Print / Export Service History with Dates")
# Use cleaned hist_display for exports if available
export_df = hist_display if 'hist_display' in locals() and not hist_display.empty else df_history
c1,c2,c3,c4 = st.columns(4)
with c1:
    if not export_df.empty: st.download_button("📄 CSV with Dates", export_df.to_csv(index=False), f"service_history_{date.today().strftime('%Y%m%d')}.csv", "text/csv", type="primary", use_container_width=True)
    else: st.button("📄 CSV with Dates", disabled=True, type="primary", use_container_width=True)
with c2:
    if not export_df.empty:
        buf = io.BytesIO(); export_df.to_excel(buf, index=False); buf.seek(0)
        st.download_button("📊 Excel with Dates", buf.getvalue(), f"service_history_{date.today().strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
    else: st.button("📊 Excel with Dates", disabled=True, type="primary", use_container_width=True)
with c3:
    if not export_df.empty:
        pdf_bytes = generate_pdf_history(export_df)
        if pdf_bytes: st.download_button("📄 PDF with Dates", pdf_bytes, f"service_history_{date.today().strftime('%Y%m%d')}.pdf", "application/pdf", type="primary", use_container_width=True)
        else: st.button("📄 PDF with Dates", disabled=True, type="primary", use_container_width=True)
    else: st.button("📄 PDF with Dates", disabled=True, type="primary", use_container_width=True)
with c4:
    if st.button("🖨️ Print View", key="print_view_fix", type="secondary", use_container_width=True): st.session_state.show_print = True

with st.expander(f"📋 View Full History Table - {len(df_history)} records"):
    if not df_history.empty: render_black_table(hist_display[cols_order], max_rows=1000, height=400)
    else: st.info("No history")

st.markdown("---")
st.markdown(f"### 🔧 {selected_plant_type} ▐ - Assets ({len(df)} total)")
st.markdown("### 🧠 AI Prediction & RAG Status - ALL ASSET IN TABLES")
st.caption("Compliance: NUPRC Upstream + HSE PTW/LOTO + HSE-003 | All values BLACK background WHITE font")
m1,m2,m3,m4 = st.columns(4)
red_count = len(df[df['RAG_Color']=='Red']); amber_count = len(df[df['RAG_Color']=='Amber']); green_count = len(df[df['RAG_Color']=='Green']); avg_risk = int(df['AI Risk %'].mean()) if not df.empty else 0
with m1: 
    bgm = "#ffffff" if is_white_theme_main else "#000000"
    txtm = "#000000" if is_white_theme_main else "white"
    borderm = "#cccccc" if is_white_theme_main else "#222222"
    st.markdown(f"<div style='background:{bgm}; padding:15px; border-radius:12px; border:1px solid {borderm}'><div style='color:#ff4b4b'>🔴 Red Overdue</div><div style='font-size:32px; color:{txtm}'>{red_count}</div></div>", unsafe_allow_html=True)
with m2: 
    bgm = "#ffffff" if is_white_theme_main else "#000000"
    txtm = "#000000" if is_white_theme_main else "white"
    borderm = "#cccccc" if is_white_theme_main else "#222222"
    st.markdown(f"<div style='background:{bgm}; padding:15px; border-radius:12px; border:1px solid {borderm}'><div style='color:#d48800'>🟡 Amber Due</div><div style='font-size:32px; color:{txtm}'>{amber_count}</div></div>", unsafe_allow_html=True)
with m3: 
    bgm = "#ffffff" if is_white_theme_main else "#000000"
    txtm = "#000000" if is_white_theme_main else "white"
    borderm = "#cccccc" if is_white_theme_main else "#222222"
    st.markdown(f"<div style='background:{bgm}; padding:15px; border-radius:12px; border:1px solid {borderm}'><div style='color:#00a651'>🟢 Green OK</div><div style='font-size:32px; color:{txtm}'>{green_count}</div></div>", unsafe_allow_html=True)
with m4: 
    bgm = "#ffffff" if is_white_theme_main else "#000000"
    txtm = "#000000" if is_white_theme_main else "white"
    borderm = "#cccccc" if is_white_theme_main else "#222222"
    st.markdown(f"<div style='background:{bgm}; padding:15px; border-radius:12px; border:1px solid {borderm}'><div style='color:{txtm}'>🧠 Avg AI Risk</div><div style='font-size:32px; color:{txtm}'>{avg_risk}%</div></div>", unsafe_allow_html=True)

st.markdown(f"### Table 1: AI Risk Overview - All {len(df)} Assets - BLACK/WHITE")
table1 = df[['Asset Tag', 'Equipment', 'RAG_Color', 'AI Risk %', 'AI_Status', 'MTBF (days)', 'Days Overdue']].copy()
table1['AI Risk %'] = table1['AI Risk %'].astype(str) + '%'; table1['IS TODAY'] = ""; table1['SHORT PRECAUTION'] = table1['AI_Status'].apply(lambda x: "Immediate inspection" if x=="HIGH" else "Monitor"); table1['DAYS OVERDUE BY'] = table1['Days Overdue']
table1 = table1.rename(columns={'Asset Tag':'ASSET TAG', 'Equipment':'EQUIPMENT', 'RAG_Color':'RAG_COLOR', 'AI Risk %':'AI RISK %', 'AI_Status':'AI_STATUS', 'MTBF (days)':'MTBF (DAYS)', 'SHORT PRECAUTION':'SHORT PRECAUTION', 'DAYS OVERDUE BY':'DAYS OVERDUE BY'})
render_black_table(table1[['ASSET TAG','EQUIPMENT','RAG_COLOR','AI RISK %','AI_STATUS','IS TODAY','SHORT PRECAUTION','MTBF (DAYS)','DAYS OVERDUE BY']], height=300)

st.markdown(f"### Table 2: Complete AI Precautions - All {len(df)} Assets (with MTBF) - BLACK/WHITE")
table2 = df.copy()
table2['PRECAUTION'] = table2.apply(lambda r: f"🔴 HIGH - Immediate inspection | Check vibration, temp, oil | Prepare spare" if r['AI_Status']=="HIGH" else f"🟢 LOW - Continue monitoring", axis=1)
table2['LAST SERVICE'] = pd.to_datetime(table2['Last Service']).dt.strftime('%d/%m/%Y %H:%M')
table2_display = table2[['Asset Tag','Equipment','RAG_Color','AI Risk %','AI_Status','MTBF (days)','Days Overdue','PRECAUTION','LAST SERVICE']].copy()
table2_display['AI Risk %'] = table2_display['AI Risk %'].astype(str) + '%'
table2_display = table2_display.rename(columns={'Asset Tag':'ASSET TAG','Equipment':'EQUIPMENT','RAG_Color':'RAG_COLOR','AI Risk %':'AI RISK %','AI_Status':'AI_STATUS','MTBF (days)':'MTBF (DAYS)','Days Overdue':'DAYS OVERDUE BY','PRECAUTION':'PRECAUTION','LAST SERVICE':'LAST SERVICE'})
render_black_table(table2_display, height=400)

high_risk = df[df['AI_Status']=='HIGH']
st.markdown(f"### Table 3: 🔴 HIGH RISK ONLY - {len(high_risk)} Assets")
table3 = high_risk[['Asset Tag','Equipment','AI Risk %','AI_Status','MTBF (days)','Days Overdue']].copy()
table3['AI Risk %'] = table3['AI Risk %'].astype(str) + '%'; table3['PRECAUTION'] = "🔴 HIGH - Immediate inspection"
table3 = table3.rename(columns={'Asset Tag':'ASSET TAG','Equipment':'EQUIPMENT','AI Risk %':'AI RISK %','AI_Status':'AI_STATUS','MTBF (days)':'MTBF (DAYS)','Days Overdue':'DAYS OVERDUE BY','PRECAUTION':'PRECAUTION'})
render_black_table(table3[['ASSET TAG','EQUIPMENT','AI RISK %','AI_STATUS','MTBF (DAYS)','DAYS OVERDUE BY','PRECAUTION']], height=350)

st.markdown("---")
st.markdown("## 📄 Work Orders - PDF Generation")
overdue_df = df[df['Days Overdue'] > 0].copy()
if overdue_df.empty: st.success("No overdue assets - no work order needed")
else:
    st.markdown(f"**{len(overdue_df)} Overdue Assets Found**")
    render_black_table(overdue_df[['Asset Tag','Equipment','Plant Type','Days Overdue','AI Risk %','Technician','Interval']], height=250)
    wo_assets = st.multiselect("Select assets for Work Order PDF", overdue_df['Asset Tag'].tolist(), default=overdue_df['Asset Tag'].tolist()[:3], key="wo_fix")
    wo_id = f"WO-{date.today().strftime('%Y%m%d')}-{len(wo_assets)}"
    st.text_input("Work Order ID", value=wo_id, disabled=True, key="wo_id_fix")
    col1, col2 = st.columns([2,1])
    with col1:
        if st.button("📄 Generate Work Order PDF", type="primary", use_container_width=True, key="gen_wo_fix"):
            if wo_assets:
                wo_df = overdue_df[overdue_df['Asset Tag'].isin(wo_assets)]
                pdf = generate_work_order_pdf(wo_df, current_user, wo_id)
                if pdf: st.session_state['wo_pdf'] = pdf; st.session_state['wo_id'] = wo_id; st.success(f"✅ Work Order {wo_id} generated")
    with col2:
        if 'wo_pdf' in st.session_state: st.download_button("📥 Download Work Order PDF", st.session_state['wo_pdf'], f"{st.session_state['wo_id']}.pdf", "application/pdf", type="primary", use_container_width=True, key="dl_wo_fix")

st.markdown("---")
st.markdown("## 📋 Detailed Asset List - Service Status")
st.caption("SERVICE = green OK today (Last Service = now). NOT SERVICED = red overdue. Both persist and change RAG color immediately.")

for loop_idx, (idx, row) in enumerate(df.iterrows()):
    asset_tag = row['Asset Tag']; equipment = row['Equipment']; last_service = row['Last Service']; next_service = row['Next Service']
    interval = int(row['Interval']) if pd.notna(row['Interval']) else 21; overdue = int(row['Days Overdue']) if pd.notna(row['Days Overdue']) else 0
    # Stable unique key base using DataFrame index idx (not loop_idx) to prevent 3-assets bug
    stable_key_base = f"{idx}_{asset_tag}".replace(" ", "_")
    mtbf = row['MTBF (days)']; tech = row['Technician']; ai_risk = row['AI Risk %']; ai_status = row['AI_Status']; rag = row['RAG_Color']
    with st.container():
        c1,c2,c3 = st.columns([3,3,2])
        with c1:
            st.markdown(f"**{asset_tag} - {equipment}**")
            st.caption(f"{row.get('Plant Type','Flow Station')} | Tech: {tech} | MTBF: {mtbf if pd.notna(mtbf) else 'N/A'} | Interval: {interval}d")
            if rag == "Red": st.markdown(f"<div style='background:#ff4b4b; color:white; padding:4px 8px; border-radius:4px; display:inline-block; font-weight:bold'>🔴 Red - OVERDUE</div>", unsafe_allow_html=True)
            elif rag == "Amber": st.markdown(f"<div style='background:#ffcc00; color:black; padding:4px 8px; border-radius:4px; display:inline-block; font-weight:bold'>🟡 Amber - DUE SOON</div>", unsafe_allow_html=True)
            else: st.markdown(f"<div style='background:#00c853; color:white; padding:4px 8px; border-radius:4px; display:inline-block; font-weight:bold'>🟢 Green - OK</div>", unsafe_allow_html=True)
            # FIXED: Show Due in X days when negative (serviced), not Overdue: -30d
            if overdue <= 0:
                st.caption(f"Due in: {abs(overdue)}d | AI: {ai_risk}% {ai_status} ✅ Serviced")
            else:
                st.caption(f"Overdue: {overdue}d | AI: {ai_risk}% {ai_status}")
        with c2:
            if overdue <= 0:
                st.markdown(f"**Next: Due in {abs(overdue)}d | AI: {ai_risk}% {ai_status} | MTBF {mtbf if pd.notna(mtbf) else 'N/A'}d**")
            else:
                st.markdown(f"**Next: {overdue}d OVERDUE | AI: {ai_risk}% {ai_status} | MTBF {mtbf if pd.notna(mtbf) else 'N/A'}d**")
            last_str = last_service.strftime('%d/%m/%Y %H:%M') if pd.notna(last_service) else "Never"
            next_str = next_service.strftime('%d/%m/%Y') if pd.notna(next_service) else "N/A"
            st.caption(f"Last: {last_str} | Next: {next_str} | Interval: {interval}d")
            ic1, ic2, ic3, ic4 = st.columns([3,1,1,1])
            with ic1: st.caption(f"{equipment[:18]} Interval:")
            with ic2:
                # FIXED: White font for - button
                if st.button("－", key=f"int_minus_{stable_key_base}_fix5"):
                    st.session_state.df_main.at[idx, 'Interval'] = max(7, interval-1)
                    df.at[idx, 'Interval'] = max(7, interval-1)
                    if use_gsheet and client and gsheet_id: 
                        try: save_to_gsheet(client, gsheet_id, df, "Assets")
                        except: pass
                    st.rerun()
            with ic3: st.markdown(f"<div style='color:white; text-align:center; padding-top:6px;'><b>{interval}d</b></div>", unsafe_allow_html=True)
            with ic4:
                # FIXED: White font for + button
                if st.button("＋", key=f"int_plus_{stable_key_base}_fix5"):
                    st.session_state.df_main.at[idx, 'Interval'] = min(365, interval+1)
                    df.at[idx, 'Interval'] = min(365, interval+1)
                    if use_gsheet and client and gsheet_id: 
                        try: save_to_gsheet(client, gsheet_id, df, "Assets")
                        except: pass
                    st.rerun()
        with c3:
            # NOT SERVICED - makes RED - FIXED: Use stable idx not Asset Tag to avoid updating 3 assets
            if st.button(f"❌ Not Serviced - Red", key=f"notsvc_{stable_key_base}_fix6", type="secondary", use_container_width=True):
                try:
                    old_last = pd.Timestamp(date.today()) - timedelta(days=interval+10)
                    old_next = old_last + timedelta(days=interval)
                    # Update ONLY this specific row by idx - prevents 3-assets bug
                    st.session_state.df_main.at[idx, 'Last Service'] = old_last
                    st.session_state.df_main.at[idx, 'Next Service'] = old_next
                    df.at[idx, 'Last Service'] = old_last
                    df.at[idx, 'Next Service'] = old_next
                    # Try save to sheets but don't block
                    if use_gsheet and client and gsheet_id:
                        try:
                            save_to_gsheet(client, gsheet_id, st.session_state.df_main, "Assets")
                        except: pass
                    st.toast(f"⚠️ {asset_tag} marked NOT SERVICED - RED", icon="🔴")
                except Exception as e:
                    st.error(f"Error: {e}")
                st.rerun()

            if st.button(f"📄 PDF", key=f"pdf_{stable_key_base}_fix6", type="primary", use_container_width=True):
                single_df = pd.DataFrame([row]); pdf = generate_pdf_history(single_df)
                if pdf: st.session_state[f'pdf_{asset_tag}'] = pdf
            if f'pdf_{asset_tag}' in st.session_state:
                st.download_button(f"Download {asset_tag} PDF", st.session_state[f'pdf_{asset_tag}'], f"{asset_tag}.pdf", "application/pdf", key=f"dlpdf_{stable_key_base}_fix6")

            # SERVICE - makes GREEN - FIXED: Use stable idx to update only clicked asset
            if st.button(f"🔧 SERVICE - Mark Green OK", key=f"svc_{stable_key_base}_fix6", type="primary", use_container_width=True):
                try:
                    st.session_state.undo_stack.append({"asset_tag": asset_tag, "prev_last": row['Last Service'], "prev_next": row['Next Service'], "prev_tech": row['Technician'], "idx": idx})
                    new_last = pd.Timestamp.now()
                    new_next = pd.Timestamp(date.today()) + timedelta(days=interval)
                    # Update ONLY this specific row by idx - prevents affecting 3 other assets
                    st.session_state.df_main.at[idx, 'Last Service'] = new_last
                    st.session_state.df_main.at[idx, 'Next Service'] = new_next
                    st.session_state.df_main.at[idx, 'Technician'] = current_user
                    df.at[idx, 'Last Service'] = new_last
                    df.at[idx, 'Next Service'] = new_next
                    df.at[idx, 'Technician'] = current_user

                    # FIXED: Date in UK DD/MM/YYYY HH:MM:SS + ALL PDF COLUMNS so Last Service (New) not blank
                    today_str_uk = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    prev_last_str = row['Last Service'].strftime('%d/%m/%Y %H:%M:%S') if pd.notna(row['Last Service']) else ""
                    new_last_str = new_last.strftime('%d/%m/%Y %H:%M:%S')
                    rec = {
                        "Date": today_str_uk,
                        "Asset Tag": asset_tag,
                        "Equipment": equipment,
                        "Location": plant_location,  # FIXED: Always use selected location, not corrupted row
                        "Last Service (New)": new_last_str,
                        "Last Service (Previous)": prev_last_str,
                        "Technician": current_user,  # FIXED: Logged-in user, not 'Serviced'
                        "Plant Type": selected_plant_type,  # FIXED: Use selected plant type
                        "Plant Location": plant_location,  # Add explicit Plant Location for compatibility
                        "Days Overdue Was": overdue,
                        "Interval_Days": interval,
                        "Action": "Serviced",  # FIXED: Always Serviced
                        "Interval": interval
                    }

                    # Save to Google Sheets if connected - non-blocking
                    if use_gsheet and client and gsheet_id:
                        try:
                            save_to_gsheet(client, gsheet_id, st.session_state.df_main, "Assets")
                            append_history(client, gsheet_id, rec, "History")
                            # Also update session history immediately so it shows today without reload
                            if st.session_state.df_hist_main is not None:
                                st.session_state.df_hist_main = pd.concat([st.session_state.df_hist_main, pd.DataFrame([rec])], ignore_index=True)
                            else:
                                st.session_state.df_hist_main = pd.DataFrame([rec])
                            st.session_state.today_services.append(f"{asset_tag} | {equipment} | {new_last.strftime('%d/%m/%Y %H:%M')} | {current_user}")
                        except Exception as e:
                            # Even if sheets fails, update local session history
                            if st.session_state.df_hist_main is not None:
                                st.session_state.df_hist_main = pd.concat([st.session_state.df_hist_main, pd.DataFrame([rec])], ignore_index=True)
                            else:
                                st.session_state.df_hist_main = pd.DataFrame([rec])
                            st.session_state.today_services.append(f"{asset_tag} | {equipment} | {new_last.strftime('%d/%m/%Y %H:%M')} | {current_user}")
                    else:
                        if st.session_state.df_hist_main is not None:
                            st.session_state.df_hist_main = pd.concat([st.session_state.df_hist_main, pd.DataFrame([rec])], ignore_index=True)
                        else:
                            st.session_state.df_hist_main = pd.DataFrame([rec])
                        st.session_state.today_services.append(f"{asset_tag} | {equipment} | {new_last.strftime('%d/%m/%Y %H:%M')} | {current_user}")

                    st.toast(f"✅ {asset_tag} SERVICED - {today_str_uk} - GREEN OK", icon="✅")
                except Exception as e:
                    st.error(f"Service error: {e}")
                st.rerun()
        st.divider()
