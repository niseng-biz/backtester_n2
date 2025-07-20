#!/usr/bin/env python3
"""
Environment check script for the backtester project.
This script verifies that all required dependencies are installed and the environment is properly configured.
"""

import sys
import subprocess
import importlib
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False


def check_virtual_environment():
    """Check if running in a virtual environment."""
    print("\n🏠 Checking virtual environment...")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
        print(f"   Virtual env path: {sys.prefix}")
        return True
    else:
        print("⚠️  Not running in virtual environment")
        print("   It's recommended to use a virtual environment")
        return False


def check_required_packages():
    """Check if all required packages are installed."""
    print("\n📦 Checking required packages...")
    
    required_packages = [
        ('pandas', '1.3.0'),
        ('numpy', '1.21.0'),
        ('matplotlib', '3.4.0'),
        ('pytest', '6.2.0'),
        ('scipy', '1.7.0'),
    ]
    
    all_installed = True
    
    for package_name, min_version in required_packages:
        try:
            module = importlib.import_module(package_name)
            if hasattr(module, '__version__'):
                version = module.__version__
                print(f"✅ {package_name} {version}")
            else:
                print(f"✅ {package_name} (version unknown)")
        except ImportError:
            print(f"❌ {package_name} - Not installed")
            all_installed = False
    
    return all_installed


def check_project_structure():
    """Check if project structure is correct."""
    print("\n📁 Checking project structure...")
    
    required_files = [
        'backtester/__init__.py',
        'backtester/models.py',
        'backtester/backtester.py',
        'backtester/analytics.py',
        'backtester/visualization.py',
        'tests/test_visualization.py',
        'requirements.txt',
        'README.md',
    ]
    
    all_present = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            all_present = False
    
    return all_present


def check_backtester_import():
    """Check if backtester package can be imported."""
    print("\n🔧 Checking backtester package import...")
    
    try:
        import backtester
        print("✅ backtester package imported successfully")
        
        # Check main components
        from backtester.backtester import Backtester
        from backtester.analytics import AnalyticsEngine
        from backtester.visualization import VisualizationEngine
        print("✅ Main components imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import backtester: {e}")
        return False


def run_quick_test():
    """Run a quick functionality test."""
    print("\n🧪 Running quick functionality test...")
    
    try:
        from backtester.models import MarketData, OrderType, OrderAction
        from datetime import datetime
        
        # Create a test MarketData object
        test_data = MarketData(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000
        )
        
        print("✅ MarketData creation test passed")
        
        # Test analytics
        from backtester.analytics import AnalyticsEngine
        analytics = AnalyticsEngine()
        print("✅ AnalyticsEngine initialization test passed")
        
        return True
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False


def main():
    """Main function to run all checks."""
    print("🚀 Backtester Environment Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Required Packages", check_required_packages),
        ("Project Structure", check_project_structure),
        ("Package Import", check_backtester_import),
        ("Quick Test", run_quick_test),
    ]
    
    results = []
    for check_name, check_func in checks:
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {check_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! Your environment is ready.")
        print("\n💡 You can now run:")
        print("   python example_usage.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\n💡 To install missing packages:")
        print("   pip install -r requirements.txt")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())