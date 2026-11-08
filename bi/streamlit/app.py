from pathlib import Path
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
.block-container {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
}
div[data-testid="stMetric"] {
    padding: 16px;
    border: 1px solid #dbe2ea;
    border-radius: 12px;
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


def metric(col, title, value, caption=None):
    col.metric(title, value)
    if caption:
        col.caption(caption)


def bar_chart(df, x, y, title, order=None):
    st.subheader(title)

    if df.empty:
        st.info("Không có dữ liệu phù hợp bộ lọc.")
        return

    fig = px.bar(
        df,
        x=x,
        y=y,
        hover_data=[
            c for c in ["total_records", "target_1"]
            if c in df.columns
        ],
        category_orders={x: order} if order else None
    )

    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=20, b=30),
        xaxis_title=None,
        yaxis_title="Tỷ lệ (%)",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


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
    st.title("DTWH")
    st.caption("Home Credit Data Lakehouse")

    page = st.radio(
        "Dashboard",
        [
            "1. Hồ sơ tiếp nhận",
            "2. Lịch sử tín dụng"
        ]
    )

    with st.expander("Trạng thái dữ liệu"):
        st.json(sources)

    st.caption(
        "Dữ liệu được xử lý trên Colab và "
        "xuất thành BI Serving Parquet."
    )


def dashboard_application():
    st.title("Giám sát rủi ro hồ sơ tiếp nhận")
    st.caption(
        "TARGET là nhãn lịch sử, không phải kết quả dự báo."
    )

    c1, c2, c3, c4, c5 = st.columns(5)

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

    a, b, c, d = st.columns(4)

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
        f"{number(overview.labeled_records)} có nhãn"
    )

    metric(
        c, "CTI trung vị",
        fmt(overview.median_cti, 4, " lần")
    )

    metric(
        d, "Credit/Goods trung vị",
        fmt(overview.median_credit_goods, 4, " lần")
    )

    a, b = st.columns(2)

    with a:
        st.metric(
            "DTI trung vị",
            fmt(overview.median_dti_pct, 2, "%")
        )
        st.caption(
            f"Số DTI hợp lệ: {number(overview.valid_dti)}"
        )

    with b:
        coverage = (
            100 * overview.labeled_records
            / overview.total_records
            if overview.total_records else None
        )
        st.metric(
            "Độ bao phủ nhãn",
            fmt(coverage, 2, "%")
        )

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

        st.caption(
            f"Ngưỡng thu nhập Train: "
            f"{fmt(t1, 0)}, {fmt(t2, 0)}, "
            f"{fmt(t3, 0)}, {fmt(t4, 0)}. "
            "Ngưỡng cố định theo Train; tỷ lệ được "
            "tính lại theo các bộ lọc hiện tại."
        )

    st.divider()

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
            hole=0.45
        )
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Tỷ lệ TARGET luôn chỉ tính trên hồ sơ có nhãn. "
        "CTI = Credit/Income; Credit/Goods = Credit/Goods Price; "
        "DTI = Annuity/Income. Các trung vị tính trên "
        "hồ sơ đang được lọc."
    )


def dashboard_history():
    st.title("Lịch sử tín dụng và hành vi thanh toán")
    st.caption(
        "Dữ liệu đã được tổng hợp theo khách hàng "
        "và cửa sổ lịch sử trên Google Colab."
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

    a, b, c, d = st.columns(4)

    metric(
        a, "Kỳ trả trễ",
        fmt(late_rate, 2, "%"),
        f"{number(inst.late_periods)} / "
        f"{number(inst.valid_periods)} kỳ đủ dữ liệu"
    )

    metric(
        b, "Khách từng có kỳ trễ",
        fmt(customer_late_rate, 2, "%"),
        f"{number(inst.customers_ever_late)} / "
        f"{number(inst.customers)} khách"
    )

    metric(
        c, "Tổng thiếu hụt",
        fmt(inst.shortfall / 1e6, 2, " triệu"),
        "Đơn vị tiền của nguồn Home Credit"
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

    st.metric(
        "Tỷ lệ phê duyệt đơn cũ",
        fmt(approval_rate, 2, "%")
    )
    st.caption(
        f"{number(previous.approved)} / "
        f"{number(previous.total)} đơn"
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

        st.metric(
            "Khách dùng thẻ trung bình >80%",
            fmt(high_rate, 2, "%")
        )
        st.caption(
            f"{number(cc_summary.high_utilization)} / "
            f"{number(cc_summary.customers)} khách"
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

        st.caption(
            "Mức sử dụng thẻ là trung bình tỷ lệ "
            "Balance/Credit Limit theo khách hàng. "
            "TARGET chỉ dùng hồ sơ Train có nhãn."
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

        st.metric(
            "Tổng dư nợ Bureau",
            fmt(
                debt / 1e9 if debt is not None else None,
                2,
                " tỷ"
            )
        )

        st.caption(
            "Tổng dư nợ Bureau là dữ liệu "
            "tổng hợp theo khách hàng, không phải "
            "dư nợ tại ngày hiện tại."
        )

    st.divider()
    st.subheader("Trạng thái Bureau theo tháng")

    if contracts or late_only:
        st.warning(
            "Không hiển thị biểu đồ Bureau theo nhóm "
            "khách hàng đang lọc: bảng BI hiện tại "
            "chỉ tổng hợp theo tháng và trạng thái, "
            "chưa lưu mã khách hàng."
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

            fig.update_layout(height=380)
            st.plotly_chart(
                fig, use_container_width=True
            )

        st.caption(
            "Mẫu số chỉ bao gồm trạng thái 0–5. "
            "C và X không được tính là không quá hạn. "
            "Nếu chọn trạng thái, tỷ lệ được tính "
            "trong tập trạng thái đã chọn."
        )

    st.divider()

    st.info(
        "Bản BI Serving không lưu giao dịch chi tiết, "
        "nên chưa hỗ trợ danh sách nhắc nợ, "
        "phân phối ngày lệch từng giao dịch hoặc "
        "trung vị ngày lệch giao dịch. "
        "Không suy diễn các chỉ số này từ dữ liệu tổng hợp."
    )

    st.caption(
        "Cửa sổ 6/12 tháng sử dụng ngày và tháng tương đối "
        "trong nguồn Home Credit. Không đại diện "
        "cho 6/12 tháng lịch tính từ hôm nay."
    )


if page == "1. Hồ sơ tiếp nhận":
    dashboard_application()
else:
    dashboard_history()
