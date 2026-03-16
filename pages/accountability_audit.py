import streamlit as st
import pandas as pd
import requests
import re
import plotly.express as px
from streamlit_echarts import st_echarts
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
from utils import load_and_prep_data, render_navbar

# Changed page_icon to a classic institution building
st.set_page_config(page_title="Negligence-Audit", page_icon="🏛️", layout="wide")

render_navbar()


@st.cache_data
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()


lottie_audit = load_lottieurl("https://lottie.host/9618b04a-4d2b-426c-8509-31e42fec757d/uQx0q4f1Wn.json")

df = load_and_prep_data()

c1, c2 = st.columns([4, 1])
with c1:
    st.title("Administrative Accountability Audit")
    st.write("Cross-reference school failures with government oversight, local SMC activity, and financial negligence.")
with c2:
    if lottie_audit: st_lottie(lottie_audit, height=120, key="audit_anim")

st.divider()

st.write("##### Audit Filters")
f1, f2 = st.columns(2)

districts = ['Statewide (All Districts)'] + sorted(df['district'].dropna().unique().tolist())
selected_district = f1.selectbox("1. Select Region", districts)

dist_df = df.copy() if selected_district == 'Statewide (All Districts)' else df[df['district'] == selected_district]

managements = ['All Managements'] + sorted(dist_df['management'].dropna().unique().tolist())
selected_mgmt = f2.selectbox("2. Select Management Type", managements)

target_df = dist_df.copy() if selected_mgmt == 'All Managements' else dist_df[dist_df['management'] == selected_mgmt]

if target_df.empty:
    st.warning("No schools found matching these filters.", icon=":material/warning:")
    st.stop()


def animated_metric_card(label, value, color, material_icon, suffix=""):
    safe_id = re.sub(r'[^a-zA-Z0-9]', '_', label)
    is_float = isinstance(value, float)

    # Injected Google Material Symbols stylesheet for sharp, enterprise vectors
    html = f"""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    <div style="background: white; padding: 20px; border-radius: 12px; border-bottom: 4px solid {color}; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; transition: transform 0.2s; cursor: pointer;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
        <span class="material-symbols-outlined" style="font-size: 36px; color: {color}; margin-bottom: 5px;">{material_icon}</span>
        <div style="font-size: 32px; font-weight: 800; color: #1e293b;"><span id="n-{safe_id}">0</span>{suffix}</div>
        <div style="font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase;">{label}</div>
    </div>
    <script>
        const el = document.getElementById('n-{safe_id}');
        const target = parseFloat('{value}');
        const isF = {'true' if is_float else 'false'} === 'true';
        let start;
        const animate = (t) => {{
            if(!start) start = t;
            const p = Math.min((t - start) / 1000, 1);
            const ease = 1 - Math.pow(1 - p, 4);
            const val = ease * target;
            el.innerText = isF ? val.toFixed(1) : Math.floor(val).toLocaleString();
            if(p < 1) requestAnimationFrame(animate); else el.innerText = isF ? target.toFixed(1) : target.toLocaleString();
        }};
        requestAnimationFrame(animate);
    </script>
    """
    components.html(html, height=160)


target_df['safe_receipt'] = pd.to_numeric(target_df['grants_receipt'], errors='coerce').fillna(0)
target_df['safe_expenditure'] = pd.to_numeric(target_df['grants_expenditure'], errors='coerce').fillna(0)

ghost_schools = target_df[target_df['total_inspections'] == 0]

unspent_df = target_df[
    (target_df['safe_receipt'] > 0) & (target_df['safe_expenditure'] < target_df['safe_receipt'])].copy()
unspent_df['wasted_funds'] = unspent_df['safe_receipt'] - unspent_df['safe_expenditure']
total_wasted = unspent_df['wasted_funds'].sum()

no_smc = target_df[target_df['active_smc'] != 1]
avg_insp = target_df['total_inspections'].mean()

st.write(f"##### Negligence Overview: {selected_mgmt} in {selected_district}")
m1, m2, m3, m4 = st.columns(4)

# Swapped emojis for Google Material Icon names
with m1: animated_metric_card("Ghost Schools (0 Insp)", len(ghost_schools), "#ef4444", "domain_disabled")
with m2: animated_metric_card("Unutilized Grant Funds", int(total_wasted), "#f59e0b", "account_balance", " INR")
with m3: animated_metric_card("Schools w/ Inactive SMCs", len(no_smc), "#8b5cf6", "group_off")
with m4: animated_metric_card("Avg Inspections per School", round(avg_insp, 1) if pd.notna(avg_insp) else 0, "#10b981",
                              "fact_check")

st.divider()

col1, col2 = st.columns(2)

with col1:
    ghost_group_col = 'district' if selected_district == 'Statewide (All Districts)' else 'block'

    st.write(f"##### 'Ghost School' Leaderboard (by {ghost_group_col.title()})")
    st.write("Regions failing to dispatch government academic inspectors.")

    if ghost_schools.empty:
        st.success("No Ghost Schools found in this selection!", icon=":material/check_circle:")
    else:
        ghost_by_dist = ghost_schools.groupby(ghost_group_col).size().reset_index(name='count')
        ghost_by_dist = ghost_by_dist.sort_values('count', ascending=True).tail(10)

        dist_names = ghost_by_dist[ghost_group_col].tolist()
        dist_vals = ghost_by_dist['count'].tolist()

        ghost_options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"left": "3%", "right": "10%", "bottom": "3%", "top": "5%", "containLabel": True},
            "xAxis": {"type": "value", "splitLine": {"show": False}},
            "yAxis": {"type": "category", "data": dist_names, "axisLabel": {"fontWeight": "bold", "color": "#475569"}},
            "series": [
                {
                    "name": "Un-Inspected Schools",
                    "type": "bar",
                    "data": dist_vals,
                    "label": {"show": True, "position": "right", "color": "#ef4444", "fontWeight": "bold"},
                    "itemStyle": {
                        "color": "#ef4444",
                        "borderRadius": [0, 8, 8, 0],
                        "shadowBlur": 5,
                        "shadowColor": "rgba(239, 68, 68, 0.4)"
                    },
                    "animationDuration": 2000,
                    "animationEasing": "elasticOut"
                }
            ]
        }
        st_echarts(options=ghost_options, height="400px")

with col2:
    fin_group_col = 'management' if selected_mgmt == 'All Managements' else ghost_group_col

    st.write(f"##### Financial Negligence (by {fin_group_col.title()})")
    st.write("Grant money left unspent despite critical infrastructure deficits.")

    if unspent_df.empty or total_wasted == 0:
        st.success("All grant funds were utilized efficiently in this selection!", icon=":material/check_circle:")
    else:
        funds_by_mgmt = unspent_df.groupby(fin_group_col)['wasted_funds'].sum().reset_index()
        funds_by_mgmt = funds_by_mgmt.sort_values('wasted_funds', ascending=False).head(7)

        rose_data = [{"value": int(row['wasted_funds']), "name": row[fin_group_col]} for _, row in
                     funds_by_mgmt.iterrows()]

        rose_options = {
            "tooltip": {"trigger": "item", "formatter": "{b}: <br/> ₹{c} ({d}%)"},
            "legend": {"top": "bottom", "textStyle": {"fontSize": 10}},
            "series": [
                {
                    "name": "Unspent Funds",
                    "type": "pie",
                    "radius": ["20%", "70%"],
                    "center": ["50%", "45%"],
                    "roseType": "area",
                    "itemStyle": {"borderRadius": 8},
                    "data": rose_data,
                    "animationType": "scale",
                    "animationEasing": "elasticOut",
                    "animationDuration": 2000
                }
            ],
            "color": ["#f59e0b", "#f97316", "#ef4444", "#8b5cf6", "#3b82f6", "#10b981", "#64748b"]
        }
        st_echarts(options=rose_options, height="450px")

st.divider()

st.write("##### Regional Oversight Matrix (Aggregated by Block)")
st.write(
    "Analyzes the correlation between Local Parent Involvement (SMC) and Government Oversight. *Aggregated at the Block level to ensure rapid, lag-free performance.*")

block_agg = target_df.groupby(['district', 'block']).agg(
    avg_smc=('smc_smdc_meetings', 'mean'),
    avg_inspections=('total_inspections', 'mean'),
    avg_score=('overall_goodness', 'mean'),
    total_schools=('udise_code', 'count')
).reset_index()

if block_agg.empty:
    st.info("Insufficient data to generate oversight matrix for this selection.", icon=":material/info:")
else:
    fig_scatter = px.scatter(
        block_agg,
        x='avg_smc', y='avg_inspections',
        color='avg_score', size='total_schools',
        hover_name='block', hover_data={'district': True, 'avg_score': ':.1f', 'total_schools': True},
        color_continuous_scale='RdYlGn',
        labels={'avg_smc': 'Avg SMC Meetings (Parent Involvement)', 'avg_inspections': 'Avg Govt Inspections',
                'avg_score': 'Compliance Score'},
        size_max=40
    )

    smc_mean = df['smc_smdc_meetings'].mean()
    insp_mean = df['total_inspections'].mean()

    fig_scatter.add_hline(y=insp_mean, line_dash="dash", line_color="rgba(255,0,0,0.5)",
                          annotation_text="State Avg Inspections")
    fig_scatter.add_vline(x=smc_mean, line_dash="dash", line_color="rgba(0,0,255,0.5)",
                          annotation_text="State Avg SMC Meetings")

    fig_scatter.update_layout(margin=dict(l=20, r=20, t=30, b=20), coloraxis_colorbar=dict(title="Score"))
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()
st.write("##### Extreme Negligence Roster")
st.write(
    "Schools that require major structural repairs, yet have **0 Government Inspections** AND **Failed to utilize their grant money**.")

extreme_df = target_df[(target_df['total_inspections'] == 0) &
                       (target_df['funds_utilized'] != 1) &
                       (target_df['classrooms_needs_major_repair'] > 0)].copy()

if extreme_df.empty:
    st.success("No schools found matching the extreme negligence criteria in this selection!",
               icon=":material/check_circle:")
else:
    st.error(f"Found {len(extreme_df)} schools matching extreme administrative failure parameters.",
             icon=":material/warning:")
    display_cols = ['udise_code', 'school_name', 'district', 'block', 'management', 'classrooms_needs_major_repair',
                    'overall_goodness']

    clean_extreme = extreme_df[display_cols].rename(columns={
        'udise_code': 'UDISE', 'school_name': 'School', 'district': 'District', 'block': 'Block',
        'management': 'Management', 'classrooms_needs_major_repair': 'Classrooms Needing Repair',
        'overall_goodness': 'Score'
    })

    st.dataframe(clean_extreme.sort_values('Score'), use_container_width=True, hide_index=True)

with st.expander("The Data Translator: What is this actually telling us?", expanded=True):
    st.markdown("<h3 style='margin-bottom: 0; color: #f8fafc;'>Shattering Administrative Assumptions</h3>",
                unsafe_allow_html=True)
    st.write(
        "Raw numbers only tell half the story. Here is what the data reveals when we look deeper into the state's administrative habits.")
    st.write("")  # Spacer

    c1, c2, c3 = st.columns(3)

    with c1:
        st.info("**Myth:** *Schools are failing because they don't have enough funding.*", icon=":material/payments:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #60a5fa; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>Financial Negligence</b> chart. Millions of rupees are sitting unspent in school bank accounts. 
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            It is a <i>procurement bottleneck</i>. Schools lack the administrative training to hire contractors, file utilization certificates, and actually spend the grant money given to them.
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.warning("**Myth:** *Government inspections are the only way to ensure a school is safe.*",
                   icon=":material/policy:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #fbbf24; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>Regional Oversight Matrix</b>. Schools with highly active School Management Committees (local parents) often maintain strong safety scores even when inspectors rarely visit.
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            When a school has 0 inspections AND no active parent committee, it enters a dangerous blind spot where complete structural failure goes unnoticed.
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.error("**Myth:** *A broken classroom is just an 'old building' problem.*", icon=":material/domain_disabled:")
        st.markdown("""
        <div style="margin-top: 15px;">
            <span style="color: #f87171; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Reality</span><br>
            Look at the <b>Extreme Negligence Roster</b>. A broken classroom becomes an <i>administrative</i> failure when the school has the grant money to fix it, but hasn't spent it.
            <br><br>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">The Root Cause</span><br>
            A lack of localized leadership. These specific schools require immediate intervention from the District Collector to unblock funds and initiate repairs.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style="background: linear-gradient(90deg, #1e293b 0%, #334155 100%); padding: 20px; border-radius: 10px; color: white; text-align: center; margin-top: 20px; margin-bottom: 5px; border: 1px solid #475569;">
            <h4 style="color: #38bdf8; margin: 0; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; font-size: 0.95rem;">The Ultimate Takeaway</h4>
            <p style="margin: 10px 0 0 0; font-size: 1.05rem;">Throwing more money at the education system will not fix the infrastructure deficit. Fixing the <b>administrative friction</b> to spend the money we already have will.</p>
        </div>
    """, unsafe_allow_html=True)