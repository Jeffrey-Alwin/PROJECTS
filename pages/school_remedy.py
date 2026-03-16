import math
import requests
import streamlit as st
from streamlit_lottie import st_lottie
from utils import load_and_prep_data, render_navbar

# Cleaned the page icon to a professional tool symbol
st.set_page_config(page_title="Remedies", page_icon="build", layout="wide")
render_navbar()

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
    st.title("Remedy Engine")
    st.write("Target specific schools to generate appropriate remedies and suggestions.")
with c2:
    if lottie_remedy: st_lottie(lottie_remedy, height=120, key="remedy_anim")

st.divider()

# --- DUAL-LAYER FILTERS ---
st.write("##### Selection Criteria")
f1, f2, f3 = st.columns(3)

districts = sorted(df['district'].dropna().unique().tolist())
selected_dist = f1.selectbox("1. Select District:", ["Choose District"] + districts)

if selected_dist == "Choose District":
    st.info("Please select a District to begin.", icon=":material/info:")
    st.stop()

# Filter blocks based on district
blocks = sorted(df[df['district'] == selected_dist]['block'].dropna().unique().tolist())
selected_block = f2.selectbox("2. Select Block:", ["Choose Block"] + blocks)

if selected_block == "Choose Block":
    st.info("Now select a Block to view school identifiers.", icon=":material/info:")
    st.stop()

# Filter dataframe for the specific block
block_df = df[(df['district'] == selected_dist) & (df['block'] == selected_block)].copy()

# UDISE SEARCH FILTER
udise_options = ["Select Option", "All Critical Schools (Batch)"] + sorted(block_df['udise_code'].unique().tolist())
selected_udise = f3.selectbox("3. Select UDISE Code:", udise_options)

def generate_action_plan(row):
    actions = []

    # BUG FIX 3: Safe Boolean check for unspent funds
    if row.get('overall_goodness', 100) < 50 and row.get('funds_utilized') != 1:
        actions.append("CRITICAL: Severe infrastructure failure, but grant funds are unspent! Initiate admin audit.")

    if row.get('classrooms_needs_major_repair', 0) > 0:
        actions.append(
            f"DANGER: {int(row['classrooms_needs_major_repair'])} classrooms require immediate major structural repair.")

    if row.get('electricity') != 1: actions.append("Install Electrical Grid Connection")
    if row.get('drinking_water') != 1: actions.append("Install Potable Water Source")
    if row.get('building') != 3: actions.append("Upgrade to Pucca Building")
    if row.get('internet') != 1: actions.append("Setup Internet Access")

    ts = row.get('total_students', 0)
    tch = row.get('total_tch', 0)
    if ts > 0:
        required_tch = math.ceil(ts / 30)
        deficit = required_tch - tch
        if deficit > 0:
            actions.append(f"High PTR: Hire/Deploy {int(deficit)} additional teachers")

    tg, tb = row.get('total_girls', 0), row.get('total_boys', 0)

    if tg > 0 and (row.get('toilet_girls', 0) == 0 or (tg / max(row.get('toilet_girls', 1), 1) > 40)):
        actions.append("Construct additional Girls' Toilets")
    if tb > 0 and (row.get('toilet_boys', 0) == 0 or (tb / max(row.get('toilet_boys', 1), 1) > 40)):
        actions.append("Construct additional Boys' Toilets")

    if tg > 0 and row.get('func_girls_cwsn_friendly') != 1:
        actions.append("Install CWSN-friendly Girls' Toilet")
    if tb > 0 and row.get('func_boys_cwsn_friendly') != 1:
        actions.append("Install CWSN-friendly Boys' Toilet")

    return " | ".join(actions) if actions else "Fully Compliant"

if selected_udise == "Select Option":
    st.write("---")
    st.info(
        "**Pro Tip:** Select a specific **UDISE Code** to see a single school, or choose **'All Critical Schools'** to see everything in this block.", icon=":material/lightbulb:")
    st.stop()

if selected_udise == "All Critical Schools (Batch)":
    target_df = block_df.copy()
    render_trigger = st.button("Generate All Action Plans for this Block")
else:
    target_df = block_df[block_df['udise_code'] == selected_udise]
    render_trigger = True

if render_trigger:
    target_df['Intervention Plan'] = target_df.apply(generate_action_plan, axis=1)
    critical_df = target_df[target_df['Intervention Plan'] != "Fully Compliant"].copy()

    if critical_df.empty:
        st.success("No schools found with violations in the current selection.", icon=":material/check_circle:")
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
        st.write("##### Intervention Action Cards")

        card_cols = st.columns(2)
        for index, (_, row) in enumerate(critical_df.iterrows()):
            with card_cols[index % 2]:
                with st.container(border=True):
                    st.markdown(f"### {row['school_name']}")
                    st.markdown(f"**UDISE ID:** `{row['udise_code']}`")

                    m1, m2 = st.columns(2)
                    m1.metric("Score", f"{row['overall_goodness']:.1f}")
                    m2.metric("Violations", int(row['violations']))

                    st.markdown("---")
                    tasks = row['Intervention Plan'].split(" | ")
                    for task in tasks:
                        if "CRITICAL" in task or "DANGER" in task:
                            st.error(task, icon=":material/warning:")
                        else:
                            st.warning(task, icon=":material/build:")

        csv = critical_df[['udise_code', 'school_name', 'Intervention Plan']].to_csv(index=False).encode('utf-8')
        st.download_button("Export Action Plan (CSV)", data=csv, file_name=f"Remedy_{selected_udise}.csv",
                           type="primary")

# --- ENTERPRISE 'MYTH VS REALITY' INTERPRETATION ---
with st.expander("The Data Translator: What is this actually telling us?", expanded=True):
    st.markdown("<h3 style='margin-bottom: 0; color: #f8fafc;'>Shattering Policy Assumptions</h3>",
                unsafe_allow_html=True)
    st.write(
        "True reform happens at the micro-level. Here is the reality of executing state-level policies on individual school campuses.")
    st.write("")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.info("**Myth:** *Statewide education reform requires a single, unified, macro-level strategy.*",
                icon=":material/account_tree:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #60a5fa; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>Intervention Action Cards</b>. A school needing a RO water plant requires a completely different administrative pipeline than a school needing 4 new teachers.
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            Macro-policies fail because they do not account for micro-deficits. Effective administration requires isolating interventions down to the individual UDISE code.
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.warning("**Myth:** *Schools with low compliance scores simply need better principals.*",
                   icon=":material/person_alert:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #fbbf24; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>CRITICAL</b> and <b>DANGER</b> alerts inside the cards. These schools are failing because they are physically crumbling or severely understaffed.
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            Systemic physical neglect. You cannot manage or lead your way out of a collapsed roof or a 100:1 pupil-teacher ratio without hard capital intervention.
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.error("**Myth:** *Identifying the problem is the hardest part of solving it.*", icon=":material/done_all:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #f87171; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>Export Action Plan (CSV)</b> button. We have instantly identified exactly what needs to be fixed. However, exporting a CSV does not pour concrete.
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            Execution friction. The final hurdle is always localized supply chain logistics, budget unlocking, and contractor deployment.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style="background: linear-gradient(90deg, #1e293b 0%, #334155 100%); padding: 20px; border-radius: 10px; color: white; text-align: center; margin-top: 20px; margin-bottom: 5px; border: 1px solid #475569;">
            <h4 style="color: #38bdf8; margin: 0; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; font-size: 0.95rem;">The Ultimate Takeaway</h4>
            <p style="margin: 10px 0 0 0; font-size: 1.05rem;">Data analytics has done its job: it has removed the guesswork. The burden now shifts entirely from the data scientist to the local administrator to execute these exact remedies.</p>
        </div>
    """, unsafe_allow_html=True)