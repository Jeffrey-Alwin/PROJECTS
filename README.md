 Tamil Nadu Education Quality & Infrastructure Command Center
 
An end-to-end Educational Analytics dashboard designed to audit, benchmark, and generate remedy plans for the Tamil Nadu school system. This project translates raw UDISE+ government data into actionable policy insights.

 Live Demo
**Access the dashboard here:** https://tn-education-analytics.streamlit.app

---

 Project Overview
This Command Center serves as a "Digital Auditor" for the state education department. It moves beyond simple spreadsheets to identify critical failure points in regional infrastructure, gender equity, and educator workforce stability.

Key Analytical Modules:
* **Home:** Statewide KPI tracking for electricity, water, sanitation, and pucca building compliance.
* **Comparison:** Cascading regional filters to compare local school systems against statewide averages.
* **Gender Equity & Sanitation:** Normalized enrollment attrition analysis and tracking of the "Pipeline Drop-off" from Primary to Higher Secondary.
* **Teacher Command Center:** A "Working Conditions Index" that calculates educator stress based on PTR, isolation, and administrative burdens.
* **Remedies:** Generates school-specific PDF/CSV intervention plans for local administrators.

---

Tech Stack
Frontend & UI: [Streamlit](https://streamlit.io/) (Python-based web framework)
Data Processing: [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) (Vectorized performance optimization)
Visualizations: [ECharts](https://echarts.apache.org/) (High-performance animated charts via `streamlit-echarts`) and [Plotly Express](https://plotly.com/python/) (Complex statistical distributions)
Animation: [LottieFiles](https://lottiefiles.com/) (Interactive UI vectors)

---

Data Science Highlights
Performance Optimization: Utilized NumPy vectorization to replace slow Pandas `.apply()` loops, resulting in sub-100ms processing for 58,000+ records.
Statistical Integrity: Implemented True Regional PTR (Pupil-Teacher Ratio) calculations to avoid the "Mean of Ratios" fallacy.
Responsive UI: Developed custom HTML/JS animated metric cards that provide a premium SaaS-like feel within a Python environment.
Normalization: Normalized enrollment data across grade spans (Primary vs. Higher Secondary) to reveal true attrition rates regardless of school size.

---

Installation & Local Setup
1. Clone the repository:
   ```bash
   git clone [https://github.com/Jeffrey-Alwin/PROJECTS.git](https://github.com/Jeffrey-Alwin/PROJECTS.git)