import streamlit as st
import pandas as pd
import requests
import re
import streamlit.components.v1 as components
from utils import load_and_prep_data, render_navbar

# Updated page icon to a clean building/construction theme
st.set_page_config(page_title="Budget Allocation", page_icon="🏗️", layout="wide")

render_navbar()


@st.cache_data
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()


lottie_tools = load_lottieurl("https://lottie.host/e2d08a54-71eb-47eb-ba04-a6217dc3c675/6XWz6GfIq8.json")


def animated_counter(label, value, color="#10b981", material_icon="assessment"):
    safe_id = re.sub(r'[^a-zA-Z0-9]', '_', label)
    safe_value = int(value) if pd.notna(value) else 0

    # Injected Google Material Symbols for sharp enterprise vectors
    html_code = f"""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    <div style="font-family: 'Segoe UI', sans-serif; text-align: center; padding: 15px 0; border-radius: 8px; background-color: #f8fafc; border: 1px solid #e2e8f0; transition: transform 0.2s ease;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
        <span class="material-symbols-outlined" style="font-size: 28px; color: {color}; margin-bottom: 5px; display: block;">{material_icon}</span>
        <span style="color: #64748b; font-size: 13px; font-weight: 700; text-transform: uppercase;">{label}</span><br>
        <span id="c-{safe_id}" style="font-size: 28px; font-weight: 800; color: {color};">0</span>
    </div>
    <script>
        const el = document.getElementById('c-{safe_id}');
        const target = parseInt('{safe_value}');
        let start;
        const animate = (t) => {{
            if(!start) start = t;
            const p = Math.min((t - start) / 1000, 1);
            const ease = 1 - Math.pow(1 - p, 4);
            el.innerText = Math.floor(ease * target).toLocaleString();
            if(p < 1) requestAnimationFrame(animate); else el.innerText = target.toLocaleString();
        }};
        requestAnimationFrame(animate);
    </script>
    """
    components.html(html_code, height=125)


df = load_and_prep_data()

c1, c2 = st.columns([4, 1])
with c1:
    st.title("Infrastructure Work Orders")
    st.write("Translating dataset deficits into physical procurement requirements.")
with c2:
    from streamlit_lottie import st_lottie

    if lottie_tools: st_lottie(lottie_tools, height=100, key="tool_anim")

st.divider()

st.write("##### Target Filter")
col1, col2, col3 = st.columns(3)

with col1:
    districts = ['All Regions'] + sorted(df['district'].dropna().unique().tolist())
    selected_dist = st.selectbox("1. Select Target Region", districts)

dist_df = df.copy() if selected_dist == 'All Regions' else df[df['district'] == selected_dist]

with col2:
    blocks = ['All Blocks'] + sorted(dist_df['block'].dropna().unique().tolist())
    selected_block = st.selectbox("2. Select Block", blocks)

block_df = dist_df.copy() if selected_block == 'All Blocks' else dist_df[dist_df['block'] == selected_block]

with col3:
    managements = ['All Managements'] + sorted(block_df['management'].dropna().unique().tolist())
    selected_mgmt = st.selectbox("3. Select Management Type", managements)

target_df = block_df.copy() if selected_mgmt == 'All Managements' else block_df[block_df['management'] == selected_mgmt]

missing_water = len(target_df[target_df['drinking_water'] != 1])
missing_power = len(target_df[target_df['electricity'] != 1])
missing_internet = len(target_df[target_df['internet'] != 1])
dilapidated_buildings = len(target_df[target_df['building'] != 3])

missing_toilets = len(target_df[
                          ((target_df['total_boys'] > 0) & (target_df['toilet_boys'] == 0)) |
                          ((target_df['total_girls'] > 0) & (target_df['toilet_girls'] == 0))
                          ])

location_text = selected_dist if selected_block == 'All Blocks' else f"{selected_block}, {selected_dist}"
st.write(f"##### Procurement Totals: {selected_mgmt} in {location_text}")

k1, k2, k3, k4, k5 = st.columns(5)
with k1: animated_counter("RO Plants Needed", missing_water, "#3b82f6", "water_drop")
with k2: animated_counter("Grid Connections", missing_power, "#f59e0b", "bolt")
with k3: animated_counter("Broadband Routers", missing_internet, "#8b5cf6", "wifi")
with k4: animated_counter("Pucca Upgrades", dilapidated_buildings, "#ef4444", "foundation")
with k5: animated_counter("Sanitation Blocks", missing_toilets, "#10b981", "wc")

st.divider()

st.write("##### Generate Specific Work Orders")
st.write("Export a list of schools requiring specific physical interventions.")

order_type = st.radio("Select Procurement Category:", [
    "Drinking Water Installations",
    "Electrical Grid Connections",
    "Broadband / Internet Setup",
    "Structural / Building Upgrades",
    "Sanitation / Toilet Blocks",
    "Student Entitlements (Books & Uniforms)"
], horizontal=False)

export_df = pd.DataFrame()

if order_type == "Drinking Water Installations":
    export_df = target_df[target_df['drinking_water'] != 1][
        ['udise_code', 'school_name', 'block', 'district', 'total_students']].copy()
    if not export_df.empty: export_df['Item to Procure'] = "1x High-Capacity RO Water Purifier"
elif order_type == "Electrical Grid Connections":
    export_df = target_df[target_df['electricity'] != 1][
        ['udise_code', 'school_name', 'block', 'district', 'total_students']].copy()
    if not export_df.empty: export_df['Item to Procure'] = "1x Standard Grid Connection & Wiring"
elif order_type == "Broadband / Internet Setup":
    export_df = target_df[target_df['internet'] != 1][
        ['udise_code', 'school_name', 'block', 'district', 'total_students']].copy()
    if not export_df.empty: export_df['Item to Procure'] = "1x Commercial Broadband Router"
elif order_type == "Structural / Building Upgrades":
    export_df = target_df[target_df['building'] != 3][
        ['udise_code', 'school_name', 'block', 'district', 'total_students']].copy()
    if not export_df.empty: export_df['Item to Procure'] = "Major Civil Works Contract"
elif order_type == "Sanitation / Toilet Blocks":
    export_df = target_df[
        ((target_df['total_boys'] > 0) & (target_df['toilet_boys'] == 0)) |
        ((target_df['total_girls'] > 0) & (target_df['toilet_girls'] == 0))
        ][['udise_code', 'school_name', 'block', 'district', 'total_students']].copy()
    if not export_df.empty: export_df['Item to Procure'] = "1x Standard Sanitation Block"
elif order_type == "Student Entitlements (Books & Uniforms)":
    export_df = target_df[target_df['entitlements_met'] != 1][
        ['udise_code', 'school_name', 'block', 'district', 'total_students']].copy()
    if not export_df.empty: export_df['Item to Procure'] = "Standard Student Entitlement Kits"

if not export_df.empty:
    st.dataframe(export_df.sort_values(by='total_students', ascending=False), use_container_width=True, hide_index=True)

    costs = {
        "Drinking Water Installations": 25000,
        "Electrical Grid Connections": 15000,
        "Broadband / Internet Setup": 8000,
        "Structural / Building Upgrades": 500000,
        "Sanitation / Toilet Blocks": 120000,
        "Student Entitlements (Books & Uniforms)": 1500
    }

    if order_type == "Student Entitlements (Books & Uniforms)":
        total_students_needing_kits = export_df['total_students'].sum()
        est_budget = total_students_needing_kits * costs.get(order_type, 0)
    else:
        est_budget = len(export_df) * costs.get(order_type, 0)

    st.success(f"**Estimated Budget Required for {location_text}:** ₹ {est_budget:,.2f}",
               icon=":material/account_balance:")

    csv = export_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Work Order (CSV)", data=csv, file_name=f"{order_type}_Orders.csv", mime='text/csv',
                       type="primary")
else:
    st.success(f"No interventions required for **{order_type}** in {location_text}.", icon=":material/check_circle:")

with st.expander("The Data Translator: What is this actually telling us?", expanded=True):
    st.markdown("<h3 style='margin-bottom: 0; color: #f8fafc;'>Shattering Procurement Assumptions</h3>",
                unsafe_allow_html=True)
    st.write(
        "Translating percentages into purchase orders. Here is the reality of funding and fixing state infrastructure.")
    st.write("")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.info("**Myth:** *Fixing the education system requires an infinite, unknowable budget.*",
                icon=":material/account_balance:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #60a5fa; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>Procurement Totals</b>. The deficit is entirely finite and quantifiable. We know exactly how many RO plants and routers are missing down to the individual block.
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            The "Black Hole" funding myth is used as an excuse for inaction. By isolating specific items (like internet or water), the budget becomes actionable rather than overwhelming.
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.warning("**Myth:** *All infrastructure problems require the same bureaucratic approval.*",
                   icon=":material/construction:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #fbbf24; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>Estimated Budgets</b>. A structural building upgrade is a massive Capital Expenditure (CapEx) requiring civil engineers. A broadband router is a micro-procurement.
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            Treating a ₹8,000 router installation with the same red tape as a ₹5,00,000 building reconstruction creates fatal delays for basic necessities.
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.error("**Myth:** *Identifying the deficit is the hardest part of the job.*", icon=":material/receipt_long:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #f87171; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>Download Work Order (CSV)</b> button. This dashboard instantly generates the shopping list, but it cannot force the state to execute the purchase.
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            Supply chain breakdown. The true bottleneck is usually found in the tendering process, corrupt local contracting, or a failure to deliver materials to geographically isolated schools.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style="background: linear-gradient(90deg, #1e293b 0%, #334155 100%); padding: 20px; border-radius: 10px; color: white; text-align: center; margin-top: 20px; margin-bottom: 5px; border: 1px solid #475569;">
            <h4 style="color: #38bdf8; margin: 0; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; font-size: 0.95rem;">The Ultimate Takeaway</h4>
            <p style="margin: 10px 0 0 0; font-size: 1.05rem;">Data without logistics is useless. This tool provides the exact cost and location for every intervention. The next step requires <b>supply chain execution</b> to turn these CSVs into physical assets.</p>
        </div>
    """, unsafe_allow_html=True)