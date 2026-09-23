# app_universal_flowstation_rig_gas_power.py - Universal for All Plant Types
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os, glob
import numpy as np

st.set_page_config(page_title="MAINTAIN-AI UNIVERSAL", layout="wide", page_icon="🏭")
st.title("🏭 MAINTAIN-AI | UNIVERSAL - Flow Station | Rig | Gas Plant | Power Plant")
st.markdown("**One app for all: Switch plant type → Auto loads assets, intervals, NUPRC/HSE rules**")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_files = [f for f in glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
xlsx_names = [os.path.basename(f) for f in xlsx_files]

if not xlsx_names:
    st.error("No Excel found - Upload your log")
    st.stop()

# --- UNIVERSAL PLANT PROFILES ---
PLANT_PROFILES = {
    "Flow Station": {
        "description": "Bonny, Forcados, Escravos - Separators, Pumps, Generators, Export Pumps",
        "assets": ["Separator Vessel", "Crude Pump", "Export Pump", "Generator", "Compressor", "PSV"],
        "intervals": {"Separator Vessel": 180, "Crude Pump": 21, "Export Pump": 21, "Generator": 30, "Compressor": 30, "PSV": 365, "Default": 30},
        "compliance": "NUPRC Upstream + HSE PTW/LOTO",
        "critical": ["Export Pump", "Separator Vessel"],
        "icon": "🛢️"
    },
    "Rig (Drilling)": {
        "description": "Jack-up, Swamp Rig - Top Drive, Mud Pumps, Drawworks, BOP",
        "assets": ["Top Drive", "Mud Pump", "Drawworks", "BOP", "Generator", "Shaker", "Crane"],
        "intervals": {"Top Drive": 14, "Mud Pump": 7, "Drawworks": 30, "BOP": 14, "Generator": 21, "Shaker": 21, "Crane": 90, "Default": 21},
        "compliance": "NUPRC + DPR Rig Safety + API",
        "critical": ["BOP", "Mud Pump", "Top Drive"],
        "icon": "🏗️"
    },
    "Gas Plant": {
        "description": "NLNG, Escravos GTL - Compressors, Dehydration, Refrigeration, Flare",
        "assets": ["Gas Compressor", "Dehydration Unit", "Refrigeration", "Flare System", "Generator", "Heat Exchanger", "PSV"],
        "intervals": {"Gas Compressor": 30, "Dehydration Unit": 60, "Refrigeration": 90, "Flare System": 180, "Generator": 30, "Heat Exchanger": 90, "PSV": 180, "Default": 60},
        "compliance": "NUPRC Midstream + NMDPRA + Process Safety",
        "critical": ["Gas Compressor", "Flare System", "Dehydration Unit"],
        "icon": "🔥"
    },
    "Power Plant": {
        "description": "IPP, Turbine Plant - GT, HRSG, Steam Turbine, BFP",
        "assets": ["Gas Turbine", "HRSG", "Steam Turbine", "BFP", "Generator", "Transformer", "Cooling Tower"],
        "intervals": {"Gas Turbine": 90, "HRSG": 180, "Steam Turbine": 180, "BFP": 30, "Generator": 30, "Transformer": 180, "Cooling Tower": 90, "Default": 90},
        "compliance": "NERC + NUPRC + OEM Siemens/GE",
        "critical": ["Gas Turbine", "BFP", "Steam Turbine"],
        "icon": "⚡"
    }
}

# --- SIDEBAR - PLANT SELECTOR ---
st.sidebar.header("🏭 Select Plant Type")
plant_type = st.sidebar.selectbox("Plant:", list(PLANT_PROFILES.keys()), index=0)
profile = PLANT_PROFILES[plant_type]

st.sidebar.markdown(f"### {profile['icon']} {plant_type}")
st.sidebar.caption(profile['description'])
st.sidebar.info(f"Compliance: {profile['compliance']}\n\nCritical: {', '.join(profile['critical'])}")

selected = st.sidebar.selectbox("Log:", xlsx_names, index=0)
full_path = os.path.join(SCRIPT_DIR, selected)

# Editable intervals per plant type
st.sidebar.header(f"⚙️ Intervals for {plant_type} (days)")
intervals = {}
for asset_type, default_days in profile['intervals'].items():
    intervals[asset_type] = st.sidebar.number_input(f"{asset_type}", min_value=7, max_value=730, value=default_days, key=f"int_{plant_type}_{asset_type}")

# Refresh
st.sidebar.header("🔄 Refresh")
auto_enabled = st.sidebar.toggle("Auto-refresh 10 mins", value=True)
interval_mins = st.sidebar.slider("Mins", 1, 60, 10)
import streamlit.components.v1 as components
if auto_enabled:
    components.html(f"<script>setTimeout(()=>window.parent.location.reload(), {interval_mins*60*1000});</script>", height=0)
components.html("""<button onclick="window.parent.location.reload()" style="background:#FF4B4B;color:white;border:none;padding:10px 20px;border-radius:8px;font-weight:bold;width:100%;cursor:pointer;">🔄 Refresh Now</button>""", height=60)

# --- LOAD DATA ---
try:
    df = pd.read_excel(full_path, engine='openpyxl')
except Exception as e:
    st.error(f"Read error: {e}")
    st.stop()

df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
df['Last Service'] = pd.to_datetime(df['Last Service'], dayfirst=True, errors='coerce')
df['Days Since Service'] = (datetime.now() - df['Last Service']).dt.days

# Filter by plant type if Location column exists - auto detect
if 'Location' in df.columns:
    # Simple filter: if user selected Flow Station, show assets that match typical flow station equipment
    # Actually we show all but highlight critical per plant
    pass

# Assign interval based on Equipment name matching profile
def get_interval_for_equipment(equip_name):
    eq_lower = str(equip_name).lower()
    # Try exact match first
    for key, val in intervals.items():
        if key.lower() in eq_lower or eq_lower in key.lower():
            return val
    # Fallback keyword matching
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

df['Interval_Days'] = df['Equipment'].apply(get_interval_for_equipment)
df['Days Overdue By'] = df['Days Since Service'] - df['Interval_Days']
df['Rule_Status'] = np.where(df['Days Overdue By'] > 0, 'OVERDUE', 'OK')
df['Next Service Due'] = df['Last Service'] + pd.to_timedelta(df['Interval_Days'], unit='D')

# Is critical per plant type?
def is_critical(equip_name):
    eq_lower = str(equip_name).lower()
    for crit in profile['critical']:
        if crit.lower() in eq_lower or eq_lower in crit.lower():
            return True
    return False

df['Is_Critical'] = df['Equipment'].apply(is_critical)

# AI Prediction (no sklearn)
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
        predictions[asset] = {
            'MTBF': round(mtbf,1),
            'Next': next_pred.strftime('%d/%m/%Y'),
            'DaysLeft': days_left,
            'Risk': 'HIGH' if days_left < 7 else 'MEDIUM' if days_left < 30 else 'LOW',
        }

# --- DISPLAY UNIVERSAL DASHBOARD ---
st.header(f"{profile['icon']} {plant_type} Dashboard - {profile['compliance']}")

latest = df.sort_values('Last Service').drop_duplicates('Asset Tag', keep='last').copy()

# Metrics
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Assets", len(latest))
c2.metric("🔴 Overdue", len(latest[latest['Rule_Status']=='OVERDUE']))
c3.metric("🟢 OK", len(latest[latest['Rule_Status']=='OK']))
c4.metric(f"🔥 Critical {plant_type}", len(latest[(latest['Is_Critical']) & (latest['Rule_Status']=='OVERDUE')]))
c5.metric("⚠️ Due 7 days", len(latest[(latest['Days Overdue By'] >= -7) & (latest['Days Overdue By'] <= 0)]))

# Filter toggle
view_mode = st.radio("View:", ["All Assets", f"Only {plant_type} Critical Assets", "Overdue Only", "OK / Maintained"], horizontal=True)

if view_mode == f"Only {plant_type} Critical Assets":
    display_df = latest[latest['Is_Critical']]
elif view_mode == "Overdue Only":
    display_df = latest[latest['Rule_Status']=='OVERDUE']
elif view_mode == "OK / Maintained":
    display_df = latest[latest['Rule_Status']=='OK']
else:
    display_df = latest

st.subheader(f"📊 {view_mode} - {plant_type}")

show_cols = ['Asset Tag','Equipment','Last Service','Days Since Service','Interval_Days','Next Service Due','Days Overdue By','Rule_Status','Is_Critical','Location']
available_cols = [c for c in show_cols if c in display_df.columns]
st.dataframe(display_df[available_cols].sort_values('Days Overdue By', ascending=False), use_container_width=True)

# Hybrid
st.header(f"🔀 Hybrid Decision for {plant_type}")
hybrid_rows = []
for asset in df['Asset Tag'].unique():
    latest_row = df[df['Asset Tag']==asset].sort_values('Last Service').iloc[-1]
    interval = get_interval_for_equipment(latest_row['Equipment'])
    days_since = latest_row['Days Since Service']
    rule_status = 'OVERDUE' if days_since > interval else 'OK'
    critical_flag = is_critical(latest_row['Equipment'])
    
    ai = predictions.get(asset, {})
    ai_risk = ai.get('Risk', 'N/A')
    
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
        "Decision": decision,
        "Priority": priority,
        "Location": latest_row.get('Location','')
    })

hybrid_df = pd.DataFrame(hybrid_rows).sort_values("Priority")
st.dataframe(hybrid_df, use_container_width=True)

# Work Orders per plant type compliance
st.header(f"📝 Work Orders - {plant_type} Compliance: {profile['compliance']}")
overdue_hybrid = hybrid_df[hybrid_df['Rule']=='OVERDUE'].head(10)

if overdue_hybrid.empty:
    st.success(f"✅ All {plant_type} assets maintained!")
else:
    for _, row in overdue_hybrid.iterrows():
        # Compliance text per plant
        if plant_type == "Flow Station":
            comp_text = "NUPRC Upstream: PTW + LOTO + HSE-003 + 7-day closeout"
        elif plant_type == "Rig (Drilling)":
            comp_text = "DPR Rig Safety + BOP test + API + PTW + Well Control cert required"
        elif plant_type == "Gas Plant":
            comp_text = "NMDPRA + Process Safety + PSSR + Hot Work + Gas Test cert"
        else:
            comp_text = "NERC + OEM GE/Siemens procedure + LOTO + Arc Flash PPE"
        
        wo = f"""WORK ORDER: WO-{plant_type[:4].upper()}-{datetime.now().year}-{row['Asset Tag']}
Plant: {plant_type} | Asset: {row['Equipment']} ({row['Asset Tag']}) | Critical: {row['Critical?']}
Last Service: {row['Last Service']} | Interval: {row['Interval']}d | Overdue by: {int(row['Days Since'] - row['Interval'])} days
Compliance: {comp_text}
Decision: {row['Decision']}

Steps:
1. {comp_text}
2. Service per {plant_type} checklist (21d for pumps, 30d for gen etc)
3. For critical {plant_type} assets ({', '.join(profile['critical'])}): Double sign-off required
4. Update Last Service = TODAY in Excel
5. Update log for AI learning

Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        with st.expander(f"WO: {row['Asset Tag']} - {row['Decision']} - {row['Equipment'][:30]}"):
            st.code(wo)

st.success(f"✅ UNIVERSAL ACTIVE - Switch plant type in sidebar: Flow Station / Rig / Gas Plant / Power Plant - Intervals auto-adjust")
st.caption(f"File: {selected} | Plant: {plant_type} | {profile['compliance']} | Refresh: {datetime.now().strftime('%H:%M:%S')}")
