import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
)

st.set_page_config(
    page_title="서울 연평균 기온 변화 분석",
    page_icon="🌡️",
    layout="wide",
)

st.title("서울의 100년 연평균 기온 변화 및 데이터 분석")
st.write(
    "서울 기상 관측 자료를 바탕으로 원본 데이터 통계와 이상치/누락 구간을 시각화합니다."
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 원본 일별 데이터
    df_clean = df.dropna(subset=["날짜", "평균기온"]).copy()
    df_clean["연도"] = df_clean["날짜"].dt.year

    # 연도별 관측 일수 및 연평균 계산
    annual = (
        df_clean.groupby("연도")
        .agg(연평균기온=("평균기온", "mean"), 관측일수=("평균기온", "count"))
        .reset_index()
    )

    # 전체 연도 범위 생성 (비어 있는 연도 확인용)
    full_years = pd.DataFrame(
        {"연도": range(annual["연도"].min(), annual["연도"].max() + 1)}
    )
    annual_full = pd.merge(full_years, annual, on="연도", how="left")

    return df_clean, annual_full


try:
    df_raw, annual_full = load_data()

    # 최근 100년 범위 설정
    max_year = int(annual_full["연도"].max())
    min_year = max_year - 99
    annual_100 = annual_full[
        (annual_full["연도"] >= min_year) & (annual_full["연도"] <= max_year)
    ].copy()

    # --- 1. 원본 데이터 요약통계 ---
    st.subheader("📊 원본 데이터 요약통계 (일별 데이터)")
    col_stat1, col_stat2 = st.columns([1, 2])

    with col_stat1:
        st.metric("총 관측 일수", f"{len(df_raw):,} 일")
        st.metric("일평균 기온 평균", f"{df_raw['평균기온'].mean():.2f} ℃")
        st.metric(
            "일평균 최저 / 최고",
            f"{df_raw['평균기온'].min():.1f} ℃ / {df_raw['평균기온'].max():.1f} ℃",
        )

    with col_stat2:
        st.write("**주요 기술통계량**")
        stats_df = df_raw[["평균기온"]].describe().T
        stats_df.columns = [
            "관측수",
            "평균",
            "표준편차",
            "최소값",
            "25%",
            "중앙값",
            "75%",
            "최대값",
        ]
        st.dataframe(stats_df.style.format("{:.2f}"), use_container_width=True)

    st.divider()

    # --- 2. 이상치 및 누락 연도 감지 ---
    # 누락 연도 (데이터가 전혀 없는 연도)
    missing_years = annual_100[annual_100["연평균기온"].isna()]["연도"].tolist()

    # 이상하게 낮은 연도 감지 (IQR 하한 미만 또는 관측일수 부족)
    q1 = annual_100["연평균기온"].quantile(0.25)
    q3 = annual_100["연평균기온"].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr

    # 관측일수가 300일 미만이거나 기온이 이상치 하한선 미만인 연도
    anomaly_low = annual_100[
        (annual_100["연평균기온"] < lower_bound)
        | (annual_100["관측일수"] < 300)
    ].dropna(subset=["연평균기온"])

    # --- 3. Plotly 시각화 ---
    st.subheader("📈 연도별 연평균 기온 및 이상치 감지 그래프")

    fig = go.Figure()

    # 기본 연평균 선 그래프
    fig.add_trace(
        go.Scatter(
            x=annual_100["연도"],
            y=annual_100["연평균기온"],
            mode="lines+markers",
            name="연평균기온",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=4),
        )
    )

    # 유난히 낮은 연도 (이상치) 빨간 점으로 강조
    if not anomaly_low.empty:
        fig.add_trace(
            go.Scatter(
                x=anomaly_low["연도"],
                y=anomaly_low["연평균기온"],
                mode="markers+text",
                name="유난히 낮은 연도 (이상치/결측 우려)",
                marker=dict(color="crimson", size=10, symbol="x"),
                text=[f"{y}년" for y in anomaly_low["연도"]],
                textposition="bottom center",
            )
        )

    # 비어 있는 연도 (결측 구간) 세로 영역으로 표시
    for m_year in missing_years:
        fig.add_vrect(
            x0=m_year - 0.5,
            x1=m_year + 0.5,
            fillcolor="gray",
            opacity=0.3,
            line_width=0,
            annotation_text=f"{m_year} (누락)",
            annotation_position="top left",
        )

    fig.update_layout(
        xaxis_title="연도",
        yaxis_title="평균기온 (℃)",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 4. 요약 리포트 카드 ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "표시 기간",
            f"{int(annual_100['연도'].min())}~{int(annual_100['연도'].max())}",
        )

    with col2:
        missing_str = (
            ", ".join(map(str, missing_years)) if missing_years else "없음"
        )
        st.metric("데이터 누락 연도", missing_str)

    with col3:
        anom_str = (
            ", ".join([str(int(y)) for y in anomaly_low["연도"]])
            if not anomaly_low.empty
            else "없음"
        )
        st.metric("유난히 낮은 연도", anom_str)

    # 이상 원인 안내 박스
    if missing_years or not anomaly_low.empty:
        st.warning(
            f"⚠️ **데이터 이상 원인 분석**\n"
            f"- **누락 연도 ({missing_str})**: 6.25 전쟁 등 기상 관측이 중단되었던 시기입니다.\n"
            f"- **유난히 낮은 연도 ({anom_str})**: 해당 연도의 일부 월(특히 여름철) 관측 데이터가 누락되어 연평균이 기형적으로 낮게 계산되었을 가능성이 높습니다."
        )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
