"""
Streamlit Dashboard for AI Coding Tools Research
Visualizes consolidated profile data from Twitter research
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="AI Coding Tools Research Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .profile-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .evidence-item {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #6c757d;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file_path="consolidated_profiles.json"):
    """Load consolidated profiles data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"❌ File not found: {file_path}")
        st.stop()
    except json.JSONDecodeError as e:
        st.error(f"❌ Error parsing JSON: {e}")
        st.stop()

def extract_dataframe(data):
    """Convert profiles to DataFrame for analysis"""
    profiles = data.get("profiles", [])
    
    rows = []
    for profile in profiles:
        row = {
            "username": profile.get("username", ""),
            "full_name": profile.get("full_name", ""),
            "roles": ", ".join(profile.get("roles", [])),
            "company": profile.get("company", ""),
            "company_size": profile.get("company_size", ""),
            "evidence_count": profile.get("evidence_count", 0),
            "first_date": profile.get("first_evidence_date", ""),
            "latest_date": profile.get("latest_evidence_date", ""),
        }
        rows.append(row)
    
    return pd.DataFrame(rows)

def main():
    # Header
    st.markdown('<div class="main-header">🤖 AI Coding Tools Research Dashboard</div>', unsafe_allow_html=True)
    
    # Load data
    data = load_data()
    metadata = data.get("metadata", {})
    profiles = data.get("profiles", [])
    df = extract_dataframe(data)
    
    # Sidebar - Filters
    st.sidebar.title("🔍 Filters")
    
    # Search by username or name
    search_query = st.sidebar.text_input("Search by username or name:", "")
    
    # Filter by evidence count
    min_evidence = st.sidebar.slider(
        "Minimum evidence count:",
        min_value=0,
        max_value=int(df["evidence_count"].max()) if not df.empty else 10,
        value=0
    )
    
    # Filter by company size
    company_sizes = ["All"] + sorted(df["company_size"].unique().tolist())
    selected_size = st.sidebar.selectbox("Company size:", company_sizes)
    
    # Apply filters
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df["username"].str.contains(search_query, case=False, na=False) |
            filtered_df["full_name"].str.contains(search_query, case=False, na=False)
        ]
    
    filtered_df = filtered_df[filtered_df["evidence_count"] >= min_evidence]
    
    if selected_size != "All":
        filtered_df = filtered_df[filtered_df["company_size"] == selected_size]
    
    filtered_profiles = [p for p in profiles if p.get("username") in filtered_df["username"].values]
    
    # Overview Metrics
    st.header("📊 Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Profiles", metadata.get("total_unique_profiles", 0))
    
    with col2:
        st.metric("Total Evidence", metadata.get("total_evidence_items", 0))
    
    with col3:
        st.metric("Source Files", metadata.get("source_files", 0))
    
    with col4:
        st.metric("Profiles Merged", metadata.get("profiles_merged", 0))
    
    with col5:
        st.metric("Duplicates Removed", metadata.get("duplicate_evidence_removed", 0))
    
    st.divider()
    
    # Analytics Section
    st.header("📈 Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Distribution", "👥 Top Profiles", "🏢 Companies", "📅 Timeline"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Evidence distribution
            fig_evidence = px.histogram(
                df,
                x="evidence_count",
                title="Evidence Count Distribution",
                labels={"evidence_count": "Number of Evidence Items", "count": "Number of Profiles"},
                color_discrete_sequence=["#1f77b4"]
            )
            st.plotly_chart(fig_evidence, use_container_width=True)
        
        with col2:
            # Company size distribution
            company_dist = df["company_size"].value_counts()
            fig_company = px.pie(
                values=company_dist.values,
                names=company_dist.index,
                title="Company Size Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_company, use_container_width=True)
    
    with tab2:
        # Top profiles by evidence
        st.subheader("🏆 Most Active Profiles (by evidence count)")
        top_profiles = df.nlargest(10, "evidence_count")[["username", "full_name", "company", "evidence_count"]]
        
        fig_top = px.bar(
            top_profiles,
            x="evidence_count",
            y="username",
            orientation="h",
            title="Top 10 Profiles by Evidence Count",
            labels={"evidence_count": "Evidence Items", "username": "Username"},
            color="evidence_count",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_top, use_container_width=True)
        
        st.dataframe(top_profiles, use_container_width=True)
    
    with tab3:
        # Company analysis
        st.subheader("🏢 Company Analysis")
        
        # Top companies by profile count
        company_counts = df["company"].value_counts().head(15)
        fig_companies = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation="h",
            title="Top 15 Companies by Profile Count",
            labels={"x": "Number of Profiles", "y": "Company"},
            color=company_counts.values,
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_companies, use_container_width=True)
    
    with tab4:
        # Timeline analysis
        st.subheader("📅 Evidence Timeline")
        
        # Collect all dates
        all_dates = []
        for profile in profiles:
            for evidence in profile.get("evidence", []):
                date_str = evidence.get("date", "")
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        all_dates.append(date_obj)
                    except Exception:
                        pass
        
        if all_dates:
            date_df = pd.DataFrame({"date": all_dates})
            date_df["year_month"] = date_df["date"].dt.to_period("M").astype(str)
            date_counts = date_df["year_month"].value_counts().sort_index()
            
            fig_timeline = px.line(
                x=date_counts.index,
                y=date_counts.values,
                title="Evidence Items Over Time",
                labels={"x": "Month", "y": "Number of Evidence Items"},
                markers=True
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("No valid dates found in evidence.")
    
    st.divider()
    
    # Profiles Section
    st.header(f"👥 Profiles ({len(filtered_profiles)} showing)")
    
    # Sorting options
    col1, col2 = st.columns([3, 1])
    with col2:
        sort_option = st.selectbox(
            "Sort by:",
            ["Evidence Count (High to Low)", "Evidence Count (Low to High)", "Username (A-Z)", "Latest Activity"]
        )
    
    # Sort profiles
    if sort_option == "Evidence Count (High to Low)":
        filtered_profiles.sort(key=lambda x: x.get("evidence_count", 0), reverse=True)
    elif sort_option == "Evidence Count (Low to High)":
        filtered_profiles.sort(key=lambda x: x.get("evidence_count", 0))
    elif sort_option == "Username (A-Z)":
        filtered_profiles.sort(key=lambda x: x.get("username", "").lower())
    elif sort_option == "Latest Activity":
        filtered_profiles.sort(key=lambda x: x.get("latest_evidence_date", ""), reverse=True)
    
    # Display profiles
    for profile in filtered_profiles:
        with st.container():
            st.markdown(f"""
            <div class="profile-card">
                <h3>@{profile.get('username', 'Unknown')}</h3>
                <p><strong>Name:</strong> {profile.get('full_name', 'N/A')}</p>
                <p><strong>Roles:</strong> {', '.join(profile.get('roles', ['N/A']))}</p>
                <p><strong>Company:</strong> {profile.get('company', 'N/A')} ({profile.get('company_size', 'N/A')})</p>
                <p><strong>Profile URL:</strong> <a href="{profile.get('profile_url', '#')}" target="_blank">{profile.get('profile_url', 'N/A')}</a></p>
                <p><strong>Evidence Items:</strong> {profile.get('evidence_count', 0)}</p>
                <p><strong>Activity Period:</strong> {profile.get('first_evidence_date', 'N/A')} to {profile.get('latest_evidence_date', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show evidence in expander
            with st.expander(f"📝 View {profile.get('evidence_count', 0)} Evidence Item(s)"):
                evidence_list = profile.get("evidence", [])
                for i, evidence in enumerate(evidence_list, 1):
                    st.markdown(f"""
                    <div class="evidence-item">
                        <p><strong>Evidence #{i}</strong> - {evidence.get('date', 'N/A')}</p>
                        <p><em>"{evidence.get('quote', 'N/A')}"</em></p>
                        <p><a href="{evidence.get('tweet_url', '#')}" target="_blank">🔗 View Tweet</a></p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    # Footer
    st.divider()
    st.markdown(f"""
    <div style="text-align: center; color: #6c757d; padding: 2rem;">
        <p>Generated at: {metadata.get('generated_at', 'N/A')}</p>
        <p>Data from {metadata.get('source_files', 0)} source files | 
        {metadata.get('total_unique_profiles', 0)} unique profiles analyzed</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
