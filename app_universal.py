# app_final_CLEAN.py - CLEAN FINAL: Upload + Refresh buttons + PDF + No install text
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os, glob
import numpy as np
from io import BytesIO

st.set_page_config(page_title="MAINTAIN-AI UNIVERSAL PDF", layout="wide", page_icon="🏭")
st.title("🏭 MAINTAIN-AI | UNIVERSAL + PDF Work Order")
st.markdown("**Flow Station | Rig | Gas Plant | Power Plant → Auto intervals 21/30/180 + PDF + Auto-update**")

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

# Sidebar
st.sidebar.header("🏭 Select Plant Type")
plant_type = st.sidebar.selectbox("Plant:", list(PLANT_PROFILES.keys()), index=0)
profile = PLANT_PROFILES[plant_type]

st.sidebar.header("🏢 Client Branding")
client_name = st.sidebar.text_input("Client Name", value="SPDC")
plant_location = st.sidebar.text_input("Plant Location", value="Bonny Terminal")
prepared_by = st.sidebar.text_input("Prepared By", value="Chidora - MAINTAIN-AI")
logo_text = st.sidebar.text_input("Company Logo Text", value="MAINTAIN-AI")

st.sidebar.header("📁 Data Source")
data_source = st.sidebar.radio("Excel Source:", ["Use Excel in Folder", "Upload Company Excel"], index=0)

if data_source == "Upload Company Excel":
    uploaded_file = st.sidebar.file_uploader("📤 Upload Excel (.xlsx)", type=["xlsx","xls","csv"])
    if uploaded_file is None:
        st.info("👈 Sidebar → Select 'Upload Company Excel' → Drag your company Excel file. Template columns: Asset Tag, Equipment, Last Service, Location, Failure, Date")
        # Sample template
        sample_df = pd.DataFrame({
            "Asset Tag": ["PUMP-101", "GEN-01", "SEP-001"],
            "Equipment": ["Sulzer Crude Pump", "Caterpillar 3512B Generator", "Separator Vessel"],
            "Date": ["01/09/2026", "02/09/2026", "03/09/2026"],
            "Last Service": ["15/08/2026", "01/08/2026", "01/03/2026"],
            "Failure": ["Bearing hot", "Low voltage", "Level issue"],
            "Location": ["Bonny", "Bonny", "Forcados"]
        })
        buf = BytesIO()
        sample_df.to_excel(buf, index=False, engine='openpyxl')
        buf.seek(0)
        st.download_button("📥 Download Template Excel", buf, file_name="Template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.stop()
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl') if not uploaded_file.name.endswith('.csv') else pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Read error: {e}")
        st.stop()
    full_path = None
    file_name_label = uploaded_file.name
else:
    if not xlsx_names:
        st.error("No Excel in folder. Add Sample-Maintenance-Log-20-Assets-FIXED.xlsx or switch to Upload Company Excel")
        st.stop()
    selected = st.sidebar.selectbox("Log:", xlsx_names, index=0)
    full_path = os.path.join(SCRIPT_DIR, selected)
    file_name_label = selected
    df = pd.read_excel(full_path, engine='openpyxl')

st.sidebar.header("⚙️ Intervals (days) 21/30/180")
intervals = {}
for asset_type, default_days in profile['intervals'].items():
    intervals[asset_type] = st.sidebar.number_input(f"{asset_type}", min_value=7, max_value=730, value=default_days, key=f"clean_{plant_type}_{asset_type}")

st.sidebar.header("🔄 Refresh")
import streamlit.components.v1 as components
auto_enabled = st.sidebar.toggle("Auto-refresh 10 mins", value=True)
interval_mins = st.sidebar.slider("Refresh interval (mins)", 1, 60, 10)
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
    if "separ" in eq or "vessel" in eq: return intervals.get("Separator Vessel", 180)
    if "gas" in eq and "turbine" in eq: return intervals.get("Gas Turbine", 90)
    if "turbine" in eq: return intervals.get("Steam Turbine", 180)
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
    try:
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
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>WO:</b> WO-{plant_type[:4].upper()}-{datetime.now().year}-{row['Asset Tag']}", styles['Normal']))
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
        story.append(Paragraph("2. Isolate, depressurize, LOTO per OEM", styles['Normal']))
        story.append(Paragraph(f"3. Service per {int(row['Interval_Days'])}d checklist", styles['Normal']))
        story.append(Paragraph("4. Test run + leak test", styles['Normal']))
        story.append(Paragraph("5. Update Last Service = TODAY + sign-off", styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Prepared: {prepared_by} | Approved: __________", styles['Normal']))
        story.append(Paragraph(f"Cost: ₦435k planned vs ₦2M failure | {logo_text} {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF error: {e} - Ensure reportlab in requirements.txt")
        return None

# Dashboard
st.header(f"{profile['icon']} {plant_type} Dashboard - {profile['compliance']}")
st.caption(f"File: {file_name_label} | Client: {client_name} | Location: {plant_location}")

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Assets", len(latest))
c2.metric("🔴 Overdue", len(latest[latest['Rule_Status']=='OVERDUE']))
c3.metric("🟢 OK", len(latest[latest['Rule_Status']=='OK']))
c4.metric(f"🔥 Critical {plant_type}", len(latest[(latest['Is_Critical']) & (latest['Rule_Status']=='OVERDUE')]))
c5.metric("⚠️ Due 7 days", len(latest[(latest['Days Overdue By'] >= -7) & (latest['Days Overdue By'] <= 0)]))

st.subheader("📊 Filtered Asset Table - All Fields")
view_mode = st.radio("View:", ["All Assets", f"Only {plant_type} Critical Assets", "Overdue Only", "OK / Maintained"], horizontal=True)
if view_mode == f"Only {plant_type} Critical Assets":
    display_df = latest[latest['Is_Critical']]
elif view_mode == "Overdue Only":
    display_df = latest[latest['Rule_Status']=='OVERDUE']
elif view_mode == "OK / Maintained":
    display_df = latest[latest['Rule_Status']=='OK']
else:
    display_df = latest

show_cols = ['Asset Tag','Equipment','Last Service','Days Since Service','Interval_Days','Next Service Due','Days Overdue By','Rule_Status','Is_Critical','Location']
available_cols = [c for c in show_cols if c in display_df.columns]
st.dataframe(display_df[available_cols].sort_values('Days Overdue By', ascending=False), use_container_width=True, height=350)

st.header(f"📝 Work Orders + PDF + Auto-Update - {plant_type}")
st.caption("Click 📄 Download PDF for PTW | Click ✅ Serviced TODAY after maintenance to auto-update Excel")

for _, row in latest.sort_values('Days Overdue By', ascending=False).iterrows():
    with st.container(border=True):
        col_a, col_b, col_c, col_d = st.columns([2.5,2,1,1])
        with col_a:
            emoji = "🔴" if row['Rule_Status']=='OVERDUE' else "🟢"
            crit = "🔥 CRITICAL" if row['Is_Critical'] else ""
            st.markdown(f"**{emoji} {row['Asset Tag']}** - {row['Equipment']} {crit}")
            st.caption(f"Last: {row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else 'N/A'} | Since: {int(row['Days Since Service'])}d | Int: {int(row['Interval_Days'])}d | Overdue: {int(row['Days Overdue By'])}d | Next: {row['Next Service Due'].strftime('%d/%m/%Y') if pd.notna(row['Next Service Due']) else 'N/A'}")
        with col_b:
            st.caption(f"Location: {row.get('Location','N/A')} | Status: {row['Rule_Status']} | Critical: {'YES' if row['Is_Critical'] else 'No'}")
            st.caption(f"Compliance: {profile['compliance']}")
        with col_c:
            pdf_buf = create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text)
            if pdf_buf:
                st.download_button("📄 PDF", pdf_buf, file_name=f"WO_{row['Asset Tag']}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", key=f"pdf_{row['Asset Tag']}_{plant_type}", use_container_width=True)
        with col_d:
            if st.button(f"✅ Serviced", key=f"serv_{row['Asset Tag']}_{plant_type}", use_container_width=True):
                if full_path:
                    try:
                        df_full = pd.read_excel(full_path, engine='openpyxl')
                        mask = df_full['Asset Tag'] == row['Asset Tag']
                        df_full.loc[mask, 'Last Service'] = datetime.now()
                        if 'Date' in df_full.columns:
                            df_full.loc[mask, 'Date'] = datetime.now()
                        df_full.to_excel(full_path, index=False, engine='openpyxl')
                        st.success(f"✅ {row['Asset Tag']} marked TODAY - Excel updated!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Update failed: {e}")
                else:
                    df_updated = df.copy()
                    mask = df_updated['Asset Tag'] == row['Asset Tag']
                    df_updated.loc[mask, 'Last Service'] = datetime.now()
                    buf = BytesIO()
                    df_updated.to_excel(buf, index=False, engine='openpyxl')
                    buf.seek(0)
                    st.download_button("⬇️ Download Updated Excel", buf, file_name=f"Updated_{row['Asset Tag']}_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_{row['Asset Tag']}_{plant_type}")

st.success(f"✅ {plant_type} Active: {len(latest)} assets | Overdue {len(latest[latest['Rule_Status']=='OVERDUE'])} | File: {file_name_label} | {profile['compliance']}")
