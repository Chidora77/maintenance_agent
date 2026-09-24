# MAINTAIN-AI FINAL - NO DUPLICATE KEYS - REFRESH FIXED - NO MIXING
import pandas as pd
import streamlit as st
from datetime import datetime
import os, glob
import numpy as np
from io import BytesIO
import time

VALID_LICENSES = {
    "SPDC-FLOW-2026": {"client": "SPDC", "expiry": "2026-12-31", "plants": ["Flow Station", "Rig (Drilling)", "Gas Plant", "Power Plant"]},
    "TOTAL-2026-GAS": {"client": "TotalEnergies", "expiry": "2026-11-30", "plants": ["Gas Plant"]},
    "FIRSTEP-TRIAL": {"client": "First E&P", "expiry": "2026-11-15", "plants": ["Flow Station"]},
    "DEMO-12345": {"client": "DEMO", "expiry": "2026-12-31", "plants": ["Flow Station", "Rig (Drilling)", "Gas Plant", "Power Plant"]},
}
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
                return {"valid": False, "reason": f"License expired on {lic['expiry']}. Contact support to renew."}
            return {"valid": True, **lic}
        except:
            return {"valid": False, "reason": "Invalid expiry"}
    return {"valid": False, "reason": "Invalid License Key. Contact support."}

st.set_page_config(page_title="MAINTAIN-AI FINAL", layout="wide")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.client_info = None
    st.session_state.license_key = ""

try:
    qp = st.query_params
    saved_key = qp.get("license", "")
    if not st.session_state.authenticated and saved_key:
        result = check_license(saved_key)
        if result["valid"]:
            st.session_state.authenticated = True
            st.session_state.client_info = result
            st.session_state.license_key = saved_key
except:
    pass

if not st.session_state.authenticated:
    st.title("MAINTAIN-AI | Licensed Version")
    st.info("No license? Contact support for access.")
    license_input = st.text_input("License Key:", type="password", placeholder="Enter license key", key="lic_input_final_unique")
    if st.button("Unlock System", type="primary", use_container_width=True, key="unlock_btn_final_unique"):
        result = check_license(license_input)
        if result["valid"]:
            st.session_state.authenticated = True
            st.session_state.client_info = result
            st.session_state.license_key = license_input.strip().upper()
            try:
                st.query_params["license"] = license_input.strip().upper()
            except:
                pass
            st.success(f"Welcome {result['client']}! Valid till {result['expiry']}")
            st.balloons()
            st.rerun()
        else:
            st.error(f"{result['reason']}")
    st.caption("Demo Key: DEMO-12345 | Admin: ChidoraAdmin2026!")
    st.stop()

try:
    if st.session_state.license_key:
        st.query_params["license"] = st.session_state.license_key
except:
    pass

client_info = st.session_state.client_info

st.sidebar.success(f"Licensed: {client_info['client']}", icon="✅")
st.sidebar.caption(f"Exp: {client_info['expiry']}")

# ONE LOGOUT BUTTON ONLY - UNIQUE KEY
if st.sidebar.button("Logout", key="logout_btn_final_v2_unique"):
    st.session_state.authenticated = False
    st.session_state.client_info = None
    try:
        st.query_params.clear()
    except:
        pass
    st.rerun()

# SEPARATED REFRESH SECTION - NO MIXING
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Refresh Controls")

# MANUAL REFRESH - SEPARATE KEY
if st.sidebar.button("🔄 Manual Refresh", use_container_width=True, key="manual_refresh_final_unique", help="Refreshes data, stays logged in"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
# AUTO REFRESH - COMPLETELY SEPARATE KEYS
auto_on = st.sidebar.toggle("Auto-refresh", value=False, key="auto_refresh_final_toggle_unique", help="Auto refresh without logout")
auto_mins = st.sidebar.slider("Auto interval (mins)", 1, 60, 10, key="auto_interval_final_unique")

if auto_on:
    if 'last_refresh_final' not in st.session_state:
        st.session_state.last_refresh_final = time.time()
    elapsed = time.time() - st.session_state.last_refresh_final
    if elapsed > auto_mins * 60:
        st.session_state.last_refresh_final = time.time()
        st.cache_data.clear()
        st.rerun()
    remaining = max(0, int(auto_mins*60 - elapsed))
    st.sidebar.caption(f"Auto in {remaining}s - stays logged in ✅")
else:
    st.sidebar.caption("Auto-refresh OFF")

st.title(f"MAINTAIN-AI | {client_info['client']}")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_files = [f for f in glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
xlsx_names = [os.path.basename(f) for f in xlsx_files]

PLANT_PROFILES = {
    "Flow Station": {"intervals": {"Separator Vessel": 180, "Crude Pump": 21, "Export Pump": 21, "Generator": 30, "Compressor": 30, "PSV": 365, "Default": 30}, "compliance": "NUPRC Upstream + HSE PTW/LOTO + HSE-003", "critical": ["Export Pump", "Separator Vessel"], "icon": "🛢️"},
    "Rig (Drilling)": {"intervals": {"Top Drive": 14, "Mud Pump": 7, "Drawworks": 30, "BOP": 14, "Generator": 21, "Shaker": 21, "Crane": 90, "Default": 21}, "compliance": "NUPRC + DPR Rig Safety + API + Well Control", "critical": ["BOP", "Mud Pump", "Top Drive"], "icon": "🏗️"},
    "Gas Plant": {"intervals": {"Gas Compressor": 30, "Dehydration Unit": 60, "Refrigeration": 90, "Flare System": 180, "Generator": 30, "Heat Exchanger": 90, "PSV": 180, "Default": 60}, "compliance": "NUPRC Midstream + NMDPRA + Process Safety + PSSR", "critical": ["Gas Compressor", "Flare System", "Dehydration Unit"], "icon": "🔥"},
    "Power Plant": {"intervals": {"Gas Turbine": 90, "HRSG": 180, "Steam Turbine": 180, "BFP": 30, "Generator": 30, "Transformer": 180, "Cooling Tower": 90, "Default": 90}, "compliance": "NERC + NUPRC + OEM Siemens/GE + Arc Flash", "critical": ["Gas Turbine", "BFP", "Steam Turbine"], "icon": "⚡"}
}

allowed_plants = client_info["plants"]
st.sidebar.header("Select Plant Type")
plant_type = st.sidebar.selectbox("Plant:", allowed_plants, index=0, key="plant_select_final_unique")
profile = PLANT_PROFILES[plant_type]

st.sidebar.header("Client Branding")
client_name = st.sidebar.text_input("Client Name", value=client_info["client"], key="client_name_final_unique")
plant_location = st.sidebar.text_input("Plant Location", value="Bonny Terminal", key="plant_loc_final_unique")
prepared_by = st.sidebar.text_input("Prepared By", value=f"{client_info['client']} - Maintenance", key="prepared_by_final_unique")
logo_text = st.sidebar.text_input("Company Logo Text", value="MAINTAIN-AI", key="logo_text_final_unique")

st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Excel Source:", ["Use Excel in Folder", "Upload Company Excel"], index=0, key="data_source_final_unique")

if data_source == "Upload Company Excel":
    uploaded_file = st.sidebar.file_uploader("Upload Excel (.xlsx)", type=["xlsx","xls","csv"], key="uploader_final_unique")
    if uploaded_file is None:
        st.info("Sidebar -> Upload company Excel.")
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
        st.download_button("Download Template", buf, file_name="Template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_template_final_unique")
        st.stop()
    df = pd.read_excel(uploaded_file, engine='openpyxl') if not uploaded_file.name.endswith('.csv') else pd.read_csv(uploaded_file)
    full_path = None
    file_name_label = uploaded_file.name
else:
    if not xlsx_names:
        st.error("No Excel in folder. Add Excel or use Upload")
        st.stop()
    selected = st.sidebar.selectbox("Log:", xlsx_names, index=0, key="log_select_final_unique")
    full_path = os.path.join(SCRIPT_DIR, selected)
    file_name_label = selected
    df = pd.read_excel(full_path, engine='openpyxl')

st.sidebar.header("Intervals (days)")
intervals = {}
for asset_type, default_days in profile['intervals'].items():
    intervals[asset_type] = st.sidebar.number_input(f"{asset_type}", min_value=7, max_value=730, value=default_days, key=f"interval_{plant_type}_{asset_type}_final_unique")

df['Date'] = pd.to_datetime(df.get('Date', datetime.now()), dayfirst=True, errors='coerce')
df['Last Service'] = pd.to_datetime(df['Last Service'], dayfirst=True, errors='coerce')
df['Days Since Service'] = (datetime.now() - df['Last Service']).dt.days

def get_interval(equip):
    eq = str(equip).lower()
    for k,v in intervals.items():
        if k.lower() in eq or eq in k.lower():
            return v
    if "mud" in eq and "pump" in eq:
        return intervals.get("Mud Pump", intervals["Default"])
    if "pump" in eq:
        return intervals.get("Crude Pump", 21)
    if "gen" in eq:
        return intervals.get("Generator", 30)
    if "comp" in eq:
        return intervals.get("Gas Compressor", 30)
    if "separ" in eq or "vessel" in eq:
        return intervals.get("Separator Vessel", 180)
    if "gas" in eq and "turbine" in eq:
        return intervals.get("Gas Turbine", 90)
    if "turbine" in eq:
        return intervals.get("Steam Turbine", 180)
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

def get_rag_status(days_overdue):
    if days_overdue > 0:
        return "Red - OVERDUE"
    elif days_overdue >= -7:
        return "Amber - Due 7 days"
    else:
        return "Green - OK"

def get_rag_emoji(days_overdue):
    if days_overdue > 0:
        return "🔴"
    elif days_overdue >= -7:
        return "🟡"
    else:
        return "🟢"

df['RAG_Status'] = df['Days Overdue By'].apply(get_rag_status)
df['RAG_Emoji'] = df['Days Overdue By'].apply(get_rag_emoji)

def calc_ai_risk(row):
    days_since = row['Days Since Service']
    interval = row['Interval_Days']
    overdue = row['Days Overdue By']
    if overdue > 0:
        return min(0.95 + (overdue/200), 1.0)
    else:
        return max(0.05, min(0.8, days_since/interval*0.8))

df['AI_Risk'] = df.apply(calc_ai_risk, axis=1)
df['AI_Status'] = df['AI_Risk'].apply(lambda x: "HIGH" if x>0.7 else "MEDIUM" if x>0.4 else "LOW")
df['Hybrid_Decision'] = df.apply(lambda r: f"{r['RAG_Emoji']} OVERDUE - {profile['compliance']} + AI {r['AI_Risk']:.0%} risk" if r['Days Overdue By']>0 else f"{r['RAG_Emoji']} OK - Next {r['Next Service Due'].strftime('%d/%m')} - AI {r['AI_Risk']:.0%}", axis=1)

latest = df.sort_values('Last Service').drop_duplicates('Asset Tag', keep='last').copy()

if 'serviced_assets' not in st.session_state:
    st.session_state.serviced_assets = {}

for asset_tag, service_date in st.session_state.serviced_assets.items():
    if asset_tag in latest['Asset Tag'].values:
        latest.loc[latest['Asset Tag']==asset_tag, 'Last Service'] = service_date
        latest.loc[latest['Asset Tag']==asset_tag, 'Days Since Service'] = (datetime.now() - service_date).days
        overdue = (datetime.now() - service_date).days - latest.loc[latest['Asset Tag']==asset_tag, 'Interval_Days'].iloc[0]
        latest.loc[latest['Asset Tag']==asset_tag, 'Days Overdue By'] = overdue
        latest.loc[latest['Asset Tag']==asset_tag, 'Rule_Status'] = "OVERDUE" if overdue>0 else "OK"
        latest.loc[latest['Asset Tag']==asset_tag, 'RAG_Status'] = get_rag_status(overdue)
        latest.loc[latest['Asset Tag']==asset_tag, 'RAG_Emoji'] = get_rag_emoji(overdue)
        latest.loc[latest['Asset Tag']==asset_tag, 'Next Service Due'] = service_date + pd.to_timedelta(latest.loc[latest['Asset Tag']==asset_tag, 'Interval_Days'].iloc[0], unit='D')
        latest.loc[latest['Asset Tag']==asset_tag, 'AI_Risk'] = 0.05

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
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>WO:</b> WO-{row['Asset Tag']} | <b>RAG:</b> {row['RAG_Status']}", styles['Normal']))
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
            ["RAG", str(row['RAG_Status'])],
            ["AI Risk", f"{row.get('AI_Risk',0):.0%} - {row.get('AI_Status','N/A')}"],
            ["Hybrid", str(row.get('Hybrid_Decision','N/A'))],
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
        story.append(Paragraph(f"Prepared: {prepared_by} | Licensed: {client_info['client']}", styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF error: {e}")
        return None

st.header(f"{profile['icon']} {plant_type} Dashboard - {profile['compliance']}")
st.caption(f"File: {file_name_label} | Client: {client_name}")

c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Assets", len(latest))
c2.metric("🔴 Red - OVERDUE", len(latest[latest['Days Overdue By'] > 0]))
c3.metric("🟡 Amber - Due 7d", len(latest[(latest['Days Overdue By'] >= -7) & (latest['Days Overdue By'] <= 0)]))
c4.metric("🟢 Green - OK", len(latest[latest['Days Overdue By'] < -7]))

st.subheader("Filtered Asset Table")
view_mode = st.radio("View:", ["All Assets", f"Only {plant_type} Critical", "Overdue Only", "OK / Green Only"], horizontal=True, key="view_mode_final_unique")
if view_mode == f"Only {plant_type} Critical":
    display_df = latest[latest['Is_Critical']]
elif view_mode == "Overdue Only":
    display_df = latest[latest['Days Overdue By'] > 0]
elif view_mode == "OK / Green Only":
    display_df = latest[latest['Days Overdue By'] < -7]
else:
    display_df = latest

show_cols = ['Asset Tag','Equipment','Last Service','Days Since Service','Interval_Days','Next Service Due','Days Overdue By','Rule_Status','RAG_Status','Is_Critical','Location','AI_Risk','Hybrid_Decision']
available_cols = [c for c in show_cols if c in display_df.columns]
st.dataframe(display_df[available_cols].sort_values('Days Overdue By', ascending=False), use_container_width=True, height=350)

st.header("RAG Status - Red Amber Green")
rag_filter = st.radio("RAG Filter:", ["All", "🔴 Red - OVERDUE", "🟡 Amber - Due 7 days", "🟢 Green - OK"], horizontal=True, key="rag_filter_final_unique")
if rag_filter == "🔴 Red - OVERDUE":
    rag_df = latest[latest['Days Overdue By'] > 0]
elif rag_filter == "🟡 Amber - Due 7 days":
    rag_df = latest[(latest['Days Overdue By'] >= -7) & (latest['Days Overdue By'] <= 0)]
elif rag_filter == "🟢 Green - OK":
    rag_df = latest[latest['Days Overdue By'] < -7]
else:
    rag_df = latest
st.dataframe(rag_df[['Asset Tag','Equipment','Days Overdue By','RAG_Status','RAG_Emoji','Next Service Due','Is_Critical']].sort_values('Days Overdue By', ascending=False), use_container_width=True, height=250)

st.header("🤖 AI Predictions - MTBF + Risk + RAG")
predictions = []
for asset in latest['Asset Tag'].unique():
    asset_hist = df[df['Asset Tag']==asset].sort_values('Date')
    if len(asset_hist) >= 2:
        diffs = asset_hist['Date'].diff().dt.days.dropna()
        mtbf = diffs.mean() if len(diffs)>0 else 30
        if np.isnan(mtbf):
            mtbf = 30
    else:
        mtbf = float(latest[latest['Asset Tag']==asset]['Interval_Days'].iloc[0]) if len(latest[latest['Asset Tag']==asset])>0 else 30
    row_latest = latest[latest['Asset Tag']==asset].iloc[0]
    ai_risk = row_latest.get('AI_Risk', 0.5)
    days_left = int(row_latest['Interval_Days'] - row_latest['Days Since Service'])
    predictions.append({
        "Asset Tag": asset,
        "Equipment": row_latest['Equipment'],
        "MTBF": round(mtbf,1),
        "Days Since": int(row_latest['Days Since Service']),
        "Interval": int(row_latest['Interval_Days']),
        "Days Left": days_left,
        "Overdue": int(row_latest['Days Overdue By']),
        "AI Risk": f"{ai_risk:.0%}",
        "AI Score": ai_risk,
        "AI Status": row_latest.get('AI_Status','LOW'),
        "RAG": f"{row_latest['RAG_Emoji']} {row_latest['RAG_Status']}",
        "Critical": "YES" if row_latest['Is_Critical'] else "No"
    })

pred_df = pd.DataFrame(predictions).sort_values("AI Score", ascending=False)
st.dataframe(pred_df, use_container_width=True, height=350)

decision_mode = st.radio("Decision Mode:", ["Hybrid AI+Rule (Recommended)", "Rule Only (21/30/180)", "AI Only (Risk Score)"], horizontal=True, key="decision_mode_final_unique")
st.caption(f"Selected: {decision_mode}")

st.header(f"🔀 Hybrid Decision for {plant_type}")
for _, row in latest.sort_values('Days Overdue By', ascending=False).head(15).iterrows():
    with st.container(border=True):
        col1, col2 = st.columns([3,1])
        with col1:
            st.markdown(f"**{row['RAG_Emoji']} {row['Asset Tag']} - {row['Equipment']}**")
            st.caption(f"Rule: {row['Rule_Status']} | RAG: {row['RAG_Status']} | Overdue {int(row['Days Overdue By'])}d | Interval {int(row['Interval_Days'])}d | Last {row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else 'N/A'}")
            st.markdown(f"**Hybrid:** {row.get('Hybrid_Decision','N/A')}")
            ai_risk = row.get('AI_Risk', 0)
            st.progress(float(ai_risk), text=f"AI Risk: {ai_risk:.0%} - {row.get('AI_Status','')} - {row['RAG_Status']}")
        with col2:
            if row['Days Overdue By'] > 0:
                st.error(f"🔴 OVERDUE {int(row['Days Overdue By'])}d")
            elif row['Days Overdue By'] >= -7:
                st.warning(f"🟡 DUE {abs(int(row['Days Overdue By']))}d")
            else:
                st.success(f"🟢 OK - Due {row['Next Service Due'].strftime('%d/%m') if pd.notna(row['Next Service Due']) else 'N/A'}")

st.header(f"📝 Work Orders + PDF + Grey/Green Tick - {plant_type}")
st.caption("🔴 Red = OVERDUE | 🟡 Amber = Due 7d | 🟢 Green = OK")

for _, row in latest.sort_values('Days Overdue By', ascending=False).iterrows():
    rag_emoji = row['RAG_Emoji']
    is_overdue = row['Days Overdue By'] > 0
    is_amber = -7 <= row['Days Overdue By'] <= 0
    is_green = row['Days Overdue By'] < -7
    with st.container(border=True):
        col_a, col_b, col_c, col_d = st.columns([2.5,2,1,1])
        with col_a:
            crit = "🔥 CRITICAL" if row['Is_Critical'] else ""
            if is_green:
                title = f"{rag_emoji} ✅ {row['Asset Tag']} - {row['Equipment']} {crit} - SERVICED GREEN"
            elif is_amber:
                title = f"{rag_emoji} ⚠️ {row['Asset Tag']} - {row['Equipment']} {crit} - DUE SOON"
            else:
                title = f"{rag_emoji} ❌ {row['Asset Tag']} - {row['Equipment']} {crit} - OVERDUE"
            st.markdown(f"**{title}**")
            st.caption(f"Last: {row['Last Service'].strftime('%d/%m/%Y') if pd.notna(row['Last Service']) else 'N/A'} | Since: {int(row['Days Since Service'])}d | Int: {int(row['Interval_Days'])}d | Overdue: {int(row['Days Overdue By'])}d")
            if is_green:
                st.success(f"✅ OK - Next {row['Next Service Due'].strftime('%d/%m/%Y')} - AI {row.get('AI_Risk',0):.0%}")
            elif is_amber:
                st.warning(f"🟡 Due in {abs(int(row['Days Overdue By']))}d")
            else:
                st.error(f"🔴 OVERDUE {int(row['Days Overdue By'])}d")
        with col_b:
            st.caption(f"Location: {row.get('Location','N/A')} | Status: {row['Rule_Status']} | RAG: {row['RAG_Status']}")
            st.caption(f"Compliance: {profile['compliance']}")
        with col_c:
            pdf_buf = create_pdf(row, plant_type, profile, client_name, plant_location, prepared_by, logo_text)
            if pdf_buf:
                st.download_button("📄 PDF", pdf_buf, file_name=f"WO_{row['Asset Tag']}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", key=f"pdf_{row['Asset Tag']}_{plant_type}_final_unique", use_container_width=True)
        with col_d:
            if is_overdue or is_amber:
                if st.button(f"❌ Not Serviced", key=f"serv_{row['Asset Tag']}_{plant_type}_final_unique", use_container_width=True):
                    now = datetime.now()
                    st.session_state.serviced_assets[row['Asset Tag']] = now
                    if full_path:
                        try:
                            df_full = pd.read_excel(full_path, engine='openpyxl')
                            mask = df_full['Asset Tag'] == row['Asset Tag']
                            df_full.loc[mask, 'Last Service'] = now
                            if 'Date' in df_full.columns:
                                df_full.loc[mask, 'Date'] = now
                            df_full.to_excel(full_path, index=False, engine='openpyxl')
                        except Exception as e:
                            st.error(f"File update failed: {e}")
                    st.success(f"✅ {row['Asset Tag']} marked TODAY - Now 🟢 GREEN!")
                    st.balloons()
                    st.rerun()
            else:
                st.button(f"✅ Serviced - GREEN", key=f"serv_green_{row['Asset Tag']}_{plant_type}_final_unique", use_container_width=True, disabled=True)
                if st.button(f"↩️ Undo", key=f"undo_{row['Asset Tag']}_{plant_type}_final_unique", use_container_width=True):
                    if row['Asset Tag'] in st.session_state.serviced_assets:
                        del st.session_state.serviced_assets[row['Asset Tag']]
                    st.rerun()

st.success(f"✅ {plant_type}: 🔴 {len(latest[latest['Days Overdue By']>0])} Red | 🟡 {len(latest[(latest['Days Overdue By'] >= -7) & (latest['Days Overdue By'] <=0)])} Amber | 🟢 {len(latest[latest['Days Overdue By']<-7])} Green")
