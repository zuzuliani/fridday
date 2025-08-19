#!/usr/bin/env python3
"""
Beautiful Web Interface for React Tavily Research Tool
Real-time research visualization with modern UI
"""

import asyncio
import json
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our research tool
try:
    from utils.reactTavily import create_researcher, ResearchRequest
except ImportError:
    st.error("❌ Could not import React Tavily. Make sure you're running from the project root.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="React Tavily Research",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .research-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .status-running {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-completed {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-error {
        background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .source-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #28a745;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .progress-bar {
        background: #e9ecef;
        border-radius: 10px;
        height: 10px;
        overflow: hidden;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables."""
    if 'research_results' not in st.session_state:
        st.session_state.research_results = None
    if 'research_status' not in st.session_state:
        st.session_state.research_status = "idle"
    if 'research_logs' not in st.session_state:
        st.session_state.research_logs = []
    if 'current_step' not in st.session_state:
        st.session_state.current_step = ""
    if 'progress' not in st.session_state:
        st.session_state.progress = 0
    if 'sources_found' not in st.session_state:
        st.session_state.sources_found = 0

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    return missing_vars

def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🔬 React Tavily Research Tool</h1>
        <p>Advanced AI-powered research with real-time workflow visualization</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with research configuration."""
    st.sidebar.header("🔧 Research Configuration")
    
    # Check environment
    missing_vars = check_environment()
    if missing_vars:
        st.sidebar.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        st.sidebar.info("Please set up your .env file with the required API keys.")
        return None
    else:
        st.sidebar.success("✅ Environment configured")
    
    # Research query input
    query = st.sidebar.text_area(
        "🔍 Research Query",
        placeholder="Enter your research question here...",
        height=100,
        help="Enter a comprehensive research question you'd like to investigate"
    )
    
    # Advanced settings
    st.sidebar.subheader("⚙️ Advanced Settings")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        max_results = st.slider("Max Results", 3, 10, 5)
        search_depth = st.selectbox("Search Depth", ["basic", "advanced"], index=1)
    
    with col2:
        include_answer = st.selectbox("Include Answer", ["none", "basic", "advanced"], index=2)
        verbose = st.checkbox("Verbose Mode", value=True)
    
    # Quick examples
    st.sidebar.subheader("💡 Quick Examples")
    examples = [
        "Impact of AI on healthcare industry",
        "Climate change mitigation strategies 2025",
        "Renewable energy adoption trends",
        "Future of remote work post-pandemic",
        "Quantum computing breakthroughs"
    ]
    
    selected_example = st.sidebar.selectbox("Choose an example:", [""] + examples)
    if selected_example and st.sidebar.button("Use Example"):
        query = selected_example
        st.rerun()
    
    # Research button
    research_config = None
    if query.strip():
        if st.sidebar.button("🚀 Start Research", type="primary", use_container_width=True):
            research_config = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
                "include_answer": include_answer,
                "verbose": verbose
            }
    
    return research_config

def render_progress_section():
    """Render the research progress section."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Progress</h3>
            <h2>{:.0f}%</h2>
        </div>
        """.format(st.session_state.progress), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📚 Sources</h3>
            <h2>{}</h2>
        </div>
        """.format(st.session_state.sources_found), unsafe_allow_html=True)
    
    with col3:
        status_class = f"status-{st.session_state.research_status}"
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ Status</h3>
            <span class="{}">{}</span>
        </div>
        """.format(status_class, st.session_state.research_status.title()), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🕐 Time</h3>
            <h2>{}</h2>
        </div>
        """.format(datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
    
    # Progress bar
    if st.session_state.progress > 0:
        st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {st.session_state.progress}%"></div>
        </div>
        """, unsafe_allow_html=True)
    
    # Current step
    if st.session_state.current_step:
        st.info(f"🔄 {st.session_state.current_step}")

def render_research_logs():
    """Render real-time research logs."""
    if st.session_state.research_logs:
        st.subheader("📋 Research Workflow")
        
        logs_container = st.container()
        with logs_container:
            for i, log in enumerate(st.session_state.research_logs[-10:]):  # Show last 10 logs
                timestamp = log.get('timestamp', '')
                message = log.get('message', '')
                log_type = log.get('type', 'info')
                
                if log_type == 'success':
                    st.success(f"✅ {timestamp} - {message}")
                elif log_type == 'error':
                    st.error(f"❌ {timestamp} - {message}")
                elif log_type == 'warning':
                    st.warning(f"⚠️ {timestamp} - {message}")
                else:
                    st.info(f"ℹ️ {timestamp} - {message}")

def render_results():
    """Render the research results."""
    if st.session_state.research_results:
        result = st.session_state.research_results
        
        st.header("📊 Research Results")
        
        # Executive Summary
        st.subheader("📝 Executive Summary")
        st.markdown(f"""
        <div class="research-card">
            <p>{result.summary}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key Findings
        if result.key_findings:
            st.subheader("🔑 Key Findings")
            for i, finding in enumerate(result.key_findings, 1):
                st.markdown(f"""
                <div class="research-card">
                    <strong>{i}.</strong> {finding}
                </div>
                """, unsafe_allow_html=True)
        
        # Detailed Analysis
        st.subheader("📈 Detailed Analysis")
        st.markdown(f"""
        <div class="research-card">
            <p>{result.detailed_analysis}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sources
        if result.sources:
            st.subheader("📚 Sources")
            
            # Create expandable sections for sources
            with st.expander(f"📖 View All {len(result.sources)} Sources", expanded=False):
                for source in result.sources:
                    st.markdown(f"""
                    <div class="source-card">
                        <strong>[{source.id}]</strong> {source.title}<br>
                        <a href="{source.url}" target="_blank">🔗 {source.url}</a>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Research Statistics
        st.subheader("📊 Research Statistics")
        metadata = result.metadata
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sources", len(result.sources))
        with col2:
            st.metric("Research Areas", metadata.get('questions_researched', 0))
        with col3:
            st.metric("Citations", len(result.citations_map))

def simulate_research_progress():
    """Simulate research progress for UI feedback."""
    progress_steps = [
        ("🧠 Breaking down query into research questions...", 15),
        ("🔍 Performing parallel web searches...", 40),
        ("📊 Analyzing search results...", 65),
        ("🔄 Consolidating findings...", 85),
        ("📋 Generating final report...", 95),
        ("✅ Research completed!", 100)
    ]
    
    for step_msg, step_progress in progress_steps:
        st.session_state.current_step = step_msg
        st.session_state.progress = step_progress
        
        # Add to logs
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.research_logs.append({
            'timestamp': timestamp,
            'message': step_msg,
            'type': 'info'
        })
        
        yield step_msg, step_progress

def run_research_sync(config: Dict):
    """Run the research synchronously."""
    try:
        st.session_state.research_status = "running"
        st.session_state.progress = 0
        st.session_state.sources_found = 0
        
        # Create researcher
        researcher = create_researcher(verbose=config.get('verbose', True))
        
        # Create research request
        request = ResearchRequest(
            query=config['query'],
            max_results=config['max_results'],
            search_depth=config['search_depth'],
            include_answer=config['include_answer'],
            verbose=config['verbose']
        )
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Update progress
        for step_msg, step_progress in simulate_research_progress():
            progress_bar.progress(step_progress / 100)
            status_text.text(step_msg)
            time.sleep(0.5)  # Visual delay
        
        # Run the actual research (this is sync in our current implementation)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(researcher.research(request))
        finally:
            loop.close()
        
        # Update final state
        st.session_state.sources_found = len(result.sources)
        st.session_state.research_status = "completed"
        st.session_state.research_results = result
        st.session_state.progress = 100
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return result
        
    except Exception as e:
        st.session_state.research_status = "error"
        st.error(f"Research failed: {str(e)}")
        return None

def main():
    """Main application."""
    init_session_state()
    render_header()
    
    # Sidebar configuration
    research_config = render_sidebar()
    
    # Main content area
    progress_container = st.container()
    logs_container = st.container()
    results_container = st.container()
    
    with progress_container:
        render_progress_section()
    
    # Start research if requested
    if research_config:
        # Reset state for new research
        st.session_state.research_results = None
        st.session_state.research_status = "idle"
        st.session_state.research_logs = []
        st.session_state.current_step = ""
        st.session_state.progress = 0
        st.session_state.sources_found = 0
        
        # Run research
        with st.spinner("🔬 Research in progress..."):
            result = run_research_sync(research_config)
    
    with logs_container:
        render_research_logs()
    
    with results_container:
        render_results()

if __name__ == "__main__":
    main()
