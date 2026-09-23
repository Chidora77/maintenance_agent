# app_secure_LICENSED.py - WITH LOGIN + LICENSE KEY + EXPIRY - Restricts usage until paid
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os, glob
import numpy as np
from io import BytesIO
import hashlib

# ============ LICENSE SYSTEM ============
# Change these for each client - this is how you control who pays

# OPTION 1: Simple password per client (easiest)
# Give each company a different password: SPDC pays, you give them "SPDC-2026-XYZ"

VALID_LICENSES = {
    # License Key : {client, expiry, plant_types_allowed}
    "SPDC-FLOW-2026": {"client": "SPDC", "expiry": "2026-12-31", "plants": ["Flow Station", "Rig (Drilling)", "Gas Plant", "Power Plant"]},
    "TOTAL-2026-GAS": {"client": "TotalEnergies", "expiry": "2026-11-30", "plants": ["Gas Plant"]},
    "FIRSTEP-TRIAL": {"client": "First E&P", "expiry": "2026-11-15", "plants": ["Flow Station"]},  # Trial expires in 22 days
    "DEMO-12345": {"client": "DEMO", "expiry": "2026-12-31", "plants": ["Flow Station", "Rig (Drilling)", "Gas Plant", "Power Plant"]},
    # Add new clients here when they pay
    # Format: LICENSE-KEY : client name, expiry YYYY-MM-DD
}

# Master admin password to manage all
ADMIN_PASSWORD = "ChidoraAdmin2026!"

def check_license(license_key):
    license_key = license_key.strip().upper()
    if license_key == ADMIN_PASSWORD:
        return {"valid": True, "client": "ADMIN", "expiry": "2099-12-31", "plants": ["Flow Station", "Rig (Drilling)", "Gas Plant", "Power Plant"], "is_admin": True}
    
    if license_key in VALID_LICENSES:
        lic = VALID_LICENSES[license_key]
        try:
            expiry_date = datetime.strptime(lic["expiry"], "%Y-%m-%d")
            if datetime.now() > expiry_date:
                return {"valid": False, "reason": f"License expired on {lic['expiry']}. Contact Chidora to renew."}
            return {"valid": True, **lic}
        except:
            return {"valid": False, "reason": "Invalid expiry format"}
    return {"valid": False, "reason": "Invalid License Key. Contact Chidora to purchase."}

# ============ LOGIN SCREEN ============
st.set_page_config(page_title="MAINTAIN-AI SECURE", layout="wide", page_icon="🔒")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.client_info = None

if not st.session_state.authenticated:
    st.title("🔒 MAINTAIN-AI | Licensed Version")
    st.markdown("**Enter your License Key to access your plant maintenance system**")
    st.markdown("---")
    
    col1, col2 = st.columns([2,1])
    with col1:
        st.info("💡 No license? Contact Chidora: +234 [your number] | Email: [your email] | Demo Key: DEMO-12345")
        license_input = st.text_input("🔑 License Key:", type="password", placeholder="Enter your license key e.g., SPDC-FLOW-2026")
        
        if st.button("🔓 Unlock System", type="primary", use_container_width=True):
            result = check_license(license_input)
            if result["valid"]:
                st.session_state.authenticated = True
                st.session_state.client_info = result
                st.session_state.license_key = license_input.strip().upper()
                st.success(f"✅ Welcome {result['client']}! License valid till {result['expiry']}")
                st.balloons()
                st.rerun()
            else:
                st.error(f"❌ {result['reason']}")
    
    with col2:
        st.markdown("### Pricing:")
        st.markdown("""
        - **Flow Station**: ₦200k / year
        - **Rig**: ₦300k / year
        - **Gas Plant**: ₦300k / year
        - **Power Plant**: ₦400k / year
        - **All Plants**: ₦800k / year (Save ₦400k)
        
        Includes: PDF Work Orders, Auto-update, NUPRC Compliance
        
        **Contact to buy:**
        Chidora - MAINTAIN-AI
        """)
    st.stop()

# ============ AUTHENTICATED - MAIN APP ============
client_info = st.session_state.client_info
is_admin = client_info.get("is_admin", False)

# Header with license info
st.sidebar.success(f"🔓 Licensed: {client_info['client']}")
st.sidebar.caption(f"Key: {st.session_state.license_key[:6]}*** | Exp: {client_info['expiry']}")
if st.sidebar.button("🔒 Logout"):
    st.session_state.authenticated = False
    st.session_state.client_info = None
    st.rerun()

st.title(f"🏭 MAINTAIN-AI | {client_info['client']} - Licensed")
if is_admin:
    st.warning("🔧 ADMIN MODE - You can see all clients")
    st.markdown("**Active Licenses:**")
    for key, info in VALID_LICENSES.items():
        exp = datetime.strptime(info["expiry"], "%Y-%m-%d")
        days_left = (exp - datetime.now()).days
        status = "✅ Active" if days_left > 0 else "❌ Expired"
        st.caption(f"{key} | {info['client']} | Exp: {info['expiry']} | {days_left} days left | {status}")

st.markdown(f"**Plant Types Allowed:** {', '.join(client_info['plants'])} | **Expiry:** {client_info['expiry']}")

# Rest of your app (same as clean version but with plant restriction)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_files = [f for f in glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
xlsx_names = [os.path.basename(f) for f in xlsx_files]

PLANT_PROFILES = {
    "Flow Station": {
        "intervals": {"Separator Vessel": 180, "Crude Pump": 21, "Export Pump": 21, "Generator": 30, "Compressor": 30, "PSV": 365, "Default": 30},
        "compliance": "NUPRC Upstream + HSE PTW/LOTO + HSE-003",
        "critical": ["Export Pump", "Separator Vessel"],
        "icon": "🛢️"
    },
    "Rig (Drilling)": {
        "intervals": {"Top Drive": 14, "Mud Pump": 7, "Drawworks": 30, "BOP": 14, "Generator": 21, "Shaker": 21, "Crane": 90, "Default": 21},
        "compliance": "NUPRC + DPR Rig Safety + API + Well Control",
        "critical": ["BOP", "Mud Pump", "Top Drive"],
        "icon": "🏗️"
    },
    "Gas Plant": {
        "intervals": {"Gas Compressor": 30, "Dehydration Unit": 60, "Refrigeration": 90, "Flare System": 180, "Generator": 30, "Heat Exchanger": 90, "PSV": 180, "Default": 60},
        "compliance": "NUPRC Midstream + NMDPRA + Process Safety + PSSR",
        "critical": ["Gas Compressor", "Flare System", "Dehydration Unit"],
        "icon": "🔥"
    },
    "Power Plant": {
        "intervals": {"Gas Turbine": 90, "HRSG": 180, "Steam Turbine": 180, "BFP": 30, "Generator": 30, "Transformer": 180, "Cooling Tower": 90, "Default": 90},
        "compliance": "NERC + NUPRC + OEM Siemens/GE + Arc Flash",
        "critical": ["Gas Turbine", "BFP", "Steam Turbine"],
        "icon": "⚡"
    }
}

# Only allow plants this license permits
allowed_plants = client_info["plants"]
st.sidebar.header("🏭 Select Plant Type")
plant_type = st.sidebar.selectbox("Plant:", allowed_plants, index=0)
profile = PLANT_PROFILES[plant_type]

st.sidebar.header("🏢 Client Branding")
client_name = st.sidebar.text_input("Client Name", value=client_info["client"])
plant_location = st.sidebar.text_input("Plant Location", value="Bonny Terminal")
prepared_by = st.sidebar.text_input("Prepared By", value=f"{client_info['client']} - Maintenance")
logo_text = st.sidebar.text_input("Company Logo Text", value="MAINTAIN-AI")

st.sidebar.header("📁 Data Source")
data_source = st.sidebar.radio("Excel Source:", ["Use Excel in Folder", "Upload Company Excel"], index=0)

if data_source == "Upload Company Excel":
    uploaded_file = st.sidebar.file_uploader("📤 Upload Excel (.xlsx)", type=["xlsx","xls","csv"])
    if uploaded_file is None:
        st.info("👈 Upload company Excel file")
        st.stop()
    df = pd.read_excel(uploaded_file, engine='openpyxl') if not uploaded_file.name.endswith('.csv') else pd.read_csv(uploaded_file)
    full_path = None
    file_name_label = uploaded_file.name
else:
    if not xlsx_names:
        st.error("No Excel in folder. Add Sample Excel or use Upload")
        st.stop()
    selected = st.sidebar.selectbox("Log:", xlsx_names, index=0)
    full_path = os.path.join(SCRIPT_DIR, selected)
    file_name_label = selected
    df = pd.read_excel(full_path, engine='openpyxl')

st.sidebar.header("⚙️ Intervals")
intervals = {}
for asset_type, default_days in profile['intervals'].items():
    intervals[asset_type] = st.sidebar.number_input(f"{asset_type}", min_value=7, max_value=730, value=default_days, key=f"lic_{plant_type}_{asset_type}")

st.sidebar.header("🔄 Refresh")
import streamlit.components.v1 as components
auto_enabled = st.sidebar.toggle("Auto-refresh 10 mins", value=True)
interval_mins = st.sidebar.slider("Refresh mins", 1, 60, 10)
if auto_enabled:
    components.html(f"<script>setTimeout(()=>window.parent.location.reload(), {interval_mins*60*1000});</script>", height=0)
components.html("""<button onclick="window.parent.location.reload()" style="background:#FF4B4B;color:white;border:none;padding:10px 20px;border-radius:8px;font-weight:bold;width:100%;cursor:pointer;">🔄 Refresh Now</button>""", height=60)

# Process
df['Date'] = pd.to_datetime(df.get('Date', datetime.now()), dayfirst=True, errors='coerce')
df['Last Service'] = pd.to_datetime(df['Last Service'], dayfirst=True, errors='coerce')
df['Days Since Service'] = (datetime.now() - df['Last Service']).dt.days

def get_interval(equip):
    eq = str(equip).lower()
    for k,v in intervals.items():
        if k.lower() in eq or eq in k.lower(): return v
    if "mud" in eq and "pump" in eq: return intervals.get("Mud Pump", intervals["Default"])
    if "pump" in eq: return intervals.get("Crude Pump", 21)
    if "gen" in eq: return intervals.get("Generator", 30)
    if "comp" in eq: return intervals.get("Gas Compressor", 30)
    if "separ" in eq: return intervals.get("Separator Vessel", 180)
    return intervals["Default"]

def is_critical(equip):
    eq = str(equip).lower()
    for crit in profile['critical']:
        if crit.lower() in eq: return True
    return False

df['Interval_Days'] = df['Equipment'].apply(get_interval)
df['Days Overdue By'] = df['Days Since Service'] - df['Interval_Days']
df['Rule_Status'] = np.where(df['Days Overdue By'] > 0, 'OVERDUE', 'OK')
df['Next Service Due'] = df['Last Service'] + pd.to_timedelta(df['Interval_Days'], unit='D')
df['Is_Critical'] = df['Equipment'].apply(is_critical)

latest = df.sort_values('Last Service').drop_duplicates('Asset Tag', keep='last').copy()

def create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"<b>{logo_text} - WORK ORDER</b>", styles['Heading1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Client:</b> {client_name} | <b>Plant:</b> {plant_type} | <b>Location:</b> {plant_location}", styles['Normal']))
    story.append(Paragraph(f"<b>License:</b> {st.session_state.license_key[:6]}*** | <b>Valid till:</b> {client_info['expiry']}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')} | <b>WO:</b> WO-{row['Asset Tag']}", styles['Normal']))
    story.append(Spacer(1, 12))
    data = [
        ["Asset Tag", str(row['Asset Tag'])],
        ["Equipment", str(row['Equipment'])],
        ["Location", str(row.get('Location','N/A'))],
        ["Last Service", row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else "N/A"],
        ["Interval", f"{int(row['Interval_Days'])} days"],
        ["Days Since", f"{int(row['Days Since Service'])} days"],
        ["Overdue By", f"{int(row['Days Overdue By'])} days"],
        ["Next Due", row['Next Service Due'].strftime('%d/%m/%Y') if pd.notna(row['Next Service Due']) else "N/A"],
        ["Status", str(row['Rule_Status'])],
        ["Critical?", "YES" if row['Is_Critical'] else "No"],
        ["Compliance", profile['compliance']],
    ]
    t = Table(data, colWidths=[2.2*inch, 3.8*inch])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (0,-1), colors.HexColor('#E0E0E0')), ('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTSIZE', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
    story.append(t)
    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>Work Steps:</b>", styles['Heading2']))
    story.append(Paragraph(f"1. {profile['compliance']} - PTW + LOTO", styles['Normal']))
    story.append(Paragraph("2. Isolate + LOTO", styles['Normal']))
    story.append(Paragraph(f"3. Service per {int(row['Interval_Days'])}d checklist", styles['Normal']))
    story.append(Paragraph("4. Test run + leak test", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Licensed to {client_name} | Prepared: {prepared_by}", styles['Normal']))
    doc.build(story)
    buffer.seek(0)
    return buffer

st.header(f"{profile['icon']} {plant_type} - {len(latest)} Assets - Licensed to {client_info['client']}")
c1,c2,c3 = st.columns(3)
c1.metric("Total", len(latest))
c2.metric("🔴 Overdue", len(latest[latest['Rule_Status']=='OVERDUE']))
c3.metric("🟢 OK", len(latest[latest['Rule_Status']=='OK']))

st.dataframe(latest[['Asset Tag','Equipment','Last Service','Days Since Service','Interval_Days','Next Service Due','Days Overdue By','Rule_Status','Is_Critical','Location']].sort_values('Days Overdue By', ascending=False), use_container_width=True)

st.header(f"📝 Work Orders + PDF")
for _, row in latest.sort_values('Days Overdue By', ascending=False).iterrows():
    with st.container(border=True):
        col_a, col_b, col_c, col_d = st.columns([2.5,2,1,1])
        with col_a:
            emoji = "🔴" if row['Rule_Status']=='OVERDUE' else "🟢"
            crit = "🔥 CRITICAL" if row['Is_Critical'] else ""
            st.markdown(f"**{emoji} {row['Asset Tag']}** - {row['Equipment']} {crit}")
            st.caption(f"Last: {row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else 'N/A'} | Overdue: {int(row['Days Overdue By'])}d | Next: {row['Next Service Due'].strftime('%d/%m/%Y') if pd.notna(row['Next Service Due']) else 'N/A'}")
        with col_b:
            st.caption(f"{row.get('Location','N/A')} | {row['Rule_Status']} | {profile['compliance']}")
        with col_c:
            pdf_buf = create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text)
            st.download_button("📄 PDF", pdf_buf, file_name=f"WO_{row['Asset Tag']}.pdf", mime="application/pdf", key=f"pdf_{row['Asset Tag']}", use_container_width=True)
        with col_d:
            if st.button(f"✅ Serviced", key=f"serv_{row['Asset Tag']}", use_container_width=True):
                if full_path:
                    df_full = pd.read_excel(full_path, engine='openpyxl')
                    mask = df_full['Asset Tag'] == row['Asset Tag']
                    df_full.loc[mask, 'Last Service'] = datetime.now()
                    df_full.to_excel(full_path, index=False, engine='openpyxl')
                    st.success(f"✅ {row['Asset Tag']} updated!")
                    st.balloons()
                else:
                    st.info("Download updated Excel")

st.success(f"✅ Licensed to {client_info['client']} till {client_info['expiry']} | {len(latest)} assets")
