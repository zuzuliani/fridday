"""
Setup script for BifrostAI Chatbot.
This script helps with initial setup and testing.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    if not env_path.exists() and example_path.exists():
        print("Creating .env file from template...")
        with open(example_path, 'r') as f:
            content = f.read()
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✅ .env file created! Please edit it with your configuration.")
        return True
    elif env_path.exists():
        print("✅ .env file already exists.")
        return True
    else:
        print("❌ .env.example not found. Cannot create .env file.")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import supabase
        import langchain
        import langgraph
        import openai
        print("✅ All required dependencies are installed.")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_vars():
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "OPENAI_API_KEY",
        "DEFAULT_LLM",
        "TAVILY_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var).startswith("your_"):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or template environment variables: {', '.join(missing_vars)}")
        print("Please edit your .env file with actual values.")
        return False
    else:
        print("✅ All required environment variables are set.")
        return True

def main():
    """Main setup function."""
    print("🚀 BifrostAI Chatbot Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected.")
    
    # Create .env file
    if not create_env_file():
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check environment variables
    if not check_env_vars():
        print("\n📝 Next steps:")
        print("1. Edit your .env file with your actual Supabase and OpenAI credentials")
        print("2. Run the SQL schema in your Supabase dashboard (sql/conversations_schema.sql)")
        print("3. Run: python setup.py to check again")
        return
    
    print("\n🎉 Setup complete!")
    print("\n📝 Next steps:")
    print("1. Make sure you've run the SQL schema in your Supabase dashboard:")
    print("   sql/conversations_schema.sql")
    print("2. Test the chatbot: python test_chatbot.py")
    print("3. Start the server: python main.py")
    print("4. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()