import streamlit as st
import pandas as pd

st.set_page_config(page_title="Refund Calculator", layout="wide")

st.title("Admission Fee Refund Processing System")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx","xls"])

if uploaded_file:

    df = pd.read_excel(uploaded_file, engine="openpyxl")

    st.subheader("Data Preview")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    st.sidebar.header("Configuration")

    # -------------------------------------------------------
    # TOTAL REMITTED FEE
    # -------------------------------------------------------
    fee_components = st.sidebar.multiselect(
        "Select Fee Components for Total Remitted Fee",
        columns
    )

    if fee_components:
        df["Total_Remitted_Fee"] = df[fee_components].fillna(0).sum(axis=1)

    # -------------------------------------------------------
    # DETECT ALLOTMENT ROUNDS AUTOMATICALLY
    # -------------------------------------------------------
    allot_cols = [c for c in columns if c.startswith("Allot_")]
    join_cols = [c for c in columns if c.startswith("JoinStatus_")]

    st.sidebar.subheader("Fee → Allotment Mapping")

    allotment_map = {}

    for allot in allot_cols:

        allotment_map[allot] = st.sidebar.multiselect(
            f"Fee Components linked to {allot}",
            columns,
            key=allot
        )

    # -------------------------------------------------------
    # FORFEIT COMPONENTS
    # -------------------------------------------------------
    forfeit_components = st.sidebar.multiselect(
        "Select Fee Components Eligible for Forfeit",
        columns
    )

    # -------------------------------------------------------
    # CALCULATE FORFEIT AMOUNT
    # -------------------------------------------------------
    def calculate_forfeit(row):

        forfeited = 0

        for allot_col in allot_cols:

            round_no = allot_col.split("_")[1]
            join_col = f"JoinStatus_{round_no}"

            if join_col in row:

                status = str(row.get(join_col,"")).strip().upper()

                if status in ["N","TC"]:

                    for fee in allotment_map.get(allot_col,[]):

                        if fee in forfeit_components:
                            forfeited += row.get(fee,0)

        return forfeited

    if fee_components:

        df["Forfeited_Amount"] = df.apply(calculate_forfeit, axis=1)

        # -------------------------------------------------------
        # REFUND LOGIC
        # -------------------------------------------------------
        def calculate_refund(row):

            total_remitted = row.get("Total_Remitted_Fee",0)
            forfeited = row.get("Forfeited_Amount",0)

            # check if candidate has any allotment
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
            if has_allotment and (pd.isna(curr_admn) or str(curr_admn).strip()==""):
                return 0

            return 0

        df["Refund_Amount"] = df.apply(calculate_refund, axis=1)

        # -------------------------------------------------------
        # DASHBOARD SUMMARY
        # -------------------------------------------------------
        st.subheader("Summary")

        col1,col2,col3 = st.columns(3)

        col1.metric("Total Remitted", f"{df['Total_Remitted_Fee'].sum():,.0f}")
        col2.metric("Total Forfeited", f"{df['Forfeited_Amount'].sum():,.0f}")
        col3.metric("Total Refund", f"{df['Refund_Amount'].sum():,.0f}")

        # -------------------------------------------------------
        # SEARCH CANDIDATE
        # -------------------------------------------------------
        st.subheader("Search Candidate")

        if "RollNo" in df.columns:

            search = st.text_input("Enter Roll Number")

            if search:
                result = df[df["RollNo"].astype(str).str.contains(search)]
                st.dataframe(result)

        # -------------------------------------------------------
        # SHOW RESULT TABLE
        # -------------------------------------------------------
        st.subheader("Refund Calculation")

        st.dataframe(df)

        # -------------------------------------------------------
        # DOWNLOAD RESULT
        # -------------------------------------------------------
        csv = df.to_csv(index=False).encode('utf-8')

        st.download_button(
            "Download Result",
            csv,
            "refund_result.csv",
            "text/csv"
        )
