#!/usr/bin/env python3
"""
Run the Shopping Agent with Google ADK interface
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set up environment
if os.path.exists('.env.adk'):
    from dotenv import load_dotenv
    load_dotenv('.env.adk')

def check_requirements():
    """Check if all required environment variables are set"""
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env.adk file or as environment variables.")
        print("For Google API key, visit: https://aistudio.google.com/app/apikey")
        return False
    
    return True

def run_web_interface():
    """Run the ADK web interface"""
    try:
        from google.adk.cli import main
        import sys
        
        # Simulate command line arguments for ADK
        sys.argv = ['adk', 'web', '--agent', 'adk_shopping_agent:agent']
        main()
        
    except ImportError:
        print("❌ Google ADK not properly installed")
        print("Run: pip install google-adk")
        return False
    except Exception as e:
        print(f"❌ Error running ADK web interface: {e}")
        return False

def run_terminal_interface():
    """Run the ADK terminal interface"""
    try:
        from google.adk.cli import main
        import sys
        
        # Simulate command line arguments for ADK
        sys.argv = ['adk', 'run', '--agent', 'adk_shopping_agent:agent']
        main()
        
    except Exception as e:
        print(f"❌ Error running ADK terminal interface: {e}")
        return False

if __name__ == "__main__":
    print("🛍️  Shopping Agent ADK Interface")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Show options
    print("\nAvailable interfaces:")
    print("1. Web Interface (recommended)")
    print("2. Terminal Interface")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == "1":
                print("\n🌐 Starting web interface...")
                print("This will open a web browser with the shopping agent interface.")
                run_web_interface()
                break
                
            elif choice == "2":
                print("\n💻 Starting terminal interface...")
                run_terminal_interface()
                break
                
            elif choice == "3":
                print("👋 Goodbye!")
                sys.exit(0)
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)