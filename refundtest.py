import streamlit as st
import pandas as pd

st.set_page_config(page_title="Refund Processing System", layout="wide")

st.title("Admission Fee Refund Processing")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx","xls"])

if uploaded_file:

    df = pd.read_excel(uploaded_file, engine="openpyxl")

    st.subheader("Data Preview")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    # ----------------------------------------------------
    # Detect allotment rounds automatically
    # ----------------------------------------------------
    allot_cols = [c for c in columns if c.startswith("Allot_")]
    join_cols = [c for c in columns if c.startswith("JoinStatus_")]

    st.sidebar.header("Configuration")

    # ----------------------------------------------------
    # Total remitted fee components
    # ----------------------------------------------------
    fee_components = st.sidebar.multiselect(
        "Select Fee Components for Total Remitted Fee",
        columns
    )

    if fee_components:
        df["Total_Remitted_Fee"] = df[fee_components].fillna(0).sum(axis=1)
    else:
        df["Total_Remitted_Fee"] = 0

    # ----------------------------------------------------
    # Fee to Allotment Mapping
    # ----------------------------------------------------
    st.sidebar.subheader("Fee → Allotment Mapping")

    allotment_map = {}

    for allot in allot_cols:
        allotment_map[allot] = st.sidebar.multiselect(
            f"Fees linked to {allot}",
            fee_components,
            key=allot
        )

    # ----------------------------------------------------
    # Forfeit calculation
    # ----------------------------------------------------
    def calculate_forfeit(row):

        forfeited = 0
    
        for allot_col in allot_cols:
    
            round_no = allot_col.split("_")[1]
            join_col = f"JoinStatus_{round_no}"
    
            allot_val = row.get(allot_col)
            join_status = str(row.get(join_col,"")).strip().upper()
    
            # check if allotment exists
            if pd.notna(allot_val) and str(allot_val).strip() != "":
    
                # non join or TC
                if join_status in ["N","TC"]:
    
                    mapped_fees = allotment_map.get(allot_col, [])
    
                    for fee_col in mapped_fees:
    
                        value = row.get(fee_col,0)
    
                        if pd.notna(value):
                            forfeited += float(value)
    
        return forfeited
           
    df["Forfeited_Amount"] = df.apply(calculate_forfeit, axis=1)

    # ----------------------------------------------------
    # Refund logic
    # ----------------------------------------------------
    def calculate_refund(row):

        total_remitted = row.get("Total_Remitted_Fee", 0)
        forfeited = row.get("Forfeited_Amount", 0)

        has_allotment = any(
            pd.notna(row.get(c)) and str(row.get(c)).strip() != ""
            for c in allot_cols
        )

        curr_admn = row.get("Curr_Admn")

        # Rule 1 : No allotment → Full refund
        if not has_allotment:
            return total_remitted

        # Rule 2 : Candidate joined
        if pd.notna(curr_admn) and str(curr_admn).strip() != "":
            return total_remitted - forfeited

        # Rule 3 : Allotted but not joined
        if has_allotment and (pd.isna(curr_admn) or str(curr_admn).strip() == ""):
            return 0

        return 0

    df["Refund_Amount"] = df.apply(calculate_refund, axis=1)

    # ----------------------------------------------------
    # Summary metrics
    # ----------------------------------------------------
    total_remitted = df["Total_Remitted_Fee"].sum()
    total_forfeit = df["Forfeited_Amount"].sum()
    total_refund = df["Refund_Amount"].sum()

    refund_candidates = (df["Refund_Amount"] > 0).sum()
    forfeit_candidates = (df["Forfeited_Amount"] > 0).sum()

    st.subheader("Summary Dashboard")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total Remitted", f"{total_remitted:,.0f}")
    c2.metric("Total Forfeited", f"{total_forfeit:,.0f}")
    c3.metric("Total Refund", f"{total_refund:,.0f}")
    c4.metric("Refund Candidates", refund_candidates)
    c5.metric("Forfeit Candidates", forfeit_candidates)

    # ----------------------------------------------------
    # Candidate search
    # ----------------------------------------------------
    st.subheader("Search Candidate")

    search_col = st.selectbox("Search Column", columns)

    search_val = st.text_input("Enter value")

    if search_val:
        result = df[df[search_col].astype(str).str.contains(search_val, case=False)]
        st.dataframe(result)

    # ----------------------------------------------------
    # Final table
    # ----------------------------------------------------
    st.subheader("Refund Calculation Table")

    st.dataframe(df)

    # ----------------------------------------------------
    # Download result
    # ----------------------------------------------------
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Result CSV",
        csv,
        "refund_results.csv",
        "text/csv"
    )
