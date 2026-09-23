# app_universal_pdf_FIXED.py - FIXED: Single clear PDF option for all assets
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os, glob
import numpy as np
from io import BytesIO

st.set_page_config(page_title="MAINTAIN-AI UNIVERSAL PDF", layout="wide", page_icon="🏭")
st.title("🏭 MAINTAIN-AI | UNIVERSAL + PDF Work Order (FIXED)")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_files = [f for f in glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
xlsx_names = [os.path.basename(f) for f in xlsx_files]

if not xlsx_names:
    st.error("No Excel found")
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

st.sidebar.header("🏭 Select Plant Type")
plant_type = st.sidebar.selectbox("Plant:", list(PLANT_PROFILES.keys()), index=0)
profile = PLANT_PROFILES[plant_type]

st.sidebar.header("🏢 Client Branding")
client_name = st.sidebar.text_input("Client Name", value="SPDC")
plant_location = st.sidebar.text_input("Plant Location", value="Bonny Terminal")
prepared_by = st.sidebar.text_input("Prepared By", value="Chidora - MAINTAIN-AI")
logo_text = st.sidebar.text_input("Company Logo Text", value="MAINTAIN-AI")

selected = st.sidebar.selectbox("Log:", xlsx_names, index=0)
full_path = os.path.join(SCRIPT_DIR, selected)

st.sidebar.header("⚙️ Intervals (days)")
intervals = {}
for asset_type, default_days in profile['intervals'].items():
    intervals[asset_type] = st.sidebar.number_input(f"{asset_type}", min_value=7, max_value=730, value=default_days, key=f"int_fix_{plant_type}_{asset_type}")

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
    if "pump" in eq and "mud" in eq:
        return intervals.get("Mud Pump", intervals["Default"])
    if "pump" in eq:
        return intervals.get("Crude Pump", intervals.get("Export Pump", 21))
    if "gen" in eq:
        return intervals.get("Generator", 30)
    if "comp" in eq:
        return intervals.get("Gas Compressor", intervals.get("Compressor", 30))
    if "separ" in eq:
        return intervals.get("Separator Vessel", 180)
    if "turbine" in eq and "gas" in eq:
        return intervals.get("Gas Turbine", 90)
    return intervals["Default"]

def is_critical(equip):
    eq = str(equip).lower()
    for crit in profile['critical']:
        if crit.lower() in eq:
            return True
    return False

df['Interval_Days'] = df['Equipment'].apply(get_interval)
df['Days Overdue By'] = df['Days Since Service'] - df['Interval_Days']
df['Rule_Status'] = np.where(df['Days Overdue By'] > 0, 'OVERDUE', 'OK')
df['Next Service Due'] = df['Last Service'] + pd.to_timedelta(df['Interval_Days'], unit='D')
df['Is_Critical'] = df['Equipment'].apply(is_critical)

latest = df.sort_values('Last Service').drop_duplicates('Asset Tag', keep='last').copy()

# --- PDF FUNCTION (SINGLE OPTION) ---
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
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')} | <b>WO No:</b> WO-{plant_type[:4].upper()}-{datetime.now().year}-{row['Asset Tag']}", styles['Normal']))
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
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#E0E0E0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))
        story.append(Paragraph("<b>Work Steps:</b>", styles['Heading2']))
        story.append(Paragraph(f"1. {profile['compliance']} - PTW + LOTO", styles['Normal']))
        story.append(Paragraph("2. Isolate, depressurize, LOTO per OEM", styles['Normal']))
        story.append(Paragraph("3. Service: Replace bearing/seal/filter as per 21/30 day checklist", styles['Normal']))
        story.append(Paragraph("4. Test run + leak test", styles['Normal']))
        story.append(Paragraph("5. Update Last Service = TODAY in Excel + sign-off", styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Prepared By: {prepared_by} | Approved: __________", styles['Normal']))
        story.append(Paragraph(f"Cost: ₦435k planned vs ₦2M failure | Generated by {logo_text} {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF library error: {e}. Make sure reportlab is in requirements.txt and reboot app.")
        return None

# Dashboard
st.header(f"{profile['icon']} {plant_type} - {len(latest)} Assets")
c1,c2,c3 = st.columns(3)
c1.metric("Total", len(latest))
c2.metric("🔴 Overdue", len(latest[latest['Rule_Status']=='OVERDUE']))
c3.metric("🟢 OK", len(latest[latest['Rule_Status']=='OK']))

st.subheader("📋 All Assets with PDF Download")

# Show table with PDF button for EACH asset (not just overdue) - FIXED
for _, row in latest.sort_values('Days Overdue By', ascending=False).iterrows():
    with st.container(border=True):
        col_a, col_b, col_c = st.columns([2,2,1])
        with col_a:
            status_emoji = "🔴" if row['Rule_Status']=='OVERDUE' else "🟢"
            crit = "🔥 CRITICAL" if row['Is_Critical'] else ""
            st.markdown(f"**{status_emoji} {row['Asset Tag']}** - {row['Equipment']} {crit}")
            st.caption(f"Last: {row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else 'N/A'} | Since: {int(row['Days Since Service'])}d | Interval: {int(row['Interval_Days'])}d | Overdue: {int(row['Days Overdue By'])}d | Next Due: {row['Next Service Due'].strftime('%d/%m/%Y') if pd.notna(row['Next Service Due']) else 'N/A'}")
        with col_b:
            st.caption(f"Location: {row.get('Location','N/A')} | Status: {row['Rule_Status']}")
            st.caption(f"Compliance: {profile['compliance']}")
        with col_c:
            pdf_buf = create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text)
            if pdf_buf:
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_buf,
                    file_name=f"WO_{row['Asset Tag']}_{plant_type.replace(' ','')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{row['Asset Tag']}_{plant_type}",
                    use_container_width=True
                )

st.info("💡 Each asset now has ONE clear 'Download PDF' button - works for OK and Overdue. After maintenance, update Last Service in Excel to TODAY and refresh.")
