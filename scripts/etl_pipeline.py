import pandas as pd
import numpy as np
import os

# ==========================
# 1. LOAD DATA
# ==========================
base = "E:/sample test  data/"

enr1 = pd.read_csv(base + "33_enr1.csv")
enr2 = pd.read_csv(base + "33_enr2.csv")
fac  = pd.read_csv(base + "33_fac.csv")
prof1 = pd.read_csv(base + "33_prof1.csv")
tch  = pd.read_csv(base + "33_tch.csv")

# ==========================
# 2. COMBINE ENROLLMENT FILES
# ==========================
enr = pd.concat([enr1, enr2], ignore_index=True)

# ==========================
# 3. CREATE ENROLLMENT FEATURES
# ==========================

# grade groups
primary_boys = ["c1_b","c2_b","c3_b","c4_b","c5_b"]
primary_girls = ["c1_g","c2_g","c3_g","c4_g","c5_g"]

middle_boys = ["c6_b","c7_b","c8_b"]
middle_girls = ["c6_g","c7_g","c8_g"]

high_boys = ["c9_b","c10_b"]
high_girls = ["c9_g","c10_g"]

hsec_boys = ["c11_b","c12_b"]
hsec_girls = ["c11_g","c12_g"]

# compute stage-wise counts
enr["primary_boys"] = enr[primary_boys].sum(axis=1)
enr["primary_girls"] = enr[primary_girls].sum(axis=1)

enr["middle_boys"] = enr[middle_boys].sum(axis=1)
enr["middle_girls"] = enr[middle_girls].sum(axis=1)

enr["high_boys"] = enr[high_boys].sum(axis=1)
enr["high_girls"] = enr[high_girls].sum(axis=1)

enr["higher_secondary_boys"] = enr[hsec_boys].sum(axis=1)
enr["higher_secondary_girls"] = enr[hsec_girls].sum(axis=1)

# total students
enr["total_students"] = (
    enr["primary_boys"] + enr["primary_girls"] +
    enr["middle_boys"] + enr["middle_girls"] +
    enr["high_boys"] + enr["high_girls"] +
    enr["higher_secondary_boys"] + enr["higher_secondary_girls"]
)

# ==========================
# 4. FIND DOMINANT CATEGORY (item_group)
# ==========================

student_cols = [c for c in enr.columns if "_b" in c or "_g" in c]
enr["row_students"] = enr[student_cols].sum(axis=1)

category = (
    enr.groupby(["pseudocode","item_group"])["row_students"]
    .sum()
    .reset_index()
)

idx = category.groupby("pseudocode")["row_students"].idxmax()
school_category = category.loc[idx][["pseudocode","item_group"]]

# ==========================
# 5. AGGREGATE ENROLLMENT PER SCHOOL
# ==========================

enr_school = enr.groupby("pseudocode").agg({
    "primary_boys":"sum",
    "primary_girls":"sum",
    "middle_boys":"sum",
    "middle_girls":"sum",
    "high_boys":"sum",
    "high_girls":"sum",
    "higher_secondary_boys":"sum",
    "higher_secondary_girls":"sum",
    "total_students":"sum"
}).reset_index()

# ==========================
# 6. TEACHER FEATURES
# ==========================

tch_school = tch.groupby("pseudocode").sum(numeric_only=True).reset_index()

tch_school["student_teacher_ratio"] = (
    enr_school["total_students"] / tch_school["total_tch"]
)

# ==========================
# 7. FACILITIES
# ==========================

fac_school = fac.groupby("pseudocode").sum(numeric_only=True).reset_index()

fac_school = fac_school.rename(columns={
    "electricity_availability":"electricity",
    "total_boys_toilet":"toilet_boys",
    "total_girls_toilet":"toilet_girls",
    "tap_fun_yn":"drinking_water",
    "building_status":"building"
})

# ==========================
# 8. PROFILE DATA
# ==========================

profile = prof1[[
    "pseudocode",
    "district",
    "block",
    "managment",
    "school_category",
    "rural_urban"
]]

profile = profile.rename(columns={"managment":"management"})

# ==========================
# 9. MERGE EVERYTHING
# ==========================

df = profile.merge(enr_school,on="pseudocode",how="left")
df = df.merge(school_category,on="pseudocode",how="left")
df = df.merge(tch_school,on="pseudocode",how="left")
df = df.merge(fac_school,on="pseudocode",how="left")

# ==========================
# 10. SELECT FINAL FEATURES
# ==========================

final_cols = [
"pseudocode",
"district",
"block",
"management",
"school_category",
"rural_urban",
"item_group",
"total_students",
"student_teacher_ratio",
"male",
"female",
"primary_boys",
"primary_girls",
"middle_boys",
"middle_girls",
"high_boys",
"high_girls",
"higher_secondary_boys",
"higher_secondary_girls",
"total_class_rooms",
"electricity",
"toilet_boys",
"toilet_girls",
"internet",
"drinking_water",
"building"
]

df = df[final_cols]

# ==========================
# 11. SAVE DATASET
# ==========================

save_path = "E:/SchoolResourceModel"
os.makedirs(save_path, exist_ok=True)

output_file = save_path + "/tamilnadu_school_dataset.csv"

df.to_csv(output_file, index=False)

print("Dataset created successfully")
print("Saved at:", output_file)
print("Dataset shape:", df.shape)
print(df)

# ==========================
# DOMINANT ITEM GROUP (excluding TOTAL = 8)
# ==========================

# columns that contain student counts
student_cols = [c for c in enr.columns if "_b" in c or "_g" in c]

# calculate total students for each row
enr["row_students"] = enr[student_cols].sum(axis=1)

# remove TOTAL category rows
enr_filtered = enr[enr["item_group"] != 8]

# compute total students per category per school
category = (
    enr_filtered
    .groupby(["pseudocode", "item_group"])["row_students"]
    .sum()
    .reset_index()
)

# find dominant category for each school
idx = category.groupby("pseudocode")["row_students"].idxmax()

school_category = category.loc[idx, ["pseudocode", "item_group"]].reset_index(drop=True)

print("Dominant item_group table created")
print(school_category.head())

df = df.drop(columns=["item_group"], errors="ignore")

df = df.merge(school_category, on="pseudocode", how="left")
print(school_category)