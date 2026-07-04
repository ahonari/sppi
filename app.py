"""
Protest Events in Iran - Interactive Dashboard
Visualizes protest events across time and space
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import json
from datetime import datetime

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Protest Events in Iran",
    page_icon="🇮🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    """Load the coded protest data from dashboard folder"""
    # Try Excel first (primary format)
    try:
        df = pd.read_excel("data/dashboard/protests_for_dashboard.xlsx")
        st.success(f"✅ Loaded {len(df)} protest events from dashboard data")
        return df
    except FileNotFoundError:
        # Try CSV as fallback
        try:
            df = pd.read_csv("data/dashboard/protests_for_dashboard.csv")
            st.success(f"✅ Loaded {len(df)} protest events from dashboard data")
            return df
        except FileNotFoundError:
            # Try old location as fallback
            try:
                df = pd.read_csv("data/processed/protests_with_coords.csv")
                st.success(f"✅ Loaded {len(df)} protest events from processed data")
                return df
            except FileNotFoundError:
                try:
                    df = pd.read_excel("data/processed/protests_with_coords.xlsx")
                    st.success(f"✅ Loaded {len(df)} protest events from processed data")
                    return df
                except FileNotFoundError:
                    # Final fallback to sample data
                    st.warning("Data file not found. Using sample data for demonstration.")
                    df = create_sample_data()
                    return df

@st.cache_data
def load_iran_geojson():
    """Load Iran GeoJSON for map background"""
    try:
        with open("data/geojson/iran_provinces.geojson", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def create_sample_data():
    """Create sample data for demonstration purposes"""
    sample_data = {
        'id': [1, 2, 3, 4, 5],
        'event_date': pd.to_datetime(['2013-07-16', '2013-07-21', '2013-07-25', '2013-08-02', '2013-08-12']),
        'lat': [35.6892, 35.6892, 35.6892, 35.6892, 35.6892],
        'lng': [51.3890, 51.3890, 51.3890, 51.3890, 51.3890],
        'event_location_name': ['تهران', 'تهران', 'تهران', 'تهران', 'تهران'],
        'arena_name': ['مقابل مجلس', 'وزارت ارشاد', 'سفارت اندونزی', 'میدان فلسطین', 'مقابل مجلس'],
        'protests_categories': [
            'Demonstrative protests (legal and nonviolent)',
            'Demonstrative protests (legal and nonviolent)',
            'Demonstrative protests (legal and nonviolent)',
            'Demonstrative protests (legal and nonviolent)',
            'Demonstrative protests (legal and nonviolent)'
        ],
        'protest_form_en': ['public assembly', 'public assembly', 'public assembly', 'march/ rally', 'public assembly'],
        'protest_form_fa': ['تجمع / اجتماع', 'تجمع / اجتماع', 'تجمع / اجتماع', 'راهپیمایی', 'تجمع / اجتماع'],
        'issue': ['Labour', 'Cultural', 'Human rights', 'Political', 'Labour'],
        'issue_specific': ['N/A', 'N/A', 'N/A', 'N/A', 'N/A'],
        'target': ['Government', 'Government', 'Government', 'Government', 'Government'],
        'organizer_type': ['Labour Union', 'Unknown', 'Ordinary Citizens', 'Unknown', 'Labour Union'],
        'civil_society_sector': ['Labour', 'Cultural', 'Human rights', 'Political', 'Labour'],
        'main_political_sector': ['Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown'],
        'size_of_participants': ['medium group <50', 'medium group <50', 'small group < 15', 'thousands, +1000', 'medium group <50'],
        'arena_type': ['Parliament area', 'In front of state buildings', 'In front of state buildings', 'Public place', 'Parliament area'],
        'violent': ['NO', 'NO', 'NO', 'NO', 'NO'],
        'protest_ritual': ['Protest', 'Protest', 'Protest', 'Protest', 'Protest'],
        'duplicate': ['No', 'No', 'No', 'No', 'No']
    }
    return pd.DataFrame(sample_data)

# ============================================================
# SIDEBAR FILTERS
# ============================================================
def create_filters(df):
    """Create sidebar filters"""
    st.sidebar.header("🔍 Filters")
    
    # Date range filter - use actual data dates as default
    min_date = df['event_date'].min()
    max_date = df['event_date'].max()
    
    # Remove any NaN/NaT values before getting min/max
    valid_dates = df['event_date'].dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min()
        max_date = valid_dates.max()
    else:
        # Fallback if no valid dates
        min_date = pd.Timestamp('2013-01-01')
        max_date = pd.Timestamp('2020-01-01')
    
    date_range = st.sidebar.date_input(
        "📅 Date Range",
        value=[min_date, max_date],  # Default to data range
        min_value=min_date,
        max_value=max_date
    )
    
    # Category filter
    categories = sorted(df['protests_categories'].dropna().unique())
    selected_categories = st.sidebar.multiselect(
        "📂 Protest Category",
        categories,
        default=categories
    )
    
    # Issue filter
    issues = sorted(df['issue'].dropna().unique())
    selected_issues = st.sidebar.multiselect(
        "📌 Issue",
        issues,
        default=issues
    )
    
    # Target filter
    targets = sorted(df['target'].dropna().unique())
    selected_targets = st.sidebar.multiselect(
        "🎯 Target",
        targets,
        default=targets
    )
    
    # Violent filter
    violent_options = ['All', 'YES', 'NO']
    selected_violent = st.sidebar.selectbox(
        "💥 Violence",
        violent_options,
        index=0
    )
    
    return {
        'date_range': date_range,
        'categories': selected_categories,
        'issues': selected_issues,
        'targets': selected_targets,
        'violent': selected_violent
    }

def apply_filters(df, filters):
    """Apply filters to the dataframe"""
    mask = pd.Series([True] * len(df), index=df.index)
    
    # Date filter - only if we have valid dates
    if len(filters['date_range']) == 2 and not df['event_date'].isna().all():
        start_date, end_date = filters['date_range']
        mask &= (df['event_date'] >= pd.to_datetime(start_date)) & (df['event_date'] <= pd.to_datetime(end_date))
    
    # Category filter
    if filters['categories']:
        mask &= df['protests_categories'].isin(filters['categories'])
    
    # Issue filter
    if filters['issues']:
        mask &= df['issue'].isin(filters['issues'])
    
    # Target filter
    if filters['targets']:
        mask &= df['target'].isin(filters['targets'])
    
    # Violent filter
    if filters['violent'] != 'All':
        mask &= df['violent'] == filters['violent']
    
    return df[mask]

# ============================================================
# GEOGRAPHIC VIEW (MAP)
# ============================================================
def render_map(df):
    """Render the interactive map"""
    st.subheader("🗺️ Geographic Distribution of Protests")
    
    if df.empty:
        st.warning("No data to display with current filters")
        return
    
    # Calculate center of map
    center_lat = df['lat'].mean()
    center_lng = df['lng'].mean()
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=6,
        tiles='CartoDB positron',  # Clean academic look
        control_scale=True
    )
    
    # Add marker cluster
    marker_cluster = MarkerCluster().add_to(m)
    
    # Color mapping for categories
    color_map = {
        'Petitioning': '#2E86C1',  # Blue
        'Demonstrative protests (legal and nonviolent)': '#28B463',  # Green
        'Confrontational protests (illegal and non violent)': '#F39C12',  # Orange
        'Violent protests': '#E74C3C',  # Red
        'Armed conflict': '#943126',  # Dark Red
        'Unknown': '#95A5A6'  # Gray
    }
    
    # Add markers
    for _, row in df.iterrows():
        # Create popup HTML with all fields
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, sans-serif; max-width: 320px; padding: 5px;">
            <h4 style="margin: 0 0 5px 0; color: #1a3a5c; border-bottom: 2px solid #eee; padding-bottom: 5px;">
                📍 {row.get('event_location_name', 'Unknown')}
            </h4>
            <p style="margin: 3px 0; color: #555; font-size: 13px;">
                <b>Location:</b> {row.get('arena_name', 'Unknown')}
            </p>
            <hr style="margin: 5px 0; border: none; border-top: 1px solid #eee;">
            
            <table style="font-size: 12px; width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 2px 0;"><b>📅 Date:</b></td>
                    <td style="padding: 2px 0;">{row.get('event_date', '').strftime('%Y-%m-%d') if pd.notna(row.get('event_date')) else 'Unknown'}</td></tr>
                <tr><td style="padding: 2px 0;"><b>📂 Category:</b></td>
                    <td style="padding: 2px 0;">{row.get('protests_categories', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>📋 Form:</b></td>
                    <td style="padding: 2px 0;">{row.get('protest_form_en', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>🇮🇷 Form (FA):</b></td>
                    <td style="padding: 2px 0;">{row.get('protest_form_fa', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>📌 Issue:</b></td>
                    <td style="padding: 2px 0;">{row.get('issue', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>🔍 Sub-issue:</b></td>
                    <td style="padding: 2px 0;">{row.get('issue_specific', 'N/A')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>🎯 Target:</b></td>
                    <td style="padding: 2px 0;">{row.get('target', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>👤 Organizer:</b></td>
                    <td style="padding: 2px 0;">{row.get('organizer_type', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>🏛️ Sector:</b></td>
                    <td style="padding: 2px 0;">{row.get('civil_society_sector', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>🗳️ Political:</b></td>
                    <td style="padding: 2px 0;">{row.get('main_political_sector', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>👥 Participants:</b></td>
                    <td style="padding: 2px 0;">{row.get('size_of_participants', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>🏟️ Arena:</b></td>
                    <td style="padding: 2px 0;">{row.get('arena_type', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>💥 Violent:</b></td>
                    <td style="padding: 2px 0;">{row.get('violent', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>🔄 Ritual:</b></td>
                    <td style="padding: 2px 0;">{row.get('protest_ritual', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>📎 Duplicate:</b></td>
                    <td style="padding: 2px 0;">{row.get('duplicate', 'No')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>📅 Multi-day:</b></td>
                    <td style="padding: 2px 0;">{row.get('is_multi_day', 'No')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>📍 Location:</b></td>
                    <td style="padding: 2px 0;">{row.get('location_category', 'Unknown')}</td></tr>
                <tr><td style="padding: 2px 0;"><b>🌍 Scope:</b></td>
                    <td style="padding: 2px 0;">{row.get('local_national_international', 'Unknown')}</td></tr>
            </table>
        </div>
        """
        
        # Get color for category
        color = color_map.get(row.get('protests_categories', 'Unknown'), '#95A5A6')
        
        # Create marker
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=folium.Popup(popup_html, max_width=350),
            icon=folium.Icon(color=color, icon='info-sign', prefix='fa')
        ).add_to(marker_cluster)
    
    # Display the map
    folium_static(m, width=700, height=550)

# ============================================================
# TEMPORAL VIEW (CHARTS)
# ============================================================
def render_temporal(df):
    """Render the temporal analysis charts"""
    st.subheader("📊 Temporal Dynamics")
    
    if df.empty:
        st.warning("No data to display with current filters")
        return
    
    # Variable selector
    variable = st.selectbox(
        "Select variable to visualize over time",
        ['protests_categories', 'issue', 'target', 'organizer_type', 'main_political_sector'],
        index=0
    )
    
    # Prepare time series data - only use rows with valid dates
    df_copy = df[df['event_date'].notna()].copy()
    
    if df_copy.empty:
        st.warning("No data with valid dates for time series visualization")
        return
    
    df_copy['month'] = df_copy['event_date'].dt.to_period('M').astype(str)
    
    # Group by month and variable
    time_data = df_copy.groupby(['month', variable]).size().reset_index(name='count')
    
    if time_data.empty:
        st.warning("No data for selected variable")
        return
    
    # ---- STACKED BAR CHART ----
    fig_bar = px.bar(
        time_data,
        x='month',
        y='count',
        color=variable,
        title=f"Protests by {variable.replace('_', ' ').title()} Over Time",
        labels={'month': 'Month', 'count': 'Number of Protests'},
        color_discrete_sequence=px.colors.qualitative.Set2,
        barmode='stack'
    )
    
    fig_bar.update_layout(
        xaxis_tickangle=-45,
        height=400,
        margin=dict(l=40, r=40, t=60, b=120),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # ---- LINE CHART (Trend) ----
    fig_line = px.line(
        time_data,
        x='month',
        y='count',
        color=variable,
        title="Monthly Trend",
        labels={'month': 'Month', 'count': 'Number of Protests'},
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig_line.update_layout(
        height=300,
        margin=dict(l=40, r=40, t=50, b=80),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_line, use_container_width=True)
    
    # ---- SUMMARY STATISTICS ----
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Protests",
            len(df),
            delta=None
        )
    
    with col2:
        most_common = df[variable].mode()
        if not most_common.empty:
            st.metric(
                f"Most Common {variable.replace('_', ' ').title()}",
                most_common.iloc[0],
                f"{df[variable].value_counts().iloc[0]} events"
            )
        else:
            st.metric(f"Most Common {variable}", "N/A")
    
    with col3:
        # Most active month
        if not df_copy.empty and 'month' in df_copy.columns:
            most_active = df_copy.groupby('month').size()
            if not most_active.empty:
                top_month = most_active.idxmax()
                st.metric(
                    "Most Active Month",
                    top_month,
                    f"{most_active.max()} events"
                )
            else:
                st.metric("Most Active Month", "N/A")
        else:
            st.metric("Most Active Month", "N/A")

# ============================================================
# MAIN APP
# ============================================================
def main():
    """Main application entry point"""
    
    # Title
    st.title("🇮🇷 Protest Events in Iran")
    st.markdown("*Interactive dashboard visualizing protest dynamics across time and space*")
    st.divider()
    
    # Load data
    df = load_data()
    
    # Convert date column - handle "Unknown" values
    if 'event_date' in df.columns:
        # Replace "Unknown" with NaN first
        df['event_date'] = df['event_date'].replace('Unknown', pd.NA)
        # Convert to datetime, coercing errors to NaT (Not a Time)
        df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
        
        # Check if we lost too many rows
        missing_dates = df['event_date'].isna().sum()
        if missing_dates > 0:
            st.warning(f"⚠️ {missing_dates} rows have invalid dates and will be excluded from time-series views")
    else:
        st.error("Data missing 'event_date' column")
        return
    
    # Remove duplicates (just in case)
    if 'duplicate' in df.columns:
        df = df[df['duplicate'] != 'Yes']
    
    # Create and apply filters
    filters = create_filters(df)
    df_filtered = apply_filters(df, filters)
    
    # Display number of records
    st.caption(f"Showing {len(df_filtered)} protests out of {len(df)} total")
    
    # ---- TWO COLUMN LAYOUT ----
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with col1:
        render_temporal(df_filtered)
    
    with col2:
        render_map(df_filtered)
    
    # ---- FOOTER ----
    st.divider()
    st.caption(
        "📊 Data source: Protest Event Database | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        "Built with Streamlit"
    )

if __name__ == "__main__":
    main()