# app_hybrid_rule_ai_NOSKLEARN.py - Works even without sklearn (instant fix)
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os, glob
import numpy as np

st.set_page_config(page_title="MAINTAIN-AI HYBRID (No Sklearn)", layout="wide", page_icon="⚙️")
st.title("⚙️🤖 MAINTAIN-AI | HYBRID: Rule + AI (Light - No sklearn needed)")
st.markdown("**Rule-Based = NUPRC Compliance | AI = MTBF Prediction (pure Python, no sklearn)**")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_files = [f for f in glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
xlsx_names = [os.path.basename(f) for f in xlsx_files]

if not xlsx_names:
    st.error("No Excel found")
    st.stop()

selected = st.sidebar.selectbox("Log:", xlsx_names, index=0)
full_path = os.path.join(SCRIPT_DIR, selected)

# Settings
st.sidebar.header("⚙️ Rule-Based")
overdue_days = st.sidebar.slider("NUPRC Overdue threshold (days)", 1, 365, 90)
recurring_thresh = st.sidebar.slider("Flag recurring if > times", 1, 10, 2)
st.sidebar.header("🔄 Refresh")
auto_enabled = st.sidebar.toggle("Auto-refresh 10 mins", value=True)
interval = st.sidebar.slider("Mins", 1, 60, 10)

import streamlit.components.v1 as components
if auto_enabled:
    components.html(f"<script>setTimeout(()=>window.parent.location.reload(), {interval*60*1000});</script>", height=0)
components.html("""<button onclick="window.parent.location.reload()" style="background:#FF4B4B;color:white;border:none;
padding:10px 20px;border-radius:8px;font-weight:bold;width:100%;cursor:pointer;">🔄 Refresh Now</button>""", height=60)

# Load
try:
    df = pd.read_excel(full_path, engine='openpyxl')
except Exception as e:
    st.error(f"Read error: {e}")
    st.stop()

df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
df['Last Service'] = pd.to_datetime(df['Last Service'], dayfirst=True, errors='coerce')
df['Days Since Service'] = (datetime.now() - df['Last Service']).dt.days
df['Rule_Status'] = np.where(df['Days Since Service'] > overdue_days, 'OVERDUE (Rule)', 'OK (Rule)')

# --- AI Prediction WITHOUT sklearn (pure Python MTBF) ---
predictions = {}
for asset in df['Asset Tag'].unique():
    adf = df[df['Asset Tag']==asset].sort_values('Date')
    if len(adf) >= 2:
        diffs = adf['Date'].diff().dt.days.dropna()
        mtbf = diffs.mean() if len(diffs)>0 else 30
        if np.isnan(mtbf):
            mtbf = 30
        last = adf['Date'].max()
        next_pred = last + timedelta(days=mtbf)
        days_left = (next_pred - datetime.now()).days
        predictions[asset] = {
            'MTBF': round(mtbf,1),
            'Next': next_pred.strftime('%d/%m/%Y'),
            'DaysLeft': days_left,
            'Risk': 'HIGH' if days_left < 7 else 'MEDIUM' if days_left < 30 else 'LOW',
            'Count': len(adf),
            'TopFailure': adf['Failure'].mode().iloc[0] if not adf.empty else "Unknown"
        }

# Hybrid Table
st.header("🔀 Hybrid Decision: Rule + AI")
hybrid_rows = []
for asset in df['Asset Tag'].unique():
    latest = df[df['Asset Tag']==asset].sort_values('Date').iloc[-1]
    rule = latest['Rule_Status']
    ai = predictions.get(asset, {})
    ai_risk = ai.get('Risk', 'N/A')
    ai_days = ai.get('DaysLeft', 'N/A')
    
    if 'OVERDUE' in rule and ai_risk == 'HIGH':
        decision = "🚨 CRITICAL - Compliance + Imminent failure"
        priority = 1
    elif 'OVERDUE' in rule:
        decision = "⚠️ SERVICE NOW - NUPRC compliance"
        priority = 2
    elif ai_risk == 'HIGH':
        decision = "🤖 PREDICTIVE - AI: Will fail <7 days"
        priority = 2
    elif ai_risk == 'MEDIUM':
        decision = "👀 WATCH - Plan in 30 days"
        priority = 3
    else:
        decision = "✅ OK"
        priority = 4
    
    hybrid_rows.append({
        "Asset Tag": asset,
        "Equipment": latest['Equipment'],
        "Days Overdue (Rule)": latest['Days Since Service'],
        "Rule Status": rule,
        "AI Risk": ai_risk,
        "AI Days To Fail": ai_days,
        "AI MTBF": ai.get('MTBF','N/A'),
        "Top Failure": ai.get('TopFailure','N/A'),
        "Hybrid Decision": decision,
        "Priority": priority
    })

hybrid_df = pd.DataFrame(hybrid_rows).sort_values("Priority")
st.dataframe(hybrid_df, use_container_width=True)

critical = hybrid_df[hybrid_df['Priority']==1]
if not critical.empty:
    st.error(f"🚨 {len(critical)} CRITICAL: {', '.join(critical['Asset Tag'].tolist())}")

# Work Orders
st.header("📝 Hybrid Work Orders")
for _, row in hybrid_df.head(5).iterrows():
    asset = row['Asset Tag']
    wo = f"""HYBRID WORK ORDER: WO-HYBRID-{datetime.now().year}-{asset}
Asset: {row['Equipment']} ({asset})
RULE: Overdue {row['Days Overdue (Rule)']} days | Status {row['Rule Status']} | NUPRC must service in 7 days
AI: MTBF {row['AI MTBF']} days | Risk {row['AI Risk']} | Predicted fail in {row['AI Days To Fail']} days | Pattern: {row['Top Failure']}
DECISION: {row['Hybrid Decision']}
Steps: 1. LOTO + PTW 2. Vibration check 3. Replace bearing + seal 4. Oil sample 5. Update log
Cost: ₦435k (prevents ₦2M failure) | Downtime: 6 hrs planned
"""
    with st.expander(f"WO: {asset} - {row['Hybrid Decision'][:50]}"):
        st.code(wo)

st.success("✅ HYBRID LIGHT ACTIVE - No sklearn needed, works on Streamlit Cloud instantly")
st.caption(f"File: {selected} | Loaded: {len(df)} rows | Last: {datetime.now().strftime('%H:%M:%S')}")
