from streamlit_echarts import st_echarts
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import re
from utils import load_and_prep_data

st.set_page_config(page_title="TN Education Analytics", page_icon="🏛️", layout="wide")
st.markdown("<br>", unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5, col_nav6, col_nav7 = st.columns(7)


with col_nav1:
    st.page_link("app.py", label="📊 HOME", use_container_width=True)
with col_nav2:
    st.page_link("pages/benchmarking.py", label="📈 COMPARISON", use_container_width=True)
with col_nav3:
    st.page_link("pages/teacher_command_center.py", label="🧑‍🏫 TEACHER CENTER", use_container_width=True)
with col_nav4:
    st.page_link("pages/school_remedy.py", label="🏥 REMEDIES", use_container_width=True)
with col_nav5:
    st.page_link("pages/quick fix.py", label="⚡ BUDGET ALLOCATION", use_container_width=True)
with col_nav6:
    st.page_link("pages/accountability_audit.py", label="📝 NEGLIGENCE-AUDIT", use_container_width=True)
with col_nav7:
    st.page_link("pages/equity2.py", label="⚖️ EQUITY-INDEX", use_container_width=True)

st.markdown("<hr style='margin-top: 10px; margin-bottom: 30px;'>", unsafe_allow_html=True)



df = load_and_prep_data()
total_schools = len(df)

st.title("📊 State-Wide Infrastructure & Governance Health")
st.write("Measuring strict compliance against RTE Act (2009) and TN School Education mandates.")

st.markdown(f"<h3 style='text-align: center; color: #4CAF50;'>🏫 Total Schools Analyzed: {total_schools:,}</h3>",
            unsafe_allow_html=True)
st.divider()


metrics_infra = {
    "Electrified (100%)": int((df['electricity'] == 1).sum()),
    "Safe Drinking Water": int((df['drinking_water'] == 1).sum()),
    "Pucca Buildings (Safe)": int((df['building'] == 3).sum()),
    # NOTE: Verify if 3 is Pucca or Dilapidated in your dataset
    "Digital Ready (Internet)": int((df['internet'] == 1).sum()),
    "RTE Teacher Ratio (1:30)": int((df['ptr'] <= 30).sum()),
    "RTE Class Space (1:30)": int(((df['total_students'] / df['total_class_rooms'].replace(0, np.nan)) <= 30).sum()),


    "Girls' Sanitation (1:40)": int(
        ((df['total_girls'] == 0) | ((df['total_girls'] / df['toilet_girls'].replace(0, np.nan)) <= 40)).sum()),
    "Boys' Sanitation (1:40)": int(
        ((df['total_boys'] == 0) | ((df['total_boys'] / df['toilet_boys'].replace(0, np.nan)) <= 40)).sum()),

    "Fully Compliant Schools": int((df['violations'] == 0).sum()),
    "Critical Priority (Need Fund)": int((df['violations'] >= 4).sum())
}

metrics_gov = {
    "Funds Utilized (>80%)": int(df['funds_utilized'].sum()),
    "Active SMC (Parent Board)": int(df['active_smc'].sum()),
    "Inspected by Officials": int(df['inspected_recently'].sum()),
    "RTE Entitlements Given": int(df['entitlements_met'].sum())
}



def create_animated_gauge(value, max_value, title):
    safe_id = re.sub(r'[^a-zA-Z0-9]', '_', title)
    safe_value = int(value) if not pd.isna(value) else 0
    max_value = int(max_value) if not pd.isna(max_value) else 1
    percentage = safe_value / max_value if max_value > 0 else 0

    if title == "Critical Priority (Need Fund)":
        if percentage > 0.5:
            color = "#ff4b4b"
        elif percentage > 0.2:
            color = "#ffa500"
        else:
            color = "#00cc96"
    else:
        if percentage < 0.5:
            color = "#ff4b4b"
        elif percentage < 0.8:
            color = "#ffa500"
        else:
            color = "#00cc96"

    circumference = 377
    offset = circumference - (circumference * percentage)

    html_code = f"""
    <div style="display: flex; flex-direction: column; align-items: center; font-family: 'Segoe UI', sans-serif;">
        <div style="position: relative; width: 160px; height: 160px;">
            <svg width="160" height="160" style="transform: rotate(-90deg);">
                <circle cx="80" cy="80" r="60" stroke="rgba(128, 128, 128, 0.2)" stroke-width="12" fill="none" />
                <circle cx="80" cy="80" r="60" stroke="{color}" stroke-width="12" fill="none" 
                        stroke-dasharray="{circumference}" stroke-dashoffset="{circumference}" 
                        style="transition: stroke-dashoffset 2s cubic-bezier(0.25, 1, 0.5, 1); stroke-linecap: round;" id="ring-{safe_id}" />
            </svg>
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 26px; font-weight: bold; color: {color};" id="num-{safe_id}">0</div>
        </div>
        <div style="color: #a0a0a0; font-size: 14px; font-weight: 600; text-align: center; margin-top: -10px;">{title}</div>
    </div>

    <script>
        setTimeout(() => {{
            const ring = document.getElementById('ring-{safe_id}');
            if(ring) ring.style.strokeDashoffset = '{offset}';
        }}, 150);

        let start = null;
        const duration = 2000; 
        const finalValue = parseInt('{safe_value}') || 0;
        const numElement = document.getElementById('num-{safe_id}');

        if (numElement) {{
            const step = (timestamp) => {{
                const ts = timestamp || performance.now();
                if (!start) start = ts;
                const progress = Math.min((ts - start) / duration, 1);
                const easeOut = 1 - Math.pow(1 - progress, 4);
                const currentVal = Math.floor(easeOut * finalValue) || 0;
                numElement.innerText = currentVal.toLocaleString();

                if (progress < 1) {{
                    window.requestAnimationFrame(step);
                }} else {{
                    numElement.innerText = finalValue.toLocaleString(); 
                }}
            }};
            window.requestAnimationFrame(step);
        }}
    </script>
    """
    components.html(html_code, height=220)



st.subheader("🏗️ Tier 1: Infrastructure & Compliance")
cols_row1 = st.columns(5)
keys_row1 = list(metrics_infra.keys())[:5]
for i, col in enumerate(cols_row1):
    with col:
        create_animated_gauge(metrics_infra[keys_row1[i]], total_schools, keys_row1[i])

cols_row2 = st.columns(5)
keys_row2 = list(metrics_infra.keys())[5:]
for i, col in enumerate(cols_row2):
    with col:
        create_animated_gauge(metrics_infra[keys_row2[i]], total_schools, keys_row2[i])

st.divider()

st.subheader("💼 Tier 2: Governance, Finance & Oversight")
cols_row3 = st.columns(4)
keys_row3 = list(metrics_gov.keys())
for i, col in enumerate(cols_row3):
    with col:
        create_animated_gauge(metrics_gov[keys_row3[i]], total_schools, keys_row3[i])

st.divider()


st.write("### 🧭 Executive Triage: The Risk Distribution")
st.write(
    "Visualizing the disproportionate concentration of critical-priority schools and their exact material deficits.")

col_rose, col_ledger = st.columns([1.5, 1])

df['is_high_risk'] = df['violations'] >= 3

risk_df = df[df['is_high_risk'] == True].groupby('district').size().reset_index(name='critical_count')
risk_df = risk_df.sort_values('critical_count', ascending=False).head(10)

with col_rose:
    st.write("##### The Burden of Failure (Top 10 Districts)")

    rose_data = []
    for _, row in risk_df.iterrows():
        rose_data.append({
            "value": int(row['critical_count']),
            "name": str(row['district'])
        })

    rose_options = {
        "tooltip": {
            "trigger": "item",
            "formatter": "<b>{b}</b><br/>{c} High-Risk Schools ({d}%)"
        },
        "legend": {
            "type": "scroll",
            "bottom": "0%",
            "textStyle": {"color": "#64748b", "fontWeight": "bold"}
        },
        "series": [
            {
                "name": "Critical Schools",
                "type": "pie",
                "radius": ["15%", "75%"],
                "center": ["50%", "45%"],
                "roseType": "area",
                "itemStyle": {
                    "borderRadius": 6,
                    "borderColor": "#ffffff",
                    "borderWidth": 2
                },
                "label": {
                    "show": True,
                    "formatter": "{b}\n{c}",
                    "color": "#64748b",
                    "fontWeight": "bold"
                },
                "labelLine": {
                    "smooth": 0.2,
                    "length": 10,
                    "length2": 15
                },
                "data": rose_data,
                "animationType": "scale",
                "animationEasing": "elasticOut",
                "animationDuration": 2000,
                "color": ["#064e3b", "#065f46", "#047857", "#059669", "#10b981", "#34d399", "#6ee7b7", "#a7f3d0", "#d1fae5", "#ecfdf5"]
            }
        ]
    }

    st_echarts(options=rose_options, height="450px")

with col_ledger:
    st.write("##### 📋 Targeted Material Deficit")
    st.write("To stabilize just these 10 districts, the state requires the following immediate physical interventions:")

    worst_districts_list = risk_df['district'].tolist()
    triage_target_df = df[df['district'].isin(worst_districts_list)]

    missing_water = len(triage_target_df[triage_target_df['drinking_water'] != 1])
    missing_power = len(triage_target_df[triage_target_df['electricity'] != 1])
    bad_buildings = len(triage_target_df[triage_target_df['building'] != 3])
    missing_toilets = len(triage_target_df[
                              ((triage_target_df['total_boys'] > 0) & (triage_target_df['toilet_boys'] == 0)) |
                              ((triage_target_df['total_girls'] > 0) & (triage_target_df['toilet_girls'] == 0))
                              ])
    def mini_metric_card(label, count, icon, color):
        html = f"""
        <div style="background-color: #f8fafc; border-left: 5px solid {color}; padding: 12px 20px; margin-bottom: 12px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">{icon}</span>
                <span style="font-size: 14px; font-weight: 600; color: #475569;">{label}</span>
            </div>
            <div style="font-size: 22px; font-weight: 800; color: #0f172a;">{count:,}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    mini_metric_card("RO Water Plants", missing_water, "💧", "#3b82f6")
    mini_metric_card("Grid Connections", missing_power, "⚡", "#f59e0b")
    mini_metric_card("Sanitation Blocks", missing_toilets, "🚻", "#10b981")
    mini_metric_card("Civil Works (Bldgs)", bad_buildings, "🏗️", "#ef4444")

    st.info(
        "**Insight:** Routing emergency funds to resolve these specific items will clear the state's largest compliance bottleneck.")