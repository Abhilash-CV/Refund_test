import streamlit as st
import pandas as pd

st.set_page_config(page_title="Refund Calculator", layout="wide")

st.title("Admission Fee Refund Calculator")

# Upload Excel
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx","xls"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    st.subheader("Preview Data")
    st.dataframe(df.head())

    columns = list(df.columns)

    st.sidebar.header("Configuration")

    # -----------------------------
    # Total Remitted Fee Components
    # -----------------------------
    fee_components = st.sidebar.multiselect(
        "Select Fee Components for Total Remitted Fee",
        columns
    )

    if fee_components:
        df["Total_Remitted_Fee"] = df[fee_components].fillna(0).sum(axis=1)

    # -----------------------------
    # Fee to Allotment Mapping
    # -----------------------------
    st.sidebar.subheader("Fee to Allotment Mapping")

    allotment_map = {}

    for i in range(1,5):

        col = f"Allot_{i}"

        if col in df.columns:

            allotment_map[col] = st.sidebar.multiselect(
                f"Fee Components linked to {col}",
                columns,
                key=col
            )

    # -----------------------------
    # Forfeit Fee Components
    # -----------------------------
    forfeit_components = st.sidebar.multiselect(
        "Select Fee Components eligible for Forfeit",
        columns
    )

    # -----------------------------
    # Refund Calculation
    # -----------------------------
    def calculate_refund(row):

        total_remitted = row.get("Total_Remitted_Fee",0)

        forfeited = 0

        for i in range(1,5):

            join_col = f"JoinStatus_{i}"
            allot_col = f"Allot_{i}"

            if join_col in row and allot_col in allotment_map:

                status = str(row[join_col]).strip().upper()

                if status in ["N","TC"]:

                    for f in allotment_map[allot_col]:

                        if f in row and f in forfeit_components:
                            forfeited += row[f]

        refund = total_remitted - forfeited

        return pd.Series([forfeited, refund])

    if fee_components:

        df[["Forfeited_Amount","Refund_Amount"]] = df.apply(
            calculate_refund, axis=1
        )

        st.subheader("Calculated Result")

        st.dataframe(df)

        st.download_button(
            "Download Result Excel",
            df.to_csv(index=False),
            "refund_calculation.csv",
            "text/csv"
        )
