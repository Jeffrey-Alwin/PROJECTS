import pandas as pd
import streamlit as st
import os


# 1. ADD show_spinner=False TO SILENCE THE ANNOYING POPUP
@st.cache_data(show_spinner=False)
def load_and_prep_data():
    """
    Loads the pre-compiled, mathematically verified master dataset.
    Guarantees sub-second load times and uses relative paths for cloud deployment.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "data", "cleansed", "tamilnadu_ultimate_master.csv")

    if not os.path.exists(file_path):
        st.error(f"🚨 Master database missing! Cannot locate: {file_path}")
        st.info("Check your GitHub repository to ensure the 'data/cleansed' folder was uploaded.")
        st.stop()

    df = pd.read_csv(file_path)

    # 2. MOVE THE TEXT CLEANING HERE (Runs once instead of every click!)
    if 'management' in df.columns:
        df['management'] = df['management'].astype(str).str.strip()

    # DATA SAFETY NET
    critical_cols = ['building', 'electricity', 'drinking_water', 'internet',
                     'toilet_boys', 'toilet_girls', 'total_boys', 'total_girls',
                     'ptr', 'total_students', 'total_class_rooms']

    for col in critical_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df


def render_navbar():
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
        st.page_link("pages/equity2.py", label="⚖️ EQUITY INDEX", use_container_width=True)

    st.markdown("<hr style='margin-top: 10px; margin-bottom: 30px;'>", unsafe_allow_html=True)