import streamlit as st
import pandas as pd

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

st.set_page_config(
    page_title="서울 연평균 기온 변화",
    page_icon="🌡️",
    layout="wide",
)

st.title("서울의 100년 연평균 기온 변화")
st.write("서울 기상 관측 자료를 바탕으로 연도별 평균기온의 변화를 보여줍니다.")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    df = df.dropna(subset=["날짜", "평균기온"])
    df["연도"] = df["날짜"].dt.year

    annual = (
        df.groupby("연도", as_index=False)["평균기온"]
        .mean()
        .rename(columns={"평균기온": "연평균기온"})
    )

    return annual


try:
    annual = load_data()

    # 전체 자료 중 최근 100년을 표시
    annual_100 = annual.tail(100).copy()

    st.subheader("연도별 연평균 기온")

    chart_data = annual_100.set_index("연도")[["연평균기온"]]

    st.line_chart(
        chart_data,
        y="연평균기온",
        x_label="연도",
        y_label="평균기온 (℃)",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "표시 기간",
            f"{int(annual_100['연도'].min())}~{int(annual_100['연도'].max())}",
        )

    with col2:
        st.metric(
            "가장 낮은 연평균 기온",
            f"{annual_100['연평균기온'].min():.1f} ℃",
        )

    with col3:
        st.metric(
            "가장 높은 연평균 기온",
            f"{annual_100['연평균기온'].max():.1f} ℃",
        )

    st.caption(
        "※ 연평균 기온은 해당 연도의 일평균 기온을 평균하여 계산했습니다."
    )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
