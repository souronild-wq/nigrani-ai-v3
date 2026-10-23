
import streamlit as st
import pandas as pd
from detector import analyze_transaction
from bulk_audit import audit_csv

st.set_page_config(
    page_title="Nigrani AI",
    page_icon="🔎",
    layout="wide"
)

# ---------------- PAGE HEADER ----------------

st.title("🔎 Nigrani AI")
st.subheader("AI-Powered Construction Procurement Audit")

st.caption(
    "Detect unusual prices, budget overruns, and duplicate invoices."
)

st.info(
    "Audit warnings are signals for human review, not proof of fraud. "
    "The included demonstration dataset is synthetic."
)

overview_tab, single_tab, bulk_tab = st.tabs([
    "📊 Audit Overview",
    "🧾 Single Invoice",
    "📁 Bulk CSV Audit"
])

# ---------------- SINGLE INVOICE ----------------

with single_tab:
    st.header("Single Invoice Analysis")

    scenario = st.selectbox(
        "Choose a test scenario",
        [
            "Custom Invoice",
            "High Price Example",
            "Normal Cement Invoice",
            "Budget Overrun Example"
        ]
    )

    defaults = {
        "Custom Invoice": (100, 450, 400, 50000, 45000),
        "High Price Example": (100, 900, 400, 100000, 90000),
        "Normal Cement Invoice": (100, 410, 400, 50000, 41000),
        "Budget Overrun Example": (100, 450, 400, 30000, 45000)
    }

    default_values = defaults[scenario]

    with st.form("single_invoice_form"):
        col1, col2 = st.columns(2)

        with col1:
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=default_values[0]
            )

            unit_price = st.number_input(
                "Invoice unit price (₹)",
                min_value=0.01,
                value=float(default_values[1])
            )

            market_price = st.number_input(
                "Reference market price (₹)",
                min_value=0.01,
                value=float(default_values[2])
            )

        with col2:
            budget = st.number_input(
                "Project budget (₹)",
                min_value=0.01,
                value=float(default_values[3])
            )

            claimed_total = st.number_input(
                "Claimed invoice total (₹)",
                min_value=0.01,
                value=float(default_values[4])
            )

        submitted = st.form_submit_button(
            "Analyze Invoice",
            type="primary"
        )

    if submitted:
        result = analyze_transaction(
            quantity=quantity,
            unit_price=unit_price,
            market_price=market_price,
            budget=budget,
            claimed_total=claimed_total
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Expected Invoice Total",
            f"₹{result['expected_total']:,.2f}"
        )

        c2.metric(
            "Price Difference",
            f"₹{result['price_difference']:,.2f}"
        )

        c3.metric(
            "Budget Used",
            f"{result['budget_usage'] * 100:.1f}%"
        )

        if result["review_needed"]:
            st.warning("⚠️ REVIEW REQUIRED")
        else:
            st.success("No review flag from the current checks.")

        st.write(
            "Machine-learning anomaly:",
            "Yes" if result["ml_anomaly"] else "No"
        )

        st.subheader("Findings")

        if result["findings"]:
            for finding in result["findings"]:
                st.write(f"• {finding}")
        else:
            st.write("No findings from the current checks.")

# ---------------- BULK CSV AUDIT ----------------

with bulk_tab:
    st.header("Bulk Invoice Audit")
    st.write("Upload an invoice CSV to run the combined audit.")

    uploaded_file = st.file_uploader(
        "Upload invoice CSV",
        type=["csv"],
        key="bulk_audit_upload"
    )

    if uploaded_file is not None:
        try:
            report = audit_csv(uploaded_file)

            # Keep the complete report in session state
            st.session_state["nigrani_report"] = report

        except Exception as error:
            st.error(f"Unable to audit this file: {error}")

    report = st.session_state.get("nigrani_report")

    if report is not None:
        total = len(report)

        flagged = int(
            report["review_required"].sum()
        )

        duplicates = int(
            report["duplicate_review_required"].sum()
        )

        ml_flags = int(
            report["ml_anomaly"].sum()
        )

        review_rate = (
            flagged / total * 100 if total else 0
        )

        # Summary metrics
        st.subheader("Audit Summary")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Invoices", total)
        c2.metric("Require Review", flagged)
        c3.metric("Duplicate Warnings", duplicates)
        c4.metric("Review Rate", f"{review_rate:.1f}%")

        # Review status chart
        st.subheader("Invoice Review Distribution")

        if total:
            chart_data = pd.DataFrame({
                "Status": ["Require Review", "No Review Flag"],
                "Invoices": [flagged, total - flagged]
            }).set_index("Status")

            st.bar_chart(chart_data)

        # Additional audit breakdown
        st.subheader("Audit Checks")

        c5, c6 = st.columns(2)

        c5.metric("ML Anomaly Flags", ml_flags)

        if "duplicate_invoice_id" in report.columns:
            duplicate_ids = int(
                report["duplicate_invoice_id"].sum()
            )
        else:
            duplicate_ids = 0

        c6.metric("Repeated Invoice IDs", duplicate_ids)

        # Filter report
        st.subheader("Invoice Details")

        show_only_flagged = st.checkbox(
            "Show only invoices requiring review",
            value=True
        )

        if show_only_flagged:
            displayed_report = report[
                report["review_required"]
            ]
        else:
            displayed_report = report

        st.dataframe(
            displayed_report,
            use_container_width=True,
            hide_index=True
        )

        # Download complete report
        csv_data = report.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Complete Audit Report",
            data=csv_data,
            file_name="nigrani_audit_report.csv",
            mime="text/csv"
        )

        st.caption(
            "Counts can overlap because an invoice may trigger "
            "multiple checks. A review flag is not proof of fraud."
        )

# ---------------- AUDIT OVERVIEW ----------------

with overview_tab:
    st.header("Audit Overview")

    overview_file = st.file_uploader(
        "Upload invoice CSV for overview",
        type=["csv"],
        key="overview_upload"
    )

    if overview_file is not None:
        try:
            overview_report = audit_csv(overview_file)

            total = len(overview_report)

            flagged = int(
                overview_report["review_required"].sum()
            )

            duplicates = int(
                overview_report["duplicate_review_required"].sum()
            )

            c1, c2, c3 = st.columns(3)

            c1.metric("Invoices Audited", total)
            c2.metric("Require Review", flagged)
            c3.metric("Duplicate Warnings", duplicates)

            overview_chart = pd.DataFrame({
                "Status": ["Require Review", "No Review Flag"],
                "Invoices": [flagged, total - flagged]
            }).set_index("Status")

            st.subheader("Review Status")
            st.bar_chart(overview_chart)

            st.subheader("Invoices Requiring Review")

            st.dataframe(
                overview_report[
                    overview_report["review_required"]
                ],
                use_container_width=True,
                hide_index=True
            )

        except Exception as error:
            st.error(f"Unable to generate overview: {error}")

    else:
        st.write(
            "Upload a CSV above, or use the Bulk CSV Audit tab "
            "to view the full audit report and download it."
        )
