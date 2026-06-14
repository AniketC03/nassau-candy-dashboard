import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nassau Candy | Shipping Analytics",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F7F8FA; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1F4E79 0%, #2E75B6 100%);
    }
    [data-testid="stSidebar"] * { color: #E8F4FD !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSlider label { color: #BDD7EE !important; font-weight: 600; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #FFFFFF !important; }

    /* KPI cards */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #2E75B6;
        margin-bottom: 8px;
    }
    .kpi-card.green  { border-left-color: #1E8449; }
    .kpi-card.orange { border-left-color: #E07B39; }
    .kpi-card.red    { border-left-color: #C0392B; }
    .kpi-label { font-size: 12px; color: #888; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #1F4E79; margin: 4px 0 2px; }
    .kpi-delta { font-size: 12px; color: #555; }

    /* Section headers */
    .section-header {
        font-size: 18px; font-weight: 700; color: #1F4E79;
        border-bottom: 2px solid #2E75B6;
        padding-bottom: 6px; margin: 24px 0 16px;
    }

    /* Alert box */
    .alert-box {
        background: #FFF8E1; border-left: 4px solid #F9A825;
        border-radius: 8px; padding: 14px 18px; margin: 12px 0;
        font-size: 13px; color: #5D4037;
    }

    /* Chart cards */
    .chart-card {
        background: white; border-radius: 12px;
        padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* Fix invisible tab labels */
    .stTabs [data-baseweb="tab"] div p,
    .stTabs [data-baseweb="tab"] { color: #333333 !important; font-weight: 500 !important; }
    .stTabs [aria-selected="true"] div p,
    .stTabs [aria-selected="true"] { color: #1F4E79 !important; font-weight: 700 !important; }

    /* Fix grey chart backgrounds */
    [data-testid="stPlotlyChart"] > div { background: white !important; border-radius: 10px; }

    /* Hide streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── Data loading & feature engineering ────────────────────────────────────────
FACTORY_MAP = {
    'Wonka Bar - Nutty Crunch Surprise': "Lot's O' Nuts",
    'Wonka Bar - Fudge Mallows':         "Lot's O' Nuts",
    'Wonka Bar -Scrumdiddlyumptious':    "Lot's O' Nuts",
    'Wonka Bar - Milk Chocolate':        "Wicked Choccy's",
    'Wonka Bar - Triple Dazzle Caramel': "Wicked Choccy's",
    'Laffy Taffy':          'Sugar Shack',
    'SweeTARTS':            'Sugar Shack',
    'Nerds':                'Sugar Shack',
    'Fun Dip':              'Sugar Shack',
    'Fizzy Lifting Drinks': 'Sugar Shack',
    'Everlasting Gobstopper': 'Secret Factory',
    'Lickable Wallpaper':   'Secret Factory',
    'Wonka Gum':            'Secret Factory',
    'Hair Toffee':          'The Other Factory',
    'Kazookles':            'The Other Factory',
}

FACTORY_COORDS = {
    "Lot's O' Nuts":    (32.881893, -111.768036),
    "Wicked Choccy's":  (32.076176, -81.088371),
    "Sugar Shack":      (48.119140, -96.181150),
    "Secret Factory":   (41.446333, -90.565487),
    "The Other Factory":(35.117500, -89.971107),
}

COLORS = {
    'primary': '#1F4E79',
    'blue':    '#2E75B6',
    'green':   '#1E8449',
    'orange':  '#E07B39',
    'red':     '#C0392B',
    'purple':  '#6C3483',
    'teal':    '#117A65',
}

PALETTE = ['#2E75B6','#E07B39','#1E8449','#C0392B','#6C3483','#117A65','#784212']

@st.cache_data
def load_data():
    df = pd.read_csv('data.csv')
    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True)
    df['Ship Date']  = pd.to_datetime(df['Ship Date'],  dayfirst=True)
    df['Lead Time']  = (df['Ship Date'] - df['Order Date']).dt.days
    df['Factory']    = df['Product Name'].map(FACTORY_MAP)
    df['Route']      = df['Factory'] + ' → ' + df['Region']
    df['Year']       = df['Order Date'].dt.year
    df['Month']      = df['Order Date'].dt.to_period('M').astype(str)
    df['Quarter']    = df['Order Date'].dt.to_period('Q').astype(str)
    df['Delay Flag'] = df['Lead Time'] > 7
    return df

df_raw = load_data()

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍬 Nassau Candy")
    st.markdown("### Shipping Analytics")
    st.markdown("---")

    st.markdown("#### 📅 Date Range")
    min_date = df_raw['Order Date'].min().date()
    max_date = df_raw['Order Date'].max().date()
    date_range = st.date_input(
        "Order date window",
        value=(min_date, max_date),
        min_value=min_date, max_value=max_date, label_visibility="collapsed"
    )

    st.markdown("#### 🗺️ Region")
    regions = st.multiselect(
        "Select regions", options=sorted(df_raw['Region'].unique()),
        default=sorted(df_raw['Region'].unique()), label_visibility="collapsed"
    )

    st.markdown("#### 🚚 Ship Mode")
    ship_modes = st.multiselect(
        "Select ship modes", options=sorted(df_raw['Ship Mode'].unique()),
        default=sorted(df_raw['Ship Mode'].unique()), label_visibility="collapsed"
    )

    st.markdown("#### 🏭 Factory")
    factories = st.multiselect(
        "Select factories", options=sorted(df_raw['Factory'].unique()),
        default=sorted(df_raw['Factory'].unique()), label_visibility="collapsed"
    )

    st.markdown("#### 📦 Division")
    divisions = st.multiselect(
        "Select divisions", options=sorted(df_raw['Division'].unique()),
        default=sorted(df_raw['Division'].unique()), label_visibility="collapsed"
    )

    st.markdown("#### ⏱️ Lead Time Threshold (days)")
    lt_threshold = st.slider(
        "Flag shipments exceeding:", min_value=1, max_value=2000,
        value=7, label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("Data: Jan 2024 – Dec 2025 · 10,194 orders")

# ─── Apply filters ─────────────────────────────────────────────────────────────
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start, end = df_raw['Order Date'].min(), df_raw['Order Date'].max()

df = df_raw[
    (df_raw['Order Date'] >= start) &
    (df_raw['Order Date'] <= end) &
    (df_raw['Region'].isin(regions)) &
    (df_raw['Ship Mode'].isin(ship_modes)) &
    (df_raw['Factory'].isin(factories)) &
    (df_raw['Division'].isin(divisions))
].copy()

df['Delay Flag'] = df['Lead Time'] > lt_threshold

# ─── Page title ────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px;'>
    <div>
        <div style='font-size:26px;font-weight:800;color:#1F4E79;line-height:1.1;'>Nassau Candy Distributor</div>
        <div style='font-size:14px;color:#666;'>Factory-to-Customer Shipping Route Efficiency Dashboard</div>
    </div>
</div>
""", unsafe_allow_html=True)

if len(df) == 0:
    st.error("No data matches the selected filters. Please adjust your selections.")
    st.stop()

# ─── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🗺️ Route Efficiency",
    "🚚 Ship Mode",
    "📍 Geographic",
    "📈 Trends"
])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════
with tab1:
    # Data anomaly alert
    st.markdown("""
    <div class='alert-box'>
        ⚠️ <strong>Data Quality Notice:</strong> Lead times range from 904 to 1,642 days — values that are physically impossible
        for a candy distributor. Ship dates appear to reflect projected future dates rather than actual deliveries.
        All comparisons should be read as <em>relative rankings</em>, not absolute benchmarks, until source data is corrected.
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    total_orders   = len(df)
    avg_lt         = df['Lead Time'].mean()
    delay_rate     = df['Delay Flag'].mean() * 100
    total_sales    = df['Sales'].sum()
    total_profit   = df['Gross Profit'].sum()
    margin         = (total_profit / total_sales * 100) if total_sales > 0 else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'>Total Orders</div>
            <div class='kpi-value'>{total_orders:,}</div>
            <div class='kpi-delta'>After filters</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='kpi-card orange'>
            <div class='kpi-label'>Avg Lead Time</div>
            <div class='kpi-value'>{avg_lt:,.0f}d</div>
            <div class='kpi-delta'>≈ {avg_lt/365:.1f} years</div></div>""", unsafe_allow_html=True)
    with c3:
        color = 'red' if delay_rate > 50 else 'orange'
        st.markdown(f"""<div class='kpi-card {color}'>
            <div class='kpi-label'>Delay Rate</div>
            <div class='kpi-value'>{delay_rate:.1f}%</div>
            <div class='kpi-delta'>>{lt_threshold}d threshold</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='kpi-card green'>
            <div class='kpi-label'>Total Sales</div>
            <div class='kpi-value'>${total_sales:,.0f}</div>
            <div class='kpi-delta'>All regions</div></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class='kpi-card green'>
            <div class='kpi-label'>Gross Profit</div>
            <div class='kpi-value'>${total_profit:,.0f}</div>
            <div class='kpi-delta'>Net of cost</div></div>""", unsafe_allow_html=True)
    with c6:
        st.markdown(f"""<div class='kpi-card green'>
            <div class='kpi-label'>Profit Margin</div>
            <div class='kpi-value'>{margin:.1f}%</div>
            <div class='kpi-delta'>Gross margin</div></div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Lead Time Distribution</div>", unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 2])

    with col_l:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=df['Lead Time'], nbinsx=40,
            marker_color='#2E75B6', opacity=0.8, name='Orders'
        ))
        fig_hist.add_vline(x=df['Lead Time'].mean(), line_dash='dash', line_color='#E07B39',
                           annotation_text=f"Mean: {df['Lead Time'].mean():.0f}d",
                           annotation_position='top right', line_width=2)
        fig_hist.add_vline(x=df['Lead Time'].median(), line_dash='dot', line_color='#1E8449',
                           annotation_text=f"Median: {df['Lead Time'].median():.0f}d",
                           annotation_position='top left', line_width=2)
        fig_hist.update_layout(
            title='Distribution of Shipping Lead Times',
            xaxis_title='Lead Time (Days)', yaxis_title='Order Count',
            plot_bgcolor='white', paper_bgcolor='white',
            height=340, margin=dict(t=50, b=40, l=40, r=20),
            showlegend=False
        )
        fig_hist.update_xaxes(showgrid=True, gridcolor='#F0F0F0')
        fig_hist.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_r:
        fig_box = go.Figure()
        for i, yr in enumerate(sorted(df['Year'].unique())):
            sub = df[df['Year'] == yr]['Lead Time']
            fig_box.add_trace(go.Box(
                y=sub, name=str(yr),
                marker_color=PALETTE[i], boxmean=True
            ))
        fig_box.update_layout(
            title='Lead Time by Year',
            yaxis_title='Lead Time (Days)',
            plot_bgcolor='white', paper_bgcolor='white',
            height=340, margin=dict(t=50, b=40, l=40, r=20),
            showlegend=False
        )
        fig_box.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
        st.plotly_chart(fig_box, use_container_width=True)

    # Division & Factory row
    st.markdown("<div class='section-header'>Volume & Sales Breakdown</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        div_stats = df.groupby('Division').agg(
            Orders=('Row ID','count'), Sales=('Sales','sum')
        ).reset_index()
        fig_div = px.pie(div_stats, names='Division', values='Orders',
                         color_discrete_sequence=PALETTE,
                         title='Orders by Product Division', hole=0.45)
        fig_div.update_traces(textinfo='label+percent', textfont_size=12)
        fig_div.update_layout(height=320, margin=dict(t=50,b=20,l=20,r=20),
                               paper_bgcolor='white', showlegend=False)
        st.plotly_chart(fig_div, use_container_width=True)

    with c2:
        fac_stats = df.groupby('Factory').agg(
            Orders=('Row ID','count'), Sales=('Sales','sum'),
            AvgLead=('Lead Time','mean')
        ).reset_index().sort_values('Orders', ascending=True)
        fig_fac = go.Figure(go.Bar(
            x=fac_stats['Orders'], y=fac_stats['Factory'],
            orientation='h', marker_color=PALETTE[:len(fac_stats)],
            text=fac_stats['Orders'].apply(lambda x: f'{x:,}'),
            textposition='outside'
        ))
        fig_fac.update_layout(
            title='Order Volume by Factory',
            xaxis_title='Orders', plot_bgcolor='white', paper_bgcolor='white',
            height=320, margin=dict(t=50,b=40,l=10,r=60),
            xaxis=dict(showgrid=True, gridcolor='#F0F0F0')
        )
        st.plotly_chart(fig_fac, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2 — ROUTE EFFICIENCY
# ══════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-header'>Route Performance Leaderboard</div>", unsafe_allow_html=True)

    min_vol = st.slider("Minimum shipments per route", 1, 500, 10, key='min_vol')

    route_stats = df.groupby('Route').agg(
        Avg_Lead=('Lead Time', 'mean'),
        Shipments=('Row ID', 'count'),
        Delay_Rate=('Delay Flag', 'mean'),
        Total_Sales=('Sales', 'sum'),
        Avg_Profit=('Gross Profit', 'mean')
    ).reset_index()
    route_stats = route_stats[route_stats['Shipments'] >= min_vol].sort_values('Avg_Lead')
    route_stats['Efficiency Score'] = (
        100 - ((route_stats['Avg_Lead'] - route_stats['Avg_Lead'].min()) /
               (route_stats['Avg_Lead'].max() - route_stats['Avg_Lead'].min() + 1e-9)) * 100
    ).round(1)
    route_stats['Delay_Rate'] = (route_stats['Delay_Rate'] * 100).round(1)
    route_stats['Avg_Lead'] = route_stats['Avg_Lead'].round(0).astype(int)
    route_stats['Avg_Profit'] = route_stats['Avg_Profit'].round(2)

    # Color bars
    colors_route = ['#1E8449' if i < 3 else ('#C0392B' if i >= len(route_stats)-3 else '#2E75B6')
                    for i in range(len(route_stats))]

    fig_route = go.Figure(go.Bar(
        x=route_stats['Avg_Lead'], y=route_stats['Route'],
        orientation='h',
        marker_color=colors_route,
        text=route_stats['Avg_Lead'].astype(str) + 'd',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Avg Lead: %{x} days<br>Shipments: %{customdata[0]:,}<br>Efficiency Score: %{customdata[1]:.1f}<extra></extra>',
        customdata=route_stats[['Shipments','Efficiency Score']].values
    ))
    fig_route.update_layout(
        title='Routes Ranked by Average Lead Time (green = fastest, red = slowest)',
        xaxis_title='Average Lead Time (Days)',
        plot_bgcolor='white', paper_bgcolor='white',
        height=max(380, len(route_stats) * 34 + 80),
        margin=dict(t=50, b=40, l=20, r=80),
        xaxis=dict(showgrid=True, gridcolor='#F0F0F0')
    )
    st.plotly_chart(fig_route, use_container_width=True)

    # Scatter — volume vs efficiency
    st.markdown("<div class='section-header'>Volume vs. Efficiency Bubble Chart</div>", unsafe_allow_html=True)
    fig_scatter = px.scatter(
        route_stats, x='Shipments', y='Avg_Lead',
        size='Total_Sales', color='Efficiency Score',
        hover_name='Route', text='Route',
        color_continuous_scale='RdYlGn',
        title='Route Volume vs. Lead Time (bubble size = total sales)',
        labels={'Avg_Lead': 'Avg Lead Time (days)', 'Shipments': 'Number of Shipments'}
    )
    fig_scatter.update_traces(textposition='top center', textfont_size=9)
    fig_scatter.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        height=440, margin=dict(t=50, b=40, l=40, r=40),
        coloraxis_colorbar=dict(title='Efficiency')
    )
    fig_scatter.update_xaxes(showgrid=True, gridcolor='#F0F0F0')
    fig_scatter.update_yaxes(showgrid=True, gridcolor='#F0F0F0')
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Route detail table
    st.markdown("<div class='section-header'>Full Route Stats Table</div>", unsafe_allow_html=True)
    display = route_stats.rename(columns={
        'Route': 'Route', 'Avg_Lead': 'Avg Lead (days)',
        'Shipments': 'Shipments', 'Delay_Rate': 'Delay Rate (%)',
        'Total_Sales': 'Total Sales ($)', 'Avg_Profit': 'Avg Profit ($)',
        'Efficiency Score': 'Efficiency Score'
    })
    display['Total Sales ($)'] = display['Total Sales ($)'].round(0).astype(int)
    st.dataframe(display.reset_index(drop=True), use_container_width=True, height=380)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 — SHIP MODE
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Ship Mode Performance Comparison</div>", unsafe_allow_html=True)

    ship_stats = df.groupby('Ship Mode').agg(
        Avg_Lead=('Lead Time','mean'),
        Orders=('Row ID','count'),
        Delay_Rate=('Delay Flag','mean'),
        Avg_Sales=('Sales','mean'),
        Avg_Cost=('Cost','mean'),
        Avg_Profit=('Gross Profit','mean')
    ).reset_index().sort_values('Avg_Lead')
    ship_stats['Delay_Rate'] = (ship_stats['Delay_Rate']*100).round(1)

    c1, c2 = st.columns(2)
    with c1:
        fig_sm = go.Figure(go.Bar(
            x=ship_stats['Ship Mode'], y=ship_stats['Avg_Lead'],
            marker_color=['#1E8449','#2E75B6','#E07B39','#C0392B'],
            text=ship_stats['Avg_Lead'].round(0).astype(int).astype(str) + 'd',
            textposition='outside'
        ))
        fig_sm.update_layout(
            title='Avg Lead Time by Ship Mode',
            yaxis_title='Days', plot_bgcolor='white', paper_bgcolor='white',
            height=360, margin=dict(t=50,b=40,l=40,r=20),
            yaxis=dict(range=[ship_stats['Avg_Lead'].min()-20, ship_stats['Avg_Lead'].max()+40],
                       showgrid=True, gridcolor='#F0F0F0')
        )
        st.plotly_chart(fig_sm, use_container_width=True)

    with c2:
        fig_vol = go.Figure(go.Bar(
            x=ship_stats['Ship Mode'], y=ship_stats['Orders'],
            marker_color=PALETTE[:4],
            text=ship_stats['Orders'].apply(lambda x: f'{x:,}'),
            textposition='outside'
        ))
        fig_vol.update_layout(
            title='Order Volume by Ship Mode',
            yaxis_title='Orders', plot_bgcolor='white', paper_bgcolor='white',
            height=360, margin=dict(t=50,b=40,l=40,r=20),
            yaxis=dict(showgrid=True, gridcolor='#F0F0F0')
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    # Lead time distribution per ship mode
    st.markdown("<div class='section-header'>Lead Time Distribution per Ship Mode</div>", unsafe_allow_html=True)
    fig_violin = go.Figure()
    dark_palette = ['#1a5276','#1e8449','#b9770e','#7b241c']
    for i, mode in enumerate(sorted(df['Ship Mode'].unique())):
        sub = df[df['Ship Mode'] == mode]['Lead Time']
        fig_violin.add_trace(go.Violin(
            y=sub, name=mode, box_visible=True, meanline_visible=True,
            fillcolor=PALETTE[i], line_color=dark_palette[i % len(dark_palette)],
            opacity=0.85
        ))
    fig_violin.update_layout(
        title=dict(text='Lead Time Spread by Ship Mode', font=dict(color='#1F4E79', size=15)),
        yaxis_title='Lead Time (Days)',
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(color='#333333'),
        height=400, margin=dict(t=50,b=40,l=40,r=20),
        showlegend=True,
        yaxis=dict(showgrid=True, gridcolor='#E0E0E0', tickfont=dict(color='#333333')),
        xaxis=dict(tickfont=dict(color='#333333'))
    )
    st.plotly_chart(fig_violin, use_container_width=True)

    # Cost-time table
    st.markdown("<div class='section-header'>Cost vs. Speed Summary</div>", unsafe_allow_html=True)
    display_sm = ship_stats[['Ship Mode','Avg_Lead','Orders','Delay_Rate','Avg_Cost','Avg_Sales']].copy()
    display_sm.columns = ['Ship Mode','Avg Lead (days)','Orders','Delay Rate (%)','Avg Cost ($)','Avg Sales ($)']
    display_sm['Avg Lead (days)'] = display_sm['Avg Lead (days)'].round(0).astype(int)
    display_sm['Avg Cost ($)'] = display_sm['Avg Cost ($)'].round(2)
    display_sm['Avg Sales ($)'] = display_sm['Avg Sales ($)'].round(2)
    st.dataframe(display_sm.reset_index(drop=True), use_container_width=True)

    st.info("💡 **Paradox:** Standard Class (cheapest) has the shortest lead time. First Class costs more but ships slowest. Consider renegotiating premium carrier contracts.")

# ══════════════════════════════════════════════════════════════════════
# TAB 4 — GEOGRAPHIC
# ══════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-header'>Regional Shipping Performance</div>", unsafe_allow_html=True)

    region_stats = df.groupby('Region').agg(
        Avg_Lead=('Lead Time','mean'),
        Orders=('Row ID','count'),
        Delay_Rate=('Delay Flag','mean'),
        Total_Sales=('Sales','sum'),
        Total_Profit=('Gross Profit','sum')
    ).reset_index().sort_values('Avg_Lead')
    region_stats['Delay_Rate'] = (region_stats['Delay_Rate']*100).round(1)

    fig_reg = make_subplots(
        rows=1, cols=2, shared_yaxes=True,
        subplot_titles=('Avg Lead Time (days)', 'Total Sales ($)')
    )
    fig_reg.add_trace(go.Bar(
        y=region_stats['Region'], x=region_stats['Avg_Lead'],
        orientation='h', marker_color=PALETTE[:4],
        text=region_stats['Avg_Lead'].round(0).astype(int).astype(str) + 'd',
        textposition='outside', name='Lead Time'
    ), row=1, col=1)
    fig_reg.add_trace(go.Bar(
        y=region_stats['Region'], x=region_stats['Total_Sales'],
        orientation='h', marker=dict(color=PALETTE[:4], opacity=0.55),
        text=region_stats['Total_Sales'].apply(lambda x: f'${x:,.0f}'),
        textposition='outside', name='Sales'
    ), row=1, col=2)
    fig_reg.update_layout(
        height=320, plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(t=50,b=40,l=80,r=80), showlegend=False
    )
    fig_reg.update_xaxes(showgrid=True, gridcolor='#F0F0F0')
    st.plotly_chart(fig_reg, use_container_width=True)

    # Factory map
    st.markdown("<div class='section-header'>Factory Locations</div>", unsafe_allow_html=True)
    fac_map_data = []
    for fac, (lat, lon) in FACTORY_COORDS.items():
        if fac in df['Factory'].values:
            cnt = df[df['Factory']==fac].shape[0]
            avg_l = df[df['Factory']==fac]['Lead Time'].mean()
            fac_map_data.append({'Factory': fac, 'lat': lat, 'lon': lon,
                                  'Orders': cnt, 'Avg Lead': round(avg_l,0)})
    fac_df = pd.DataFrame(fac_map_data)

    if not fac_df.empty:
        fig_map = px.scatter_mapbox(
            fac_df, lat='lat', lon='lon', size='Orders',
            color='Avg Lead', hover_name='Factory',
            hover_data={'Orders': True, 'Avg Lead': True, 'lat': False, 'lon': False},
            color_continuous_scale='RdYlGn_r',
            size_max=40,
            zoom=3, center={'lat': 39.5, 'lon': -98.5},
            mapbox_style='carto-positron',
            title='Factory Locations (bubble size = order volume, color = avg lead time)'
        )
        fig_map.update_layout(
            height=480, margin=dict(t=50,b=0,l=0,r=0),
            paper_bgcolor='white',
            coloraxis_colorbar=dict(title='Avg Lead (days)')
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # State-level table
    st.markdown("<div class='section-header'>Top States by Order Volume</div>", unsafe_allow_html=True)
    state_stats = df.groupby('State/Province').agg(
        Orders=('Row ID','count'),
        Avg_Lead=('Lead Time','mean'),
        Total_Sales=('Sales','sum'),
        Delay_Rate=('Delay Flag','mean')
    ).reset_index().sort_values('Orders', ascending=False).head(20)
    state_stats['Avg_Lead'] = state_stats['Avg_Lead'].round(0).astype(int)
    state_stats['Delay_Rate'] = (state_stats['Delay_Rate']*100).round(1)
    state_stats['Total_Sales'] = state_stats['Total_Sales'].round(0).astype(int)
    state_stats.columns = ['State/Province','Orders','Avg Lead (days)','Total Sales ($)','Delay Rate (%)']
    st.dataframe(state_stats.reset_index(drop=True), use_container_width=True, height=420)

# ══════════════════════════════════════════════════════════════════════
# TAB 5 — TRENDS
# ══════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-header'>Monthly Lead Time Trend</div>", unsafe_allow_html=True)

    monthly = df.groupby('Month').agg(
        Avg_Lead=('Lead Time','mean'),
        Orders=('Row ID','count'),
        Total_Sales=('Sales','sum')
    ).reset_index().sort_values('Month')

    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(go.Scatter(
        x=monthly['Month'], y=monthly['Avg_Lead'].round(0),
        name='Avg Lead Time', mode='lines+markers',
        line=dict(color='#2E75B6', width=2.5),
        marker=dict(size=5),
        fill='tozeroy', fillcolor='rgba(46,117,182,0.08)'
    ), secondary_y=False)
    fig_trend.add_trace(go.Bar(
        x=monthly['Month'], y=monthly['Orders'],
        name='Order Volume', opacity=0.3,
        marker_color='#E07B39'
    ), secondary_y=True)

    # Highlight 2025 jump
    fig_trend.add_vrect(
        x0='2025-01', x1=monthly['Month'].max(),
        fillcolor='rgba(192,57,43,0.05)', line_width=0,
        annotation_text='2025 performance drop',
        annotation_position='top left',
        annotation_font_color='#C0392B'
    )
    fig_trend.update_xaxes(tickangle=45)
    fig_trend.update_yaxes(title_text='Avg Lead Time (days)', secondary_y=False,
                            showgrid=True, gridcolor='#F0F0F0')
    fig_trend.update_yaxes(title_text='Order Volume', secondary_y=True, showgrid=False)
    fig_trend.update_layout(
        title='Monthly Shipping Lead Time & Order Volume',
        plot_bgcolor='white', paper_bgcolor='white',
        height=420, margin=dict(t=50,b=60,l=60,r=60),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Quarterly breakdown
    st.markdown("<div class='section-header'>Quarterly Performance by Region</div>", unsafe_allow_html=True)
    qtr = df.groupby(['Quarter','Region'])['Lead Time'].mean().reset_index()
    qtr['Lead Time'] = qtr['Lead Time'].round(0)
    fig_qtr = px.line(
        qtr, x='Quarter', y='Lead Time', color='Region',
        markers=True, color_discrete_sequence=PALETTE,
        title='Quarterly Avg Lead Time by Region',
        labels={'Lead Time': 'Avg Lead Time (days)'}
    )
    fig_qtr.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        height=380, margin=dict(t=50,b=60,l=60,r=20),
        xaxis=dict(tickangle=45),
        yaxis=dict(showgrid=True, gridcolor='#F0F0F0')
    )
    st.plotly_chart(fig_qtr, use_container_width=True)

    # YoY comparison
    st.markdown("<div class='section-header'>Year-over-Year Lead Time Comparison</div>", unsafe_allow_html=True)
    yoy = df.groupby(['Year','Ship Mode'])['Lead Time'].mean().reset_index()
    yoy['Lead Time'] = yoy['Lead Time'].round(0)
    fig_yoy = px.bar(
        yoy, x='Ship Mode', y='Lead Time', color='Year',
        barmode='group', color_discrete_sequence=['#2E75B6','#E07B39'],
        title='Avg Lead Time by Ship Mode: 2024 vs 2025',
        labels={'Lead Time': 'Avg Lead Time (days)'}
    )
    fig_yoy.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        height=360, margin=dict(t=50,b=40,l=60,r=20),
        yaxis=dict(showgrid=True, gridcolor='#F0F0F0')
    )
    st.plotly_chart(fig_yoy, use_container_width=True)

    # Product-level drill
    st.markdown("<div class='section-header'>Product-Level Lead Time Heatmap</div>", unsafe_allow_html=True)
    prod_region = df.groupby(['Product Name','Region'])['Lead Time'].mean().reset_index()
    prod_region['Lead Time'] = prod_region['Lead Time'].round(0)
    prod_pivot = prod_region.pivot(index='Product Name', columns='Region', values='Lead Time')
    fig_heat = go.Figure(go.Heatmap(
        z=prod_pivot.values,
        x=prod_pivot.columns.tolist(),
        y=prod_pivot.index.tolist(),
        colorscale='RdYlGn_r',
        text=[[str(int(v)) if not np.isnan(v) else '' for v in row] for row in prod_pivot.values],
        texttemplate='%{text}',
        colorbar=dict(title='Days')
    ))
    fig_heat.update_layout(
        title='Avg Lead Time by Product × Region (days)',
        plot_bgcolor='white', paper_bgcolor='white',
        height=480, margin=dict(t=50,b=60,l=20,r=20),
        xaxis_title='Region', yaxis_title='Product'
    )
    st.plotly_chart(fig_heat, use_container_width=True)
