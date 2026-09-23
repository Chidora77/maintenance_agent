# app_final_CLIENT_INSTALL.py - FINAL VERSION: Auto-updates Excel, no manual editing needed
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os, glob
import numpy as np
from io import BytesIO

st.set_page_config(page_title="MAINTAIN-AI CLIENT INSTALL", layout="wide", page_icon="🏭")
st.title("🏭 MAINTAIN-AI | CLIENT INSTALL - Auto-Update + PDF")
st.markdown("**Company installs on their PC → Technician clicks 'Mark Serviced' → Excel auto-updates → No manual editing**")

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

st.sidebar.header("🏭 Plant Type")
plant_type = st.sidebar.selectbox("Plant:", list(PLANT_PROFILES.keys()), index=0)
profile = PLANT_PROFILES[plant_type]

st.sidebar.header("🏢 Client Branding")
client_name = st.sidebar.text_input("Client Name", value="SPDC")
plant_location = st.sidebar.text_input("Plant Location", value="Bonny Terminal")
prepared_by = st.sidebar.text_input("Prepared By", value="Maintenance Team")

# Data source selection
st.sidebar.header("📁 Data Source")
data_source = st.sidebar.radio("Choose:", ["Use Excel in Folder", "Upload Company Excel"], index=0)

if data_source == "Upload Company Excel":
    uploaded_file = st.sidebar.file_uploader("Upload Excel", type=["xlsx","xls"])
    if uploaded_file is None:
        st.info("👈 Upload Excel file to start")
        st.stop()
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    full_path = None
else:
    if not xlsx_names:
        st.error("No Excel in folder. Upload one or add Sample-Maintenance-Log-20-Assets-FIXED.xlsx to folder")
        st.stop()
    selected = st.sidebar.selectbox("Select Log:", xlsx_names, index=0)
    full_path = os.path.join(SCRIPT_DIR, selected)
    df = pd.read_excel(full_path, engine='openpyxl')

st.sidebar.header("⚙️ Intervals")
intervals = {}
for asset_type, default_days in profile['intervals'].items():
    intervals[asset_type] = st.sidebar.number_input(f"{asset_type}", min_value=7, max_value=730, value=default_days, key=f"final_{plant_type}_{asset_type}")

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

def create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"<b>MAINTAIN-AI - WORK ORDER</b>", styles['Heading1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Client:</b> {client_name} | <b>Plant:</b> {plant_type} | <b>Location:</b> {plant_location}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')} | <b>WO:</b> WO-{row['Asset Tag']}-{datetime.now().strftime('%Y%m%d')}", styles['Normal']))
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
    story.append(Paragraph("5. Update Last Service = TODAY", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Prepared: {prepared_by} | Approved: __________", styles['Normal']))
    doc.build(story)
    buffer.seek(0)
    return buffer

# Dashboard
st.header(f"{profile['icon']} {plant_type} - {len(latest)} Assets")
c1,c2,c3 = st.columns(3)
c1.metric("Total", len(latest))
c2.metric("🔴 Overdue", len(latest[latest['Rule_Status']=='OVERDUE']))
c3.metric("🟢 OK", len(latest[latest['Rule_Status']=='OK']))

st.subheader("📊 All Assets")
st.dataframe(latest[['Asset Tag','Equipment','Last Service','Days Since Service','Interval_Days','Next Service Due','Days Overdue By','Rule_Status','Is_Critical','Location']].sort_values('Days Overdue By', ascending=False), use_container_width=True)

# WORK ORDERS WITH AUTO-UPDATE
st.header(f"📝 Work Orders + PDF + Auto-Update - {plant_type}")
st.info("💡 After fixing asset, click '✅ Mark as Serviced TODAY' - Excel auto-updates, no manual editing needed! | 📄 Download PDF for PTW")

for _, row in latest.sort_values('Days Overdue By', ascending=False).iterrows():
    with st.container(border=True):
        col_a, col_b, col_c, col_d = st.columns([2,2,1,1])
        with col_a:
            emoji = "🔴" if row['Rule_Status']=='OVERDUE' else "🟢"
            crit = "🔥 CRITICAL" if row['Is_Critical'] else ""
            st.markdown(f"**{emoji} {row['Asset Tag']}** - {row['Equipment']} {crit}")
            st.caption(f"Last: {row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else 'N/A'} | Since: {int(row['Days Since Service'])}d | Int: {int(row['Interval_Days'])}d | Overdue: {int(row['Days Overdue By'])}d | Next: {row['Next Service Due'].strftime('%d/%m/%Y') if pd.notna(row['Next Service Due']) else 'N/A'}")
        with col_b:
            st.caption(f"Loc: {row.get('Location','N/A')} | Status: {row['Rule_Status']} | {profile['compliance']}")
        with col_c:
            pdf_buf = create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by)
            st.download_button("📄 PDF", pdf_buf, file_name=f"WO_{row['Asset Tag']}.pdf", mime="application/pdf", key=f"pdf_{row['Asset Tag']}", use_container_width=True)
        with col_d:
            # AUTO-UPDATE BUTTON - This updates Excel automatically!
            if st.button(f"✅ Serviced", key=f"serviced_{row['Asset Tag']}", use_container_width=True):
                if full_path:
                    # Update the Excel file directly
                    df_full = pd.read_excel(full_path, engine='openpyxl')
                    # Update Last Service for this Asset Tag to TODAY
                    mask = df_full['Asset Tag'] == row['Asset Tag']
                    df_full.loc[mask, 'Last Service'] = datetime.now()
                    # Also update Date column
                    if 'Date' in df_full.columns:
                        df_full.loc[mask, 'Date'] = datetime.now()
                    df_full.to_excel(full_path, index=False, engine='openpyxl')
                    st.success(f"✅ {row['Asset Tag']} marked serviced TODAY ({datetime.now().strftime('%d/%m/%Y')}) - Excel updated! Refresh page.")
                    st.balloons()
                else:
                    st.warning("⚠️ Uploaded file mode - Download updated Excel below and replace your file")
                    df_updated = df.copy()
                    mask = df_updated['Asset Tag'] == row['Asset Tag']
                    df_updated.loc[mask, 'Last Service'] = datetime.now()
                    buf = BytesIO()
                    df_updated.to_excel(buf, index=False, engine='openpyxl')
                    buf.seek(0)
                    st.download_button("⬇️ Download Updated Excel", buf, file_name=f"Updated_{plant_type}_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_{row['Asset Tag']}")

st.markdown("---")
st.subheader("💾 Installation Options for Company")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **Option A: Cloud (Easiest - No Install)**
    1. Share your Streamlit link: `https://maintenanceagent-...streamlit.app/`
    2. Company opens link on any PC/phone
    3. They upload Excel or use existing
    4. They download PDFs
    5. **Pros:** No install, works anywhere, you manage updates
    6. **Cons:** Needs internet
    """)
with col2:
    st.markdown("""
    **Option B: Install on Company PC (Offline)**
    1. Copy folder `maintenance_agent` to their PC
    2. Install Python + run: `pip install -r requirements.txt`
    3. Run: `streamlit run app_final_CLIENT_INSTALL.py`
    4. Opens at `http://localhost:8501`
    5. **Pros:** Works offline, data stays in company, auto-updates Excel
    6. **Cons:** You need to visit to install
    """)

# Download updated full Excel
if full_path:
    st.markdown("---")
    buf_all = BytesIO()
    df.to_excel(buf_all, index=False, engine='openpyxl')
    buf_all.seek(0)
    st.download_button("⬇️ Download Current Full Excel (Backup)", buf_all, file_name=f"Backup_{plant_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
