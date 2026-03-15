# 🏫 Tamil Nadu Educational Equity Engine

A production-grade resource allocation and benchmarking dashboard designed to optimize government funding for schools in Tamil Nadu using UDISE+ open data.

## 🚀 Project Overview
This tool shifts educational data analysis from descriptive statistics to prescriptive analytics. It calculates a custom **Multivariate Goodness/Priority Score** for schools, enabling policymakers to dynamically identify critical infrastructure gaps and automatically generate resource allocation remedies.

### Key Features
* **Macro-Analytics (State-Wide):** Tracks foundational government mandates (RTE Pupil-Teacher Ratios, basic utility access).
* **Micro-Analytics (School-Level):** A search-based allocator that calculates exact numerical remedies (e.g., "Allocate 3 Teachers," "Build 2 Toilets") based on current enrollment.
* **Category Benchmarking:** Interactive Plotly visualizations comparing feature-wise adequacy across Government, Private, and Aided institutions.

## 🛠️ Technical Architecture
* **Language:** Python
* **Data Engineering:** Pandas, Scikit-Learn (MinMax Scaling, Composite Indexing)
* **Frontend/Deployment:** Streamlit Multipage Application (MPA)
* **Visualizations:** Plotly Express

## 🧠 The Mathematics (Scoring Logic)
The engine calculates "Need Ratios" (Students per Resource), normalizes them to resolve magnitude discrepancies using Min-Max scaling, and applies a weighted formula to calculate an overall `Goodness Score` (0.0 to 1.0) and `Priority Score`.

## 💻 How to Run Locally
1. Clone the repository: `git clone <your-repo-link>`
2. Install dependencies: `pip install -r requirements.txt`
3. Launch the app: `streamlit run app.py`