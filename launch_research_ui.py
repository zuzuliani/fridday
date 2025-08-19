#!/usr/bin/env python3
"""
Launch script for the React Tavily Research Web Interface
"""

import os
import subprocess
import sys
from pathlib import Path

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, will install with requirements")

def check_requirements():
    """Check if required packages are installed."""
    missing_packages = []
    
    try:
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        missing_packages.append("streamlit")
    
    try:
        import dotenv
        print("✅ python-dotenv is installed")
    except ImportError:
        missing_packages.append("python-dotenv")
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing requirements...")
        return False
    
    return True

def install_requirements():
    """Install required packages."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False

def check_environment():
    """Check if environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file or environment")
        return False
    
    print("✅ Environment variables configured")
    return True

def launch_ui():
    """Launch the Streamlit web interface."""
    print("🚀 Launching React Tavily Research Web Interface...")
    print("🌐 The interface will open in your default browser")
    print("📝 You can also access it at: http://localhost:8501")
    print()
    
    try:
        # Launch streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "web_interface.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Research interface closed.")
    except Exception as e:
        print(f"❌ Failed to launch interface: {e}")

def main():
    """Main launcher function."""
    print("🔬 React Tavily Research Tool - Web Interface Launcher")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("web_interface.py").exists():
        print("❌ web_interface.py not found. Make sure you're in the project root directory.")
        return
    
    # Check requirements
    if not check_requirements():
        if not install_requirements():
            print("❌ Failed to install requirements. Please run: pip install -r requirements.txt")
            return
    
    # Check environment
    if not check_environment():
        print("💡 Tip: Create a .env file with your API keys:")
        print("   OPENAI_API_KEY=your_openai_key")
        print("   TAVILY_API_KEY=your_tavily_key")
        return
    
    # Launch the interface
    launch_ui()

if __name__ == "__main__":
    main()
