"""
Streamlit dashboard for Job Application Tracker.
Displays KPIs, visualizations, and recent events.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.models import (
    get_all_applications,
    get_recent_events,
    get_status_counts,
    get_event_type_counts,
    get_applications_by_date_range
)
from app.config import DB_PATH

# Page config
st.set_page_config(
    page_title="Job Application Tracker",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def load_data():
    """Load data from database."""
    applications = get_all_applications()
    events = get_recent_events(limit=200)
    status_counts = get_status_counts()
    event_counts = get_event_type_counts()
    
    return applications, events, status_counts, event_counts


def calculate_kpis(applications, events):
    """Calculate key performance indicators."""
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    
    # Total applications (last 30 days)
    recent_apps = [
        app for app in applications
        if datetime.fromisoformat(app['first_seen_date']) > thirty_days_ago
    ]
    total_recent = len(recent_apps)
    
    # Active pipeline (not rejected/offer)
    active_statuses = ['applied', 'in_review', 'assessment', 'interview']
    active_count = sum(1 for app in applications if app['status'] in active_statuses)
    
    # Interviews scheduled
    interview_count = sum(1 for app in applications if app['status'] == 'interview')
    
    # Rejections
    rejection_count = sum(1 for app in applications if app['status'] == 'rejected')
    
    # Response rate (events excluding confirmations / total applications)
    non_confirmation_events = [e for e in events if e['event_type'] != 'confirmation']
    response_rate = len(non_confirmation_events) / max(len(applications), 1) * 100
    
    return {
        'total_recent': total_recent,
        'active_count': active_count,
        'interview_count': interview_count,
        'rejection_count': rejection_count,
        'response_rate': response_rate
    }


def render_kpis(kpis):
    """Render KPI metrics."""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Applications (30d)",
            value=kpis['total_recent'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Active Pipeline",
            value=kpis['active_count'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="Interviews",
            value=kpis['interview_count'],
            delta=None
        )
    
    with col4:
        st.metric(
            label="Rejections",
            value=kpis['rejection_count'],
            delta=None
        )
    
    with col5:
        st.metric(
            label="Response Rate",
            value=f"{kpis['response_rate']:.1f}%",
            delta=None
        )


def plot_applications_over_time(applications):
    """Plot applications over time."""
    if not applications:
        st.info("No applications to display")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(applications)
    df['first_seen_date'] = pd.to_datetime(df['first_seen_date'], errors='coerce')
    df = df.dropna(subset=['first_seen_date'])  # Remove rows with invalid dates
    if df.empty:
        st.info("No valid application dates to display")
        return
    df['date'] = df['first_seen_date'].dt.date
    
    # Count by date
    date_counts = df.groupby('date').size().reset_index(name='count')
    
    # Create line chart
    fig = px.line(
        date_counts,
        x='date',
        y='count',
        title='Applications Over Time',
        labels={'date': 'Date', 'count': 'Number of Applications'}
    )
    
    fig.update_traces(mode='lines+markers')
    fig.update_layout(hovermode='x unified')
    
    st.plotly_chart(fig, use_container_width=True)


def plot_status_distribution(status_counts):
    """Plot status distribution."""
    if not status_counts:
        st.info("No status data to display")
        return
    
    # Create DataFrame
    df = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
    
    # Sort by count
    df = df.sort_values('Count', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        df,
        x='Status',
        y='Count',
        title='Application Status Distribution',
        labels={'Status': 'Status', 'Count': 'Number of Applications'},
        color='Count',
        color_continuous_scale='Blues'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_funnel(applications, events):
    """Plot application funnel."""
    # Calculate funnel stages
    total_apps = len(applications)
    
    # Count by status
    status_order = ['applied', 'in_review', 'assessment', 'interview', 'offer']
    status_counts = {}
    
    for status in status_order:
        count = sum(1 for app in applications if app['status'] == status)
        status_counts[status] = count
    
    # Create funnel
    fig = go.Figure(go.Funnel(
        y=list(status_counts.keys()),
        x=list(status_counts.values()),
        textinfo="value+percent initial"
    ))
    
    fig.update_layout(title='Application Funnel')
    
    st.plotly_chart(fig, use_container_width=True)


def render_recent_events(events):
    """Render recent events table."""
    if not events:
        st.info("No events to display")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(events)
    
    # Select and rename columns
    display_df = df[[
        'event_time', 'company', 'role_title', 'event_type',
        'subject', 'confidence', 'action_suggestion'
    ]].copy()
    
    display_df['event_time'] = pd.to_datetime(display_df['event_time'], errors='coerce')
    display_df = display_df.dropna(subset=['event_time'])  # Remove rows with invalid times
    display_df = display_df.sort_values('event_time', ascending=False)
    
    # Format datetime using apply instead of .dt accessor
    display_df['event_time'] = display_df['event_time'].apply(
        lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else ''
    )
    
    # Format confidence
    display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
    
    # Rename columns
    display_df.columns = [
        'Time', 'Company', 'Role', 'Event Type',
        'Subject', 'Confidence', 'Action'
    ]
    
    st.dataframe(display_df, use_container_width=True, height=400)


def render_applications_table(applications):
    """Render applications table."""
    if not applications:
        st.info("No applications to display")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(applications)
    
    # Select columns
    display_df = df[[
        'application_id', 'company', 'role_title', 'status',
        'platform', 'first_seen_date', 'last_updated'
    ]].copy()
    
    # Format dates - handle both datetime objects and strings
    display_df['first_seen_date'] = pd.to_datetime(display_df['first_seen_date'], errors='coerce')
    display_df['last_updated'] = pd.to_datetime(display_df['last_updated'], errors='coerce')
    
    # Now safe to use .dt accessor
    display_df['first_seen_date'] = display_df['first_seen_date'].apply(
        lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
    )
    display_df['last_updated'] = display_df['last_updated'].apply(
        lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else ''
    )
    
    # Rename columns
    display_df.columns = [
        'ID', 'Company', 'Role', 'Status',
        'Platform', 'First Seen', 'Last Updated'
    ]
    
    st.dataframe(display_df, use_container_width=True, height=400)


def main():
    """Main dashboard function."""
    # Header
    st.title("💼 Job Application Tracker")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh (60s)")
        
        st.markdown("---")
        
        # Filters
        st.subheader("Filters")
        
        # Date range
        days_filter = st.selectbox(
            "Time Range",
            options=[7, 14, 30, 60, 90, 180, 365],
            index=2,
            format_func=lambda x: f"Last {x} days"
        )
        
        st.markdown("---")
        
        # Database info
        st.subheader("Database")
        st.text(f"Path: {DB_PATH}")
    
    # Load data
    try:
        applications, events, status_counts, event_counts = load_data()
        
        # Calculate KPIs
        kpis = calculate_kpis(applications, events)
        
        # Render KPIs
        st.subheader("📊 Key Metrics")
        render_kpis(kpis)
        
        st.markdown("---")
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            plot_applications_over_time(applications)
        
        with col2:
            plot_status_distribution(status_counts)
        
        # Funnel
        plot_funnel(applications, events)
        
        st.markdown("---")
        
        # Tabs for detailed views
        tab1, tab2 = st.tabs(["Recent Events", "All Applications"])
        
        with tab1:
            st.subheader("📧 Recent Events")
            render_recent_events(events)
        
        with tab2:
            st.subheader("📋 All Applications")
            render_applications_table(applications)
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the database has been initialized. Run: `python -m app.db.init_db`")
    
    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    main()
