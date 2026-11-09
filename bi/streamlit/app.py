from pathlib import Path
from html import escape
import pandas as pd
import plotly.express as px
import streamlit as st

from data_access import connect, query, scalar

st.set_page_config(
    page_title="DTWH | Home Credit Risk",
    page_icon="📊",
    layout="wide"
)

ROOT = Path(__file__).resolve().parents[2]

st.markdown("""
<style>
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"] {
    background:#FFFFFF!important;color:#172A42!important;color-scheme:light!important;
}
.block-container {max-width:1530px;padding:1.6rem 2rem 3rem}
[data-testid="stSidebar"] {background:#0B2C55!important}
[data-testid="stSidebar"] * {color:#FFFFFF}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background:#1C5086;border-radius:10px
}
h1,h2,h3 {color:#16385F!important;letter-spacing:-.02em}
h1{font-size:1.85rem!important;font-weight:780!important}
h3{font-size:1.13rem!important;font-weight:700!important}
[data-testid="stWidgetLabel"] p {color:#233B56!important;font-weight:650!important}
[data-baseweb="select"]>div {background:#FFFFFF!important;border-color:#C6D5E4!important}
[data-testid="stPlotlyChart"] {
    background:#FFFFFF!important;border:1px solid #DEE6EF;
    border-radius:12px;padding:8px
}
[data-testid="stHorizontalBlock"] {row-gap:1rem}
[data-testid="stMetric"] {background:#F2F6FA!important;border:1px solid #DEE6EF;
    border-radius:12px;padding:15px}
[data-testid="stCaptionContainer"] p {color:#55677D!important}
.dtwh-brand{font-size:1.45rem;font-weight:800;color:#FFFFFF}
.dtwh-brand-sub{font-size:.8rem;color:#C7DDF4;margin:0 0 17px}
.dtwh-header {background:#F4F8FC;border:1px solid #DCE6F1;
    border-radius:13px;padding:18px 21px;margin-bottom:17px}
.dtwh-header h1{margin:3px 0 5px}
.dtwh-header p{color:#536B83;font-size:.94rem;margin:0}
.dtwh-kicker{font-size:.73rem;font-weight:800;letter-spacing:.09em;color:#296F9C}
.dtwh-filter-head{font-size:1rem;font-weight:750;color:#164879;margin:12px 0 7px}
.dtwh-section{font-size:1.14rem;font-weight:800;color:#164879;margin:23px 0 12px}
.dtwh-kpi{min-height:117px;padding:17px;border-radius:13px;
    border:1px solid #DFE6EE;background:var(--kpi-bg,#EAF3FC)!important}
.dtwh-kpi:before{display:none!important}
.dtwh-kpi-label{font-size:.83rem;font-weight:700;color:#455A72}
.dtwh-kpi-value{font-size:clamp(1.32rem,1.85vw,1.98rem);font-weight:800;
    color:#111827!important;letter-spacing:-.03em;margin:9px 0 5px;white-space:nowrap}
.dtwh-kpi-detail{font-size:.77rem;color:#566A7E;line-height:1.4}
@media(max-width:768px){
    .block-container{padding:1.1rem .8rem 2rem}
    .dtwh-header{padding:13px}
    .dtwh-kpi{min-height:103px;padding:12px}
    .dtwh-kpi-value{font-size:1.35rem}
}
</style>
""", unsafe_allow_html=True)

def fmt(value, digits=2, suffix=""):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):,.{digits}f}{suffix}"


def number(value):
    if value is None or pd.isna(value):
        return "0"
    return f"{int(value):,}"


def metric_card(title, value, detail=None, accent="blue"):
    colors = {
        "blue": "#EAF3FC",
        "red": "#FFF0EC",
        "teal": "#E7F6F1",
        "violet": "#F0ECFA",
        "orange": "#FFF2E4",
        "slate": "#F0F4F8",
    }
    color = colors.get(accent, colors["blue"])
    detail_html = (
        f'<div class="dtwh-kpi-detail">{escape(str(detail))}</div>'
        if detail else '<div class="dtwh-kpi-detail">&nbsp;</div>'
    )
    st.markdown(
        f'<div class="dtwh-kpi" style="--kpi-bg:{color}">'
        f'<div class="dtwh-kpi-label">{escape(str(title))}</div>'
        f'<div class="dtwh-kpi-value">{escape(str(value))}</div>'
        f'{detail_html}</div>',
        unsafe_allow_html=True
    )


def metric(col, title, value, caption=None, accent="blue"):
    with col:
        metric_card(title, value, caption, accent)


def section(title):
    st.markdown(
        f'<div class="dtwh-section">{escape(title)}</div>',
        unsafe_allow_html=True
    )


CHART_COLORS = {
    "TARGET theo Credit/Goods": "#4C91BD",
    "TARGET theo nhóm tuổi": "#D98979",
    "TARGET theo loại hợp đồng": "#65A291",
    "TARGET theo học vấn": "#9383B8",
    "TARGET = 1 theo nhóm thu nhập": "#C59A5C",
    "TARGET theo mức sử dụng thẻ": "#C88372",
}


def bar_chart(df, x, y, title, order=None):
    st.subheader(title)
    if df.empty:
        st.info("Không có dữ liệu phù hợp bộ lọc.")
        return

    fig = px.bar(
        df, x=x, y=y,
        color_discrete_sequence=[CHART_COLORS.get(title, "#4C91BD")],
        hover_data=[
            c for c in ["total_records", "target_1", "customers"]
            if c in df.columns
        ],
        category_orders={x: order} if order else None
    )
    fig.update_traces(
        marker_line_width=0,
        texttemplate="%{y:.2f}%",
        textposition="outside",
        textfont=dict(size=12, color="#111827"),
        cliponaxis=False
    )
    upper = max(5.0, float(df[y].max()) * 1.24)
    fig.update_layout(
        template="plotly_white",
        height=340,
        margin=dict(l=12, r=12, t=30, b=45),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(size=12, color="#172A42"),
        xaxis=dict(title=None, showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(title="Tỷ lệ (%)", gridcolor="#E5ECF3",
                   range=[0, upper], ticksuffix="%"),
        showlegend=False, bargap=0.3
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


def cohort_condition(alias, contracts, late_only):
    clauses = []
    params = []

    if contracts:
        placeholders = ",".join("?" for _ in contracts)
        clauses.append(f"""
            EXISTS (
                SELECT 1
                FROM previous_contract_bridge b
                WHERE b.SK_ID_CURR = {alias}.SK_ID_CURR
                AND b.NAME_CONTRACT_TYPE IN ({placeholders})
            )
        """)
        params.extend(contracts)

    if late_only:
        clauses.append(f"""
            EXISTS (
                SELECT 1
                FROM installments_customer_window h
                WHERE h.SK_ID_CURR = {alias}.SK_ID_CURR
                AND h.window_months = 0
                AND h.max_delta > 0
            )
        """)

    if not clauses:
        return "TRUE", []

    return " AND ".join(clauses), params


try:
    con, sources = connect(ROOT)
except Exception as exc:
    st.error(f"Không đọc được BI Serving: {exc}")
    st.stop()

with st.sidebar:
    st.markdown(
        '<div class="dtwh-brand">◈ DTWH</div>'
        '<div class="dtwh-brand-sub">Home Credit · Risk Analytics</div>',
        unsafe_allow_html=True
    )

    page = st.radio(
        "Điều hướng",
        ["1. Hồ sơ tiếp nhận", "2. Lịch sử tín dụng"]
    )
    st.divider()
    with st.expander("Chi tiết nguồn dữ liệu"):
        st.json(sources)


def dashboard_application():
    st.markdown(
        '<div class="dtwh-header"><div>'
        '<div class="dtwh-kicker">DASHBOARD 01 · APPLICATION RISK</div>'
        '<h1>Giám sát rủi ro hồ sơ tiếp nhận</h1>'
        '<p>Phân tích hồ sơ vay, tỷ lệ TARGET và các chỉ số tài chính</p>'
        '</div></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="dtwh-filter-head">⌕ &nbsp; Bộ lọc hồ sơ</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3, gap="medium")
    c4, c5 = st.columns(2, gap="medium")

    contracts_all = query(con, """
        SELECT DISTINCT NAME_CONTRACT_TYPE
        FROM application_dashboard
        WHERE NAME_CONTRACT_TYPE IS NOT NULL
        ORDER BY 1
    """).iloc[:, 0].tolist()

    education_all = query(con, """
        SELECT DISTINCT NAME_EDUCATION_TYPE
        FROM application_dashboard
        WHERE NAME_EDUCATION_TYPE IS NOT NULL
        ORDER BY 1
    """).iloc[:, 0].tolist()

    contract = c1.multiselect(
        "Loại hợp đồng", contracts_all
    )

    age = c2.multiselect(
        "Nhóm tuổi",
        ["<20", "20-30", "30-40", "40-50", "50-60", ">60"]
    )

    education = c3.multiselect(
        "Học vấn", education_all
    )

    income_range = c4.slider(
        "Phân vị thu nhập (%)",
        0, 100, (0, 100)
    )

    dataset = c5.selectbox(
        "Tập dữ liệu",
        ["Tất cả", "Train", "Test"]
    )

    conditions = ["1=1"]
    params = []

    if contract:
        conditions.append(
            "NAME_CONTRACT_TYPE IN ("
            + ",".join("?" for _ in contract) + ")"
        )
        params.extend(contract)

    if age:
        conditions.append(
            "age_group IN ("
            + ",".join("?" for _ in age) + ")"
        )
        params.extend(age)

    if education:
        conditions.append(
            "NAME_EDUCATION_TYPE IN ("
            + ",".join("?" for _ in education) + ")"
        )
        params.extend(education)

    if dataset != "Tất cả":
        conditions.append("dataset = ?")
        params.append(dataset)

    if income_range != (0, 100):
        lo, hi = con.execute("""
            SELECT
                quantile_cont(AMT_INCOME_TOTAL, ?),
                quantile_cont(AMT_INCOME_TOTAL, ?)
            FROM application_dashboard
            WHERE AMT_INCOME_TOTAL > 0
        """, [
            income_range[0] / 100,
            income_range[1] / 100
        ]).fetchone()

        conditions.append(
            "AMT_INCOME_TOTAL BETWEEN ? AND ?"
        )
        params.extend([lo, hi])

    where_sql = " AND ".join(conditions)

    overview = query(con, f"""
        SELECT
            COUNT(*) AS total_records,
            COUNT(*) FILTER (
                WHERE dataset = 'Train'
            ) AS train_records,
            COUNT(*) FILTER (
                WHERE dataset = 'Test'
            ) AS test_records,
            COUNT(TARGET) AS labeled_records,
            COUNT(*) FILTER (
                WHERE TARGET = 1
            ) AS target_1,
            100.0 * AVG(TARGET) AS target_rate_pct,
            MEDIAN(cti) AS median_cti,
            MEDIAN(credit_goods) AS median_credit_goods,
            100.0 * MEDIAN(dti) AS median_dti_pct,
            COUNT(dti) AS valid_dti
        FROM application_dashboard
        WHERE {where_sql}
    """, params).iloc[0]

    section("Tổng quan danh mục hồ sơ")
    a, b, c = st.columns(3, gap="medium")

    metric(
        a, "Tổng hồ sơ",
        number(overview.total_records),
        f"Train: {number(overview.train_records)} | "
        f"Test: {number(overview.test_records)}"
    )

    metric(
        b, "TARGET = 1",
        fmt(overview.target_rate_pct, 2, "%"),
        f"{number(overview.target_1)} / "
        f"{number(overview.labeled_records)} hồ sơ có nhãn",
        "red"
    )

    metric(
        c, "CTI trung vị",
        fmt(overview.median_cti, 4, " lần"),
        accent="teal"
    )

    a, b, c = st.columns(3, gap="medium")

    metric(
        a, "Credit/Goods trung vị",
        fmt(overview.median_credit_goods, 4, " lần"),
        accent="violet"
    )

    metric(
        b, "DTI trung vị",
        fmt(overview.median_dti_pct, 2, "%"),
        f"{number(overview.valid_dti)} hồ sơ có DTI hợp lệ",
        "orange"
    )

    coverage = (
        100 * overview.labeled_records / overview.total_records
        if overview.total_records else None
    )
    metric(
        c, "Độ bao phủ nhãn",
        fmt(coverage, 2, "%"),
        accent="blue"
    )

    section("Phân tích tỷ lệ TARGET = 1")

    labeled_where = (
        f"({where_sql}) AND TARGET IS NOT NULL"
    )

    if not overview.labeled_records:
        st.info(
            "Bộ lọc hiện tại không có hồ sơ mang nhãn TARGET."
        )
    else:
        group_specs = [
            (
                "cg_group",
                """CASE
                    WHEN credit_goods IS NULL
                        THEN 'Không hợp lệ'
                    WHEN credit_goods <= 0.5 THEN '<=0.5'
                    WHEN credit_goods <= 0.8 THEN '0.5-0.8'
                    WHEN credit_goods <= 1 THEN '0.8-1'
                    WHEN credit_goods <= 1.2 THEN '1-1.2'
                    WHEN credit_goods <= 1.5 THEN '1.2-1.5'
                    ELSE '>1.5'
                END""",
                "TARGET theo Credit/Goods",
                ["<=0.5", "0.5-0.8", "0.8-1",
                 "1-1.2", "1.2-1.5", ">1.5",
                 "Không hợp lệ"]
            ),
            (
                "age_group",
                "age_group",
                "TARGET theo nhóm tuổi",
                ["<20", "20-30", "30-40",
                 "40-50", "50-60", ">60"]
            ),
            (
                "NAME_CONTRACT_TYPE",
                "NAME_CONTRACT_TYPE",
                "TARGET theo loại hợp đồng",
                None
            ),
            (
                "NAME_EDUCATION_TYPE",
                "NAME_EDUCATION_TYPE",
                "TARGET theo học vấn",
                None
            )
        ]

        for start in (0, 2):
            left, right = st.columns(2)

            for col, spec in zip(
                [left, right],
                group_specs[start:start + 2]
            ):
                field, expr, title, order = spec

                grouped = query(con, f"""
                    SELECT
                        {expr} AS group_name,
                        COUNT(*) AS total_records,
                        SUM(TARGET) AS target_1,
                        100.0 * AVG(TARGET) AS rate
                    FROM application_dashboard
                    WHERE {labeled_where}
                    GROUP BY 1
                    ORDER BY 1
                """, params)

                with col:
                    bar_chart(
                        grouped, "group_name", "rate",
                        title, order
                    )

    third_left, third_right = st.columns(2, gap="medium")
    with third_left:
        if overview.labeled_records:
            thresholds = con.execute("""
                SELECT
                    quantile_cont(AMT_INCOME_TOTAL, 0.2),
                    quantile_cont(AMT_INCOME_TOTAL, 0.4),
                    quantile_cont(AMT_INCOME_TOTAL, 0.6),
                    quantile_cont(AMT_INCOME_TOTAL, 0.8)
                FROM application_dashboard
                WHERE dataset = 'Train'
                  AND AMT_INCOME_TOTAL > 0
                  AND isfinite(AMT_INCOME_TOTAL)
            """).fetchone()

            t1, t2, t3, t4 = thresholds

            income_groups = query(con, f"""
                SELECT
                    CASE
                        WHEN AMT_INCOME_TOTAL IS NULL
                          OR AMT_INCOME_TOTAL <= 0
                            THEN '00. Không hợp lệ'
                        WHEN AMT_INCOME_TOTAL <= ?
                            THEN '01. Nhóm 1'
                        WHEN AMT_INCOME_TOTAL <= ?
                            THEN '02. Nhóm 2'
                        WHEN AMT_INCOME_TOTAL <= ?
                            THEN '03. Nhóm 3'
                        WHEN AMT_INCOME_TOTAL <= ?
                            THEN '04. Nhóm 4'
                        ELSE '05. Nhóm 5'
                    END AS income_group,
                    COUNT(*) AS total_records,
                    SUM(TARGET) AS target_1,
                    100.0 * AVG(TARGET) AS rate
                FROM application_dashboard
                WHERE {labeled_where}
                GROUP BY 1
                ORDER BY 1
            """, [t1, t2, t3, t4] + params)

            bar_chart(
                income_groups,
                "income_group",
                "rate",
                "TARGET = 1 theo nhóm thu nhập"
            )
        else:
            st.subheader("TARGET = 1 theo nhóm thu nhập")
            st.info("Không có dữ liệu có nhãn.")

    with third_right:
        st.subheader("Cơ cấu hồ sơ")
        composition = query(con, f"""
            SELECT
                NAME_CONTRACT_TYPE,
                COUNT(*) AS records
            FROM application_dashboard
            WHERE {where_sql}
            GROUP BY 1
            ORDER BY 2 DESC
        """, params)

        if not composition.empty:
            fig = px.pie(
                composition,
                names="NAME_CONTRACT_TYPE",
                values="records",
                hole=0.52,
                color_discrete_sequence=["#4D8FBF", "#E59C78", "#7DAF9D"]
            )
            fig.update_traces(
                textinfo="percent", textposition="inside",
                textfont=dict(color="#111827", size=12)
            )
            fig.update_layout(
                template="plotly_white",
                height=350,
                paper_bgcolor="#FFFFFF",
                font=dict(color="#34445B", size=13),
                margin=dict(l=10, r=10, t=6, b=65),
                legend=dict(orientation="h", yanchor="top", y=-0.12,
                            xanchor="center", x=0.5,
                            font=dict(color="#111827", size=12))
            )
            st.plotly_chart(fig, use_container_width=True)


def dashboard_history():
    st.markdown(
        '<div class="dtwh-header"><div>'
        '<div class="dtwh-kicker">DASHBOARD 02 · CREDIT HISTORY</div>'
        '<h1>Lịch sử tín dụng và hành vi thanh toán</h1>'
        '<p>Theo dõi lịch sử trả góp, hợp đồng và dư nợ tín dụng</p>'
        '</div></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="dtwh-filter-head">⌕ &nbsp; Bộ lọc lịch sử</div>',
        unsafe_allow_html=True
    )

    f1, f2, f3 = st.columns(3)

    window_label = f1.selectbox(
        "Cửa sổ lịch sử",
        ["Toàn bộ", "6 tháng", "12 tháng"]
    )

    months = {
        "Toàn bộ": 0,
        "6 tháng": 6,
        "12 tháng": 12
    }[window_label]

    contract_options = query(con, """
        SELECT DISTINCT NAME_CONTRACT_TYPE
        FROM previous_contract_bridge
        WHERE NAME_CONTRACT_TYPE IS NOT NULL
        ORDER BY 1
    """).iloc[:, 0].tolist()

    contracts = f2.multiselect(
        "Loại hợp đồng cũ",
        contract_options
    )

    late_only = f3.checkbox(
        "Chỉ khách từng có kỳ trễ"
    )

    inst_filter, inst_params = cohort_condition(
        "i", contracts, late_only
    )

    inst = query(con, f"""
        SELECT
            COUNT(*) AS customers,
            COALESCE(SUM(i.periods), 0) AS periods,
            COALESCE(SUM(i.valid_periods), 0) AS valid_periods,
            COALESCE(SUM(i.late_periods), 0) AS late_periods,
            COUNT(*) FILTER (
                WHERE i.max_delta > 0
            ) AS customers_ever_late,
            COALESCE(SUM(i.shortfall_sum), 0) AS shortfall
        FROM installments_customer_window i
        WHERE i.window_months = ?
          AND {inst_filter}
    """, [months] + inst_params).iloc[0]

    late_rate = (
        100 * inst.late_periods / inst.valid_periods
        if inst.valid_periods else None
    )

    customer_late_rate = (
        100 * inst.customers_ever_late / inst.customers
        if inst.customers else None
    )

    section("Chất lượng thanh toán")
    a, b, c, d = st.columns(4, gap="medium")

    metric(
        a, "Kỳ trả trễ",
        fmt(late_rate, 2, "%"),
        f"{number(inst.late_periods)} / "
        f"{number(inst.valid_periods)} kỳ đủ dữ liệu",
        "red"
    )

    metric(
        b, "Khách từng có kỳ trễ",
        fmt(customer_late_rate, 2, "%"),
        f"{number(inst.customers_ever_late)} / "
        f"{number(inst.customers)} khách",
        "orange"
    )

    metric(
        c, "Tổng thiếu hụt",
        fmt(inst.shortfall / 1e6, 2, " triệu"),
        "Đơn vị tiền theo nguồn",
        "violet"
    )

    metric(
        d, "Số kỳ trả góp",
        number(inst.periods)
    )

    prev_filter, prev_params = cohort_condition(
        "p", contracts, late_only
    )

    previous = query(con, f"""
        SELECT
            COALESCE(SUM(p.previous_applications), 0) AS total,
            COALESCE(SUM(p.approved_applications), 0) AS approved
        FROM previous_customer_window p
        WHERE p.window_months = ?
          AND {prev_filter}
    """, [months] + prev_params).iloc[0]

    approval_rate = (
        100 * previous.approved / previous.total
        if previous.total else None
    )

    cc_filter, cc_params = cohort_condition(
        "cc", contracts, late_only
    )

    cc_summary = query(con, f"""
        SELECT
            COUNT(*) AS customers,
            COUNT(*) FILTER (
                WHERE cc.utilization > 0.8
            ) AS high_utilization,
            AVG(cc.utilization) AS avg_utilization
        FROM credit_card_customer_window cc
        WHERE cc.window_months = ?
          AND {cc_filter}
    """, [months] + cc_params).iloc[0]

    high_rate = (
        100 * cc_summary.high_utilization
        / cc_summary.customers
        if cc_summary.customers else None
    )

    debt_filter, debt_params = cohort_condition(
        "b", contracts, late_only
    )
    debt = scalar(con, f"""
        SELECT SUM(b.bureau_debt_sum)
        FROM bureau_customer_debt b
        WHERE {debt_filter}
    """, debt_params)

    section("Tổng quan tín dụng")
    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        st.subheader("Lịch sử đơn vay")
        metric_card(
            "Tỷ lệ phê duyệt đơn cũ",
            fmt(approval_rate, 2, "%"),
            f"{number(previous.approved)} / {number(previous.total)} đơn",
            "teal"
        )
    with k2:
        st.subheader("Sử dụng thẻ tín dụng")
        metric_card(
            "Khách dùng thẻ trung bình >80%",
            fmt(high_rate, 2, "%"),
            f"{number(cc_summary.high_utilization)} / "
            f"{number(cc_summary.customers)} khách",
            "orange"
        )
    with k3:
        st.subheader("Dư nợ bên ngoài")
        metric_card(
            "Tổng dư nợ Bureau",
            fmt(debt / 1e9 if debt is not None else None, 2, " tỷ"),
            accent="violet"
        )

    chart_left, chart_right = st.columns(2, gap="medium")
    with chart_left:
        card_groups = query(con, f"""
            SELECT CASE
                WHEN cc.utilization IS NULL THEN 'Không hợp lệ'
                WHEN cc.utilization <= 0 THEN '≤0%'
                WHEN cc.utilization <= .3 THEN '0–30%'
                WHEN cc.utilization <= .5 THEN '30–50%'
                WHEN cc.utilization <= .8 THEN '50–80%'
                WHEN cc.utilization <= 1 THEN '80–100%'
                ELSE '>100%' END AS usage_group,
                COUNT(*) AS customers,
                COUNT(a.TARGET) AS labeled_customers,
                SUM(CASE WHEN a.TARGET = 1 THEN 1 ELSE 0 END) AS target_1,
                100.0 * AVG(a.TARGET) AS rate
            FROM credit_card_customer_window cc
            LEFT JOIN application_dashboard a
              ON a.SK_ID_CURR = cc.SK_ID_CURR
             AND a.dataset = 'Train'
            WHERE cc.window_months = ? AND {cc_filter}
            GROUP BY 1 ORDER BY 1
        """, [months] + cc_params)
        bar_chart(
            card_groups[card_groups.labeled_customers > 0],
            "usage_group", "rate", "TARGET theo mức sử dụng thẻ",
            ["≤0%", "0–30%", "30–50%", "50–80%",
             "80–100%", ">100%", "Không hợp lệ"]
        )

    with chart_right:
        st.subheader("Biến động trạng thái Bureau theo tháng")
        if contracts or late_only:
            st.warning(
                "Bộ lọc nhóm khách hàng không áp dụng "
                "cho dữ liệu Bureau theo tháng."
            )
        else:
            all_statuses = ["0", "1", "2", "3", "4", "5", "C", "X"]
            selected = st.multiselect(
                "Trạng thái", all_statuses, default=all_statuses
            )
            display_mode = st.radio(
                "Đơn vị", ["Tỷ trọng (%)", "Số bản ghi"],
                horizontal=True
            )
            bureau = query(con, """
                WITH status_month AS (
                    SELECT MONTHS_BALANCE,
                           CAST(STATUS AS VARCHAR) AS status,
                           SUM(records) AS n
                    FROM bureau_month_status
                    WHERE (? = 0 OR MONTHS_BALANCE BETWEEN ? AND 0)
                    GROUP BY 1, 2
                )
                SELECT MONTHS_BALANCE, status, n,
                       100.0 * n / NULLIF(
                           SUM(n) OVER (PARTITION BY MONTHS_BALANCE), 0
                       ) AS share_pct
                FROM status_month ORDER BY MONTHS_BALANCE, status
            """, [months, -months + 1])

            bureau = bureau[bureau["status"].isin(selected)]
            if bureau.empty:
                st.info("Không có trạng thái phù hợp.")
            else:
                value_col = (
                    "share_pct" if display_mode == "Tỷ trọng (%)"
                    else "n"
                )
                status_colors = {
                    "0": "#4A8ABD", "1": "#E19477",
                    "2": "#71A793", "3": "#A08CBD",
                    "4": "#C6A15F", "5": "#D77986",
                    "C": "#608B92", "X": "#8892A1"
                }
                fig = px.line(
                    bureau,
                    x="MONTHS_BALANCE", y=value_col,
                    color="status", markers=True,
                    color_discrete_map=status_colors,
                    category_orders={"status": all_statuses},
                    labels={
                        "MONTHS_BALANCE": "Tháng tương đối",
                        "status": "Trạng thái",
                        "share_pct": "Tỷ trọng (%)",
                        "n": "Số bản ghi"
                    }
                )
                fig.update_traces(
                    line=dict(width=2.6), marker=dict(size=5)
                )
                fig.update_layout(
                    template="plotly_white",
                    height=385,
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    font=dict(color="#172A42", size=12),
                    margin=dict(l=12, r=12, t=12, b=82),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="#E5EBF2"),
                    legend=dict(
                        orientation="h", yanchor="top", y=-.22,
                        xanchor="center", x=.5, title=None,
                        font=dict(color="#111827", size=11)
                    )
                )
                st.plotly_chart(
                    fig, use_container_width=True,
                    config={"displaylogo": False}
                )


if page == "1. Hồ sơ tiếp nhận":
    dashboard_application()
else:
    dashboard_history()
