import streamlit as st
import pandas as pd
import requests
import re
from streamlit_echarts import st_echarts
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
from utils import load_and_prep_data, render_navbar

st.set_page_config(page_title="Teacher Center", page_icon="🧑‍🏫", layout="wide")

render_navbar()



@st.cache_data
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()


lottie_teacher = load_lottieurl("https://lottie.host/7e0de9d5-78ef-410a-85d7-3932cf2b71e1/Z8j5Wp7mYh.json")

df = load_and_prep_data()



def calculate_comfort_score(row):
    score = 100


    tch = row.get('total_tch', 0)
    students = row.get('total_students', 0)
    if tch <= 1 and students > 0: score -= 20


    if row.get('classrooms_needs_major_repair', 0) > 0: score -= 15


    if row.get('electricity') != 1 or row.get('drinking_water') != 1 or row.get('functional_toilets', 1) == 0:
        score -= 15


    if row.get('ptr', 0) > 30: score -= 15


    if row.get('approachable_road', 1) != 1: score -= 10


    if row.get('teacher_involve_non_training_assignment', 0) > 0: score -= 10

    # BUG FIX 3: Bulletproof Booleans for Admin neglect
    if row.get('active_smc') != 1: score -= 10
    if row.get('funds_utilized') != 1: score -= 5

    return max(0, score)



df['teacher_comfort_score'] = df.apply(calculate_comfort_score, axis=1)


c1, c2 = st.columns([4, 1])
with c1:
    st.title("🧑‍🏫 Educator Workforce Analytics")
    st.write("Analyzing staff allocations, contractual reliance, digital readiness, and working conditions.")
with c2:
    if lottie_teacher: st_lottie(lottie_teacher, height=120, key="tch_anim")

st.divider()


st.write("##### Target Workforce Filters")
col1, col2, col3 = st.columns(3)

with col1:
    districts = ['Statewide (All Districts)'] + sorted(df['district'].dropna().unique().tolist())
    selected_district = st.selectbox("1. Select Region", districts)

dist_df = df.copy() if selected_district == 'Statewide (All Districts)' else df[df['district'] == selected_district]

with col2:
    blocks = ['All Blocks'] + sorted(dist_df['block'].dropna().unique().tolist())
    selected_block = st.selectbox("2. Select Block", blocks)

block_df = dist_df.copy() if selected_block == 'All Blocks' else dist_df[dist_df['block'] == selected_block]

with col3:
    managements = ['All Managements'] + sorted(block_df['management'].dropna().unique().tolist())
    selected_mgmt = st.selectbox("3. Select Management Type", managements)

target_df = block_df.copy() if selected_mgmt == 'All Managements' else block_df[block_df['management'] == selected_mgmt]

if target_df.empty:
    st.warning("No schools found matching these filters.")
    st.stop()

location_text = selected_district if selected_block == 'All Blocks' else f"{selected_block}, {selected_district}"


if selected_district == 'Statewide (All Districts)':
    group_col = 'district'
elif selected_block == 'All Blocks':
    group_col = 'block'
else:
    group_col = 'school_name'



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



total_teachers = target_df['total_tch'].sum()
total_students = target_df['total_students'].sum()
contract_pct = (target_df['contract'].sum() / total_teachers * 100) if total_teachers > 0 else 0
avg_comfort = target_df['teacher_comfort_score'].mean()


avg_ptr = (total_students / total_teachers) if total_teachers > 0 else 0

st.write(f"##### 📊 Workforce Baseline: {selected_mgmt} in {location_text}")
m1, m2, m3, m4 = st.columns(4)
with m1: animated_metric_card("Total Teaching Staff", int(total_teachers), "#3b82f6", "👨‍🏫")
with m2: animated_metric_card("True Regional PTR", round(avg_ptr, 1), "#10b981", "⚖️", ":1")
with m3: animated_metric_card("Contractual Reliance", round(contract_pct, 1), "#f59e0b", "📑", "%")
with m4: animated_metric_card("Avg Environment Score", round(avg_comfort, 1), "#8b5cf6", "🌡️", "/100")

st.divider()


st.write("##### 🌡️ The Working Conditions Index")
st.write(
    "A custom metric evaluating educator stress based on overcrowding, physical safety, sanitation, and admin burnout.")

col_gauge, col_hist = st.columns([1, 1.5])

with col_gauge:
    gauge_color = "#10b981" if avg_comfort >= 80 else "#f59e0b" if avg_comfort >= 60 else "#ef4444"

    gauge_options = {
        "series": [
            {
                "type": "gauge",
                "startAngle": 180, "endAngle": 0, "min": 0, "max": 100,
                "splitNumber": 10,
                "itemStyle": {"color": gauge_color, "shadowColor": "rgba(0,0,0,0.1)", "shadowBlur": 10},
                "progress": {"show": True, "roundCap": True, "width": 18},
                "pointer": {"length": "12%", "width": 15, "offsetCenter": [0, "-60%"], "itemStyle": {"color": "auto"}},
                "axisLine": {"roundCap": True, "lineStyle": {"width": 18}},
                "axisTick": {"show": False}, "splitLine": {"show": False}, "axisLabel": {"show": False},
                "detail": {
                    "backgroundColor": "#fff", "borderColor": gauge_color, "borderWidth": 2, "width": "60%",
                    "lineHeight": 40, "height": 40, "borderRadius": 8, "offsetCenter": [0, "35%"],
                    "valueAnimation": True, "formatter": "{value}/100", "color": "auto", "fontWeight": "bolder",
                    "fontSize": 20
                },
                "data": [{"value": round(avg_comfort, 1) if pd.notna(avg_comfort) else 0}]
            }
        ]
    }
    st_echarts(options=gauge_options, height="350px")

with col_hist:
    bins = [0, 20, 40, 60, 80, 100]
    labels = ['0-20', '21-40', '41-60', '61-80', '81-100']

    hist_counts = pd.cut(target_df['teacher_comfort_score'], bins=bins, labels=labels,
                         include_lowest=True).value_counts().sort_index()

    hist_options = {
        "title": {
            "text": "Distribution of Educator Stress Levels",
            "left": "center",
            "textStyle": {"fontSize": 15, "color": "#1e293b", "fontFamily": "sans-serif"}
        },
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "5%", "right": "5%", "bottom": "15%", "top": "15%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"color": "#64748b", "fontWeight": "bold"},
            "name": "Working Conditions Score (Out of 100)",
            "nameLocation": "middle",
            "nameGap": 30
        },
        "yAxis": {
            "type": "value",
            "name": "Number of Schools",
            "axisLabel": {"color": "#64748b"}
        },
        "series": [{
            "name": "Schools",
            "type": "bar",
            "data": hist_counts.tolist(),
            "itemStyle": {
                "color": "#8b5cf6",
                "borderRadius": [4, 4, 0, 0]
            },
            "barWidth": "95%",
            "animationDuration": 2000,
            "animationEasing": "cubicOut"
        }]
    }

    st_echarts(options=hist_options, height="350px")

st.divider()

col1, col2 = st.columns(2)


with col1:
    st.write(f"##### 🏢 Workforce Stability (by {group_col.title().replace('_', ' ')})")

    staff_group = target_df.groupby(group_col)[['regular', 'contract', 'total_tch']].sum().reset_index()
    staff_group['contract_ratio'] = staff_group['contract'] / staff_group['total_tch'].replace(0, 1)
    staff_group = staff_group.sort_values('contract_ratio', ascending=True).tail(10)

    bar_options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {"bottom": 0, "textStyle": {"fontWeight": "bold"}},
        "grid": {"left": "3%", "right": "4%", "bottom": "10%", "top": "5%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": staff_group[group_col].tolist(), "axisLabel": {"fontWeight": "bold"}},
        "series": [
            {"name": "Regular Staff", "type": "bar", "stack": "total",
             "itemStyle": {"color": "#3b82f6", "borderRadius": [5, 0, 0, 5]}, "data": staff_group['regular'].tolist(),
             "animationDuration": 2000},
            {"name": "Contract Staff", "type": "bar", "stack": "total",
             "itemStyle": {"color": "#f59e0b", "borderRadius": [0, 5, 5, 0]}, "data": staff_group['contract'].tolist(),
             "animationDuration": 2000}
        ]
    }
    st_echarts(options=bar_options, height="400px")


with col2:
    st.write("##### 💻 The Digital Skill Mismatch")

    trained = target_df['trained_comp'].sum()
    untrained = max(0, total_teachers - trained)  # Prevents negative numbers if bad data exists

    doughnut_options = {
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} Teachers ({d}%)"},
        "legend": {"bottom": 0, "textStyle": {"fontWeight": "bold"}},
        "series": [
            {
                "name": "Digital Training", "type": "pie", "radius": ["45%", "70%"], "avoidLabelOverlap": False,
                "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2},
                "label": {"show": False, "position": "center"},
                "emphasis": {"label": {"show": True, "fontSize": "20", "fontWeight": "bold"}},
                "data": [
                    {"value": int(trained), "name": "Digitally Trained", "itemStyle": {"color": "#00BA97"}},
                    {"value": int(untrained), "name": "Lacks Digital Training", "itemStyle": {"color": "#001F17"}}
                ],
                "animationType": "scale", "animationEasing": "elasticOut", "animationDuration": 2000
            }
        ]
    }
    st_echarts(options=doughnut_options, height="400px")

st.divider()

col3, col4 = st.columns(2)


with col3:
    st.write("##### 📋 Extracurricular Admin Burdens")

    if 'teacher_involve_non_training_assignment' in target_df.columns:
        burnout_df = target_df[target_df['teacher_involve_non_training_assignment'] > 0]
        if not burnout_df.empty:
            burn_group = burnout_df.groupby(group_col).size().reset_index(name='count')
            burn_group = burn_group.sort_values('count', ascending=False).head(20)

            tree_data = [{"name": str(row[group_col]), "value": int(row['count'])} for _, row in burn_group.iterrows()]

            min_val = int(burn_group['count'].min())
            max_val = int(burn_group['count'].max())

            if min_val == max_val:
                max_val += 1

            heatmap_options = {
                "title": {
                    "text": f"Top {group_col.title().replace('_', ' ')}s by Administrative Burden",
                    "left": "center",
                    "textStyle": {"fontSize": 13, "color": "#64748b", "fontWeight": "normal"}
                },
                "tooltip": {
                    "trigger": "item",
                    "formatter": "<b>{b}</b><br/>Affected Schools: {c}",
                    "backgroundColor": "rgba(255, 255, 255, 0.95)",
                    "borderColor": "#e2e8f0",
                    "textStyle": {"color": "#1e293b"}
                },
                "visualMap": {
                    "type": "continuous",
                    "min": min_val,
                    "max": max_val,
                    "inRange": {
                        "color": ["#e9d5ff", "#a855f7", "#4c1d95"]
                    },
                    "show": False
                },
                "series": [{
                    "type": "treemap",
                    "data": tree_data,
                    "width": "100%",
                    "height": "85%",
                    "roam": False,
                    "nodeClick": False,
                    "breadcrumb": {"show": False},
                    "label": {
                        "show": True,
                        "formatter": "{b}\n{c}",
                        "color": "#ffffff",
                        "fontWeight": "bold"
                    },
                    "itemStyle": {
                        "borderColor": "#ffffff",
                        "borderWidth": 2,
                        "gapWidth": 2
                    },
                    "animationDurationUpdate": 1000
                }]
            }

            st_echarts(options=heatmap_options, height="400px")
        else:
            st.success("🎉 No schools reported non-academic staff burdens in this selection!")
    else:
        st.info("Non-academic assignment data unavailable.")


with col4:
    st.write("##### 🚨 The 'Lone Educator' Roster")


    lone_df = target_df[(target_df['total_tch'] <= 1) & (target_df['total_students'] > 0)].copy()

    if lone_df.empty:
        st.success(f"🎉 No critically understaffed schools found in {location_text}.")
    else:
        st.error(f"**CRITICAL ALARM:** {len(lone_df)} schools operate with 1 or 0 assigned teachers.")

        if group_col == 'school_name':
            display_cols = ['udise_code', 'school_name', 'total_students', 'total_tch']
            rename_map = {'udise_code': 'UDISE', 'school_name': 'School Name', 'total_students': 'Students',
                          'total_tch': 'Teachers'}
        else:
            display_cols = ['udise_code', 'school_name', group_col, 'total_students', 'total_tch']
            rename_map = {'udise_code': 'UDISE', 'school_name': 'School Name',
                          group_col: group_col.title().replace('_', ' '), 'total_students': 'Students',
                          'total_tch': 'Teachers'}

        display_df = lone_df[display_cols].sort_values('total_students', ascending=False)
        display_df.rename(columns=rename_map, inplace=True)

        st.dataframe(display_df.head(50), use_container_width=True, hide_index=True, height=350)