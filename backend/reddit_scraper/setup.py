#!/usr/bin/env python3
"""
Setup script for Reddit Scraper
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing dependencies: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported."""
    print("\nTesting imports...")
    
    required_modules = [
        "snscrape.modules.reddit",
        "json",
        "argparse",
        "requests",
        "bs4",
        "lxml"
    ]
    
    all_good = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            all_good = False
    
    return all_good

def create_output_directory():
    """Create output directory for Reddit data."""
    output_dir = "reddit_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ Created output directory: {output_dir}")
    else:
        print(f"✓ Output directory already exists: {output_dir}")

def run_test_collection():
    """Run a small test collection."""
    print("\nRunning test collection...")
    try:
        result = subprocess.run([
            sys.executable, "reddit_collector.py",
            "--keywords", "python",
            "--min_posts", "5",
            "--single_run"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ Test collection completed successfully!")
            print("Output:", result.stdout[-200:] if len(result.stdout) > 200 else result.stdout)
            return True
        else:
            print("✗ Test collection failed!")
            print("Error:", result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ Test collection timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"✗ Test collection error: {e}")
        return False

def main():
    print("Reddit Scraper Setup")
    print("=" * 30)
    
    # Install dependencies
    if not install_dependencies():
        print("\nSetup failed at dependency installation.")
        return False
    
    # Test imports
    if not test_imports():
        print("\nSetup failed at import testing.")
        print("Try running: pip install -r requirements.txt")
        return False
    
    # Create output directory
    create_output_directory()
    
    # Ask user if they want to run test collection
    response = input("\nWould you like to run a test collection? (y/N): ").lower().strip()
    if response in ['y', 'yes']:
        if run_test_collection():
            print("\n🎉 Setup completed successfully!")
            print("\nYou can now run the Reddit collector with:")
            print("python reddit_collector.py --keywords 'your,keywords' --min_posts 100")
            print("\nOr use a predefined configuration:")
            print("python sample_runner.py programming")
        else:
            print("\n⚠️ Setup completed but test collection failed.")
            print("You may still be able to use the collector, but please check the configuration.")
    else:
        print("\n✓ Setup completed!")
        print("\nTo get started:")
        print("python reddit_collector.py --keywords 'your,keywords' --min_posts 100")
    
    return True

if __name__ == "__main__":
    main()
