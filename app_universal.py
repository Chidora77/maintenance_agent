# app_universal_COMPLETE.py - FINAL: Full Tables + Hybrid + PDF + All Plant Types
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os, glob
import numpy as np
from io import BytesIO

st.set_page_config(page_title="MAINTAIN-AI UNIVERSAL COMPLETE", layout="wide", page_icon="🏭")
st.title("🏭 MAINTAIN-AI | UNIVERSAL + PDF Work Order (COMPLETE)")
st.markdown("**Flow Station | Rig | Gas Plant | Power Plant → Full Dashboard + Hybrid AI + PDF**")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_files = [f for f in glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
xlsx_names = [os.path.basename(f) for f in xlsx_files]

if not xlsx_names:
    st.error("No Excel found - Upload Sample-Maintenance-Log-20-Assets-FIXED.xlsx")
    st.stop()

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

st.sidebar.header("🏢 Client Branding for PDF")
client_name = st.sidebar.text_input("Client Name", value="SPDC")
plant_location = st.sidebar.text_input("Plant Location", value="Bonny Terminal")
prepared_by = st.sidebar.text_input("Prepared By", value="Chidora - MAINTAIN-AI")
logo_text = st.sidebar.text_input("Company Logo Text", value="MAINTAIN-AI")

selected = st.sidebar.selectbox("Log:", xlsx_names, index=0)
full_path = os.path.join(SCRIPT_DIR, selected)

st.sidebar.header("⚙️ Intervals (days) - Edit 21/30/180")
intervals = {}
for asset_type, default_days in profile['intervals'].items():
    intervals[asset_type] = st.sidebar.number_input(f"{asset_type}", min_value=7, max_value=730, value=default_days, key=f"complete_{plant_type}_{asset_type}")

st.sidebar.header("🔄 Refresh")
import streamlit.components.v1 as components
auto_enabled = st.sidebar.toggle("Auto-refresh 10 mins", value=False)
if auto_enabled:
    components.html(f"<script>setTimeout(()=>window.parent.location.reload(), {600*1000});</script>", height=0)
components.html("""<button onclick="window.parent.location.reload()" style="background:#FF4B4B;color:white;border:none;padding:10px 20px;border-radius:8px;font-weight:bold;width:100%;cursor:pointer;">🔄 Refresh Now</button>""", height=60)

# Load
try:
    df = pd.read_excel(full_path, engine='openpyxl')
except Exception as e:
    st.error(f"Read error: {e}")
    st.stop()

df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
df['Last Service'] = pd.to_datetime(df['Last Service'], dayfirst=True, errors='coerce')
df['Days Since Service'] = (datetime.now() - df['Last Service']).dt.days

def get_interval(equip):
    eq = str(equip).lower()
    for k,v in intervals.items():
        if k.lower() in eq or eq in k.lower():
            return v
    if "pump" in eq and "mud" in eq: return intervals.get("Mud Pump", intervals["Default"])
    if "pump" in eq: return intervals.get("Crude Pump", intervals.get("Export Pump", 21))
    if "gen" in eq: return intervals.get("Generator", 30)
    if "comp" in eq: return intervals.get("Gas Compressor", intervals.get("Compressor", 30))
    if "separ" in eq or "vessel" in eq: return intervals.get("Separator Vessel", 180)
    if "turbine" in eq and "gas" in eq: return intervals.get("Gas Turbine", 90)
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

# AI predictions
predictions = {}
for asset in df['Asset Tag'].unique():
    adf = df[df['Asset Tag']==asset].sort_values('Date')
    if len(adf) >= 2:
        diffs = adf['Date'].diff().dt.days.dropna()
        mtbf = diffs.mean() if len(diffs)>0 else 30
        if np.isnan(mtbf): mtbf = 30
        last = adf['Date'].max()
        next_pred = last + timedelta(days=mtbf)
        days_left = (next_pred - datetime.now()).days
        predictions[asset] = {'MTBF': round(mtbf,1), 'Next': next_pred.strftime('%d/%m/%Y'), 'DaysLeft': days_left, 'Risk': 'HIGH' if days_left < 7 else 'MEDIUM' if days_left < 30 else 'LOW'}

latest = df.sort_values('Last Service').drop_duplicates('Asset Tag', keep='last').copy()

# PDF function
def create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text, ai_info):
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
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>WO No:</b> WO-{plant_type[:4].upper()}-{datetime.now().year}-{row['Asset Tag']}", styles['Normal']))
        story.append(Spacer(1, 12))
        data = [
            ["Asset Tag", str(row['Asset Tag'])],
            ["Equipment", str(row['Equipment'])],
            ["Location", str(row.get('Location','N/A'))],
            ["Last Service", row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else "N/A"],
            ["Days Since Service", f"{int(row['Days Since Service'])} days"],
            ["Maintenance Interval", f"{int(row['Interval_Days'])} days"],
            ["Days Overdue By", f"{int(row['Days Overdue By'])} days"],
            ["Next Service Due", row['Next Service Due'].strftime('%d/%m/%Y') if pd.notna(row['Next Service Due']) else "N/A"],
            ["Rule Status", str(row['Rule_Status'])],
            ["Critical Asset?", "YES - Shutdown Risk" if row['Is_Critical'] else "No"],
            ["Compliance", profile['compliance']],
            ["AI MTBF", f"{ai_info.get('MTBF','N/A')} days"],
            ["AI Risk", ai_info.get('Risk','N/A')],
            ["AI Days to Failure", f"{ai_info.get('DaysLeft','N/A')} days"],
        ]
        t = Table(data, colWidths=[2.2*inch, 3.8*inch])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (0,-1), colors.HexColor('#E0E0E0')), ('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTSIZE', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
        story.append(t)
        story.append(Spacer(1, 16))
        story.append(Paragraph("<b>Work Steps:</b>", styles['Heading2']))
        story.append(Paragraph(f"1. {profile['compliance']} - PTW + LOTO + HSE", styles['Normal']))
        story.append(Paragraph("2. Isolate, depressurize, LOTO per OEM", styles['Normal']))
        story.append(Paragraph(f"3. Service per {plant_type} checklist - {int(row['Interval_Days'])}d interval", styles['Normal']))
        story.append(Paragraph("4. Vibration + oil analysis + thermography", styles['Normal']))
        story.append(Paragraph("5. Test run + leak test + functional test", styles['Normal']))
        story.append(Paragraph("6. Update Last Service = TODAY in Excel + sign-off", styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<b>Cost:</b> ₦435k planned vs ₦2M unplanned | <b>Downtime:</b> 6 hrs vs 24 hrs", styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Prepared By:</b> {prepared_by} | <b>Approved By:</b> ________________ | <b>Date:</b> __________", styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<i>Generated by {logo_text} Universal - {plant_type} - NUPRC Compliant - {datetime.now().strftime('%d/%m/%Y')}</i>", styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF error: {e} - Add reportlab to requirements.txt")
        return None

# ============ SECTION 1: DASHBOARD ============
st.header(f"{profile['icon']} {plant_type} Dashboard - {profile['compliance']}")
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Assets", len(latest))
c2.metric("🔴 Overdue", len(latest[latest['Rule_Status']=='OVERDUE']))
c3.metric("🟢 OK", len(latest[latest['Rule_Status']=='OK']))
c4.metric(f"🔥 Critical {plant_type}", len(latest[(latest['Is_Critical']) & (latest['Rule_Status']=='OVERDUE')]))
c5.metric("⚠️ Due 7 days", len(latest[(latest['Days Overdue By'] >= -7) & (latest['Days Overdue By'] <= 0)]))

# ============ SECTION 2: FILTERED TABLE (Previous code you liked) ============
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
st.dataframe(display_df[available_cols].sort_values('Days Overdue By', ascending=False), use_container_width=True, height=400)

# ============ SECTION 3: HYBRID DECISION (Previous code) ============
st.header(f"🔀 Hybrid Decision for {plant_type}")
hybrid_rows = []
for asset in df['Asset Tag'].unique():
    latest_row = df[df['Asset Tag']==asset].sort_values('Last Service').iloc[-1]
    interval = get_interval(latest_row['Equipment'])
    days_since = latest_row['Days Since Service']
    rule_status = 'OVERDUE' if days_since > interval else 'OK'
    critical_flag = is_critical(latest_row['Equipment'])
    ai = predictions.get(asset, {})
    ai_risk = ai.get('Risk','N/A')
    if rule_status=='OVERDUE' and critical_flag and ai_risk=='HIGH':
        decision = "🚨 CRITICAL - Shutdown Risk"
        priority = 1
    elif rule_status=='OVERDUE' and critical_flag:
        decision = f"🔥 CRITICAL {plant_type} - Service NOW"
        priority = 1
    elif rule_status=='OVERDUE':
        decision = f"⚠️ OVERDUE - {interval}d interval"
        priority = 2
    elif ai_risk=='HIGH':
        decision = "🤖 PREDICTIVE - Fail <7 days"
        priority = 2
    else:
        decision = "✅ OK"
        priority = 4
    hybrid_rows.append({
        "Asset Tag": asset,
        "Equipment": latest_row['Equipment'],
        "Plant Type": plant_type,
        "Last Service": latest_row['Last Service'].strftime('%d/%m/%Y') if pd.notna(latest_row['Last Service']) else "N/A",
        "Days Since": days_since,
        "Interval": interval,
        "Critical?": "YES" if critical_flag else "No",
        "Rule": rule_status,
        "AI Risk": ai_risk,
        "AI MTBF": ai.get('MTBF','N/A'),
        "Decision": decision,
        "Priority": priority,
        "Location": latest_row.get('Location','')
    })
hybrid_df = pd.DataFrame(hybrid_rows).sort_values("Priority")
st.dataframe(hybrid_df, use_container_width=True, height=400)

# ============ SECTION 4: PDF DOWNLOAD (New) ============
st.header(f"📝 Work Orders + PDF Download - {plant_type}")
st.caption("Each asset below has PDF button + detailed info. Branded with Client Name / Location / Compliance")

for _, row in latest.sort_values('Days Overdue By', ascending=False).iterrows():
    ai_info = predictions.get(row['Asset Tag'], {})
    with st.container(border=True):
        col_a, col_b, col_c = st.columns([2.5,2.5,1])
        with col_a:
            status_emoji = "🔴" if row['Rule_Status']=='OVERDUE' else "🟢"
            crit = "🔥 CRITICAL" if row['Is_Critical'] else ""
            st.markdown(f"**{status_emoji} {row['Asset Tag']}** - {row['Equipment']} {crit}")
            st.caption(f"Last: {row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else 'N/A'} | Since: {int(row['Days Since Service'])}d | Interval: {int(row['Interval_Days'])}d | Overdue: {int(row['Days Overdue By'])}d")
            st.caption(f"Next Due: {row['Next Service Due'].strftime('%d/%m/%Y') if pd.notna(row['Next Service Due']) else 'N/A'} | AI MTBF: {ai_info.get('MTBF','N/A')}d | AI Risk: {ai_info.get('Risk','N/A')}")
        with col_b:
            st.caption(f"Location: {row.get('Location','N/A')} | Status: {row['Rule_Status']} | Critical: {'YES' if row['Is_Critical'] else 'No'}")
            st.caption(f"Compliance: {profile['compliance']}")
            st.caption(f"Client: {client_name} | Plant: {plant_type} | {plant_location}")
        with col_c:
            pdf_buf = create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text, ai_info)
            if pdf_buf:
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_buf,
                    file_name=f"WO_{row['Asset Tag']}_{plant_type.replace(' ','')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key=f"pdf_complete_{row['Asset Tag']}_{plant_type}",
                    use_container_width=True
                )

st.success(f"✅ COMPLETE ACTIVE - Full Dashboard + Hybrid AI + PDF - {plant_type} | {profile['compliance']} | Client: {client_name}")
st.caption(f"File: {selected} | Branding: {logo_text} | {plant_location} | Refresh: {datetime.now().strftime('%H:%M:%S')}")
