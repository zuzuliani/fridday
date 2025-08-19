"""
Simple React Tavily Research Tool Demo

This script demonstrates the enhanced research workflow with verbose output
and properly formatted results with citations.
"""

import asyncio
import os
from dotenv import load_dotenv
from reactTavily import create_researcher, ResearchRequest

# Load environment variables
load_dotenv()

async def main():
    """Run a simple research demonstration."""
    print("🔬 React Tavily Research Tool - Live Demo")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with the required API keys.")
        return
    
    try:
        # Create researcher
        researcher = create_researcher()
        
        # Research query - change this to whatever you want to research!
        user_query = "What does the current political and economic situation of Brazil look like?"
        
        print(f"🔍 Research Query: {user_query}\n")
        
        # Create research request with verbose mode and advanced Tavily settings
        request = ResearchRequest(
            query=user_query,
            max_results=5,
            search_depth="advanced",    # Use Tavily's advanced search depth
            include_answer="advanced",  # Use Tavily's advanced answer inclusion
            verbose=True               # Show detailed workflow
        )
        
        # Perform research
        result = await researcher.research(request)
        
        # Display final results with proper formatting
        print("\n" + "=" * 80)
        print("📋 RESEARCH REPORT")
        print("=" * 80)
        
        print(f"\n🎯 QUERY: {result.query}")
        
        print(f"\n📊 EXECUTIVE SUMMARY:")
        print(result.summary)
        
        print(f"\n🔑 KEY FINDINGS:")
        for i, finding in enumerate(result.key_findings, 1):
            print(f"{i}. {finding}")
        
        print(f"\n📈 DETAILED ANALYSIS:")
        print(result.detailed_analysis)
        
        print(f"\n📚 REFERENCES:")
        for source in result.sources:
            print(f"[{source.id}] {source.title}")
            print(f"    {source.url}")
            print()
        
        print(f"\n📊 RESEARCH STATISTICS:")
        metadata = result.metadata
        print(f"• Total Sources: {metadata.get('sources_count', 0)}")
        print(f"• Research Areas: {metadata.get('questions_researched', 0)}")
        print(f"• Citations Used: {len(result.citations_map)}")
        print(f"• Research Date: {metadata.get('research_date', 'Unknown')}")
        
        print("\n" + "=" * 80)
        print("✅ Research Complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Research failed: {str(e)}")

if __name__ == "__main__":
    # Check if we can import the module
    try:
        from reactTavily import create_researcher, ResearchRequest
        print("✅ React Tavily module loaded successfully\n")
    except ImportError as e:
        print(f"❌ Failed to import React Tavily module: {e}")
        print("Make sure to install dependencies: pip install -r requirements.txt")
        exit(1)
    
    # Run the demo
    asyncio.run(main())
