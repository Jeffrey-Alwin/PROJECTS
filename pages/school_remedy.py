import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
import math
from streamlit_lottie import st_lottie
import streamlit.components.v1 as components
from utils import load_and_prep_data, render_navbar

st.set_page_config(page_title="Remedies", page_icon="🛠️", layout="wide")
render_navbar()


# --- LOTTIE ANIMATION LOADER ---
@st.cache_data
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()


lottie_remedy = load_lottieurl("https://lottie.host/9f50e185-9b2f-48e0-bb93-90d1edcf29f5/kLwE0Kj7X1.json")

# Load the ultimate dataset
df = load_and_prep_data()

# --- HEADER ---
c1, c2 = st.columns([4, 1])
with c1:
    st.title("🛠️ Remedy Engine")
    st.write("Target specific schools to generate appropriate remedies and suggestions")
with c2:
    if lottie_remedy: st_lottie(lottie_remedy, height=120, key="remedy_anim")

st.divider()

# --- DUAL-LAYER FILTERS ---
st.write("#####  Selection Criteria")
f1, f2, f3 = st.columns(3)

districts = sorted(df['district'].dropna().unique().tolist())
selected_dist = f1.selectbox("1. Select District:", ["Choose District"] + districts)

if selected_dist == "Choose District":
    st.info("Please select a District to begin.")
    st.stop()

# Filter blocks based on district
blocks = sorted(df[df['district'] == selected_dist]['block'].dropna().unique().tolist())
selected_block = f2.selectbox("2. Select Block:", ["Choose Block"] + blocks)

if selected_block == "Choose Block":
    st.info("Now select a Block to view school identifiers.")
    st.stop()

# Filter dataframe for the specific block
block_df = df[(df['district'] == selected_dist) & (df['block'] == selected_block)].copy()

# UDISE SEARCH FILTER
udise_options = ["Select Option", "All Critical Schools (Batch)"] + sorted(block_df['udise_code'].unique().tolist())
selected_udise = f3.selectbox("3. Select UDISE Code:", udise_options)


# --- THE BULLETPROOF REMEDY LOGIC ENGINE ---
def generate_action_plan(row):
    actions = []

    # BUG FIX 3: Safe Boolean check for unspent funds
    if row.get('overall_goodness', 100) < 50 and row.get('funds_utilized') != 1:
        actions.append("🚨 CRITICAL: Severe infrastructure failure, but grant funds are unspent! Initiate admin audit.")

    if row.get('classrooms_needs_major_repair', 0) > 0:
        actions.append(
            f"⚠️ DANGER: {int(row['classrooms_needs_major_repair'])} classrooms require immediate major structural repair.")

    if row.get('electricity') != 1: actions.append("⚡ Install Electrical Grid Connection")
    if row.get('drinking_water') != 1: actions.append("💧 Install Potable Water Source")
    if row.get('building') != 3: actions.append("🏗️ Upgrade to Pucca Building")
    if row.get('internet') != 1: actions.append("📡 Setup Internet Access")

    # BUG FIX 1: Flawless RTE Staffing Math using math.ceil()
    ts = row.get('total_students', 0)
    tch = row.get('total_tch', 0)
    if ts > 0:
        required_tch = math.ceil(ts / 30)
        deficit = required_tch - tch
        if deficit > 0:
            actions.append(f"👨‍🏫 High PTR: Hire/Deploy {int(deficit)} additional teachers")

    tg, tb = row.get('total_girls', 0), row.get('total_boys', 0)

    # Standard Sanitation
    if tg > 0 and (row.get('toilet_girls', 0) == 0 or (tg / max(row.get('toilet_girls', 1), 1) > 40)):
        actions.append("🚺 Construct additional Girls' Toilets")
    if tb > 0 and (row.get('toilet_boys', 0) == 0 or (tb / max(row.get('toilet_boys', 1), 1) > 40)):
        actions.append("🚹 Construct additional Boys' Toilets")

    # BUG FIX 2: CWSN Equity for both genders
    if tg > 0 and row.get('func_girls_cwsn_friendly') != 1:
        actions.append("♿ Install CWSN-friendly Girls' Toilet")
    if tb > 0 and row.get('func_boys_cwsn_friendly') != 1:
        actions.append("♿ Install CWSN-friendly Boys' Toilet")

    return " | ".join(actions) if actions else "✅ Fully Compliant"


# --- RENDER LOGIC ---
if selected_udise == "Select Option":
    st.write("---")
    st.info(
        " **Pro Tip:** Select a specific **UDISE Code** to see a single school, or choose **'All Critical Schools'** to see everything in this block.")
    st.stop()

# Prepare Data
if selected_udise == "All Critical Schools (Batch)":
    target_df = block_df.copy()
    render_trigger = st.button(" Generate All Action Plans for this Block")
else:
    target_df = block_df[block_df['udise_code'] == selected_udise]
    render_trigger = True

if render_trigger:
    target_df['Intervention Plan'] = target_df.apply(generate_action_plan, axis=1)
    critical_df = target_df[target_df['Intervention Plan'] != "✅ Fully Compliant"].copy()

    if critical_df.empty:
        st.success(f"🎉 No schools found with violations in the current selection.")
    else:
        # Summary Metrics
        plans_text = " ".join(critical_df['Intervention Plan'].tolist())
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Water Projects", plans_text.count("Potable Water"))
        with c2:
            st.metric("Power Projects", plans_text.count("Electrical"))
        with c3:
            st.metric("Teacher Deficits", plans_text.count("Hire/Deploy"))
        with c4:
            st.metric("Structural Risks", plans_text.count("DANGER"))

        st.divider()
        st.write(f"##### 📋 Intervention Action Cards")

        card_cols = st.columns(2)
        for index, (_, row) in enumerate(critical_df.iterrows()):
            with card_cols[index % 2]:
                with st.container(border=True):
                    st.markdown(f"### 🏫 {row['school_name']}")
                    st.markdown(f"**📍 UDISE ID:** `{row['udise_code']}`")

                    m1, m2 = st.columns(2)
                    m1.metric("Score", f"{row['overall_goodness']:.1f}")
                    m2.metric("Violations", int(row['violations']))

                    st.markdown("---")
                    tasks = row['Intervention Plan'].split(" | ")
                    for task in tasks:
                        if "CRITICAL" in task or "DANGER" in task:
                            st.error(task, icon="🚨")
                        else:
                            st.warning(task, icon="🔧")

        # Export
        csv = critical_df[['udise_code', 'school_name', 'Intervention Plan']].to_csv(index=False).encode('utf-8')
        st.download_button(" Export Action Plan (CSV)", data=csv, file_name=f"Remedy_{selected_udise}.csv",
                           type="primary")