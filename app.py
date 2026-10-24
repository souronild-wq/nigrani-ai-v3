
import io

import pandas as pd
import streamlit as st

from detector import analyze_transaction
from bulk_audit import audit_csv
from trustcheck import check_invoice


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Nigrani AI | Risk Intelligence",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# PROFESSIONAL DARK THEME
# ==================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b1120;
        color: #e5eaf5;
    }

    [data-testid="stSidebar"] {
        background-color: #101a2e;
        border-right: 1px solid #273750;
    }

    h1, h2, h3 {
        color: #f1f5f9;
    }

    p, label {
        color: #c3cee0;
    }

    [data-testid="stMetric"] {
        background-color: #131f33;
        border: 1px solid #273750;
        border-radius: 12px;
        padding: 18px;
    }

    [data-testid="stMetricLabel"] {
        color: #9eafc9;
    }

    [data-testid="stMetricValue"] {
        color: #f1f5f9;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        background-color: #087f8c;
        color: white;
        border: 1px solid #1597a5;
        border-radius: 8px;
        font-weight: 600;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: #096875;
        color: white;
    }

    .brand {
        font-size: 25px;
        font-weight: 800;
        color: #f1f5f9;
    }

    .subtitle {
        color: #8fa3c0;
        font-size: 14px;
    }

    .section-label {
        color: #35c6d3;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .notice {
        background-color: #17243a;
        border: 1px solid #344761;
        border-left: 4px solid #35c6d3;
        padding: 13px 16px;
        border-radius: 7px;
        color: #cbd7e8;
        font-size: 13px;
    }

    .footer {
        color: #7586a1;
        font-size: 12px;
        text-align: center;
        padding-top: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# GENERAL HELPERS
# ==================================================

def money(value):
    """Format a number as Indian rupees."""
    try:
        return f"₹{float(value):,.2f}"
    except (ValueError, TypeError):
        return "N/A"


def show_header(title, description):
    st.markdown(
        '<div class="section-label">'
        'NIGRANI AI / RISK INTELLIGENCE'
        '</div>',
        unsafe_allow_html=True,
    )
    st.title(title)
    st.markdown(
        f'<div class="subtitle">{description}</div>',
        unsafe_allow_html=True,
    )
    st.divider()


def risk_color(level):
    colors = {
        "Critical": "#ff6b81",
        "High": "#ff9f43",
        "Moderate": "#feca57",
        "Low": "#4adeb0",
    }
    return colors.get(level, "#c3cee0")


# ==================================================
# SINGLE-INVOICE RISK DISPLAY
# ==================================================

def show_risk_assessment(result):
    score = int(result["risk_score"])
    level = result["risk_level"]

    st.subheader("Invoice Risk Assessment")

    col1, col2, col3 = st.columns(3)

    col1.metric("Risk Score", f"{score}/100")
    col2.metric("Risk Level", level)
    col3.metric(
        "Review Required",
        "Yes" if result["review_needed"] else "No",
    )

    st.progress(score / 100)

    st.markdown(
        f"**Risk category:** "
        f"<span style='color:{risk_color(level)}'>"
        f"{level}</span>",
        unsafe_allow_html=True,
    )

    st.caption(
        "The score indicates review priority, not the probability "
        "of fraud."
    )

    st.markdown("#### Explainable Risk Factors")

    factors = result.get("risk_factors", [])

    if factors:
        for factor in factors:
            with st.container(border=True):
                left, right = st.columns([3, 1])

                with left:
                    st.markdown(f"**{factor['factor']}**")
                    st.write(factor["reason"])

                with right:
                    st.metric("Points", f"+{factor['points']}")
    else:
        st.success("No configured risk factors were triggered.")


# ==================================================
# BULK RISK SCORING
# ==================================================

def add_risk_scores(report):
    """Calculate risk scores for each invoice in a CSV report."""

    report = report.copy()

    required_columns = [
        "quantity",
        "unit_price",
        "market_price",
        "budget",
        "total_amount",
    ]

    missing = [
        column
        for column in required_columns
        if column not in report.columns
    ]

    if missing:
        st.warning(
            "Some risk scores cannot be calculated. Missing columns: "
            + ", ".join(missing)
        )
        return report

    scores = []
    levels = []
    explanations = []
    ml_flags = []

    for _, row in report.iterrows():
        try:
            result = analyze_transaction(
                quantity=float(row["quantity"]),
                unit_price=float(row["unit_price"]),
                market_price=float(row["market_price"]),
                budget=float(row["budget"]),
                claimed_total=float(row["total_amount"]),
            )

            scores.append(result["risk_score"])
            levels.append(result["risk_level"])
            ml_flags.append(result["ml_anomaly"])

            factors = result.get("risk_factors", [])

            explanations.append(
                "; ".join(
                    f"{factor['factor']} (+{factor['points']})"
                    for factor in factors
                )
                if factors
                else "No configured risk factors"
            )

        except (ValueError, TypeError, KeyError):
            scores.append(None)
            levels.append("Not scored")
            ml_flags.append(False)
            explanations.append("Invalid or incomplete invoice data")

    report["risk_score"] = scores
    report["risk_level"] = levels
    report["ml_anomaly"] = ml_flags
    report["risk_explanation"] = explanations

    return report


# ==================================================
# REPORT METRICS AND CHARTS
# ==================================================

def show_report_metrics(report):
    total = len(report)

    if "risk_score" in report.columns:
        scores = pd.to_numeric(
            report["risk_score"],
            errors="coerce",
        )
    else:
        scores = pd.Series(
            [float("nan")] * total,
            index=report.index,
        )

    flagged = int((scores >= 25).sum())
    critical = int((scores >= 75).sum())
    average = scores.mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Invoices", total)
    col2.metric("Invoices to Review", flagged)
    col3.metric("Critical Risk", critical)
    col4.metric(
        "Average Risk Score",
        f"{average:.1f}/100" if pd.notna(average) else "N/A",
    )


def show_risk_chart(report):
    if "risk_level" not in report.columns:
        return

    st.subheader("Risk Distribution")

    order = [
        "Critical",
        "High",
        "Moderate",
        "Low",
        "Not scored",
    ]

    counts = (
        report["risk_level"]
        .value_counts()
        .reindex(order, fill_value=0)
    )

    counts = counts[counts > 0]

    if not counts.empty:
        chart_data = counts.rename_axis(
            "Risk Level"
        ).reset_index(name="Invoices")

        st.bar_chart(
            chart_data,
            x="Risk Level",
            y="Invoices",
        )


# ==================================================
# AUDIT TABLE AND CSV EXPORT
# ==================================================

def show_report_table(report, key_prefix="report"):
    st.subheader("Invoice Review Table")

    display_report = report.copy()

    if "risk_score" in display_report.columns:
        display_report["risk_score"] = pd.to_numeric(
            display_report["risk_score"],
            errors="coerce",
        )

        display_report = display_report.sort_values(
            "risk_score",
            ascending=False,
            na_position="last",
        )

    col1, col2 = st.columns(2)

    with col1:
        flagged_only = st.checkbox(
            "Show invoices requiring attention",
            key=f"{key_prefix}_flagged",
        )

    with col2:
        search = st.text_input(
            "Search invoice or supplier",
            key=f"{key_prefix}_search",
        )

    if flagged_only and "risk_score" in display_report.columns:
        display_report = display_report[
            display_report["risk_score"] >= 25
        ]

    if search:
        matches = display_report.astype(str).apply(
            lambda column: column.str.contains(
                search,
                case=False,
                na=False,
            )
        )
        display_report = display_report[matches.any(axis=1)]

    st.dataframe(
        display_report,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download Audit CSV",
        data=display_report.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="nigrani_risk_audit_report.csv",
        mime="text/csv",
        key=f"{key_prefix}_csv_download",
    )


# ==================================================
# EXCEL REPORT GENERATOR
# ==================================================

def create_excel_report(report):
    """Generate an Excel workbook containing four audit sheets."""

    data = report.copy()

    # Ensure risk columns exist.
    if "risk_score" in data.columns:
        data["risk_score"] = pd.to_numeric(
            data["risk_score"],
            errors="coerce",
        )
    else:
        data["risk_score"] = 0

    if "risk_level" not in data.columns:
        data["risk_level"] = "Not scored"

    # Convert financial amounts safely.
    if "total_amount" in data.columns:
        data["total_amount"] = pd.to_numeric(
            data["total_amount"],
            errors="coerce",
        )

    # Overall audit summary.
    total_value = (
        data["total_amount"].sum()
        if "total_amount" in data.columns
        else 0
    )

    average_score = data["risk_score"].mean()

    summary = pd.DataFrame(
        {
            "Metric": [
                "Report Type",
                "Total Invoices",
                "Invoices Requiring Review",
                "Critical-Risk Invoices",
                "Total Invoice Value",
                "Average Risk Score",
                "Risk Score Review Threshold",
            ],
            "Value": [
                "Nigrani AI Procurement Audit",
                len(data),
                int((data["risk_score"] >= 25).sum()),
                int((data["risk_score"] >= 75).sum()),
                total_value,
                (
                    round(average_score, 2)
                    if pd.notna(average_score)
                    else "N/A"
                ),
                25,
            ],
        }
    )

    # Risk-level breakdown.
    risk_summary = (
        data["risk_level"]
        .value_counts()
        .rename_axis("Risk Level")
        .reset_index(name="Invoice Count")
    )

    # Supplier analysis.
    if "supplier" in data.columns:
        supplier_summary = (
            data.groupby("supplier", dropna=False)
            .agg(
                Invoice_Count=("supplier", "size"),
                Average_Risk=("risk_score", "mean"),
                Highest_Risk=("risk_score", "max"),
            )
            .reset_index()
        )

        if "total_amount" in data.columns:
            spending = (
                data.groupby("supplier", dropna=False)
                .agg(
                    Total_Spending=("total_amount", "sum")
                )
                .reset_index()
            )

            supplier_summary = supplier_summary.merge(
                spending,
                on="supplier",
                how="left",
            )

        supplier_summary["Average_Risk"] = (
            supplier_summary["Average_Risk"].round(1)
        )
    else:
        supplier_summary = pd.DataFrame(
            {
                "Message": [
                    "Supplier data is unavailable in this report."
                ]
            }
        )

    # Generate workbook in memory.
    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        summary.to_excel(
            writer,
            sheet_name="Audit Summary",
            index=False,
        )

        data.to_excel(
            writer,
            sheet_name="Invoice Details",
            index=False,
        )

        risk_summary.to_excel(
            writer,
            sheet_name="Risk Breakdown",
            index=False,
        )

        supplier_summary.to_excel(
            writer,
            sheet_name="Supplier Analysis",
            index=False,
        )

        # Basic professional formatting.
        for worksheet in writer.sheets.values():
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions

            for cell in worksheet[1]:
                cell.font = cell.font.copy(
                    bold=True,
                    color="FFFFFF",
                )
                cell.fill = cell.fill.copy(
                    fill_type="solid",
                    fgColor="17365D",
                )

            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter

                for cell in column_cells:
                    value = str(cell.value or "")
                    max_length = max(max_length, len(value))

                worksheet.column_dimensions[
                    column_letter
                ].width = min(max_length + 3, 40)

    output.seek(0)
    return output.getvalue()


def save_report(report):
    st.session_state["nigrani_report"] = report


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:
    st.markdown(
        '<div class="brand">🔎 NIGRANI AI</div>',
        unsafe_allow_html=True,
    )

    st.caption("Procurement Risk Intelligence")
    st.divider()

    page = st.radio(
        "WORKSPACE",
        [
            "Dashboard",
            "Single Invoice",
            "Bulk Audit",
            "Supplier Analytics",
        ],
    )

    st.divider()
    st.markdown("**SYSTEM STATUS**")
    st.success("Risk engine configured")
    st.success("ML model integration configured")

    st.caption(
        "Audit findings require human review."
    )


# ==================================================
# DASHBOARD
# ==================================================

if page == "Dashboard":
    show_header(
        "Audit Dashboard",
        "Monitor invoice risks and prioritize procurement reviews.",
    )

    st.markdown(
        '<div class="notice">'
        "Run a bulk audit to see invoice statistics, risk levels, "
        "and downloadable reports."
        "</div>",
        unsafe_allow_html=True,
    )

    report = st.session_state.get("nigrani_report")

    if report is None:
        st.info(
            "No audit report available yet. "
            "Open Bulk Audit and upload a CSV file."
        )
    else:
        show_report_metrics(report)
        show_risk_chart(report)
        show_report_table(report, "dashboard")


# ==================================================
# SINGLE INVOICE ANALYSIS
# ==================================================

elif page == "Single Invoice":
    show_header(
        "Single Invoice Analysis",
        "Evaluate one invoice using configured rules and the ML model.",
    )

    with st.form("single_invoice_form"):
        st.subheader("Invoice Details")

        col1, col2 = st.columns(2)

        with col1:
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=100,
                step=1,
            )

            unit_price = st.number_input(
                "Unit Price (₹)",
                min_value=0.01,
                value=900.0,
                step=10.0,
            )

            market_price = st.number_input(
                "Reference Market Price (₹)",
                min_value=0.01,
                value=400.0,
                step=10.0,
            )

        with col2:
            budget = st.number_input(
                "Approved Budget (₹)",
                min_value=0.01,
                value=50000.0,
                step=1000.0,
            )

            claimed_total = st.number_input(
                "Claimed Invoice Total (₹)",
                min_value=0.01,
                value=90000.0,
                step=1000.0,
            )

        submitted = st.form_submit_button(
            "Analyze Invoice",
            use_container_width=True,
        )

    if submitted:
        try:
            result = analyze_transaction(
                quantity=quantity,
                unit_price=unit_price,
                market_price=market_price,
                budget=budget,
                claimed_total=claimed_total,
            )

            st.divider()
            show_risk_assessment(result)

            st.subheader("Financial Summary")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Expected Total",
                money(result["expected_total"]),
            )

            col2.metric(
                "Price Difference vs Reference",
                money(result["price_difference"]),
            )

            col3.metric(
                "Budget Used",
                f"{result['budget_usage'] * 100:.1f}%",
            )

            st.subheader("Audit Findings")

            findings = result.get("findings", [])

            if findings:
                for finding in findings:
                    st.warning(finding)
            else:
                st.success("No configured rule-based findings.")

            st.caption(
                "ML anomaly detected: "
                + ("Yes" if result["ml_anomaly"] else "No")
            )

        except (ValueError, TypeError, KeyError) as error:
            st.error(f"Unable to analyze invoice: {error}")


# ==================================================
# BULK AUDIT
# ==================================================

elif page == "Bulk Audit":
    show_header(
        "Bulk Invoice Audit",
        "Upload a CSV, score invoices, and export a review-ready report.",
    )

    st.markdown(
        '<div class="notice">'
        "Risk scoring requires the columns: quantity, unit_price, "
        "market_price, budget, total_amount."
        "</div>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload invoice CSV",
        type=["csv"],
        help="Choose a procurement transaction CSV file.",
    )

    if uploaded_file is not None:
        if st.button(
            "Run Bulk Audit",
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    "Auditing invoices and calculating risk scores..."
                ):
                    uploaded_file.seek(0)
                    report = audit_csv(uploaded_file)

                    if not isinstance(report, pd.DataFrame):
                        report = pd.DataFrame(report)

                    report = add_risk_scores(report)
                    save_report(report)

                st.success("Bulk audit completed.")

            except Exception as error:
                st.error(f"Bulk audit failed: {error}")

    report = st.session_state.get("nigrani_report")

    if report is not None:
        st.divider()

        show_report_metrics(report)
        show_risk_chart(report)
        show_report_table(report, "bulk")

        st.divider()
        st.subheader("Complete Excel Audit Report")

        st.write(
            "Download a workbook containing the audit summary, "
            "invoice details, risk breakdown, and supplier analysis."
        )

        try:
            excel_data = create_excel_report(report)

            st.download_button(
                label="Download Complete Excel Audit Report",
                data=excel_data,
                file_name="nigrani_complete_audit_report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key="complete_excel_report",
                use_container_width=True,
            )

        except Exception as error:
            st.error(
                "Could not create the Excel report. "
                f"Details: {error}"
            )
            st.info(
                "Install the Excel dependency using: "
                "python -m pip install openpyxl"
            )


# ==================================================
# SUPPLIER ANALYTICS
# ==================================================

elif page == "Supplier Analytics":
    show_header(
        "Supplier Analytics",
        "Compare supplier invoice activity, spending, and review risk.",
    )

    report = st.session_state.get("nigrani_report")

    if report is None:
        st.info(
            "No audit report available. Run a Bulk Audit first."
        )

    elif "supplier" not in report.columns:
        st.warning(
            "The report does not contain a 'supplier' column."
        )

    else:
        data = report.copy()

        if "risk_score" in data.columns:
            data["risk_score"] = pd.to_numeric(
                data["risk_score"],
                errors="coerce",
            )
        else:
            data["risk_score"] = float("nan")

        if "total_amount" in data.columns:
            data["total_amount"] = pd.to_numeric(
                data["total_amount"],
                errors="coerce",
            )
        else:
            data["total_amount"] = 0.0

        summary = (
            data.groupby("supplier", dropna=False)
            .agg(
                invoice_count=("supplier", "size"),
                average_risk=("risk_score", "mean"),
                total_spending=("total_amount", "sum"),
                highest_risk=("risk_score", "max"),
            )
            .reset_index()
        )

        flagged_counts = (
            data.assign(
                flagged=data["risk_score"].ge(25)
            )
            .groupby("supplier", dropna=False)["flagged"]
            .sum()
            .reset_index(name="invoices_to_review")
        )

        summary = summary.merge(
            flagged_counts,
            on="supplier",
            how="left",
        )

        summary["average_risk"] = summary[
            "average_risk"
        ].round(1)

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Suppliers",
            summary["supplier"].nunique(),
        )

        col2.metric(
            "Invoices to Review",
            int(summary["invoices_to_review"].sum()),
        )

        col3.metric(
            "Total Invoice Value",
            money(summary["total_spending"].sum()),
        )

        st.divider()

        st.subheader("Average Risk by Supplier")

        risk_data = summary.dropna(
            subset=["average_risk"]
        ).sort_values(
            "average_risk",
            ascending=False,
        )

        if not risk_data.empty:
            st.bar_chart(
                risk_data,
                x="supplier",
                y="average_risk",
            )
        else:
            st.info("No valid risk scores are available.")

        st.subheader("Total Spending by Supplier")

        spending_data = summary.sort_values(
            "total_spending",
            ascending=False,
        )

        if not spending_data.empty:
            st.bar_chart(
                spending_data,
                x="supplier",
                y="total_spending",
            )

        st.subheader("Supplier Review Summary")

        st.dataframe(
            summary.sort_values(
                ["average_risk", "invoices_to_review"],
                ascending=[False, False],
                na_position="last",
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Supplier Summary",
            data=summary.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="nigrani_supplier_analytics.csv",
            mime="text/csv",
            key="supplier_summary_download",
        )

        st.caption(
            "Higher risk scores indicate review priority, "
            "not proof of supplier misconduct."
        )


# ==================================================
# TRUSTCHECK INVOICE VERIFICATION
# ==================================================

elif page == "TrustCheck":
    show_header(
        "TrustCheck",
        "Verify invoice details and understand why an invoice "
        "may need further review.",
    )

    st.info(
        "TrustCheck uses rule-based checks. Its score indicates "
        "review priority, not the probability of fraud."
    )

    with st.form("trustcheck_invoice_form"):
        st.subheader("Invoice Details")

        col1, col2 = st.columns(2)

        with col1:
            invoice_id = st.text_input(
                "Invoice ID",
                value="INV-TEST-001",
            )

            supplier = st.text_input(
                "Supplier",
                value="ABC Suppliers",
            )

            material = st.text_input(
                "Material",
                value="Steel",
            )

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=10,
                step=1,
            )

        with col2:
            unit_price = st.number_input(
                "Unit Price (₹)",
                min_value=0.01,
                value=100.0,
                step=10.0,
            )

            market_price = st.number_input(
                "Reference Market Price (₹)",
                min_value=0.01,
                value=100.0,
                step=10.0,
            )

            budget = st.number_input(
                "Approved Budget (₹)",
                min_value=0.01,
                value=1500.0,
                step=100.0,
            )

            claimed_total = st.number_input(
                "Claimed Invoice Total (₹)",
                min_value=0.0,
                value=1000.0,
                step=100.0,
            )

        submitted = st.form_submit_button(
            "Run TrustCheck",
            use_container_width=True,
        )

    if submitted:
        result = check_invoice(
            quantity=quantity,
            unit_price=unit_price,
            market_price=market_price,
            budget=budget,
            claimed_total=claimed_total,
            invoice_id=invoice_id,
            supplier=supplier,
            material=material,
        )

        st.divider()
        st.subheader("TrustCheck Results")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Review Priority Score",
            f"{result['trust_score']}/100",
        )

        col2.metric(
            "Verification Status",
            result["status"],
        )

        col3.metric(
            "Review Required",
            "Yes" if result["review_required"] else "No",
        )

        st.progress(result["trust_score"] / 100)

        if result["status"] == "Invalid Data":
            st.error("Invalid invoice data. Please review the inputs.")
        elif result["trust_score"] >= 60:
            st.error("High review priority. Investigate this invoice.")
        elif result["review_required"]:
            st.warning("Some checks failed. Further review is recommended.")
        else:
            st.success("The invoice passed the configured basic checks.")

        st.subheader("Checks Passed")

        if result["checks_passed"]:
            for check in result["checks_passed"]:
                st.write(f"✅ {check}")
        else:
            st.write("No checks passed.")

        st.subheader("Findings")

        if result["findings"]:
            for finding in result["findings"]:
                st.warning(
                    f"**{finding['severity']} severity:** "
                    f"{finding['reason']}"
                )
        else:
            st.success("No configured TrustCheck findings.")

        if "expected_total" in result:
            st.subheader("Financial Summary")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Expected Total",
                money(result["expected_total"]),
            )

            col2.metric(
                "Claimed Total",
                money(result["claimed_total"]),
            )

            col3.metric(
                "Price Difference",
                money(result["price_difference"]),
            )

        st.caption(
            "TrustCheck identifies potential irregularities. "
            "A human reviewer must determine the appropriate action."
        )

# ==================================================
# FOOTER
# ==================================================

st.markdown(
    """
    <div class="footer">
        Nigrani AI · Procurement Risk Intelligence<br>
        Prototype for audit assistance — human review is required.
    </div>
    """,
    unsafe_allow_html=True,
)
