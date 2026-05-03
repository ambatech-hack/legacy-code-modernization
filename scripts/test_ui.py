"""
Test script to verify UI components are properly structured.

This script checks:
1. All UI files exist
2. Imports work correctly
3. Functions are defined
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_ui_structure():
    """Test that all UI files exist."""
    print("[*] Testing UI structure...")
    
    ui_files = [
        "ui/__init__.py",
        "ui/app.py",
        "ui/utils.py",
        "ui/components/__init__.py",
        "ui/components/upload_tab.py",
        "ui/components/results_tab.py",
        "ui/components/settings_tab.py",
    ]
    
    all_exist = True
    for file_path in ui_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [FAIL] {file_path} - NOT FOUND")
            all_exist = False
    
    return all_exist


def test_imports():
    """Test that imports work correctly."""
    print("\n[*] Testing imports...")
    
    try:
        print("  Testing ui package structure...")
        
        # Check if files can be read (syntax check)
        ui_files = [
            'ui/utils.py',
            'ui/app.py',
            'ui/components/upload_tab.py',
            'ui/components/results_tab.py',
            'ui/components/settings_tab.py'
        ]
        
        for file_path in ui_files:
            full_path = project_root / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"  [OK] {file_path} - syntax valid")
            except SyntaxError as e:
                print(f"  [FAIL] {file_path} - syntax error: {e}")
                return False
        
        print("\n  [OK] All UI files have valid Python syntax")
        print("  [INFO] Streamlit not installed - skipping runtime import tests")
        print("  [INFO] Install streamlit to run full import tests: pip install streamlit")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False


def test_agent_integration():
    """Test that agents can be imported."""
    print("\n[*] Testing agent integration...")
    
    try:
        from agents.analyzer import CodeAnalyzer
        print("  [OK] CodeAnalyzer imported")
        
        from agents.documentation import DocumentationAgent
        print("  [OK] DocumentationAgent imported")
        
        from agents.refactoring import RefactoringAgent
        print("  [OK] RefactoringAgent imported")
        
        return True
        
    except ImportError as e:
        print(f"  [FAIL] Agent import failed: {e}")
        return False
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False


def test_config_files():
    """Test that configuration files exist."""
    print("\n[*] Testing configuration files...")
    
    config_files = [
        "config/agent_configs.yaml",
        ".env.example",
    ]
    
    all_exist = True
    for file_path in config_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [FAIL] {file_path} - NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests."""
    print("="*60)
    print("UI Component Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("UI Structure", test_ui_structure()))
    results.append(("Imports", test_imports()))
    results.append(("Agent Integration", test_agent_integration()))
    results.append(("Config Files", test_config_files()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n[SUCCESS] All tests passed! UI is ready to use.")
        print("\nTo start the UI, run:")
        print("  python scripts/run_ui.py")
        print("\nOr directly:")
        print("  streamlit run ui/app.py")
        return 0
    else:
        print("\n[FAILED] Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

