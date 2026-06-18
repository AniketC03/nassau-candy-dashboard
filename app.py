"""
Nassau Candy Distributor — Factory-to-Customer Shipping Route Efficiency Dashboard
Run with:  streamlit run app.py
Requires:  Nassau_Candy_Distributor.csv in the same folder.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Page config & light styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nassau Candy | Shipping Route Efficiency",
    page_icon="🚚",
    layout="wide",
)

st.markdown("""
<style>
.metric-note {color:#888; font-size:0.8rem;}
div[data-testid="stMetricValue"] {font-size: 1.6rem;}
</style>
""", unsafe_allow_html=True)

US_STATE_ABBR = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO',
    'Connecticut':'CT','Delaware':'DE','District of Columbia':'DC','Florida':'FL','Georgia':'GA',
    'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY',
    'Louisiana':'LA','Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN',
    'Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH',
    'New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND',
    'Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI',
    'South Carolina':'SC','South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT',
    'Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'
}

FACTORY_COORDS = {
    "Lot's O' Nuts":     (32.881893, -111.768036),
    "Wicked Choccy's":   (32.076176,  -81.088371),
    "Sugar Shack":       (48.119140,  -96.181150),
    "Secret Factory":    (41.446333,  -90.565487),
    "The Other Factory": (35.117500,  -89.971107),
}

PRODUCT_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows":         "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious":    "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate":        "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy":              "Sugar Shack",
    "SweeTARTS":                "Sugar Shack",
    "Nerds":                    "Sugar Shack",
    "Fun Dip":                  "Sugar Shack",
    "Fizzy Lifting Drinks":     "Sugar Shack",
    "Everlasting Gobstopper":   "Secret Factory",
    "Hair Toffee":              "The Other Factory",
    "Lickable Wallpaper":       "Secret Factory",
    "Wonka Gum":                "Secret Factory",
    "Kazookles":                "The Other Factory",
}

DATA_PATH = "Nassau_Candy_Distributor.csv"


# ---------------------------------------------------------------------------
# Data loading & feature engineering (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    text_cols = ['Ship Mode', 'Country/Region', 'City', 'State/Province', 'Division', 'Region', 'Product Name']
    for c in text_cols:
        df[c] = df[c].astype(str).str.strip()

    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['Order Date', 'Ship Date'])

    df['Lead Time'] = (df['Ship Date'] - df['Order Date']).dt.days
    df = df[df['Lead Time'] >= 0]  # remove invalid negative lead times, per cleaning spec

    df['Factory'] = df['Product Name'].map(PRODUCT_FACTORY)
    df = df.dropna(subset=['Factory'])
    df['Factory Lat'] = df['Factory'].map(lambda f: FACTORY_COORDS[f][0])
    df['Factory Lon'] = df['Factory'].map(lambda f: FACTORY_COORDS[f][1])

    df['Route (Region)'] = df['Factory'] + ' -> ' + df['Region']
    df['Route (State)'] = df['Factory'] + ' -> ' + df['State/Province']
    df['State Abbr'] = df['State/Province'].map(US_STATE_ABBR)

    return df


try:
    raw_df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"Could not find `{DATA_PATH}`. Place the CSV file in the same folder as app.py.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.title("🚚 Filters")

min_date, max_date = raw_df['Order Date'].min().date(), raw_df['Order Date'].max().date()
date_range = st.sidebar.date_input(
    "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

regions = sorted(raw_df['Region'].unique())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

available_states = sorted(raw_df[raw_df['Region'].isin(selected_regions)]['State/Province'].unique())
selected_states = st.sidebar.multiselect("State / Province", available_states, default=available_states)

ship_modes = sorted(raw_df['Ship Mode'].unique())
selected_modes = st.sidebar.multiselect("Ship Mode", ship_modes, default=ship_modes)

lt_min, lt_max = int(raw_df['Lead Time'].min()), int(raw_df['Lead Time'].max())
default_threshold = int(raw_df['Lead Time'].quantile(0.75))
delay_threshold = st.sidebar.slider(
    "Delay threshold (days) — shipments above this are flagged 'Delayed'",
    min_value=lt_min, max_value=lt_max, value=default_threshold
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ Data quality note: Order Date and Ship Date in the source data are not "
    "co-dated, producing inflated absolute lead-time values. Use this dashboard "
    "for **relative** route/mode comparisons, not literal day counts. See the "
    "EDA notebook, Section 3, for details."
)

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
mask = (
    (raw_df['Order Date'].dt.date >= start_date)
    & (raw_df['Order Date'].dt.date <= end_date)
    & (raw_df['Region'].isin(selected_regions))
    & (raw_df['State/Province'].isin(selected_states))
    & (raw_df['Ship Mode'].isin(selected_modes))
)
df = raw_df[mask].copy()
df['Delayed'] = df['Lead Time'] > delay_threshold

st.title("Factory → Customer Shipping Route Efficiency")
st.caption("Nassau Candy Distributor — Logistics Analytics Dashboard")

if df.empty:
    st.warning("No shipments match the current filters. Adjust filters in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# Top KPI row
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Shipments", f"{len(df):,}")
k2.metric("Avg Lead Time", f"{df['Lead Time'].mean():.0f} d")
k3.metric("Delay Rate", f"{df['Delayed'].mean()*100:.1f}%")
k4.metric("Total Sales", f"${df['Sales'].sum():,.0f}")
k5.metric("Routes Active", f"{df['Route (State)'].nunique():,}")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Route Efficiency Overview",
    "🗺️ Geographic Shipping Map",
    "🚢 Ship Mode Comparison",
    "🔎 Route Drill-Down",
])

# ---------------------------------------------------------------------------
# TAB 1 — Route Efficiency Overview
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Average Lead Time by Route")

    granularity = st.radio("Route granularity", ["Factory → Region", "Factory → State"], horizontal=True)
    route_col = 'Route (Region)' if granularity == "Factory → Region" else 'Route (State)'
    min_shipments = st.slider("Minimum shipments per route to include", 1, 50, 10, key="t1_minship")

    route_agg = df.groupby(route_col).agg(
        Total_Shipments=('Order ID', 'count'),
        Avg_Lead_Time=('Lead Time', 'mean'),
        Std_Lead_Time=('Lead Time', 'std'),
        Delay_Rate=('Delayed', 'mean'),
        Total_Sales=('Sales', 'sum'),
    ).reset_index()
    route_agg = route_agg[route_agg['Total_Shipments'] >= min_shipments].sort_values('Avg_Lead_Time')

    if route_agg.empty:
        st.info("No routes meet the minimum shipment threshold — lower it in the slider above.")
    else:
        lo, hi = route_agg['Avg_Lead_Time'].min(), route_agg['Avg_Lead_Time'].max()
        route_agg['Efficiency Score'] = 100 if hi == lo else (100 * (hi - route_agg['Avg_Lead_Time']) / (hi - lo)).round(1)

        c1, c2 = st.columns(2)
        with c1:
            top10 = route_agg.head(10)
            fig = px.bar(top10, x='Avg_Lead_Time', y=route_col, orientation='h',
                         title="Top 10 Most Efficient Routes", color_discrete_sequence=['#27AE60'])
            fig.update_layout(yaxis={'categoryorder': 'total descending'}, xaxis_title="Avg Lead Time (days)")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            bottom10 = route_agg.tail(10)
            fig = px.bar(bottom10, x='Avg_Lead_Time', y=route_col, orientation='h',
                         title="Bottom 10 Least Efficient Routes", color_discrete_sequence=['#C0392B'])
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, xaxis_title="Avg Lead Time (days)")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Route Performance Leaderboard")
        display_df = route_agg.sort_values('Efficiency Score', ascending=False).rename(columns={
            route_col: 'Route', 'Total_Shipments': 'Shipments', 'Avg_Lead_Time': 'Avg Lead Time (d)',
            'Std_Lead_Time': 'Std Dev (d)', 'Delay_Rate': 'Delay Rate', 'Total_Sales': 'Total Sales ($)'
        })
        display_df['Delay Rate'] = (display_df['Delay Rate'] * 100).round(1)
        st.dataframe(
            display_df.style.format({
                'Avg Lead Time (d)': '{:.1f}', 'Std Dev (d)': '{:.1f}',
                'Delay Rate': '{:.1f}%', 'Total Sales ($)': '${:,.0f}', 'Efficiency Score': '{:.1f}'
            }),
            use_container_width=True, height=400
        )

# ---------------------------------------------------------------------------
# TAB 2 — Geographic Shipping Map
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("US Shipping Efficiency Heatmap")

    us_df = df[df['Country/Region'] == 'United States'].copy()
    state_agg = us_df.groupby(['State/Province', 'State Abbr']).agg(
        Volume=('Order ID', 'count'),
        Avg_Lead_Time=('Lead Time', 'mean'),
        Delay_Rate=('Delayed', 'mean'),
    ).reset_index()

    if state_agg.empty:
        st.info("No US shipments match current filters.")
    else:
        map_metric = st.radio("Color by", ["Avg Lead Time", "Delay Rate", "Shipment Volume"], horizontal=True)
        metric_map = {"Avg Lead Time": "Avg_Lead_Time", "Delay Rate": "Delay_Rate", "Shipment Volume": "Volume"}
        color_col = metric_map[map_metric]
        color_scale = "RdYlGn_r" if map_metric != "Shipment Volume" else "Blues"

        fig = px.choropleth(
            state_agg, locations='State Abbr', locationmode="USA-states",
            color=color_col, scope="usa", color_continuous_scale=color_scale,
            hover_name='State/Province',
            hover_data={'Volume': True, 'Avg_Lead_Time': ':.1f', 'Delay_Rate': ':.1%', 'State Abbr': False},
            title=f"US States Colored by {map_metric}"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Regional Bottleneck Map: Volume vs. Lead Time")
        region_agg = df.groupby('Region').agg(
            Volume=('Order ID', 'count'), Avg_Lead_Time=('Lead Time', 'mean'), Delay_Rate=('Delayed', 'mean')
        ).reset_index()
        fig2 = px.scatter(
            region_agg, x='Volume', y='Avg_Lead_Time', text='Region', size='Volume',
            color='Delay_Rate', color_continuous_scale='RdYlGn_r',
            title="Bubble size = volume, color = delay rate"
        )
        fig2.update_traces(textposition='top center')
        st.plotly_chart(fig2, use_container_width=True)

        canada_df = df[df['Country/Region'] == 'Canada']
        if not canada_df.empty:
            st.subheader("Canada — Provincial Summary")
            ca_agg = canada_df.groupby('State/Province').agg(
                Volume=('Order ID', 'count'), Avg_Lead_Time=('Lead Time', 'mean'), Delay_Rate=('Delayed', 'mean')
            ).reset_index().sort_values('Volume', ascending=False)
            ca_agg['Delay_Rate'] = (ca_agg['Delay_Rate'] * 100).round(1)
            st.dataframe(ca_agg.rename(columns={'Delay_Rate': 'Delay Rate (%)', 'Avg_Lead_Time': 'Avg Lead Time (d)'}),
                         use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 3 — Ship Mode Comparison
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Lead Time Comparison by Ship Mode")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.box(df, x='Ship Mode', y='Lead Time', color='Ship Mode',
                     title="Lead Time Distribution by Ship Mode")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        mode_agg = df.groupby('Ship Mode').agg(
            Orders=('Order ID', 'count'), Avg_Lead_Time=('Lead Time', 'mean'), Delay_Rate=('Delayed', 'mean')
        ).reset_index().sort_values('Avg_Lead_Time')
        fig = px.bar(mode_agg, x='Ship Mode', y='Delay_Rate', color='Ship Mode',
                     title="Delay Rate by Ship Mode")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Cost–Time Tradeoff")
    mode_financials = df.groupby('Ship Mode').agg(
        Orders=('Order ID', 'count'), Avg_Sales=('Sales', 'mean'), Avg_Cost=('Cost', 'mean'),
        Avg_Gross_Profit=('Gross Profit', 'mean'), Avg_Lead_Time=('Lead Time', 'mean'),
        Delay_Rate=('Delayed', 'mean'),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=mode_financials['Ship Mode'], y=mode_financials['Avg_Cost'],
                          name='Avg Cost ($)', marker_color='#E67E22'))
    fig.add_trace(go.Scatter(x=mode_financials['Ship Mode'], y=mode_financials['Avg_Lead_Time'],
                              name='Avg Lead Time (days)', yaxis='y2', mode='lines+markers',
                              line=dict(color='#2980B9', width=3)))
    fig.update_layout(
        title="Average Cost vs. Average Lead Time by Ship Mode",
        yaxis=dict(title='Avg Cost ($)'),
        yaxis2=dict(title='Avg Lead Time (days)', overlaying='y', side='right'),
        legend=dict(orientation='h', y=1.1)
    )
    st.plotly_chart(fig, use_container_width=True)

    mode_financials['Delay_Rate'] = (mode_financials['Delay_Rate'] * 100).round(1)
    st.dataframe(
        mode_financials.rename(columns={
            'Avg_Sales': 'Avg Sales ($)', 'Avg_Cost': 'Avg Cost ($)', 'Avg_Gross_Profit': 'Avg Gross Profit ($)',
            'Avg_Lead_Time': 'Avg Lead Time (d)', 'Delay_Rate': 'Delay Rate (%)'
        }).round(2),
        use_container_width=True
    )

# ---------------------------------------------------------------------------
# TAB 4 — Route Drill-Down
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Route Drill-Down")

    drill_factory = st.selectbox("Factory", sorted(df['Factory'].unique()))
    states_for_factory = sorted(df[df['Factory'] == drill_factory]['State/Province'].unique())
    drill_state = st.selectbox("State / Province", states_for_factory)

    route_df = df[(df['Factory'] == drill_factory) & (df['State/Province'] == drill_state)]

    if route_df.empty:
        st.info("No shipments for this route under current filters.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Shipments", f"{len(route_df):,}")
        c2.metric("Avg Lead Time", f"{route_df['Lead Time'].mean():.1f} d")
        c3.metric("Delay Rate", f"{route_df['Delayed'].mean()*100:.1f}%")
        c4.metric("Total Sales", f"${route_df['Sales'].sum():,.0f}")

        st.markdown(f"**State-level performance:** {drill_factory} → {drill_state}")

        fig = px.scatter(
            route_df.sort_values('Order Date'), x='Order Date', y='Lead Time', color='Ship Mode',
            hover_data=['Order ID', 'Product Name', 'Sales'],
            title=f"Order-Level Shipment Timeline: {drill_factory} → {drill_state}"
        )
        fig.add_hline(y=delay_threshold, line_dash='dash', line_color='red',
                       annotation_text='Delay threshold')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Product Mix on this Route")
        prod_mix = route_df.groupby('Product Name').agg(
            Units=('Units', 'sum'), Sales=('Sales', 'sum'), Avg_Lead_Time=('Lead Time', 'mean')
        ).reset_index().sort_values('Sales', ascending=False)
        st.dataframe(prod_mix.style.format({'Sales': '${:,.0f}', 'Avg_Lead_Time': '{:.1f}'}),
                     use_container_width=True)

        with st.expander("Raw order-level records for this route"):
            st.dataframe(
                route_df[['Order ID', 'Order Date', 'Ship Date', 'Lead Time', 'Ship Mode',
                          'Product Name', 'Sales', 'Units', 'Delayed']].sort_values('Order Date'),
                use_container_width=True
            )

st.markdown("---")
st.caption("Built for Nassau Candy Distributor — Factory-to-Customer Shipping Route Efficiency Analysis")
