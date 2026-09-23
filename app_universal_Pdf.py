# app_universal_pdf.py - Universal + PDF Work Order Generator
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os, glob
import numpy as np
from io import BytesIO

st.set_page_config(page_title="MAINTAIN-AI UNIVERSAL + PDF", layout="wide", page_icon="🏭")
st.title("🏭 MAINTAIN-AI | UNIVERSAL + PDF Work Order")
st.markdown("**Flow Station | Rig | Gas Plant | Power Plant → Generate Branded PDF Work Orders**")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_files = [f for f in glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
xlsx_names = [os.path.basename(f) for f in xlsx_files]

if not xlsx_names:
    st.error("No Excel found")
    st.stop()

# --- PLANT PROFILES ---
PLANT_PROFILES = {
    "Flow Station": {
        "assets": ["Separator Vessel", "Crude Pump", "Export Pump", "Generator", "Compressor", "PSV"],
        "intervals": {"Separator Vessel": 180, "Crude Pump": 21, "Export Pump": 21, "Generator": 30, "Compressor": 30, "PSV": 365, "Default": 30},
        "compliance": "NUPRC Upstream + HSE PTW/LOTO + HSE-003",
        "critical": ["Export Pump", "Separator Vessel"],
        "icon": "🛢️"
    },
    "Rig (Drilling)": {
        "assets": ["Top Drive", "Mud Pump", "Drawworks", "BOP", "Generator", "Shaker", "Crane"],
        "intervals": {"Top Drive": 14, "Mud Pump": 7, "Drawworks": 30, "BOP": 14, "Generator": 21, "Shaker": 21, "Crane": 90, "Default": 21},
        "compliance": "NUPRC + DPR Rig Safety + API + Well Control",
        "critical": ["BOP", "Mud Pump", "Top Drive"],
        "icon": "🏗️"
    },
    "Gas Plant": {
        "assets": ["Gas Compressor", "Dehydration Unit", "Refrigeration", "Flare System", "Generator", "Heat Exchanger", "PSV"],
        "intervals": {"Gas Compressor": 30, "Dehydration Unit": 60, "Refrigeration": 90, "Flare System": 180, "Generator": 30, "Heat Exchanger": 90, "PSV": 180, "Default": 60},
        "compliance": "NUPRC Midstream + NMDPRA + Process Safety + PSSR",
        "critical": ["Gas Compressor", "Flare System", "Dehydration Unit"],
        "icon": "🔥"
    },
    "Power Plant": {
        "assets": ["Gas Turbine", "HRSG", "Steam Turbine", "BFP", "Generator", "Transformer", "Cooling Tower"],
        "intervals": {"Gas Turbine": 90, "HRSG": 180, "Steam Turbine": 180, "BFP": 30, "Generator": 30, "Transformer": 180, "Cooling Tower": 90, "Default": 90},
        "compliance": "NERC + NUPRC + OEM Siemens/GE + Arc Flash",
        "critical": ["Gas Turbine", "BFP", "Steam Turbine"],
        "icon": "⚡"
    }
}

# Sidebar - Plant + Branding
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

st.sidebar.header("⚙️ Intervals (days)")
intervals = {}
for asset_type, default_days in profile['intervals'].items():
    intervals[asset_type] = st.sidebar.number_input(f"{asset_type}", min_value=7, max_value=730, value=default_days, key=f"int_pdf_{plant_type}_{asset_type}")

# Load data
try:
    df = pd.read_excel(full_path, engine='openpyxl')
except Exception as e:
    st.error(f"Read error: {e}")
    st.stop()

df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
df['Last Service'] = pd.to_datetime(df['Last Service'], dayfirst=True, errors='coerce')
df['Days Since Service'] = (datetime.now() - df['Last Service']).dt.days

def get_interval_for_equipment(equip_name):
    eq_lower = str(equip_name).lower()
    for key, val in intervals.items():
        if key.lower() in eq_lower or eq_lower in key.lower():
            return val
    if "pump" in eq_lower and "mud" in eq_lower:
        return intervals.get("Mud Pump", intervals.get("Default", 21))
    if "pump" in eq_lower:
        return intervals.get("Crude Pump", intervals.get("Export Pump", intervals.get("BFP", 21)))
    if "gen" in eq_lower:
        return intervals.get("Generator", 30)
    if "comp" in eq_lower:
        return intervals.get("Gas Compressor", intervals.get("Compressor", 30))
    if "separ" in eq_lower or "vessel" in eq_lower:
        return intervals.get("Separator Vessel", 180)
    if "turbine" in eq_lower and "gas" in eq_lower:
        return intervals.get("Gas Turbine", 90)
    if "turbine" in eq_lower:
        return intervals.get("Steam Turbine", 180)
    return intervals.get("Default", 30)

def is_critical(equip_name):
    eq_lower = str(equip_name).lower()
    for crit in profile['critical']:
        if crit.lower() in eq_lower or eq_lower in crit.lower():
            return True
    return False

df['Interval_Days'] = df['Equipment'].apply(get_interval_for_equipment)
df['Days Overdue By'] = df['Days Since Service'] - df['Interval_Days']
df['Rule_Status'] = np.where(df['Days Overdue By'] > 0, 'OVERDUE', 'OK')
df['Next Service Due'] = df['Last Service'] + pd.to_timedelta(df['Interval_Days'], unit='D')
df['Is_Critical'] = df['Equipment'].apply(is_critical)

# Predictions
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
        predictions[asset] = {'MTBF': round(mtbf,1), 'DaysLeft': days_left, 'Risk': 'HIGH' if days_left < 7 else 'MEDIUM' if days_left < 30 else 'LOW'}

latest = df.sort_values('Last Service').drop_duplicates('Asset Tag', keep='last').copy()

# Dashboard
st.header(f"{profile['icon']} {plant_type} Dashboard")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Assets", len(latest))
c2.metric("🔴 Overdue", len(latest[latest['Rule_Status']=='OVERDUE']))
c3.metric("🟢 OK", len(latest[latest['Rule_Status']=='OK']))
c4.metric(f"🔥 Critical Overdue", len(latest[(latest['Is_Critical']) & (latest['Rule_Status']=='OVERDUE')]))

# --- PDF GENERATION FUNCTION ---
def create_work_order_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text, predictions):
    # Try reportlab, fallback to fpdf-like simple PDF if not available
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import inch
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        title_style.fontSize = 16
        heading_style = styles['Heading2']
        heading_style.fontSize = 12
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        
        story = []
        
        # Header
        story.append(Paragraph(f"<b>{logo_text} - WORK ORDER</b>", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Client:</b> {client_name} | <b>Plant:</b> {plant_type} | <b>Location:</b> {plant_location}", normal_style))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>WO No:</b> WO-{plant_type[:4].upper()}-{datetime.now().year}-{row['Asset Tag']}", normal_style))
        story.append(Spacer(1, 12))
        
        # Asset details table
        asset_data = [
            ["Asset Tag", row['Asset Tag']],
            ["Equipment", row['Equipment']],
            ["Location", row.get('Location','N/A')],
            ["Last Service", row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else "N/A"],
            ["Days Since Service", f"{int(row['Days Since Service'])} days"],
            ["Maintenance Interval", f"{int(row['Interval_Days'])} days"],
            ["Days Overdue By", f"{int(row['Days Overdue By'])} days"],
            ["Next Service Due", row['Next Service Due'].strftime('%d/%m/%Y') if pd.notna(row['Next Service Due']) else "N/A"],
            ["Status", row['Rule_Status']],
            ["Critical Asset?", "YES - Shutdown Risk" if row['Is_Critical'] else "No"],
        ]
        
        ai = predictions.get(row['Asset Tag'], {})
        asset_data.append(["AI MTBF", f"{ai.get('MTBF','N/A')} days"])
        asset_data.append(["AI Predicted Risk", ai.get('Risk','N/A')])
        asset_data.append(["AI Days to Failure", f"{ai.get('DaysLeft','N/A')} days"])
        
        t = Table(asset_data, colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 12))
        
        # Compliance
        story.append(Paragraph(f"<b>Compliance Requirement:</b> {profile['compliance']}", heading_style))
        story.append(Spacer(1, 6))
        
        # Work steps per plant type
        if plant_type == "Flow Station":
            steps = [
                "1. PTW + LOTO + HSE-003 Risk Assessment + Gas Test",
                "2. Isolate equipment, depressurize, drain",
                "3. Vibration analysis + oil sample + thermography",
                "4. Replace bearing/seal per OEM (21-day checklist for pumps)",
                "5. Functional test + leak test",
                "6. Update Last Service = TODAY in Excel, sign-off"
            ]
        elif plant_type == "Rig (Drilling)":
            steps = [
                "1. PTW + Well Control cert + BOP test + LOTO",
                "2. Stop drilling, secure well",
                "3. Inspect Top Drive / Mud Pump per API",
                "4. Replace liners, seals, check BOP stack",
                "5. Pressure test + function test",
                "6. Update log, Toolpusher sign-off"
            ]
        elif plant_type == "Gas Plant":
            steps = [
                "1. PSSR + Hot Work + Gas Test + PTW + Process Safety",
                "2. Depressurize + purge + isolate",
                "3. Vibration + gas leak detection",
                "4. Service compressor/dehydration per OEM",
                "5. Leak test + performance test",
                "6. Update Last Service, OIM sign-off"
            ]
        else:
            steps = [
                "1. PTW + LOTO + Arc Flash PPE + NERC compliance",
                "2. Isolate GT/HRSG per Siemens/GE procedure",
                "3. Borescope + vibration + oil analysis",
                "4. Replace filters, check BFP",
                "5. Run test + performance check",
                "6. Update log, update maintenance history"
            ]
        
        story.append(Paragraph("<b>Work Steps:</b>", heading_style))
        for s in steps:
            story.append(Paragraph(s, normal_style))
        
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Cost:</b> ₦435k planned vs ₦2M unplanned failure | <b>Downtime:</b> 6 hrs planned vs 24 hrs unplanned", normal_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Prepared By:</b> {prepared_by} | <b>Approved By:</b> ________________ | <b>Date:</b> __________", normal_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<i>Generated by {logo_text} Universal - {plant_type} - NUPRC Compliant - {datetime.now().strftime('%d/%m/%Y')}</i>", normal_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    except ImportError:
        # Fallback - create simple text PDF manually if reportlab not installed
        from io import BytesIO
        # Create simple text file as PDF fallback
        buffer = BytesIO()
        text = f"""
{logo_text} - WORK ORDER
Client: {client_name} | Plant: {plant_type} | Location: {plant_location}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')} | WO: WO-{plant_type[:4].upper()}-{datetime.now().year}-{row['Asset Tag']}

Asset: {row['Equipment']} ({row['Asset Tag']})
Last Service: {row['Last Service']}
Days Since: {row['Days Since Service']} | Interval: {row['Interval_Days']} | Overdue: {row['Days Overdue By']}
Status: {row['Rule_Status']} | Critical: {row['Is_Critical']}
Compliance: {profile['compliance']}

Steps: PTW + LOTO + Service per OEM + Update Last Service

Prepared By: {prepared_by}
"""
        buffer.write(text.encode())
        buffer.seek(0)
        return buffer

# --- DISPLAY + PDF DOWNLOAD ---
st.header(f"📝 Work Orders + PDF - {plant_type}")

# Bulk PDF
overdue_list = latest[latest['Rule_Status']=='OVERDUE'].sort_values('Days Overdue By', ascending=False)

if overdue_list.empty:
    st.success(f"✅ No overdue assets for {plant_type}")
else:
    st.warning(f"🔴 {len(overdue_list)} overdue - Generate PDFs below")
    
    # Option to download all as one PDF or individually
    if st.button(f"📄 Generate Combined PDF for All {len(overdue_list)} Overdue Assets"):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet
            from io import BytesIO
            
            buffer_all = BytesIO()
            from reportlab.lib.pagesizes import A4
            doc = SimpleDocTemplate(buffer_all, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            for _, r in overdue_list.iterrows():
                story.append(Paragraph(f"<b>WORK ORDER - {r['Asset Tag']} - {r['Equipment']}</b>", styles['Heading1']))
                story.append(Paragraph(f"Client: {client_name} | Plant: {plant_type} | Overdue by {int(r['Days Overdue By'])} days", styles['Normal']))
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Last Service: {r['Last Service']} | Interval: {int(r['Interval_Days'])}d | Location: {r.get('Location','')}", styles['Normal']))
                story.append(Paragraph(f"Compliance: {profile['compliance']}", styles['Normal']))
                story.append(Spacer(1, 12))
                story.append(PageBreak())
            
            doc.build(story)
            buffer_all.seek(0)
            st.download_button("⬇️ Download Combined PDF", buffer_all, file_name=f"WO_{plant_type}_{datetime.now().strftime('%Y%m%d')}_All.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Need reportlab - add to requirements: {e}")
    
    # Individual PDFs
    for _, row in overdue_list.iterrows():
        col1, col2 = st.columns([3,1])
        with col1:
            with st.expander(f"WO: {row['Asset Tag']} - {row['Equipment'][:40]} - Overdue {int(row['Days Overdue By'])}d (Interval {int(row['Interval_Days'])}d)"):
                st.write(f"**Last Service:** {row['Last Service']} | **Days Since:** {int(row['Days Since Service'])} | **Interval:** {int(row['Interval_Days'])}d")
                st.write(f"**Next Due:** {row['Next Service Due']} | **Status:** {row['Rule_Status']} | **Critical:** {'YES' if row['Is_Critical'] else 'No'}")
                st.write(f"**Compliance:** {profile['compliance']}")
                ai = predictions.get(row['Asset Tag'], {})
                st.write(f"**AI:** MTBF {ai.get('MTBF','N/A')}d | Risk {ai.get('Risk','N/A')} | Days to Fail {ai.get('DaysLeft','N/A')}")
        
        with col2:
            # Generate PDF for this row
            try:
                pdf_buffer = create_work_order_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text, predictions)
                st.download_button(
                    f"📄 PDF {row['Asset Tag']}",
                    pdf_buffer,
                    file_name=f"WO_{plant_type}_{row['Asset Tag']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{row['Asset Tag']}"
                )
            except Exception as e:
                st.error(f"PDF error: {e} - Add reportlab to requirements.txt")

st.header("📦 Requirements Update for PDF")
st.code("streamlit\npandas\nopenpyxl\nscikit-learn\nnumpy\nreportlab", language="text")
st.info("Add 'reportlab' to your requirements.txt on GitHub, commit, reboot - PDFs will work on Streamlit Cloud")

st.success("✅ UNIVERSAL + PDF ACTIVE - Client can download branded PDF work orders per plant type")
st.caption(f"Branding: {client_name} | {plant_location} | {logo_text} | {plant_type} | {datetime.now().strftime('%H:%M:%S')}")
