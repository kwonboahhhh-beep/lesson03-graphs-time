import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"
)

st.set_page_config(page_title="영화 데이터 그래프 도감 1 - 시간", layout="wide")


# ---------------------------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_URL, dtype={"날짜": str})
    # 하이픈 없는 여덟 자리 숫자(예: 20240101)를 진짜 날짜로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], format="%Y%m%d")
    return df.sort_values("날짜").reset_index(drop=True)


def show_insight(text: str) -> None:
    """그래프 아래에 '이 그래프로 알 수 있는 것' 한 문장을 보여 주는 자리."""
    st.markdown(f"**이 그래프로 알 수 있는 것** : {text}")


df = load_data()

st.title("영화 데이터 그래프 도감 1 - 시간")
st.caption("일별 박스오피스 10위권 기록 (1년치)")


# ---------------------------------------------------------------------------
# 구역 1. 영화 한 편의 일관객 변화
# ---------------------------------------------------------------------------
def section_daily_audience(data: pd.DataFrame) -> None:
    st.header("1. 영화 한 편의 날짜별 일관객")

    # 일관객 합계가 큰 영화부터 드롭다운에 나열
    movies = (
        data.groupby("영화명")["일관객"].sum().sort_values(ascending=False).index.tolist()
    )
    movie = st.selectbox("영화를 골라 보세요", movies, key="sec1_movie")

    one = data[data["영화명"] == movie]

    fig = px.line(one, x="날짜", y="일관객", title=f"{movie} - 날짜별 일관객")
    fig.update_traces(
        hovertemplate="%{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra></extra>"
    )
    fig.update_layout(xaxis_title="날짜", yaxis_title="일관객(명)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    show_insight("여기에 이 그래프로 알 수 있는 내용을 한 문장으로 적어 주세요.")


section_daily_audience(df)


# ---------------------------------------------------------------------------
# 구역 2. 일관객 합계 상위 5편 비교
# ---------------------------------------------------------------------------
def section_top5_audience(data: pd.DataFrame) -> None:
    st.header("2. 일관객 합계 상위 5편 비교")

    # 기간 전체 일관객 합계가 가장 큰 5편 (큰 순서대로)
    top5 = data.groupby("영화명")["일관객"].sum().nlargest(5).index.tolist()
    top = data[data["영화명"].isin(top5)]

    fig = px.line(
        top,
        x="날짜",
        y="일관객",
        color="영화명",
        category_orders={"영화명": top5},
        title="일관객 합계 상위 5편의 날짜별 일관객",
    )
    fig.update_traces(
        hovertemplate="%{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra>%{fullData.name}</extra>"
    )
    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="일관객(명)",
        legend_title_text="영화명 (클릭하면 켜고 끌 수 있어요)",
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True)

    show_insight("여기에 이 그래프로 알 수 있는 내용을 한 문장으로 적어 주세요.")


st.divider()
section_top5_audience(df)


# ---------------------------------------------------------------------------
# 구역 3. 날짜별 10위권 일관객 합계 (영역 그래프)
# ---------------------------------------------------------------------------
def section_daily_total(data: pd.DataFrame) -> None:
    st.header("3. 날짜별 10위권 일관객 합계")

    # 그날 10위권 영화들의 일관객을 모두 더한 값
    daily = data.groupby("날짜", as_index=False)["일관객"].sum()
    # 합계가 가장 컸던 3일
    top3 = daily.nlargest(3, "일관객")

    fig = px.area(daily, x="날짜", y="일관객", title="날짜별 10위권 일관객 합계")
    fig.update_traces(
        hovertemplate="%{x|%Y-%m-%d}<br>10위권 합계: %{y:,}명<extra></extra>"
    )

    # 최고 3일을 점으로 찍고 날짜를 적어 줌 (라벨이 겹치지 않게 위치를 나눔)
    fig.add_trace(
        go.Scatter(
            x=top3["날짜"],
            y=top3["일관객"],
            mode="markers+text",
            text=top3["날짜"].dt.strftime("%Y-%m-%d"),
            textposition=["top center", "top left", "top right"],
            marker=dict(size=11, color="red", line=dict(width=1, color="white")),
            name="합계 최고 3일",
            hovertemplate="%{x|%Y-%m-%d}<br>10위권 합계: %{y:,}명<extra></extra>",
        )
    )
    # 위쪽 라벨이 잘리지 않도록 y축 여유 확보
    fig.update_yaxes(range=[0, daily["일관객"].max() * 1.15])
    fig.update_layout(
        xaxis_title="날짜", yaxis_title="일관객 합계(명)", showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    show_insight("여기에 이 그래프로 알 수 있는 내용을 한 문장으로 적어 주세요.")


st.divider()
section_daily_total(df)


# ---------------------------------------------------------------------------
# 구역 4. 일관객 합계 TOP 10 영화 (가로 막대그래프)
# ---------------------------------------------------------------------------
def section_top10_bar(data: pd.DataFrame) -> None:
    st.header("4. 일관객 합계 TOP 10 영화")

    # 영화별 일관객 합계와 10위권에 든 날수
    summary = (
        data.groupby("영화명")
        .agg(일관객합계=("일관객", "sum"), 순위권일수=("날짜", "nunique"))
        .reset_index()
        .nlargest(10, "일관객합계")
    )

    fig = px.bar(
        summary,
        x="일관객합계",
        y="영화명",
        orientation="h",
        custom_data=["순위권일수"],
        title="영화별 일관객 합계 TOP 10",
    )
    fig.update_traces(
        hovertemplate=(
            "%{y}<br>일관객 합계: %{x:,}명"
            "<br>10위권에 든 날: %{customdata[0]}일<extra></extra>"
        )
    )
    # 관객이 많은 영화가 위에 오도록 정렬
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(xaxis_title="일관객 합계(명)", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    show_insight("여기에 이 그래프로 알 수 있는 내용을 한 문장으로 적어 주세요.")


st.divider()
section_top10_bar(df)


# ---------------------------------------------------------------------------
# 구역 5. 월 × 요일별 일관객 합계 (히트맵)
# ---------------------------------------------------------------------------
def section_month_weekday_heatmap(data: pd.DataFrame) -> None:
    st.header("5. 월 × 요일별 일관객 합계")

    weekdays = ["월", "화", "수", "목", "금", "토", "일"]  # 월요일부터 일요일 순서

    # 날짜에서 월과 요일을 뽑아 새 열로 만듦
    tmp = data.assign(
        월=data["날짜"].dt.month,
        요일=data["날짜"].dt.dayofweek.map(dict(enumerate(weekdays))),
    )
    pivot = (
        tmp.pivot_table(
            index="요일", columns="월", values="일관객", aggfunc="sum", fill_value=0
        )
        .reindex(weekdays)  # 요일 순서 고정
    )
    pivot.columns = [f"{m}월" for m in pivot.columns]

    fig = px.imshow(
        pivot,
        color_continuous_scale="Blues",  # 진할수록 관객이 많음
        aspect="auto",
        labels=dict(x="월", y="요일", color="일관객 합계(명)"),
        title="월 × 요일별 일관객 합계",
    )
    fig.update_traces(
        hovertemplate="%{x} %{y}요일<br>일관객 합계: %{z:,}명<extra></extra>"
    )
    st.plotly_chart(fig, use_container_width=True)

    show_insight("여기에 이 그래프로 알 수 있는 내용을 한 문장으로 적어 주세요.")


st.divider()
section_month_weekday_heatmap(df)

# ---------------------------------------------------------------------------
# 구역 6 이후: 새 그래프는 아래에 구역 함수를 만들어 추가하세요.
# ---------------------------------------------------------------------------
# st.divider()
# section_next_chart(df)
