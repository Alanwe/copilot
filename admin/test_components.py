#!/usr/bin/env python
"""
Component testing script for the Azure Components Foundry.
This script orchestrates testing across components and services.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def setup_logging(verbose=False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def get_repo_root():
    """Get the repository root path."""
    try:
        # Try to get root from git
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return Path(result.stdout.strip())
    except Exception:
        # Fallback: assume script is in admin directory
        return Path(__file__).parent.parent


def find_components():
    """
    Find all components in the repository.
    
    Returns:
        A list of (service_name, component_name) tuples.
    """
    repo_root = get_repo_root()
    components_dir = repo_root / "components"
    components = []
    
    # Check if components directory exists
    if not components_dir.exists():
        return components
    
    # Find all components with testable structure
    for service_dir in components_dir.iterdir():
        if not service_dir.is_dir():
            continue
        
        for component_dir in service_dir.iterdir():
            if not component_dir.is_dir():
                continue
            
            # Check if it has tests directory or pytest.ini
            tests_dir = component_dir / "tests"
            if tests_dir.exists() or (component_dir / "pytest.ini").exists():
                components.append((service_dir.name, component_dir.name))
    
    return components


def run_tests_for_component(service_name, component_name, verbose=False, coverage=False):
    """
    Run tests for a specific component.
    
    Args:
        service_name: Service name
        component_name: Component name
        verbose: Whether to use verbose output
        coverage: Whether to collect coverage information
    
    Returns:
        A dictionary with test results.
    """
    repo_root = get_repo_root()
    component_dir = repo_root / "components" / service_name / component_name
    
    if not component_dir.exists():
        return {
            "service": service_name,
            "component": component_name,
            "status": "error",
            "message": f"Component directory not found: {component_dir}",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "duration_seconds": 0
        }
    
    try:
        # Change to component directory
        os.chdir(component_dir)
        start_time = time.time()
        
        # Build pytest command
        cmd = ["pytest"]
        if verbose:
            cmd.append("-v")
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=term", "--cov-report=xml:coverage.xml"])
        
        # Run the tests
        logging.info(f"Running tests for {service_name}/{component_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        # Parse the output to get test counts
        output = result.stdout + "\n" + result.stderr
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        tests_skipped = 0
        
        # Try to extract test counts (this is a simple heuristic and may need refinement)
        lines = output.split("\n")
        for line in lines:
            if "failed" in line and "passed" in line and "skipped" in line and "=" in line:
                parts = line.split("=")[1].strip().split()
                for part in parts:
                    if "passed" in part:
                        tests_passed = int(part.split(" ")[0])
                    elif "failed" in part:
                        tests_failed = int(part.split(" ")[0])
                    elif "skipped" in part:
                        tests_skipped = int(part.split(" ")[0])
        
        tests_run = tests_passed + tests_failed
        
        # Format the results
        test_results = {
            "service": service_name,
            "component": component_name,
            "status": "passed" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "tests_skipped": tests_skipped,
            "duration_seconds": round(end_time - start_time, 2)
        }
        
        # Add coverage information if collected
        if coverage and (component_dir / "coverage.xml").exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(component_dir / "coverage.xml")
                root = tree.getroot()
                coverage_pct = float(root.attrib.get("line-rate", 0)) * 100
                test_results["coverage"] = {
                    "percent": round(coverage_pct, 2),
                    "file": str(component_dir / "coverage.xml")
                }
            except Exception as e:
                logging.warning(f"Failed to parse coverage report: {str(e)}")
        
        return test_results
    
    except Exception as e:
        return {
            "service": service_name,
            "component": component_name,
            "status": "error",
            "message": str(e),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "duration_seconds": 0
        }


def run_tests_for_all_components(verbose=False, coverage=False, service_filter=None):
    """
    Run tests for all components.
    
    Args:
        verbose: Whether to use verbose output
        coverage: Whether to collect coverage information
        service_filter: Only test components for this service (optional)
    
    Returns:
        A dictionary with test results for all components.
    """
    components = find_components()
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "components_tested": 0,
        "components_passed": 0,
        "components_failed": 0,
        "components_error": 0,
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "tests_skipped": 0,
        "total_duration_seconds": 0,
        "component_results": []
    }
    
    # Filter components by service if specified
    if service_filter:
        components = [c for c in components if c[0] == service_filter]
        if not components:
            logging.warning(f"No testable components found for service: {service_filter}")
    
    if not components:
        logging.warning("No testable components found")
        return results
    
    logging.info(f"Running tests for {len(components)} component(s)...")
    start_time = time.time()
    
    for service_name, component_name in components:
        component_result = run_tests_for_component(
            service_name, component_name, verbose, coverage
        )
        results["component_results"].append(component_result)
        
        # Update summary statistics
        results["components_tested"] += 1
        if component_result["status"] == "passed":
            results["components_passed"] += 1
        elif component_result["status"] == "failed":
            results["components_failed"] += 1
        else:  # Error
            results["components_error"] += 1
        
        results["tests_run"] += component_result["tests_run"]
        results["tests_passed"] += component_result["tests_passed"]
        results["tests_failed"] += component_result["tests_failed"]
        results["tests_skipped"] += component_result["tests_skipped"]
    
    end_time = time.time()
    results["total_duration_seconds"] = round(end_time - start_time, 2)
    
    return results


def run_tests_for_changed_components(verbose=False, coverage=False):
    """
    Run tests only for components that have changed since the last commit.
    
    Args:
        verbose: Whether to use verbose output
        coverage: Whether to collect coverage information
    
    Returns:
        A dictionary with test results for changed components.
    """
    try:
        # Get list of changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, check=True
        )
        changed_files = result.stdout.strip().split("\n")
        
        # Also check for staged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "--staged"],
            capture_output=True, text=True, check=True
        )
        staged_files = result.stdout.strip().split("\n")
        
        changed_files.extend(staged_files)
        
        # Find affected components
        repo_root = get_repo_root()
        components_dir = repo_root / "components"
        affected_components = set()
        
        for file_path in changed_files:
            if not file_path:
                continue
                
            path = Path(file_path)
            try:
                rel_path = path.relative_to(components_dir)
                if len(rel_path.parts) >= 2:
                    service_name = rel_path.parts[0]
                    component_name = rel_path.parts[1]
                    affected_components.add((service_name, component_name))
            except ValueError:
                # Not in components directory, skip
                pass
        
        if not affected_components:
            logging.info("No components affected by recent changes")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "components_tested": 0,
                "message": "No components affected by recent changes",
                "component_results": []
            }
        
        # Convert to list of tuples
        components_to_test = list(affected_components)
        logging.info(f"Found {len(components_to_test)} component(s) affected by recent changes")
        
        # Run tests for affected components
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "components_tested": 0,
            "components_passed": 0,
            "components_failed": 0,
            "components_error": 0,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "total_duration_seconds": 0,
            "component_results": []
        }
        
        start_time = time.time()
        
        for service_name, component_name in components_to_test:
            component_dir = repo_root / "components" / service_name / component_name
            test_dir = component_dir / "tests"
            
            # Only run tests if a tests directory exists
            if test_dir.exists() and test_dir.is_dir():
                component_result = run_tests_for_component(
                    service_name, component_name, verbose, coverage
                )
                results["component_results"].append(component_result)
                
                # Update summary statistics
                results["components_tested"] += 1
                if component_result["status"] == "passed":
                    results["components_passed"] += 1
                elif component_result["status"] == "failed":
                    results["components_failed"] += 1
                else:  # Error
                    results["components_error"] += 1
                
                results["tests_run"] += component_result["tests_run"]
                results["tests_passed"] += component_result["tests_passed"]
                results["tests_failed"] += component_result["tests_failed"]
                results["tests_skipped"] += component_result["tests_skipped"]
        
        end_time = time.time()
        results["total_duration_seconds"] = round(end_time - start_time, 2)
        
        return results
    
    except Exception as e:
        logging.error(f"Error determining changed components: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "message": str(e),
            "component_results": []
        }


def generate_report(results, output_path=None):
    """
    Generate a test report.
    
    Args:
        results: Test results dictionary
        output_path: Path to save the report (optional)
    
    Returns:
        Path to the report file if saved, None otherwise.
    """
    # Generate JSON report
    if output_path:
        output_file = Path(output_path)
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logging.info(f"Test report saved to {output_file}")
            return output_file
        except Exception as e:
            logging.error(f"Error saving test report: {str(e)}")
            return None
    
    return None


def print_summary(results):
    """Print a summary of test results."""
    print("\n===== Test Summary =====")
    print(f"Time: {results.get('timestamp', datetime.utcnow().isoformat())}")
    print(f"Components Tested: {results.get('components_tested', 0)}")
    print(f"Components Passed: {results.get('components_passed', 0)}")
    print(f"Components Failed: {results.get('components_failed', 0)}")
    print(f"Components Error: {results.get('components_error', 0)}")
    print(f"Total Tests: {results.get('tests_run', 0)}")
    print(f"Tests Passed: {results.get('tests_passed', 0)}")
    print(f"Tests Failed: {results.get('tests_failed', 0)}")
    print(f"Tests Skipped: {results.get('tests_skipped', 0)}")
    print(f"Duration: {results.get('total_duration_seconds', 0):.2f} seconds")
    print("========================")
    
    if results.get('components_failed', 0) > 0 or results.get('components_error', 0) > 0:
        print("\nFailed Components:")
        for component in results.get('component_results', []):
            if component.get('status') in ['failed', 'error']:
                print(f"- {component.get('service', '')}/{component.get('component', '')}")
                if component.get('message'):
                    print(f"  Error: {component.get('message')}")
    
    print("\n")


def run_integration_tests(test_directory, verbose=False):
    """
    Run integration tests from a specific directory.
    
    Args:
        test_directory: Directory containing integration tests
        verbose: Whether to use verbose output
    
    Returns:
        A dictionary with test results.
    """
    test_dir = Path(test_directory)
    if not test_dir.exists() or not test_dir.is_dir():
        logging.error(f"Integration test directory not found: {test_dir}")
        return {
            "status": "error",
            "message": f"Integration test directory not found: {test_dir}",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "duration_seconds": 0
        }
    
    try:
        # Change to test directory
        os.chdir(test_dir)
        start_time = time.time()
        
        # Build pytest command
        cmd = ["pytest"]
        if verbose:
            cmd.append("-v")
        
        # Run the tests
        logging.info(f"Running integration tests from {test_dir}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        # Parse the output to get test counts
        output = result.stdout + "\n" + result.stderr
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        tests_skipped = 0
        
        # Try to extract test counts (this is a simple heuristic and may need refinement)
        lines = output.split("\n")
        for line in lines:
            if "failed" in line and "passed" in line and "skipped" in line and "=" in line:
                parts = line.split("=")[1].strip().split()
                for part in parts:
                    if "passed" in part:
                        tests_passed = int(part.split(" ")[0])
                    elif "failed" in part:
                        tests_failed = int(part.split(" ")[0])
                    elif "skipped" in part:
                        tests_skipped = int(part.split(" ")[0])
        
        tests_run = tests_passed + tests_failed
        
        # Format the results
        return {
            "type": "integration",
            "directory": str(test_dir),
            "status": "passed" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "tests_skipped": tests_skipped,
            "duration_seconds": round(end_time - start_time, 2),
            "output": output if result.returncode != 0 else None
        }
    
    except Exception as e:
        return {
            "type": "integration",
            "directory": str(test_dir),
            "status": "error",
            "message": str(e),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "duration_seconds": 0
        }


def main():
    """Main entry point for the component testing script."""
    parser = argparse.ArgumentParser(
        description="Run tests for Azure Components Foundry components"
    )
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Test all components command
    all_parser = subparsers.add_parser(
        "all", help="Test all components"
    )
    all_parser.add_argument(
        "--service", help="Only test components for this service"
    )
    all_parser.add_argument(
        "--coverage", action="store_true", help="Collect code coverage information"
    )
    all_parser.add_argument(
        "--report", help="Generate a test report file"
    )
    
    # Test specific component command
    component_parser = subparsers.add_parser(
        "component", help="Test a specific component"
    )
    component_parser.add_argument(
        "--service", required=True, help="Service name"
    )
    component_parser.add_argument(
        "--component", required=True, help="Component name"
    )
    component_parser.add_argument(
        "--coverage", action="store_true", help="Collect code coverage information"
    )
    component_parser.add_argument(
        "--report", help="Generate a test report file"
    )
    
    # Test changed components command
    changed_parser = subparsers.add_parser(
        "changed", help="Test components with changes"
    )
    changed_parser.add_argument(
        "--coverage", action="store_true", help="Collect code coverage information"
    )
    changed_parser.add_argument(
        "--report", help="Generate a test report file"
    )
    
    # Run integration tests command
    integration_parser = subparsers.add_parser(
        "integration", help="Run integration tests"
    )
    integration_parser.add_argument(
        "--directory", required=True, help="Directory containing integration tests"
    )
    integration_parser.add_argument(
        "--report", help="Generate a test report file"
    )
    
    # Global arguments
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging and output"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging(args.verbose)
    
    # Default command if none specified
    if not args.command:
        args.command = "all"
    
    # Execute requested command
    try:
        if args.command == "all":
            results = run_tests_for_all_components(
                verbose=args.verbose,
                coverage=args.coverage,
                service_filter=args.service
            )
            print_summary(results)
            
            if args.report:
                generate_report(results, args.report)
        
        elif args.command == "component":
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "components_tested": 1,
                "component_results": []
            }
            
            component_result = run_tests_for_component(
                args.service, args.component, verbose=args.verbose, coverage=args.coverage
            )
            results["component_results"].append(component_result)
            
            if component_result["status"] == "passed":
                results["components_passed"] = 1
                results["components_failed"] = 0
                results["components_error"] = 0
            elif component_result["status"] == "failed":
                results["components_passed"] = 0
                results["components_failed"] = 1
                results["components_error"] = 0
            else:
                results["components_passed"] = 0
                results["components_failed"] = 0
                results["components_error"] = 1
            
            results["tests_run"] = component_result["tests_run"]
            results["tests_passed"] = component_result["tests_passed"]
            results["tests_failed"] = component_result["tests_failed"]
            results["tests_skipped"] = component_result["tests_skipped"]
            results["total_duration_seconds"] = component_result["duration_seconds"]
            
            print_summary(results)
            
            if args.report:
                generate_report(results, args.report)
        
        elif args.command == "changed":
            results = run_tests_for_changed_components(
                verbose=args.verbose,
                coverage=args.coverage
            )
            print_summary(results)
            
            if args.report:
                generate_report(results, args.report)
        
        elif args.command == "integration":
            integration_results = run_integration_tests(
                args.directory, verbose=args.verbose
            )
            
            # Format results to match the summary format
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "integration",
                "tests_run": integration_results["tests_run"],
                "tests_passed": integration_results["tests_passed"],
                "tests_failed": integration_results["tests_failed"],
                "tests_skipped": integration_results["tests_skipped"],
                "total_duration_seconds": integration_results["duration_seconds"],
                "status": integration_results["status"]
            }
            
            print_summary(results)
            
            if args.report:
                generate_report(integration_results, args.report)
        
        else:
            parser.print_help()
        
    except KeyboardInterrupt:
        logging.warning("Testing interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logging.error(f"Error during testing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()