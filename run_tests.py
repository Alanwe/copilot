#!/usr/bin/env python
"""
Main test runner for Azure Components Foundry.
Runs the essential tests needed for coverage validation and component testing.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def setup_argparse():
    """Setup argument parser for the test runner."""
    parser = argparse.ArgumentParser(description="Run Azure Components Foundry tests")
    parser.add_argument("--runtime", action="store_true", help="Run runtime tests with coverage")
    parser.add_argument("--component", type=str, help="Run tests for a specific component")
    parser.add_argument("--all-components", action="store_true", help="Run tests for all components")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    return parser

def run_runtime_tests(verbose=False):
    """Run the runtime tests with coverage."""
    print("Running runtime tests with coverage...")
    
    # Use our simplified coverage approach
    script_path = Path(__file__).parent / "tests" / "runtime" / "run_coverage.sh"
    cmd = ["bash", str(script_path)]
    
    # Execute the command
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print("Runtime tests failed!")
        return False
    
    print("Runtime tests completed successfully!")
    return True

def get_components():
    """Get list of available components."""
    components_dir = Path(__file__).parent / "components"
    return [d.name for d in components_dir.iterdir() if d.is_dir() and (d / "src").exists()]

def run_component_tests(component, verbose=False):
    """Run tests for a specific component."""
    component_dir = Path(__file__).parent / "components" / component
    
    if not component_dir.exists() or not (component_dir / "src").exists():
        print(f"Component '{component}' not found or invalid!")
        return False
    
    print(f"Running tests for component: {component}")
    
    # Try to find a simple_test.py file first
    simple_test = component_dir / "simple_test.py"
    if simple_test.exists():
        print(f"Running {simple_test.name}...")
        result = subprocess.run([sys.executable, str(simple_test)], check=False)
        if result.returncode != 0:
            print(f"Simple test for component '{component}' failed!")
            return False
    
    # Look for more tests in tests/ directory
    tests_dir = component_dir / "tests"
    if tests_dir.exists():
        print(f"Running pytest for {component}/tests/...")
        cmd = ["python", "-m", "pytest", str(tests_dir), "-v"]
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"Pytest tests for component '{component}' failed!")
            return False
    
    print(f"All tests for component '{component}' passed!")
    return True

def main():
    """Main function to run tests."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    success = True
    
    # Run runtime tests if requested
    if args.runtime:
        if not run_runtime_tests(args.verbose):
            success = False
    
    # Run component tests if requested
    if args.component:
        if not run_component_tests(args.component, args.verbose):
            success = False
    
    # Run all component tests if requested
    if args.all_components:
        components = get_components()
        print(f"Found {len(components)} components: {', '.join(components)}")
        
        for component in components:
            if not run_component_tests(component, args.verbose):
                success = False
    
    # If no specific tests were requested, show help
    if not (args.runtime or args.component or args.all_components):
        parser.print_help()
        return True
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
