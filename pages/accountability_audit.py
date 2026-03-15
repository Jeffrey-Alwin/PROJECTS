import streamlit as st
import pandas as pd
import requests
import re
import plotly.express as px
from streamlit_echarts import st_echarts
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
from utils import load_and_prep_data, render_navbar

st.set_page_config(page_title="Negligence-Audit", page_icon="👁️", layout="wide")

render_navbar()

# --- LOTTIE ANIMATION LOADER ---
@st.cache_data
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()


lottie_audit = load_lottieurl("https://lottie.host/9618b04a-4d2b-426c-8509-31e42fec757d/uQx0q4f1Wn.json")

df = load_and_prep_data()


# --- HEADER ---
c1, c2 = st.columns([4, 1])
with c1:
    st.title(" Administrative Accountability Audit")
    st.write("Cross-reference school failures with government oversight, local SMC activity, and financial negligence.")
with c2:
    if lottie_audit: st_lottie(lottie_audit, height=120, key="audit_anim")

st.divider()

# --- DUAL MASTER FILTERS ---
st.write("##### Audit Filters")
f1, f2 = st.columns(2)

districts = ['Statewide (All Districts)'] + sorted(df['district'].dropna().unique().tolist())
selected_district = f1.selectbox("1. Select Region", districts)

dist_df = df.copy() if selected_district == 'Statewide (All Districts)' else df[df['district'] == selected_district]

managements = ['All Managements'] + sorted(dist_df['management'].dropna().unique().tolist())
selected_mgmt = f2.selectbox("2. Select Management Type", managements)

target_df = dist_df.copy() if selected_mgmt == 'All Managements' else dist_df[dist_df['management'] == selected_mgmt]

if target_df.empty:
    st.warning("No schools found matching these filters.")
    st.stop()


# --- DYNAMIC METRICS ENGINE ---
def animated_metric_card(label, value, color, icon, suffix=""):
    safe_id = re.sub(r'[^a-zA-Z0-9]', '_', label)
    is_float = isinstance(value, float)
    html = f"""
    <div style="background: white; padding: 20px; border-radius: 12px; border-bottom: 4px solid {color}; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; transition: transform 0.2s; cursor: pointer;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size: 30px; margin-bottom: 5px;">{icon}</div>
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


# --- BULLETPROOF AUDIT MATH ---
# 1. Force NaNs to 0 so un-reported expenditure doesn't escape the audit
target_df['safe_receipt'] = pd.to_numeric(target_df['grants_receipt'], errors='coerce').fillna(0)
target_df['safe_expenditure'] = pd.to_numeric(target_df['grants_expenditure'], errors='coerce').fillna(0)

ghost_schools = target_df[target_df['total_inspections'] == 0]

unspent_df = target_df[(target_df['safe_receipt'] > 0) & (target_df['safe_expenditure'] < target_df['safe_receipt'])].copy()
unspent_df['wasted_funds'] = unspent_df['safe_receipt'] - unspent_df['safe_expenditure']
total_wasted = unspent_df['wasted_funds'].sum()

# 2. Strict Type-Safety: Catch False, 0, and NaNs
no_smc = target_df[target_df['active_smc'] != 1]
avg_insp = target_df['total_inspections'].mean()

st.write(f"##### 🚨 Negligence Overview: {selected_mgmt} in {selected_district}")
m1, m2, m3, m4 = st.columns(4)
with m1: animated_metric_card("Ghost Schools (0 Insp)", len(ghost_schools), "#ef4444", "👻")
with m2: animated_metric_card("Unutilized Grant Funds", int(total_wasted), "#f59e0b", "💸", " INR")
with m3: animated_metric_card("Schools w/ Inactive SMCs", len(no_smc), "#8b5cf6", "👨‍👩‍👧‍👦")
with m4: animated_metric_card("Avg Inspections per School", round(avg_insp, 1) if pd.notna(avg_insp) else 0, "#10b981", "📋")

st.divider()

col1, col2 = st.columns(2)

# --- 1. ECHARTS: THE GHOST SCHOOL LEADERBOARD ---
with col1:
    ghost_group_col = 'district' if selected_district == 'Statewide (All Districts)' else 'block'

    st.write(f"##### 📉 'Ghost School' Leaderboard (by {ghost_group_col.title()})")
    st.write("Regions failing to dispatch government academic inspectors.")

    if ghost_schools.empty:
        st.success("🎉 No Ghost Schools found in this selection!")
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

# --- 2. ECHARTS: FINANCIAL NEGLIGENCE ROSE CHART ---
with col2:
    fin_group_col = 'management' if selected_mgmt == 'All Managements' else ghost_group_col

    st.write(f"##### 💸 Financial Negligence (by {fin_group_col.title()})")
    st.write("Grant money left unspent despite critical infrastructure deficits.")

    if unspent_df.empty or total_wasted == 0:
        st.success("🎉 All grant funds were utilized efficiently in this selection!")
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

# --- 3. THE OVERSIGHT QUADRANT ---
st.write("##### ⚖️ Regional Oversight Matrix (Aggregated by Block)")
st.write("Analyzes the correlation between Local Parent Involvement (SMC) and Government Oversight. *Aggregated at the Block level to ensure rapid, lag-free performance.*")

block_agg = target_df.groupby(['district', 'block']).agg(
    avg_smc=('smc_smdc_meetings', 'mean'),
    avg_inspections=('total_inspections', 'mean'),
    avg_score=('overall_goodness', 'mean'),
    total_schools=('udise_code', 'count')
).reset_index()

# Removed the strict <15 filter to ensure high-performing outlier blocks are not deleted from the audit
if block_agg.empty:
    st.info("Insufficient data to generate oversight matrix for this selection.")
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

# --- 4. EXTREME NEGLIGENCE ROSTER ---
st.divider()
st.write("##### 🚨 Extreme Negligence Roster")
st.write("Schools that require major structural repairs, yet have **0 Government Inspections** AND **Failed to utilize their grant money**.")

# 3. Strict Type-Safety: Used != 1 to catch all variations of missing funds_utilized data
extreme_df = target_df[(target_df['total_inspections'] == 0) &
                       (target_df['funds_utilized'] != 1) &
                       (target_df['classrooms_needs_major_repair'] > 0)].copy()

if extreme_df.empty:
    st.success("🎉 No schools found matching the extreme negligence criteria in this selection!")
else:
    st.error(f"Found {len(extreme_df)} schools matching extreme administrative failure parameters.")
    display_cols = ['udise_code', 'school_name', 'district', 'block', 'management', 'classrooms_needs_major_repair',
                    'overall_goodness']

    clean_extreme = extreme_df[display_cols].rename(columns={
        'udise_code': 'UDISE', 'school_name': 'School', 'district': 'District', 'block': 'Block',
        'management': 'Management', 'classrooms_needs_major_repair': 'Classrooms Needing Repair',
        'overall_goodness': 'Score'
    })

    st.dataframe(clean_extreme.sort_values('Score'), use_container_width=True, hide_index=True)