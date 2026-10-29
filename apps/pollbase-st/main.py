"""Interactive dashboard for exploring UK voting-intention polling data."""

import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Pollbase Interactive - v0.1-st",
    layout="wide",
)

# Party series and their chart colors.
PARTY_COLORS = {
    "Con": "#0087DC",
    "Lab": "#E4003B",
    "LD": "#FAA61A",
    "Green": "#6AB023",
    "Reform": "#12B6CF",
    "Restore Britain": "#6B7280",
    "Your Party": "#7C3AED",
}

# Paths to data and assets bundled with the app.
DATA_PATH = Path(__file__).with_name("result.csv")
ABOUT_PATH = Path(__file__).with_name("about.md")
LOGO_PATH = Path(__file__).with_name("UKCharts.png")
CC_BY_LOGO_URL = (
    "https://mirrors.creativecommons.org/presskit/buttons/"
    "88x31/svg/by.svg"
    )

# Party columns to expose in charts and tables.
PARTY_COLUMNS = [
    "Con",
    "Lab",
    "LD",
    "Green",
    "Reform",
    "Restore Britain",
    "Your Party",
]

# Polling companies selected when the app first loads.
DEFAULT_COMPANIES = [
    "YouGov",
    "Ipsos",
    "More in Common",
    "Survation",
    "Opinium",
    "Find Out Now",
    "Deltapoll",
    "BMG",
    "JL Partners",
    "Focaldata",
]


@st.cache_data
def load_pollbase(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load, clean, and sort polling data from a CSV file."""
    df = pd.read_csv(path)
    df.columns = [str(col).strip() for col in df.columns]

    df["Date"] = pd.to_datetime(
        df["Date"].str.strip(),
        format="%d/%m/%y",
        errors="coerce",
    )
    df["Polling Company"] = df["Polling Company"].str.strip()
    df["Publisher"] = df["Publisher"].fillna("None").str.strip()

    for col in PARTY_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Date", "Polling Company"])
    df = df.dropna(subset=PARTY_COLUMNS, how="all")
    df = df.drop_duplicates().sort_values("Date").reset_index(drop=True)

    return df


@st.cache_data
def logo_data_uri(path: Path = LOGO_PATH) -> str:
    """Return the local logo as a data URI for the HTML banner."""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


# Date presets are relative to the latest date in the loaded data.
PERIOD_OPTIONS = ["Last 3 months", "Last 6 months", "Last year", "All data"]
PERIOD_MONTHS = {"Last 3 months": 3, "Last 6 months": 6, "Last year": 12}


def _preset_start_date(min_date, max_date, period: str):
    """Get a preset's start date, bounded by the earliest poll date."""
    if period == "All data":
        return min_date

    start = (
        pd.Timestamp(max_date) - pd.DateOffset(months=PERIOD_MONTHS[period])
    ).date()
    return max(min_date, start)


def date_range_control(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Render sidebar date controls and return the selected date bounds."""
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()

    def apply_preset() -> None:
        period = st.session_state["period_preset"]
        st.session_state["date_range"] = (
            _preset_start_date(min_date, max_date, period),
            max_date,
        )

    st.sidebar.radio(
        "Time period",
        options=PERIOD_OPTIONS,
        index=PERIOD_OPTIONS.index("All data"),
        key="period_preset",
        on_change=apply_preset,
    )

    if "date_range" not in st.session_state:
        st.session_state["date_range"] = (min_date, max_date)

    selected = st.sidebar.date_input(
        "Date range",
        min_value=min_date,
        max_value=max_date,
        key="date_range",
    )

    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        start_date, end_date = selected
    else:
        start_date, end_date = min_date, max_date

    return pd.Timestamp(start_date), pd.Timestamp(end_date)


def sidebar_filters(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Render party and polling-company filters and return their selections."""
    companies = sorted(df["Polling Company"].dropna().unique())

    parties = st.sidebar.multiselect(
        "Parties",
        options=PARTY_COLUMNS,
        default=PARTY_COLUMNS,
    )
    selected_companies = st.sidebar.multiselect(
        "Polling companies",
        options=companies,
        default=[
            company for company in companies if company in DEFAULT_COMPANIES
        ],
    )

    return parties, selected_companies


df = load_pollbase()
start_date, end_date = date_range_control(df)
parties, companies = sidebar_filters(df)

# Embed the logo so the title banner works in the browser-based Stlite app.
st.html(
    f"""
    <div style="
      display: flex; align-items: center; flex-wrap: wrap; gap: 1.5rem;
      background-color: #F3F1EC; border-radius: 0.75rem;
      padding: 1rem 1.5rem; margin-bottom: 1.25rem;
    ">
      <img src="{logo_data_uri()}" alt="UKCharts logo"
           style="height: clamp(48px, 8vw, 76px); width: auto;" />
      <h1 style="
        margin: 0; color: #1F2937; line-height: 1.1; font-weight: 700;
        color: darkblue; font-size: clamp(1.6rem, 4vw, 2.4rem);
      ">
        Pollbase Interactive Plus:
        <span style="font-size: smaller; font-weight: normal; color: darkblue">
          UK Voting Intentions
        </span>
      </h1>
    </div>
    """
)

trend_tab, snapshot_tab, raw_data_tab, about_tab = st.tabs(
    [
        "**Trend**",
        "**Snapshot**",
        "**Raw Data**",
        "**About**",
    ]
)

with snapshot_tab:
    mask = (
        df["Date"].between(start_date, end_date)
        & df["Polling Company"].isin(companies)
    )
    filtered_df = df.loc[mask]

    if filtered_df.empty:
        st.info("No polls match the selected filters.")
    else:
        last_date = filtered_df["Date"].max()
        # Average same-day polls to show one latest value per party.
        snapshot_df = (
            filtered_df.loc[
                filtered_df["Date"] == last_date,
                ["Date", *parties],
            ]
            .melt(id_vars="Date", var_name="Party", value_name="Share")
            .dropna(subset=["Share"])
            .groupby("Party", as_index=False)["Share"]
            .mean()
            .sort_values("Share", ascending=False)
        )

        if snapshot_df.empty:
            st.info("No polls match the selected filters.")
        else:
            fig = px.bar(
                snapshot_df,
                x="Party",
                y="Share",
                color="Party",
                color_discrete_map=PARTY_COLORS,
                text="Share",
                title=f"Snapshot of party standings: {last_date:%d %B %Y}",
                labels={"Share": "Vote share (%)"},
            )
            fig.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside",
            )
            fig.update_layout(
                showlegend=False,
                yaxis_range=[0, snapshot_df["Share"].max() * 1.15],
            )
            st.plotly_chart(fig,  width='stretch',)

with raw_data_tab:
    mask = (
        df["Date"].between(start_date, end_date)
        & df["Polling Company"].isin(companies)
    )
    raw_df = df.loc[
        mask,
        ["Date", "Polling Company", "Publisher", "Source", *parties],
    ].copy()
    raw_df["Date"] = raw_df["Date"].dt.date
    st.dataframe(raw_df, hide_index=True)

with trend_tab:
    mask = (
        df["Date"].between(start_date, end_date)
        & df["Polling Company"].isin(companies)
    )
    trend_df = (
        df.loc[mask, ["Date", *parties]]
        .melt(id_vars="Date", var_name="Party", value_name="Share")
        .dropna(subset=["Share"])
    )

    fig = px.scatter(
        trend_df,
        x="Date",
        y="Share",
        color="Party",
        color_discrete_map=PARTY_COLORS,
        trendline="lowess",
        labels={"Share": "Vote share (%)", "Date": ""},
    )
    # Show individual polls alongside a LOWESS trendline for each party.
    fig.update_traces(
        marker=dict(size=5, opacity=0.45),
        selector=dict(mode="markers"),
    )
    fig.update_layout(hovermode="x unified", legend_title_text="Party")
    st.plotly_chart(fig, width='stretch',)

with about_tab:
    st.markdown(ABOUT_PATH.read_text(encoding="utf-8"))


# Credit the source data and show its reuse license.
st.markdown(
    f"""
    <div style="
      margin-top: 2rem; padding-top: 1rem;
      border-top: 1px solid rgba(128, 128, 128, 0.3);
      display: flex; align-items: center; justify-content: center;
      flex-wrap: wrap; gap: 0.5rem; font-size: 0.85rem;
    ">
      <span>
        Data derived from Dr Mark Pack's
        <a href="https://www.markpack.org.uk/opinion-polls/" target="_blank"
           rel="noopener noreferrer">Pollbase</a>.
      </span>
      <span>
        Charts may be downloaded and reused under the Creative Commons CC BY
        license.
      </span>
      <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank"
         rel="noopener noreferrer"
         aria-label="Creative Commons Attribution 4.0"
         title="Creative Commons Attribution 4.0">
        <img
          src="{CC_BY_LOGO_URL}"
          alt="CC BY" height="22"
        />
      </a>
    </div>
    """,
    unsafe_allow_html=True,
)
