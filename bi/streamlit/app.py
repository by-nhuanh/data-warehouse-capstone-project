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
:root {
  --d-navy:#092B56; --d-navy2:#0F407A; --d-blue:#126EB1;
  --d-text:#152B48; --d-muted:#516784; --d-border:#DCE7F4;
}
.stApp {
  background:linear-gradient(135deg,#F6FAFF 0%,#FFFFFF 55%,#F3F8FF 100%);
  color:var(--d-text);
}
.block-container {max-width:1580px;padding:1.65rem 2.1rem 3rem}
[data-testid="stSidebar"] {
  background:linear-gradient(165deg,#092953 0%,#0D3A74 85%,#10539C 100%);
  border-right:0;
}
[data-testid="stSidebar"] * {color:#F3F8FF}
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stRadio"] p {color:#F3F8FF!important}
[data-testid="stSidebar"] [role="radiogroup"] label {
  border-radius:11px;padding:8px 10px;margin-bottom:4px;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
  background:rgba(90,159,239,.33);
}
[data-testid="stSidebar"] [data-testid="stExpander"]{
  border:1px solid rgba(224,239,255,.23);
  border-radius:10px;
}
h1,h2,h3 {color:#0C2D59!important;letter-spacing:-.025em}
h1 {font-size:clamp(1.65rem,2.2vw,2.2rem)!important;font-weight:750!important}
h3 {font-size:1.14rem!important;font-weight:700!important}
[data-testid="stWidgetLabel"] p {
  font-weight:650!important;color:#263F60!important;font-size:.92rem!important;
}
[data-baseweb="select"]>div {
  background:#FFFFFF!important;border:1px solid #BACDE3!important;
  border-radius:9px!important;min-height:42px;
}
[data-testid="stPlotlyChart"] {
  background:#FFFFFF;
  border:1px solid var(--d-border);
  border-radius:14px;
  padding:8px;
  box-shadow:0 5px 17px rgba(12,51,95,.052);
}
[data-testid="stPlotlyChart"]>div{border-radius:11px}
[data-testid="stCaptionContainer"] p{color:var(--d-muted)!important;line-height:1.5}
[data-testid="stHorizontalBlock"]{row-gap:1rem}
[data-testid="stAlert"]{border-radius:11px}
[data-testid="stMetric"] {
  background:#FFFFFF;border:1px solid var(--d-border);
  padding:16px 18px;border-radius:12px;
}
.dtwh-header{
  display:flex;align-items:center;justify-content:space-between;gap:16px;
  padding:15px 20px;margin:0 0 20px;border-radius:17px;
  background:linear-gradient(100deg,#EFF6FF,#FFFFFF);
  border:1px solid #DCE9FA;
}
.dtwh-header h1{font-size:1.75rem!important;margin:0 0 4px}
.dtwh-header p{color:#506784;font-size:.93rem;margin:0}
.dtwh-kicker{font-size:.73rem;font-weight:750;letter-spacing:.1em;
  text-transform:uppercase;color:#126EB1;margin-bottom:3px}
.dtwh-brand{font-size:1.42rem;font-weight:820;color:#FFFFFF}
.dtwh-brand-sub{font-size:.79rem;color:#C7E0FC;margin:2px 0 18px}
.dtwh-sidebar-status{padding:12px 14px;background:rgba(100,170,245,.16);
  border:1px solid rgba(200,228,255,.24);border-radius:10px;
  font-size:.89rem;color:#E9F5FF}
.dtwh-section{font-weight:750;font-size:1.13rem;color:#0C3470;
  margin:23px 0 11px}
.dtwh-filter-head{font-size:1rem;font-weight:750;color:#0C3470;
  padding:3px 0 11px}
.dtwh-kpi{position:relative;overflow:hidden;min-height:125px;
  padding:17px 17px 15px;border-radius:14px;
  border:1px solid #DAE7F5;
  background:linear-gradient(150deg,#FFFFFF 46%,var(--kpi-tint,#F1F7FF));
  box-shadow:0 5px 15px rgba(13,58,110,.06)}
.dtwh-kpi:before{content:"";position:absolute;left:0;top:0;bottom:0;
  width:4px;background:var(--kpi-color,#126EB1)}
.dtwh-kpi-label{font-size:.81rem;font-weight:700;color:#46607E;line-height:1.45}
.dtwh-kpi-value{font-size:clamp(1.42rem,1.8vw,1.95rem);
  font-weight:820;color:var(--kpi-color,#0F376C);
  white-space:nowrap;letter-spacing:-.04em;margin:9px 0 5px}
.dtwh-kpi-detail{font-size:.77rem;color:#58708F;line-height:1.35}
@media(max-width:768px){
  .block-container{padding:1.1rem .8rem 2rem}
  .dtwh-header{padding:13px;display:block}
  .dtwh-kpi{min-height:105px;padding:13px 14px}
  .dtwh-kpi-value{font-size:1.4rem}
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
        "blue": ("#0D5F9E", "#ECF5FF"),
        "red": ("#C32346", "#FFF1F4"),
        "teal": ("#087C77", "#ECFAF7"),
        "violet": ("#6139B1", "#F4F0FF"),
        "orange": ("#B54709", "#FFF5E8"),
    }
    color, tint = colors.get(accent, colors["blue"])
    detail_html = (
        f'<div class="dtwh-kpi-detail">{escape(str(detail))}</div>'
        if detail else '<div class="dtwh-kpi-detail">&nbsp;</div>'
    )
    st.markdown(
        f'<div class="dtwh-kpi" style="--kpi-color:{color};--kpi-tint:{tint}">'
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


def bar_chart(df, x, y, title, order=None):
    st.subheader(title)

    if df.empty:
        st.info("Không có dữ liệu phù hợp bộ lọc.")
        return

    fig = px.bar(
        df,
        x=x,
        y=y,
        color_discrete_sequence=["#116DA6"],
        hover_data=[
            c for c in ["total_records", "target_1", "customers"]
            if c in df.columns
        ],
        category_orders={x: order} if order else None
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>"
    )
    fig.update_layout(
        template="plotly_white",
        height=365,
        margin=dict(l=14, r=14, t=18, b=46),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", size=13, color="#34445B"),
        xaxis=dict(title=None, showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(
            title="Tỷ lệ (%)",
            gridcolor="#E8EEF5",
            zeroline=False,
            ticksuffix="%"
        ),
        showlegend=False,
        bargap=0.28
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displaylogo": False}
    )


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
    ready_count = sum(
        item.get("status") == "READY" for item in sources.values()
    )
    st.markdown(
        f'<div class="dtwh-sidebar-status">✓ &nbsp;'
        f'{ready_count}/{len(sources)} nguồn dữ liệu sẵn sàng</div>',
        unsafe_allow_html=True
    )
    with st.expander("Chi tiết nguồn dữ liệu"):
        st.json(sources)


def dashboard_application():
    st.markdown(
        '<div class="dtwh-header"><div>'
        '<div class="dtwh-kicker">Dashboard 01 · Application risk</div>'
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

        with st.expander("Ngưỡng phân nhóm thu nhập", expanded=False):
            st.caption(
                f"Ngưỡng theo Train: {fmt(t1, 0)} · {fmt(t2, 0)} · "
                f"{fmt(t3, 0)} · {fmt(t4, 0)}. "
                "Tỷ lệ thay đổi theo bộ lọc."
            )

    st.divider()

    section("Cơ cấu hồ sơ")

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
            color_discrete_sequence=["#116DA6", "#16A6A0", "#90B8D8"]
        )
        fig.update_layout(
            template="plotly_white",
            height=350,
            paper_bgcolor="#FFFFFF",
            font=dict(color="#34445B", size=13),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Phương pháp tính", expanded=False):
        st.caption(
            "TARGET chỉ tính trên hồ sơ có nhãn. "
            "CTI = Credit/Income; Credit/Goods = Credit/Goods Price; "
            "DTI = Annuity/Income. Trung vị tính theo bộ lọc."
        )


def dashboard_history():
    st.markdown(
        '<div class="dtwh-header"><div>'
        '<div class="dtwh-kicker">Dashboard 02 · Credit history</div>'
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

    section("Lịch sử đơn vay")
    metric_card(
        "Tỷ lệ phê duyệt đơn cũ",
        fmt(approval_rate, 2, "%"),
        f"{number(previous.approved)} / "
        f"{number(previous.total)} đơn",
        "teal"
    )

    st.divider()

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

    a, b = st.columns(2)

    with a:
        st.subheader("Sử dụng thẻ tín dụng")

        metric_card(
            "Khách dùng thẻ trung bình >80%",
            fmt(high_rate, 2, "%"),
            f"{number(cc_summary.high_utilization)} / "
            f"{number(cc_summary.customers)} khách",
            "orange"
        )

        card_groups = query(con, f"""
            SELECT
                CASE
                    WHEN cc.utilization IS NULL
                        THEN 'Không hợp lệ'
                    WHEN cc.utilization <= 0
                        THEN '<=0%'
                    WHEN cc.utilization <= 0.3
                        THEN '0-30%'
                    WHEN cc.utilization <= 0.5
                        THEN '30-50%'
                    WHEN cc.utilization <= 0.8
                        THEN '50-80%'
                    WHEN cc.utilization <= 1
                        THEN '80-100%'
                    ELSE '>100%'
                END AS usage_group,
                COUNT(*) AS customers,
                COUNT(a.TARGET) AS labeled_customers,
                SUM(
                    CASE WHEN a.TARGET = 1 THEN 1 ELSE 0 END
                ) AS target_1,
                100.0 * AVG(a.TARGET) AS rate
            FROM credit_card_customer_window cc
            LEFT JOIN application_dashboard a
              ON a.SK_ID_CURR = cc.SK_ID_CURR
             AND a.dataset = 'Train'
            WHERE cc.window_months = ?
              AND {cc_filter}
            GROUP BY 1
            ORDER BY 1
        """, [months] + cc_params)

        bar_chart(
            card_groups[
                card_groups.labeled_customers > 0
            ],
            "usage_group",
            "rate",
            "TARGET theo mức sử dụng thẻ",
            [
                "<=0%", "0-30%", "30-50%",
                "50-80%", "80-100%", ">100%",
                "Không hợp lệ"
            ]
        )

        with st.expander("Cách tính mức sử dụng thẻ", expanded=False):
            st.caption(
                "Trung bình Balance/Credit Limit theo khách hàng; "
                "TARGET lấy từ tập Train có nhãn."
            )

    with b:
        st.subheader("Dư nợ bên ngoài")

        debt_filter, debt_params = cohort_condition(
            "b", contracts, late_only
        )

        debt = scalar(con, f"""
            SELECT SUM(b.bureau_debt_sum)
            FROM bureau_customer_debt b
            WHERE {debt_filter}
        """, debt_params)

        metric_card(
            "Tổng dư nợ Bureau",
            fmt(
                debt / 1e9 if debt is not None else None,
                2,
                " tỷ"
            ),
            accent="violet"
        )

        with st.expander("Phạm vi dư nợ", expanded=False):
            st.caption(
                "Tổng dư nợ lịch sử theo khách hàng, "
                "không phải số dư tại ngày hiện tại."
            )

    st.divider()
    st.subheader("Trạng thái Bureau theo tháng")

    if contracts or late_only:
        st.info(
            "Biểu đồ Bureau theo tháng không hỗ trợ "
            "bộ lọc nhóm khách hàng hiện tại."
        )
    else:
        status_options = [
            "0", "1", "2", "3", "4", "5", "C", "X"
        ]

        statuses = st.multiselect(
            "Trạng thái Bureau",
            status_options
        )

        conditions = ["1=1"]
        args = []

        if months:
            conditions.append(
                "MONTHS_BALANCE BETWEEN ? AND 0"
            )
            args.append(-months + 1)

        if statuses:
            conditions.append(
                "STATUS IN ("
                + ",".join("?" for _ in statuses) + ")"
            )
            args.extend(statuses)

        bureau_where = " AND ".join(conditions)

        bureau = query(con, f"""
            SELECT
                MONTHS_BALANCE,
                SUM(
                    CASE WHEN STATUS IN ('1','2','3','4','5')
                    THEN records ELSE 0 END
                ) AS late_records,
                SUM(
                    CASE WHEN STATUS IN ('0','1','2','3','4','5')
                    THEN records ELSE 0 END
                ) AS valid_records,
                100.0 * SUM(
                    CASE WHEN STATUS IN ('1','2','3','4','5')
                    THEN records ELSE 0 END
                ) / NULLIF(
                    SUM(
                        CASE WHEN STATUS IN
                            ('0','1','2','3','4','5')
                        THEN records ELSE 0 END
                    ), 0
                ) AS rate
            FROM bureau_month_status
            WHERE {bureau_where}
            GROUP BY 1
            ORDER BY 1
        """, args)

        bureau = bureau.dropna(subset=["rate"])

        if bureau.empty:
            st.info("Không có trạng thái 0–5 để tính tỷ lệ.")
        else:
            fig = px.line(
                bureau,
                x="MONTHS_BALANCE",
                y="rate",
                markers=True,
                labels={
                    "MONTHS_BALANCE": "Tháng tương đối",
                    "rate": "Tỷ lệ (%)"
                }
            )

            fig.update_traces(
                line=dict(color="#116DA6", width=2.8),
                marker=dict(size=6)
            )
            fig.update_layout(
                template="plotly_white",
                height=380,
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(color="#34445B", size=13),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#E8EEF5", ticksuffix="%"),
                margin=dict(l=14, r=14, t=16, b=28)
            )
            st.plotly_chart(
                fig, use_container_width=True
            )

        with st.expander("Cách tính tỷ lệ Bureau", expanded=False):
            st.caption(
                "Mẫu số chỉ gồm trạng thái 0–5. "
                "C/X không được tính là không quá hạn. "
                "Bộ lọc trạng thái thay đổi tập mẫu."
            )

    st.divider()

    with st.expander("Phạm vi dữ liệu và phương pháp", expanded=False):
        st.caption(
            "Các cửa sổ 6/12 tháng dựa trên mốc tương đối của nguồn. "
            "Không bao gồm giao dịch chi tiết hoặc danh sách nhắc nợ."
        )


if page == "1. Hồ sơ tiếp nhận":
    dashboard_application()
else:
    dashboard_history()
