import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
from streamlit_echarts import st_echarts
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
from utils import load_and_prep_data, render_navbar
import plotly.express as px

st.set_page_config(page_title="Gender Equity & Sanitation", page_icon="🚺", layout="wide")

render_navbar()

# --- LOTTIE ANIMATION LOADER ---
@st.cache_data(show_spinner=False)
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

lottie_equity = load_lottieurl("https://lottie.host/80dc18d8-fb5a-4e20-9118-a6d1dc40b490/CXZP5m2j9M.json")


# --- UNIFIED KPI ROW (1 IFRAME INSTEAD OF 4 FOR HIGH PERFORMANCE) ---
def render_kpi_row(kpis):
    cards_html = ""
    scripts = ""
    for i, kpi in enumerate(kpis):
        safe_val = float(kpi['value']) if pd.notna(kpi['value']) else 0.0
        cards_html += f"""
        <div style="flex: 1; min-width: 200px; padding: 15px; background: #f8fafc; border-radius: 8px; border-left: 4px solid {kpi['color']}; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <span style="color: #64748b; font-size: 14px; font-weight: 700; text-transform: uppercase;">{kpi['label']}</span><br>
            <span id="c-{i}" style="font-size: 32px; font-weight: 900; color: {kpi['color']};">0</span><span style="font-size: 20px; font-weight: 700; color: {kpi['color']};">{kpi.get('suffix', '')}</span>
        </div>
        """
        scripts += f"""
        setTimeout(() => {{
            const el_{i} = document.getElementById('c-{i}');
            const target_{i} = {safe_val};
            let start_{i};
            const animate_{i} = (t) => {{
                if(!start_{i}) start_{i} = t;
                const p = Math.min((t - start_{i}) / 1000, 1);
                const ease = 1 - Math.pow(1 - p, 4);
                let current = ease * target_{i};
                el_{i}.innerText = (current % 1 !== 0) ? current.toFixed(1) : Math.floor(current).toLocaleString();
                if(p < 1) requestAnimationFrame(animate_{i}); else el_{i}.innerText = (target_{i} % 1 !== 0) ? target_{i}.toFixed(1) : target_{i}.toLocaleString();
            }};
            requestAnimationFrame(animate_{i});
        }}, 50); // slight delay ensures DOM is ready
        """

    full_html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; display: flex; gap: 20px; flex-wrap: wrap; justify-content: space-between; width: 100%;">
        {cards_html}
    </div>
    <script>
        {scripts}
    </script>
    """
    components.html(full_html, height=120)


# Load Data
df = load_and_prep_data()

# --- ENGINEERING SPECIFIC EQUITY METRICS (VECTORIZED FOR SPEED) ---
df['girls_per_toilet'] = np.where(
    df['toilet_girls'] > 0,
    df['total_girls'] / df['toilet_girls'],
    np.where(df['total_girls'] > 0, 999, 0)
)
df['critical_sanitation'] = df['girls_per_toilet'] > 40


# --- HEADER ---
c1, c2 = st.columns([4, 1])
with c1:
    st.title("🚺 Gender Equity & Sanitation Audit")
    st.write("Tracking the correlation between female sanitation infrastructure, special needs inclusion, and middle-to-high school dropout rates.")
with c2:
    if lottie_equity: st_lottie(lottie_equity, height=100, key="eq_anim")

st.divider()


# --- TOP LEVEL KPIs ---
st.write("##### 🚨 Statewide Risk Profile")

valid_ratios = df[df['toilet_girls'] > 0]['girls_per_toilet']
avg_ratio = valid_ratios.mean() if not valid_ratios.empty else 0

kpi_data = [
    {"label": "Total Female Enrollment", "value": df['total_girls'].sum(), "color": "#d946ef", "suffix": ""},
    {"label": "Zero Girls Toilets (Active)", "value": len(df[(df['toilet_girls'] == 0) & (df['total_girls'] > 0)]), "color": "#ef4444", "suffix": ""},
    {"label": "RTE Violations (>40:1 Ratio)", "value": len(df[df['critical_sanitation']]), "color": "#f97316", "suffix": ""},
    {"label": "State Avg Girls/Toilet", "value": avg_ratio, "color": "#8b5cf6", "suffix": ":1"}
]

render_kpi_row(kpi_data)

st.divider()


# --- 1. ECHARTS: THE NORMALIZED DROPOUT THESIS ---
st.write("##### 📉 The Pipeline Drop-off: Normalized Enrollment Attrition")
st.write("Normalized by dividing stage totals by the number of grades to reveal true dropout velocity.")

raw_girls = [df['primary_girls'].sum(), df['middle_girls'].sum(), df['high_girls'].sum(), df['higher_secondary_girls'].sum()]
raw_boys = [df['primary_boys'].sum(), df['middle_boys'].sum(), df['high_boys'].sum(), df['higher_secondary_boys'].sum()]
norm_factors = [5, 3, 2, 2]

girls_norm = [int(total / factor) for total, factor in zip(raw_girls, norm_factors)]
boys_norm = [int(total / factor) for total, factor in zip(raw_boys, norm_factors)]
stages = ['Primary (Gr 1-5)', 'Middle (Gr 6-8)', 'High (Gr 9-10)', 'Hr Sec (Gr 11-12)']

attrition_options = {
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "legend": {"data": ["Avg Girls per Grade", "Avg Boys per Grade"], "top": "0%"},
    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
    "xAxis": [{"type": "category", "boundaryGap": False, "data": stages,
               "axisLabel": {"fontWeight": "bold", "color": "#475569"}}],
    "yAxis": [{"type": "value", "name": "Students per Grade", "axisLabel": {"color": "#475569"}}],
    "series": [
        {
            "name": "Avg Girls per Grade", "type": "line", "smooth": True,
            "lineStyle": {"width": 4, "color": "#ec4899"},
            "itemStyle": {"color": "#ec4899"},
            "areaStyle": {"color": "rgba(236, 72, 153, 0.2)"},
            "data": girls_norm, "animationDuration": 2000
        },
        {
            "name": "Avg Boys per Grade", "type": "line", "smooth": True,
            "lineStyle": {"width": 4, "color": "#3b82f6"},
            "itemStyle": {"color": "#3b82f6"},
            "areaStyle": {"color": "rgba(59, 130, 246, 0.2)"},
            "data": boys_norm, "animationDuration": 2000
        }
    ]
}

col_chart, col_text = st.columns([2.5, 1])
with col_chart:
    st_echarts(options=attrition_options, height="400px")
with col_text:
    girl_drop = ((girls_norm[0] - girls_norm[-1]) / girls_norm[0]) * 100 if girls_norm[0] > 0 else 0
    boy_drop = ((boys_norm[0] - boys_norm[-1]) / boys_norm[0]) * 100 if boys_norm[0] > 0 else 0
    # 1. Determine the right words based on the math
    girl_word = "drops" if girl_drop > 0 else "increases"
    boy_word = "drop" if boy_drop > 0 else "increase"

    # 2. Build the core sentence using absolute values (removes the minus sign)
    insight_text = f"**Insight:** Female enrollment {girl_word} by **{abs(girl_drop):.1f}%** from Primary to Higher Secondary, compared to a **{abs(boy_drop):.1f}%** {boy_word} for males."

    # 3. Apply the right context and color (Red for drops, Green for increases)
    if girl_drop > 0:
        insight_text += " Lack of proper sanitation in higher grades is a known catalyst for this attrition."
        st.error(insight_text)
    else:
        insight_text += " This positive retention indicates strong upper-level continuation or incoming migration."
        st.success(insight_text)
st.divider()

col_pie, col_bar = st.columns(2)

with col_pie:
    st.write("##### ⚖️ Statewide Sanitation Severity")

    schools_with_girls = df[df['total_girls'] > 0]
    compliant = len(schools_with_girls[schools_with_girls['girls_per_toilet'] <= 40])
    crisis = len(schools_with_girls[(schools_with_girls['girls_per_toilet'] > 40) & (schools_with_girls['girls_per_toilet'] < 999)])
    no_toilets = len(schools_with_girls[schools_with_girls['girls_per_toilet'] == 999])

    pie_options = {
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} Schools ({d}%)"},
        "legend": {"bottom": "0%", "textStyle": {"fontWeight": "bold"}},
        "series": [{
            "type": "pie", "radius": ["40%", "70%"], "avoidLabelOverlap": False,
            "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": False},
            "data": [
                {"value": compliant, "name": "Compliant (<40:1)", "itemStyle": {"color": "#10b981"}},
                {"value": crisis, "name": "RTE Crisis (>40:1)", "itemStyle": {"color": "#f59e0b"}},
                {"value": no_toilets, "name": "Zero Facilities", "itemStyle": {"color": "#ef4444"}}
            ],
            "animationType": "scale", "animationEasing": "elasticOut", "animationDuration": 2000
        }]
    }
    st_echarts(options=pie_options, height="350px")

with col_bar:
    st.write("##### ♿ CWSN Negligence by Management")

    cwsn_df = df[(df['total_girls'] > 0) & (df['func_girls_cwsn_friendly'] != 1)]
    cwsn_mgmt = cwsn_df.groupby('management').size().reset_index(name='count').sort_values('count', ascending=True).tail(7)

    bar_options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "3%", "right": "10%", "bottom": "10%", "top": "5%", "containLabel": True},
        "xAxis": {"type": "value", "splitLine": {"show": False}},
        "yAxis": {"type": "category", "data": cwsn_mgmt['management'].tolist(), "axisLabel": {"fontWeight": "bold", "color": "#475569"}},
        "series": [{
            "name": "Schools Missing CWSN Toilets", "type": "bar", "data": cwsn_mgmt['count'].tolist(),
            "label": {"show": True, "position": "right", "color": "#8b5cf6", "fontWeight": "bold"},
            "itemStyle": {"color": "#8b5cf6", "borderRadius": [0, 5, 5, 0]},
            "animationDuration": 2000, "animationEasing": "cubicOut"
        }]
    }
    st_echarts(options=bar_options, height="350px")

st.divider()


# --- THE GEOGRAPHIC DIVIDE: RURAL VS URBAN EQUITY ---
st.write("##### 🌍 The Geographic Divide: Rural vs. Urban Equity")
st.write("Does a student's location dictate their resources? Comparing overcrowding and infrastructure across geographies.")

if 'rural_urban' in df.columns:
    geo_df = df.copy()
    geo_df['Geography'] = geo_df['rural_urban'].map({1: 'Rural', 2: 'Urban'}).fillna('Unknown')
    geo_clean = geo_df[geo_df['Geography'] != 'Unknown']

    if not geo_clean.empty:
        c_geo1, c_geo2 = st.columns(2)

        with c_geo1:
            st.write("**Classroom Overcrowding Severity**")
            st.write(
                "Grouping schools into strict policy buckets based on their Pupil-Teacher Ratio (RTE Limit: 30:1).")

            ptr_df = geo_clean[geo_clean['ptr'] > 0].copy()

            # 1. Create strict policy buckets
            bins = [0, 30, 40, 60, 9999]
            labels = ['Compliant (≤30)', 'Overcrowded (31-40)', 'Severe (41-60)', 'Crisis (>60)']
            ptr_df['Severity'] = pd.cut(ptr_df['ptr'], bins=bins, labels=labels)

            # 2. Pivot the data so ECharts can read it easily
            severity_counts = ptr_df.groupby(['Geography', 'Severity']).size().unstack(fill_value=0)
            geographies = severity_counts.index.tolist()

            # 3. Build the Animated ECharts Series
            colors = ['#10b981', '#f59e0b', '#ef4444', '#7f1d1d']
            series_data = []

            for i, label in enumerate(labels):
                if label in severity_counts.columns:
                    series_data.append({
                        "name": label,
                        "type": "bar",
                        "data": severity_counts[label].tolist(),
                        "itemStyle": {"color": colors[i], "borderRadius": [4, 4, 0, 0]},
                        "label": {"show": True, "position": "top", "color": "#475569", "fontWeight": "bold"},
                        "animationDuration": 2000,
                        "animationEasing": "elasticOut"
                    })

            # 4. Compile the ECharts Options
            bar_options = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "legend": {"bottom": "0%", "textStyle": {"fontWeight": "bold", "color": "#475569"}},
                "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "10%", "containLabel": True},
                "xAxis": {
                    "type": "category",
                    "data": geographies,
                    "axisLabel": {"fontWeight": "bold", "fontSize": 14, "color": "#1e293b"},
                    "axisTick": {"show": False}
                },
                "yAxis": {
                    "type": "value",
                    "splitLine": {"lineStyle": {"color": "#e2e8f0", "type": "dashed"}},
                    "axisLabel": {"color": "#64748b"}
                },
                "series": series_data
            }

            st_echarts(options=bar_options, height="400px")

        with c_geo2:
            st.write("**The Infrastructure Gap (Radar)**")
            st.write("Visualizing the disparity in basic physical and digital resources.")

            def get_geo_metrics(geography):
                subset = geo_clean[geo_clean['Geography'] == geography]
                if subset.empty: return [0, 0, 0, 0]
                return [
                    (subset['electricity'] == 1).mean() * 100,
                    (subset['internet'] == 1).mean() * 100,
                    (subset['drinking_water'] == 1).mean() * 100,
                    (subset['building'] == 3).mean() * 100
                ]

            rural_metrics = get_geo_metrics('Rural')
            urban_metrics = get_geo_metrics('Urban')

            radar_options = {
                "tooltip": {"trigger": "item"},
                "legend": {"bottom": 0, "textStyle": {"fontWeight": "bold"}},
                "radar": {
                    "indicator": [
                        {"name": "Power Grid", "max": 100},
                        {"name": "Internet Access", "max": 100},
                        {"name": "Drinking Water", "max": 100},
                        {"name": "Pucca Building", "max": 100}
                    ],
                    "center": ["50%", "45%"],
                    "radius": "65%",
                    "splitArea": {"areaStyle": {"color": ["#f8fafc", "#f1f5f9", "#e2e8f0", "#cbd5e1"]}}
                },
                "series": [{
                    "type": "radar",
                    "data": [
                        {
                            "value": rural_metrics,
                            "name": "Rural Schools",
                            "itemStyle": {"color": "#10b981"},
                            "areaStyle": {"color": "rgba(16, 185, 129, 0.4)"},
                            "lineStyle": {"width": 3}
                        },
                        {
                            "value": urban_metrics,
                            "name": "Urban Schools",
                            "itemStyle": {"color": "#3b82f6"},
                            "areaStyle": {"color": "rgba(59, 130, 246, 0.4)"},
                            "lineStyle": {"width": 3}
                        }
                    ],
                    "animationDuration": 2000,
                    "animationEasing": "cubicOut"
                }]
            }
            st_echarts(options=radar_options, height="400px")
    else:
        st.info("Insufficient Rural/Urban data for this selection.")
else:
    st.info("Rural/Urban demographic column not found in dataset.")

st.divider()


# --- ACTIONABLE INTERVENTION LIST ---
st.write("##### 🎯 Priority Intervention Targets (Top 50 Critical Ratios)")
st.write("These schools have female students enrolled but represent the most severe violations of basic sanitation dignity.")

critical_df = df[(df['total_girls'] > 0) & (df['girls_per_toilet'] > 40)].sort_values(by='girls_per_toilet', ascending=False)
show_df = critical_df[['udise_code', 'school_name', 'district', 'management', 'total_girls', 'toilet_girls', 'girls_per_toilet']].head(50).copy()

show_df['girls_per_toilet'] = show_df['girls_per_toilet'].apply(lambda x: "🚨 0 Toilets Available" if x == 999 else f"{int(x)}:1")
show_df.rename(
    columns={'udise_code': 'UDISE', 'school_name': 'School Name', 'district': 'District', 'management': 'Management',
             'total_girls': 'Total Girls', 'toilet_girls': 'Girls Toilets', 'girls_per_toilet': 'Current Ratio'},
    inplace=True)

st.dataframe(show_df, use_container_width=True, hide_index=True)