
import re
from urllib.parse import urlparse

import pandas as pd
import streamlit as st


# ============================================================
# NIGRANI AI - FRAUD DETECTION AND WEBSITE SAFETY PLATFORM
# ============================================================

st.set_page_config(
    page_title="Nigrani AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------

for key in ["expense_claims", "bill_records", "audit_history"]:
    if key not in st.session_state:
        st.session_state[key] = []


# ------------------------------------------------------------
# COMMON FUNCTIONS
# ------------------------------------------------------------

def money(value):
    return f"₹{value:,.2f}"


def show_header(title, description):
    st.title(title)
    st.caption(description)
    st.divider()


def show_result(score, findings, passed_message="No configured warning detected."):
    score = max(0, min(100, int(score)))

    c1, c2 = st.columns(2)
    c1.metric("Review Score", f"{score}/100")
    c2.metric(
        "Review Status",
        "High Priority" if score >= 60
        else "Needs Review" if score >= 30
        else "Basic Checks Passed",
    )

    st.progress(score / 100)

    if findings:
        st.subheader("Findings")
        for finding in findings:
            st.warning(finding)
    else:
        st.success(passed_message)

    st.caption(
        "This tool identifies potential warning signs. "
        "It does not prove fraud or guarantee authenticity."
    )


def calculate_invoice(quantity, unit_price, market_price, budget, claimed_total):
    findings = []
    score = 0

    expected_total = quantity * unit_price
    price_difference = claimed_total - expected_total

    if quantity <= 0:
        findings.append("Quantity must be greater than zero.")
        score += 40

    if unit_price <= 0 or market_price <= 0:
        findings.append("Unit price and market price must be positive.")
        score += 40

    if budget <= 0:
        findings.append("Approved budget must be greater than zero.")
        score += 30

    if claimed_total < 0:
        findings.append("Claimed total cannot be negative.")
        score += 40

    if not findings:
        if abs(price_difference) > 0.01:
            findings.append(
                f"Claimed total differs from the calculated total by "
                f"{money(price_difference)}."
            )
            score += 30

        if unit_price > market_price * 1.20:
            findings.append(
                "Unit price is more than 20% above the supplied market price."
            )
            score += 30

        if claimed_total > budget:
            findings.append("Claimed total exceeds the approved budget.")
            score += 30

    return {
        "expected_total": expected_total,
        "price_difference": price_difference,
        "findings": findings,
        "score": min(score, 100),
    }


def record_audit(module, reference, score, findings):
    st.session_state.audit_history.append({
        "Module": module,
        "Reference": reference,
        "Score": score,
        "Status": (
            "High Priority" if score >= 60
            else "Needs Review" if score >= 30
            else "Basic Checks Passed"
        ),
        "Findings": "; ".join(findings) if findings else "None",
    })


# ------------------------------------------------------------
# WEBSITE SAFETY CHECK
# ------------------------------------------------------------

def check_website(raw_url):
    findings = []
    score = 0
    raw_url = raw_url.strip()

    if not raw_url:
        return 100, ["Enter a website address to check."]

    if any(ord(char) < 32 or char.isspace() for char in raw_url):
        return 100, ["The URL contains spaces or control characters."]

    candidate = raw_url
    if "://" not in candidate:
        candidate = "https://" + candidate

    try:
        parsed = urlparse(candidate)
        hostname = parsed.hostname
    except ValueError:
        return 100, ["The URL could not be parsed."]

    if parsed.scheme not in ("http", "https"):
        findings.append("The URL does not use HTTP or HTTPS.")
        score += 50

    if not hostname or "." not in hostname:
        findings.append("The address does not look like a complete domain.")
        score += 40
        return min(score, 100), findings

    if parsed.username is not None or parsed.password is not None:
        findings.append("The URL contains credentials before the hostname.")
        score += 40

    if parsed.scheme == "http":
        findings.append("The connection uses HTTP rather than encrypted HTTPS.")
        score += 20

    if hostname.replace(".", "").isdigit():
        findings.append("The hostname appears to be an IP address.")
        score += 20

    if "xn--" in hostname.lower():
        findings.append("The domain contains an internationalized domain label.")
        score += 20

    suspicious_terms = [
        "login", "verify", "secure", "account",
        "update", "password", "wallet", "confirm",
    ]
    if any(term in hostname.lower() for term in suspicious_terms):
        findings.append(
            "The hostname contains a term commonly used in account-related URLs."
        )
        score += 15

    if hostname.count("-") >= 3:
        findings.append("The hostname contains several hyphens.")
        score += 15

    if len(hostname) > 50:
        findings.append("The hostname is unusually long.")
        score += 10

    if parsed.port is not None and parsed.port not in (80, 443):
        findings.append("The URL uses a non-standard web port.")
        score += 10

    return min(score, 100), findings


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.title("🛡️ Nigrani AI")
    st.caption("Fraud Detection & Digital Safety")

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Single Invoice",
            "TrustCheck",
            "Expense Fraud Detector",
            "Fake Bill Detector",
            "Website Safety",
            "Bulk Audit",
            "Supplier Analytics",
        ],
    )

    st.divider()
    st.caption("Rule-based checks • Human review recommended")


# ============================================================
# 1. DASHBOARD
# ============================================================

if page == "Dashboard":
    show_header(
        "Nigrani AI Dashboard",
        "Your central workspace for invoice auditing, expense checks, "
        "bill verification and website safety.",
    )

    history = st.session_state.audit_history

    total_checks = len(history)
    flagged = sum(item["Score"] >= 30 for item in history)
    high_priority = sum(item["Score"] >= 60 for item in history)

    c1, c2, c3 = st.columns(3)
    c1.metric("Checks Performed", total_checks)
    c2.metric("Flagged for Review", flagged)
    c3.metric("High-Priority Results", high_priority)

    st.subheader("Available Tools")

    cards = [
        ("🧾 Single Invoice", "Check invoice totals and pricing."),
        ("🔍 TrustCheck", "Review invoice irregularities."),
        ("💳 Expense Fraud Detector", "Check expense claims and duplicates."),
        ("📄 Fake Bill Detector", "Check bill calculations and repeated IDs."),
        ("🌐 Website Safety", "Screen URLs for suspicious indicators."),
        ("📊 Bulk Audit", "Review multiple transactions using CSV."),
        ("🏢 Supplier Analytics", "Summarize spending by supplier."),
    ]

    cols = st.columns(2)
    for index, (title, description) in enumerate(cards):
        with cols[index % 2]:
            st.markdown(f"**{title}**")
            st.write(description)

    if history:
        st.subheader("Recent Checks")
        st.dataframe(
            pd.DataFrame(history[-10:][::-1]),
            use_container_width=True,
            hide_index=True,
        )
        report = pd.DataFrame(history)
        st.download_button(
            "Download Check History (CSV)",
            data=report.to_csv(index=False).encode("utf-8"),
            file_name="nigrani_audit_history.csv",
            mime="text/csv",
        )
    else:
        st.info("Your check history will appear here after your first check.")


# ============================================================
# 2. SINGLE INVOICE
# ============================================================

elif page == "Single Invoice":
    show_header(
        "Single Invoice Audit",
        "Check a single invoice against its market price and approved budget.",
    )

    with st.form("single_invoice_form"):
        invoice_id = st.text_input("Invoice ID", "INV-001")
        supplier = st.text_input("Supplier", "ABC Suppliers")
        quantity = st.number_input("Quantity", min_value=1, value=10)
        unit_price = st.number_input(
            "Unit Price (₹)", min_value=0.01, value=100.0
        )
        market_price = st.number_input(
            "Market Price per Unit (₹)", min_value=0.01, value=100.0
        )
        budget = st.number_input(
            "Approved Budget (₹)", min_value=0.01, value=1500.0
        )
        claimed_total = st.number_input(
            "Claimed Invoice Total (₹)", min_value=0.0, value=1000.0
        )

        submitted = st.form_submit_button("Audit Invoice")

    if submitted:
        result = calculate_invoice(
            quantity, unit_price, market_price, budget, claimed_total
        )
        st.subheader("Invoice Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Expected Total", money(result["expected_total"]))
        c2.metric("Claimed Total", money(claimed_total))
        c3.metric("Difference", money(result["price_difference"]))

        show_result(result["score"], result["findings"])
        record_audit(
            "Single Invoice",
            invoice_id or supplier or "Invoice",
            result["score"],
            result["findings"],
        )


# ============================================================
# 3. TRUSTCHECK
# ============================================================

elif page == "TrustCheck":
    show_header(
        "TrustCheck",
        "Run configured invoice checks and highlight potential irregularities.",
    )

    st.info(
        "This initial version uses rule-based checks, not a trained fraud model."
    )

    with st.form("trustcheck_form"):
        invoice_id = st.text_input("Invoice ID", "INV-TEST-001")
        supplier = st.text_input("Supplier", "ABC Suppliers")
        material = st.text_input("Material", "Steel")

        quantity = st.number_input("Quantity", min_value=1, value=10)
        unit_price = st.number_input(
            "Unit Price (₹)", min_value=0.01, value=100.0
        )
        market_price = st.number_input(
            "Market Price (₹)", min_value=0.01, value=100.0
        )
        budget = st.number_input(
            "Approved Budget (₹)", min_value=0.01, value=1500.0
        )
        claimed_total = st.number_input(
            "Claimed Total (₹)", min_value=0.0, value=1000.0
        )

        submitted = st.form_submit_button("Run TrustCheck")

    if submitted:
        result = calculate_invoice(
            quantity, unit_price, market_price, budget, claimed_total
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Review Score", f"{result['score']}/100")
        c2.metric(
            "Status",
            "High Priority" if result["score"] >= 60
            else "Needs Review" if result["score"] >= 30
            else "Basic Checks Passed",
        )
        c3.metric("Findings", len(result["findings"]))

        st.write(f"**Invoice:** {invoice_id}")
        st.write(f"**Supplier:** {supplier}")
        st.write(f"**Material:** {material}")
        st.write(f"**Calculated Total:** {money(result['expected_total'])}")

        show_result(result["score"], result["findings"])
        record_audit(
            "TrustCheck",
            invoice_id or supplier or "Invoice",
            result["score"],
            result["findings"],
        )


# ============================================================
# 4. EXPENSE FRAUD DETECTOR
# ============================================================

elif page == "Expense Fraud Detector":
    show_header(
        "Expense Fraud Detector",
        "Screen expense claims for duplicate references, excessive amounts "
        "and spending-limit violations.",
    )

    with st.form("expense_form"):
        claim_id = st.text_input("Expense / Claim ID", "EXP-001")
        employee = st.text_input("Employee Name or ID", "EMP-001")
        category = st.selectbox(
            "Expense Category",
            ["Travel", "Food", "Accommodation", "Equipment", "Other"],
        )
        amount = st.number_input("Claimed Amount (₹)", min_value=0.0, value=500.0)
        approved_limit = st.number_input(
            "Approved Limit (₹)", min_value=0.01, value=1000.0
        )
        usual_amount = st.number_input(
            "Usual Amount for This Expense (₹)",
            min_value=0.0,
            value=500.0,
        )
        submitted = st.form_submit_button("Check Expense")

    if submitted:
        findings = []
        score = 0

        if not claim_id.strip():
            findings.append("Claim ID is missing.")
            score += 30

        if amount <= 0:
            findings.append("Claim amount must be greater than zero.")
            score += 40

        if amount > approved_limit:
            findings.append("Expense exceeds the approved limit.")
            score += 40

        if usual_amount > 0 and amount > usual_amount * 2:
            findings.append(
                "Claim is more than twice the stated usual amount."
            )
            score += 30

        duplicate = any(
            item["claim_id"].casefold() == claim_id.strip().casefold()
            and claim_id.strip()
            for item in st.session_state.expense_claims
        )

        if duplicate:
            findings.append(
                "This claim ID was already submitted in this app session."
            )
            score += 50

        score = min(score, 100)

        st.subheader("Expense Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Claimed Amount", money(amount))
        c2.metric("Approved Limit", money(approved_limit))
        c3.metric("Variance", money(amount - approved_limit))

        show_result(score, findings)

        if claim_id.strip():
            st.session_state.expense_claims.append({
                "claim_id": claim_id.strip(),
                "employee": employee,
                "category": category,
                "amount": amount,
            })

        record_audit(
            "Expense Fraud Detector",
            claim_id or employee or "Expense",
            score,
            findings,
        )


# ============================================================
# 5. FAKE BILL DETECTOR
# ============================================================

elif page == "Fake Bill Detector":
    show_header(
        "Fake Bill Detector",
        "Check bill arithmetic, required details and duplicate bill references.",
    )

    st.warning(
        "Arithmetic and field checks cannot establish whether a document "
        "was genuinely issued. This version does not authenticate bills with issuers."
    )

    with st.form("fake_bill_form"):
        bill_id = st.text_input("Bill Number", "BILL-001")
        issuer = st.text_input("Business / Issuer Name", "ABC Traders")
        tax_id = st.text_input("Tax ID (if applicable)", "GST-EXAMPLE")
        description = st.text_input("Item / Service Description", "Office supplies")
        quantity = st.number_input("Quantity", min_value=1, value=2)
        unit_price = st.number_input("Unit Price (₹)", min_value=0.0, value=500.0)
        tax_percent = st.number_input(
            "Tax Rate (%)", min_value=0.0, max_value=100.0, value=18.0
        )
        claimed_total = st.number_input(
            "Total Printed on Bill (₹)", min_value=0.0, value=1180.0
        )

        submitted = st.form_submit_button("Verify Bill")

    if submitted:
        findings = []
        score = 0

        expected_subtotal = quantity * unit_price
        expected_tax = expected_subtotal * tax_percent / 100
        expected_total = expected_subtotal + expected_tax

        if not bill_id.strip():
            findings.append("Bill number is missing.")
            score += 25

        if not issuer.strip():
            findings.append("Issuer name is missing.")
            score += 25

        if not description.strip():
            findings.append("Item or service description is missing.")
            score += 15

        if not tax_id.strip():
            findings.append("Tax ID was not supplied; verify whether it is required.")
            score += 10

        if unit_price <= 0:
            findings.append("Unit price must be greater than zero.")
            score += 30

        if abs(claimed_total - expected_total) > 1.0:
            findings.append(
                f"Printed total differs from the calculated total "
                f"({money(expected_total)})."
            )
            score += 40

        duplicate = any(
            item["bill_id"].casefold() == bill_id.strip().casefold()
            and bill_id.strip()
            for item in st.session_state.bill_records
        )

        if duplicate:
            findings.append(
                "This bill number was already checked in this app session."
            )
            score += 40

        score = min(score, 100)

        st.subheader("Bill Calculation")
        c1, c2, c3 = st.columns(3)
        c1.metric("Subtotal", money(expected_subtotal))
        c2.metric("Calculated Tax", money(expected_tax))
        c3.metric("Expected Total", money(expected_total))

        st.metric("Printed Total", money(claimed_total))
        show_result(score, findings)

        if bill_id.strip():
            st.session_state.bill_records.append({
                "bill_id": bill_id.strip(),
                "issuer": issuer,
                "description": description,
                "claimed_total": claimed_total,
            })

        record_audit(
            "Fake Bill Detector",
            bill_id or issuer or "Bill",
            score,
            findings,
        )


# ============================================================
# 6. WEBSITE SAFETY
# ============================================================

elif page == "Website Safety":
    show_header(
        "Website Safety Checker",
        "Screen a URL for common suspicious patterns before deciding whether to visit.",
    )

    st.warning(
        "This is a basic heuristic checker. It does not query threat-intelligence "
        "databases, inspect website content, or guarantee a website is safe."
    )

    with st.form("website_safety_form"):
        website = st.text_input(
            "Website URL",
            placeholder="https://example.com",
        )
        submitted = st.form_submit_button("Check Website")

    if submitted:
        score, findings = check_website(website)

        if score >= 60:
            st.error("High review priority")
        elif score >= 30:
            st.warning("Some suspicious indicators were found")
        elif findings:
            st.info("Review the findings before proceeding")
        else:
            st.success("No configured warning indicators were detected")

        st.metric("URL Risk Indicator Score", f"{score}/100")
        st.progress(score / 100)

        if findings:
            for finding in findings:
                st.warning(finding)
        elif website.strip():
            st.success("No configured suspicious patterns were detected.")

        record_audit(
            "Website Safety",
            website or "URL",
            score,
            findings,
        )

        st.caption(
            "Do not enter passwords, payment details or other sensitive data "
            "on a website based only on this result."
        )


# ============================================================
# 7. BULK AUDIT
# ============================================================

elif page == "Bulk Audit":
    show_header(
        "Bulk Audit",
        "Upload a CSV file to screen multiple invoice transactions.",
    )

    st.write(
        "Required columns: `invoice_id`, `quantity`, `unit_price`, "
        "`market_price`, `budget`, `claimed_total`."
    )

    uploaded = st.file_uploader("Upload transaction CSV", type=["csv"])

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            df.columns = [column.strip().lower() for column in df.columns]

            required = [
                "invoice_id", "quantity", "unit_price",
                "market_price", "budget", "claimed_total",
            ]

            missing = [column for column in required if column not in df.columns]

            if missing:
                st.error("Missing required columns: " + ", ".join(missing))
            else:
                results = []

                for _, row in df.iterrows():
                    try:
                        quantity = float(row["quantity"])
                        unit_price = float(row["unit_price"])
                        market_price = float(row["market_price"])
                        budget = float(row["budget"])
                        claimed_total = float(row["claimed_total"])

                        result = calculate_invoice(
                            quantity,
                            unit_price,
                            market_price,
                            budget,
                            claimed_total,
                        )

                        results.append({
                            "invoice_id": str(row["invoice_id"]),
                            "expected_total": result["expected_total"],
                            "claimed_total": claimed_total,
                            "review_score": result["score"],
                            "status": (
                                "High Priority" if result["score"] >= 60
                                else "Needs Review" if result["score"] >= 30
                                else "Basic Checks Passed"
                            ),
                            "findings": "; ".join(result["findings"]),
                        })
                    except (TypeError, ValueError, OverflowError):
                        results.append({
                            "invoice_id": str(row["invoice_id"]),
                            "expected_total": None,
                            "claimed_total": row["claimed_total"],
                            "review_score": 100,
                            "status": "Invalid Data",
                            "findings": "One or more numeric fields are invalid.",
                        })

                report = pd.DataFrame(results)

                c1, c2, c3 = st.columns(3)
                c1.metric("Transactions", len(report))
                c2.metric(
                    "Flagged",
                    int((report["review_score"] >= 30).sum()),
                )
                c3.metric(
                    "High Priority",
                    int((report["review_score"] >= 60).sum()),
                )

                st.dataframe(report, use_container_width=True, hide_index=True)

                st.download_button(
                    "Download Audit Report",
                    data=report.to_csv(index=False).encode("utf-8"),
                    file_name="nigrani_bulk_audit.csv",
                    mime="text/csv",
                )

                for _, row in report.iterrows():
                    record_audit(
                        "Bulk Audit",
                        str(row["invoice_id"]),
                        int(row["review_score"]),
                        [row["findings"]] if row["findings"] else [],
                    )

        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            st.error(f"Could not read this CSV file: {exc}")


# ============================================================
# 8. SUPPLIER ANALYTICS
# ============================================================

elif page == "Supplier Analytics":
    show_header(
        "Supplier Analytics",
        "Analyze transaction totals and spending by supplier using a CSV file.",
    )

    st.write("Required columns: `supplier` and `claimed_total`.")

    uploaded = st.file_uploader(
        "Upload supplier transaction CSV",
        type=["csv"],
        key="supplier_csv",
    )

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            df.columns = [column.strip().lower() for column in df.columns]

            required = ["supplier", "claimed_total"]
            missing = [column for column in required if column not in df.columns]

            if missing:
                st.error("Missing required columns: " + ", ".join(missing))
            else:
                df["claimed_total"] = pd.to_numeric(
                    df["claimed_total"], errors="coerce"
                )
                df = df.dropna(subset=["supplier", "claimed_total"])

                if df.empty:
                    st.info("No valid supplier transactions were found.")
                else:
                    summary = (
                        df.groupby("supplier", as_index=False)
                        .agg(
                            transaction_count=("claimed_total", "size"),
                            total_spending=("claimed_total", "sum"),
                            average_transaction=("claimed_total", "mean"),
                        )
                        .sort_values("total_spending", ascending=False)
                    )

                    c1, c2 = st.columns(2)
                    c1.metric("Suppliers", len(summary))
                    c2.metric("Total Spending", money(df["claimed_total"].sum()))

                    st.subheader("Spending by Supplier")
                    st.bar_chart(
                        summary.set_index("supplier")["total_spending"]
                    )
                    st.dataframe(
                        summary,
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.download_button(
                        "Download Supplier Summary",
                        data=summary.to_csv(index=False).encode("utf-8"),
                        file_name="nigrani_supplier_analytics.csv",
                        mime="text/csv",
                    )

        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            st.error(f"Could not read this CSV file: {exc}")


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption(
    "Nigrani AI • Fraud screening and digital safety support • "
    "Always verify flagged results with reliable evidence."
)
