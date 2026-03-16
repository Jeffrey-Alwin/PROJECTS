import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import re
from streamlit_lottie import st_lottie
from streamlit_echarts import st_echarts
import plotly.express as px
from utils import load_and_prep_data, render_navbar

st.set_page_config(page_title="District Analytics", page_icon="📍", layout="wide")
render_navbar()


@st.cache_data
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

lottie_analytics = load_lottieurl("https://lottie.host/2847da95-00c5-4386-90c7-23420084a9e5/4c4n1O1QnK.json")

# Load the dataset
df = load_and_prep_data()



col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title(" District & Management Analytics")
    st.write("Compare local school systems against statewide benchmarks and identify extreme outliers.")
with col_head2:
    if lottie_analytics:
        st_lottie(lottie_analytics, height=120, key="header_anim")

st.divider()


st.write("#####  Regional & Management Filters")
col1, col2, col3 = st.columns(3)

with col1:
    districts = ['Statewide (All Districts)'] + sorted(df['district'].dropna().unique().tolist())
    selected_district = st.selectbox("1. Select District", districts)

dist_df = df.copy() if selected_district == 'Statewide (All Districts)' else df[df['district'] == selected_district]

with col2:
    blocks = ['All Blocks'] + sorted(dist_df['block'].dropna().unique().tolist())
    selected_block = st.selectbox("2. Select Block", blocks)

block_df = dist_df.copy() if selected_block == 'All Blocks' else dist_df[dist_df['block'] == selected_block]

with col3:

    managements = ['All Managements'] + sorted(block_df['management'].dropna().unique().tolist())
    selected_mgmt = st.selectbox("3. Select Management Type", managements)


target_df = block_df.copy() if selected_mgmt == 'All Managements' else block_df[block_df['management'] == selected_mgmt]



def animated_metric(label, value, suffix="", delta=None):
    safe_id = re.sub(r'[^a-zA-Z0-9]', '_', label)
    is_float = isinstance(value, float)


    delta_html = ""
    if delta is not None:
        color = "#10b981" if delta >= 0 else "#ef4444"
        arrow = "↑" if delta >= 0 else "↓"
        delta_html = f"<div style='color: {color}; font-size: 14px; font-weight: bold; margin-top: 5px;'>{arrow} {abs(delta):.1f} vs State Avg</div>"

    html_code = f"""
    <div style="font-family: 'Segoe UI', sans-serif; background: #f8fafc; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #e2e8f0; transition: transform 0.2s ease; cursor: pointer;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
        <div style="color: #64748b; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">{label}</div>
        <div style="font-size: 42px; font-weight: 800; color: #4f46e5;">
            <span id="n-{safe_id}">0</span><span style="font-size: 22px; color: #94a3b8; margin-left: 4px;">{suffix}</span>
        </div>
        {delta_html}
    </div>
    <script>
        const el = document.getElementById('n-{safe_id}');
        const target = parseFloat('{value}');
        const isF = {'true' if is_float else 'false'} === 'true';
        let start;
        const animate = (t) => {{
            if(!start) start = t;
            const p = Math.min((t - start) / 1200, 1);
            const ease = 1 - Math.pow(1 - p, 4);
            const val = ease * target;
            el.innerText = isF ? val.toFixed(1) : Math.floor(val).toLocaleString();
            if(p < 1) requestAnimationFrame(animate); else el.innerText = isF ? target.toFixed(1) : target.toLocaleString();
        }};
        requestAnimationFrame(animate);
    </script>
    """
    components.html(html_code, height=160)


location_text = selected_district if selected_block == 'All Blocks' else f"{selected_block}, {selected_district}"
st.subheader(f"📊 Profile: {selected_mgmt} ({location_text})")

if target_df.empty:
    st.warning("No schools found for this specific District, Block, and Management combination.")
else:

    statewide_avg = df['overall_goodness'].mean()
    local_avg = target_df['overall_goodness'].mean()
    benchmark_delta = local_avg - statewide_avg

    m1, m2, m3 = st.columns(3)
    with m1:
        animated_metric("Total Schools", len(target_df))
    with m2:
        animated_metric("Total Students", int(target_df['total_students'].sum()))
    with m3:
        animated_metric("Average Score", round(local_avg, 1), suffix="/ 100", delta=benchmark_delta)

    st.divider()


    st.write("##### Compliance Health Profile")


    compliance_data = {
        'Power Grid': (target_df['electricity'] == 1).mean() * 100,
        'Drinking Water': (target_df['drinking_water'] == 1).mean() * 100,
        'Pucca Buildings': (target_df['building'] == 3).mean() * 100,
        'Internet Access': (target_df['internet'] == 1).mean() * 100,
        'Active SMC': (target_df['active_smc'] == 1).mean() * 100,
        'Funds Utilized': (target_df['funds_utilized'] == 1).mean() * 100,
        'RTE Entitlements': (target_df['entitlements_met'] == 1).mean() * 100,
        'Teacher Ratio': ((target_df['ptr'] > 0) & (target_df['ptr'] <= 30)).mean() * 100
    }

    comp_df = pd.DataFrame(list(compliance_data.items()), columns=['Feature', 'Score'])
    comp_df_sorted = comp_df.sort_values(by='Score', ascending=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        radar_options = {
            "title": {"text": "System Footprint", "left": "center",
                      "textStyle": {"color": "#444", "fontSize": 24, "fontFamily": "Segoe UI"}},
            "tooltip": {"trigger": "item"},
            "radar": {
                "radius": "75%", "center": ["50%", "55%"],
                "indicator": [{"name": f, "max": 100} for f in comp_df['Feature']],
                "splitArea": {"show": True, "areaStyle": {"color": ["rgba(250,250,250,0.3)", "rgba(200,200,200,0.1)"]}},
                "axisName": {"color": "#666", "fontSize": 15, "fontFamily": "Segoe UI", "fontWeight": "bold"}
            },
            "series": [{
                "name": "Compliance", "type": "radar",
                "data": [{"value": comp_df['Score'].tolist(), "name": "Score (%)"}],
                "itemStyle": {"color": "#4f46e5"}, "areaStyle": {"color": "rgba(79, 70, 229, 0.3)"},
                "lineStyle": {"width": 4}
            }],
            "animationDuration": 2000, "animationEasing": "cubicOut", "animationDurationUpdate": 1000
        }
        st_echarts(options=radar_options, height="550px")

    with col_chart2:
        bar_data = [{"value": round(s, 1),
                     "itemStyle": {"color": '#ef4444' if s < 50 else '#f59e0b' if s < 80 else '#10b981',
                                   "borderRadius": [0, 6, 6, 0]}} for s in comp_df_sorted['Score']]
        bar_options = {
            "title": {"text": "Strengths vs. Critical Needs", "left": "center",
                      "textStyle": {"color": "#444", "fontSize": 24, "fontFamily": "Segoe UI"}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"left": "2%", "right": "15%", "bottom": "5%", "top": "15%", "containLabel": True},
            "xAxis": {"type": "value", "max": 100, "splitLine": {"show": False}, "axisLabel": {"show": False}},
            "yAxis": {"type": "category", "data": comp_df_sorted['Feature'].tolist(), "axisLine": {"show": False},
                      "axisTick": {"show": False},
                      "axisLabel": {"color": "#666", "fontFamily": "Segoe UI", "fontWeight": "bold", "fontSize": 15}},
            "series": [{"type": "bar", "data": bar_data,
                        "label": {"show": True, "position": "right", "formatter": "{c}%", "color": "#666",
                                  "fontWeight": "bold", "fontSize": 16}}],
            "animationDuration": 2000, "animationEasing": "elasticOut", "animationDurationUpdate": 1000
        }
        st_echarts(options=bar_options, height="550px")

    st.divider()


    st.write("##### 🏫 Local School Rankings")

    tab1, tab2 = st.tabs(["🏆 Top 50 Premier Schools", "🚨 Bottom 50 Critical Needs"])
    display_cols = ['udise_code', 'school_name', 'district', 'overall_goodness', 'total_students']

    def prep_table(dataframe):
        # Ensured that if a column is missing, it doesn't crash the table
        valid_cols = [col for col in display_cols if col in dataframe.columns]
        clean_df = dataframe[valid_cols].copy()
        clean_df.rename(columns={'udise_code': 'UDISE Code', 'school_name': 'School Name', 'district': 'District',
                                 'overall_goodness': 'Compliance Score', 'total_students': 'Students'}, inplace=True)
        return clean_df

    table_config = {
        "School Name": st.column_config.TextColumn("School Name", width="large"),
        "Compliance Score": st.column_config.ProgressColumn("Compliance Score", format="%d / 100", min_value=0,
                                                            max_value=100)
    }

    with tab1:
        top_50_df = target_df.sort_values(by='overall_goodness', ascending=False).head(50)
        st.dataframe(prep_table(top_50_df), use_container_width=True, hide_index=True, height=400,
                     column_config=table_config)

    with tab2:
        bot_50_df = target_df.sort_values(by='overall_goodness', ascending=True).head(50)
        st.dataframe(prep_table(bot_50_df), use_container_width=True, hide_index=True, height=400,
                     column_config=table_config)


    st.divider()
    st.write(f"##### 🌍Footprints: {selected_mgmt} in {location_text}")

    st.write("**Targeted Demographic Overview**")

    rural_pct = (target_df['rural_urban'] == 1).mean() * 100 if 'rural_urban' in target_df.columns else 0
    female_pct = (target_df['total_girls'].sum() / target_df['total_students'].sum()) * 100 if target_df['total_students'].sum() > 0 else 0
    total_teachers = int(target_df['total_tch'].sum()) if 'total_tch' in target_df.columns else 0
    repair_rate = (target_df['classrooms_needs_major_repair'] > 0).mean() * 100 if 'classrooms_needs_major_repair' in target_df.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        animated_metric("Rural Concentration", round(rural_pct, 1), suffix="%")
    with k2:
        animated_metric("Female Student Ratio", round(female_pct, 1), suffix="%")
    with k3:
        animated_metric("Total Educator Workforce", total_teachers)
    with k4:
        animated_metric("Requires Major Repairs", round(repair_rate, 1), suffix="%")

    st.write("---")

    col_mac1, col_mac2 = st.columns([1, 1.5])


    with col_mac1:
        st.write("**🚧 Geographic Isolation**")
        if 'approachable_road' in target_df.columns:
            isolated = target_df[target_df['approachable_road'] != 1]
            if not isolated.empty:
                st.error(
                    f"**Isolation Alert:** {len(isolated)} targeted schools lack an approachable all-weather road. These schools face severe logistical delays.")
                with st.expander("View Isolated Schools Data"):
                    st.dataframe(
                        isolated[['udise_code', 'school_name', 'district', 'overall_goodness']].reset_index(drop=True),
                        use_container_width=True)
            else:
                st.success(f"✅ All targeted schools have approachable road access.")
        else:
            st.info("Road access data unavailable.")


    with col_mac2:
        st.write("**🏙️ Infrastructure Equity: Rural vs. Urban**")
        if 'rural_urban' in target_df.columns:
            df_geography = target_df.copy()
            df_geography['Location'] = df_geography['rural_urban'].map({1: 'Rural', 2: 'Urban'}).fillna('Unknown')
            clean_geo = df_geography[df_geography['Location'] != 'Unknown']

            if not clean_geo.empty:
                fig_ru = px.box(
                    clean_geo, x="Location", y="overall_goodness", color="Location",
                    color_discrete_map={'Rural': '#10b981', 'Urban': '#3b82f6'},
                    title=f"Compliance Spread for {selected_mgmt}"
                )
                fig_ru.update_layout(transition=dict(duration=500), margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_ru, use_container_width=True)
            else:
                st.info("No Rural/Urban data available for this specific selection.")
        else:
            st.info("Rural/Urban demographic data is not currently mapped in the dataset.")