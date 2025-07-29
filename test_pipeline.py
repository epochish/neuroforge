#!/usr/bin/env python3
"""
Test script for Phase 1 PoC
Demonstrates the complete pipeline from scraping to querying
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("Stdout:", e.stdout)
        if e.stderr:
            print("Stderr:", e.stderr)
        return False

def check_files():
    """Check if required files exist"""
    print("\n📁 Checking for required files...")
    
    files_to_check = [
        "requirements.txt",
        "scraper.py", 
        "vector_store.py",
        "query.py"
    ]
    
    missing_files = []
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (missing)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present!")
    return True

def main():
    """Run the complete test pipeline"""
    print("🧪 Testing NeuroForge Phase 1 Pipeline")
    print("=" * 50)
    
    # Check files
    if not check_files():
        print("\n❌ Cannot proceed - missing required files")
        sys.exit(1)
    
    # Test URL (Wikipedia page about AI)
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    
    print(f"\n🎯 Testing with URL: {test_url}")
    
    # Step 1: Install dependencies
    if not run_command("pip3 install -r requirements.txt", "Installing dependencies"):
        print("\n❌ Failed to install dependencies")
        sys.exit(1)
    
    # Step 2: Scrape the webpage
    if not run_command(f"python scraper.py '{test_url}'", "Scraping webpage"):
        print("\n❌ Failed to scrape webpage")
        sys.exit(1)
    
    # Step 3: Build vector store
    if not run_command("python vector_store.py", "Building vector store"):
        print("\n❌ Failed to build vector store")
        sys.exit(1)
    
    # Step 4: Test query
    test_query = "What is artificial intelligence?"
    if not run_command(f"python query.py '{test_query}'", "Testing query"):
        print("\n❌ Failed to run query")
        sys.exit(1)
    
    print("\n🎉 Pipeline test completed successfully!")
    print("\n📊 Generated files:")
    
    # List generated files
    generated_files = [
        "scraped_data_en_wikipedia_org.json",
        "faiss_index",
        "metadata.pkl"
    ]
    
    for file in generated_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} (missing)")
    
    print("\nTry these commands:")
    print(" python query.py 'What are the main applications of AI?'")
    print(" python query.py --interactive")

if __name__ == "__main__":
    main() 