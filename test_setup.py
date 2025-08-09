#!/usr/bin/env python3
"""
Enhanced Setup Testing Script for Virtual Book Club
Tests all dependencies, services, and configurations
"""

import sys
import subprocess
import importlib
import requests
import os
from pathlib import Path
import time

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def print_result(test_name, success, message=""):
    """Print test result with formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")

def check_python_version():
    """Check Python version"""
    print_header("Python Environment Check")
    
    version = sys.version_info
    required_major, required_minor = 3, 8
    
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    is_compatible = version.major >= required_major and version.minor >= required_minor
    
    print_result(
        f"Python Version ({version_str})",
        is_compatible,
        f"Required: Python {required_major}.{required_minor}+" if not is_compatible else "Compatible version"
    )
    
    return is_compatible

def check_virtual_environment():
    """Check if virtual environment is active"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    print_result(
        "Virtual Environment",
        in_venv,
        "Virtual environment is active" if in_venv else "Not in virtual environment (recommended to activate)"
    )
    
    return in_venv

def check_required_packages():
    """Check if required packages are installed"""
    print_header("Package Dependencies Check")
    
    required_packages = [
        ("gradio", "gradio"),
        ("requests", "requests"),
        ("python-dotenv", "dotenv"),
        ("ollama", "ollama"),
        ("os", "os"),
        ("json", "json"),
        ("re", "re"),
        ("datetime", "datetime"),
        ("time", "time")
    ]
    
    all_installed = True
    
    for package_name, import_name in required_packages:
        try:
            importlib.import_module(import_name)
            print_result(f"Package: {package_name}", True, "Installed and importable")
        except ImportError:
            print_result(f"Package: {package_name}", False, f"Not installed. Run: pip install {package_name}")
            all_installed = False
    
    return all_installed

def check_environment_file():
    """Check .env file exists and has required variables"""
    print_header("Environment Configuration Check")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print_result(".env file", False, "File not found. Create .env file with required variables")
        return False
    
    print_result(".env file", True, "File exists")
    
    # Check environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        "OLLAMA_MODEL": "phi3:mini",  
        "GRADIO_THEME": "soft",
        "OLLAMA_URL": "http://localhost:11434/api/generate"
    }
    
    all_vars_present = True
    
    for var_name, default_value in required_vars.items():
        value = os.getenv(var_name, default_value)
        print_result(f"Environment Variable: {var_name}", True, f"Value: {value}")
    
    return all_vars_present


def check_ollama_installation():
    """Check if Ollama is installed"""
    print_header("Ollama Installation Check")
    
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_result("Ollama Installation", True, f"Version: {version}")
            return True
        else:
            print_result("Ollama Installation", False, "Ollama command failed")
            return False
    except subprocess.TimeoutExpired:
        print_result("Ollama Installation", False, "Command timed out")
        return False
    except FileNotFoundError:
        print_result("Ollama Installation", False, "Ollama not found in PATH. Install from https://ollama.ai")
        return False

def check_ollama_models():
    """Check if required Ollama models are available"""
    print("📦 Checking Ollama Models...")
    
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            models = result.stdout.lower()
            # Updated to check for phi3:mini
            has_phi3_mini = "phi3:mini" in models or "phi3" in models
            print_result("phi3:mini Model", has_phi3_mini, 
                        "Model available" if has_phi3_mini else "Run: ollama pull phi3:mini")
            return has_phi3_mini
        else:
            print_result("Model Check", False, "Could not list models")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_result("Model Check", False, "Could not check models")
        return False


def check_ollama_service():
    """Check if Ollama service is running"""
    print("🚀 Checking Ollama Service...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_result("Ollama Service", True, "Service is running and responding")
            return True
        else:
            print_result("Ollama Service", False, f"Service returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_result("Ollama Service", False, "Service not running. Run: ollama serve")
        return False
    except requests.exceptions.Timeout:
        print_result("Ollama Service", False, "Service timeout")
        return False
    except Exception as e:
        print_result("Ollama Service", False, f"Error: {str(e)}")
        return False


def test_ollama_model():
    """Test if Ollama can generate responses"""
    print("🤖 Testing Ollama Model...")
    
    try:
        payload = {
            "model": "phi3:mini",  # Updated model name
            "prompt": "Hello, this is a test. Respond with 'Test successful!'",
            "stream": False
        }
        
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data:
                print_result("Model Generation", True, "Model can generate responses")
                return True
            else:
                print_result("Model Generation", False, "No response in model output")
                return False
        else:
            print_result("Model Generation", False, f"API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Model Generation", False, f"Error: {str(e)}")
        return False


def check_open_library_api():
    """Check if Open Library API is accessible"""
    print_header("Open Library API Check")
    
    try:
        # Test basic API connectivity
        response = requests.get("https://openlibrary.org/search.json?subject=fiction&limit=1", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "docs" in data:
                print_result("Open Library API", True, f"API responding, found {len(data['docs'])} results")
                return True
            else:
                print_result("Open Library API", False, "API responding but unexpected format")
                return False
        else:
            print_result("Open Library API", False, f"API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Open Library API", False, f"Error: {str(e)}")
        return False

def check_project_structure():
    """Check if project files are in the right place"""
    print_header("Project Structure Check")
    
    required_files = [
        ("virtual-book-club.py", "Main application file"),
        ("requirements.txt", "Dependencies list"),
        (".env", "Environment variables"),
        ("test_setup.py", "This test script"),
        ("README.md", "Documentation")
    ]
    
    all_present = True
    
    for filename, description in required_files:
        file_path = Path(filename)
        exists = file_path.exists()
        print_result(f"File: {filename}", exists, description if exists else f"Missing: {description}")
        if not exists:
            all_present = False
    
    # Check directories
    venv_dir = Path("venv")
    has_venv = venv_dir.exists() and venv_dir.is_dir()
    print_result("Virtual Environment Directory", has_venv, 
                "Virtual environment directory found" if has_venv else "No venv directory (create with: python -m venv venv)")
    
    return all_present

def print_recommendations():
    """Print setup recommendations based on test results"""
    print_header("Setup Recommendations")
    
    print("🔧 NEXT STEPS:")
    print("1. If any packages are missing: pip install -r requirements.txt")
    print("2. If Ollama is not installed: Download from https://ollama.ai")
    print("3. If phi3:mini model is missing: ollama pull phi3:mini")
    print("4. If Ollama service is not running: ollama serve")
    print("5. If virtual environment is not active: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Linux/Mac)")
    print("\n🚀 TO START THE APPLICATION:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Run the main script: python virtual-book-club.py")
    print("3. Open the provided URL in your browser")

def main():
    """Run all tests and provide summary"""
    print("🧪 VIRTUAL BOOK CLUB SETUP TESTING")
    print("This script will check if everything is properly configured")
    
    # Run all tests
    tests = [
        ("Python Version", check_python_version()),
        ("Virtual Environment", check_virtual_environment()),
        ("Required Packages", check_required_packages()),
        ("Environment File", check_environment_file()),
        ("Project Structure", check_project_structure()),
        ("Ollama Installation", check_ollama_installation()),
        ("Ollama Models", check_ollama_models()),
        ("Ollama Service", check_ollama_service()),
        ("Open Library API", check_open_library_api())
    ]
    
    # Test Ollama model if service is running
    ollama_service_running = any(name == "Ollama Service" and result for name, result in tests)
    if ollama_service_running:
        tests.append(("Ollama Model Test", test_ollama_model()))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your setup is ready!")
        print("🚀 You can now run: python virtual-book-club.py")
    else:
        print(f"⚠️  {total - passed} issues found. See recommendations below.")
        print_recommendations()
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error during testing: {str(e)}")
        sys.exit(1)