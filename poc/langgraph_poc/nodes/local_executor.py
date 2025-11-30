"""Node for executing tests locally."""
from typing import Dict, Any
from pathlib import Path
from .. state import FailureAnalysisState
from ..config import Config
from ..clients.test_finder import JavaTestFinder
from ..clients.java_executor import JavaTestExecutor


def local_executor(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Execute failed tests locally to reproduce the issue. 
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    debug_logger = state.get('_debug_logger')
    
    if debug_logger:
        debug_logger.stage_start("Local Executor")
    
    print("🔧 Executing tests locally...")
    
    # Get repository path
    repo_path = state.get('repo_path')
    
    if not repo_path:
        print("   ❌ No repository path provided")
        if debug_logger:
            debug_logger.log_detail("Error", "No repository path")
            debug_logger.stage_end("Local Executor", "ERROR")
        
        return {
            **state,
            'local_output': '',
            'local_errors': ['No repository path provided'],
            'local_exit_code': -1,
            'execution_success': False,
            'workflow_status': 'executed'
        }
    
    # Get failure details
    failure_details = state.get('failure_details') or {}
    
    if failure_details. get('failure_count', 0) == 0:
        print("   ℹ️  No test failures detected - skipping local execution")
        if debug_logger:
            debug_logger.log_detail("Status", "No failures to reproduce")
            debug_logger.stage_end("Local Executor", "SKIPPED")
        
        return {
            **state,
            'local_output': 'No failures to reproduce',
            'local_errors': [],
            'local_exit_code': 0,
            'execution_success': True,
            'workflow_status': 'executed'
        }
    
    try:
        # Initialize test finder
        print(f"   📂 Searching for tests in: {repo_path}")
        
        if debug_logger:
            debug_logger.log_detail("Repository Path", repo_path)
        
        test_finder = JavaTestFinder(repo_path)
        
        # Detect build system
        build_system = test_finder.detect_build_system()
        
        if not build_system:
            print("   ⚠️  Could not detect Maven or Gradle - skipping local execution")
            if debug_logger:
                debug_logger.log_detail("Build System", "Not detected")
                debug_logger.stage_end("Local Executor", "SKIPPED")
            
            return {
                **state,
                'local_output': 'Build system not detected (Maven/Gradle required)',
                'local_errors': ['No pom.xml or build.gradle found'],
                'local_exit_code': -1,
                'execution_success': False,
                'workflow_status': 'executed'
            }
        
        print(f"   ✅ Detected build system: {build_system. upper()}")
        
        if debug_logger:
            debug_logger.log_detail("Build System", build_system. upper())
        
        # Find test files for failed tests
        print(f"   🔍 Looking for {failure_details['failure_count']} failed test(s)...")
        
        # Specify the test directory
        test_dirs = ['src/main/java/com/crb/mcsend/testers']
        
        found_tests = test_finder.find_tests_for_failures(failure_details, test_dirs)
        
        if not found_tests:
            print("   ⚠️  Could not locate failed test files in repository")
            if debug_logger:
                debug_logger.log_detail("Tests Found", 0)
                debug_logger.log_detail("Search Dirs", str(test_dirs))
                debug_logger.stage_end("Local Executor", "WARNING")
            
            return {
                **state,
                'local_output': 'Failed tests not found in repository',
                'local_errors': ['Test files could not be located'],
                'local_exit_code': -1,
                'execution_success': False,
                'workflow_status': 'executed'
            }
        
        print(f"   ✅ Found {len(found_tests)} test file(s)")
        
        if debug_logger:
            debug_logger.log_detail("Tests Found", len(found_tests))
            debug_logger.log_section("Located Tests")
            for i, test in enumerate(found_tests, 1):
                debug_logger.log_data(f"Test {i}", {
                    "Class": test.get('class_name'),
                    "Method": test.get('method_name'),
                    "File": test.get('file_path')
                })
        
        # Display found tests
        for test in found_tests:
            print(f"      • {test. get('class_name')}. {test.get('method_name')}")
        
        # Execute the tests
        print(f"   ▶️  Running tests with {build_system.upper()}...")
        
        executor = JavaTestExecutor(repo_path, build_system)
        
        result = executor.run_specific_tests(found_tests, timeout=300)
        
        if debug_logger:
            debug_logger.log_section("Execution Results")
            debug_logger.log_data("Result", {
                "Success": result['success'],
                "Exit Code": result['exit_code'],
                "Command": result. get('command', 'N/A'),
                "Output Length": len(result.get('output', '')),
                "Error Count": len(result.get('errors', []))
            })
        
        # Parse results
        if result['success']:
            print("   ✅ Tests executed successfully")
        else:
            print(f"   ❌ Tests failed with exit code: {result['exit_code']}")
        
        if result. get('output'):
            print(f"   📄 Output: {len(result['output'])} characters")
        
        if result.get('errors'):
            print(f"   ⚠️  Errors: {len(result['errors'])} error(s)")
            for error in result['errors'][:3]:  # Show first 3 errors
                print(f"      • {error[:100]}...")
        
        if debug_logger:
            debug_logger.stage_end("Local Executor", "SUCCESS" if result['success'] else "FAILURE")
        
        return {
            **state,
            'local_output': result.get('output', ''),
            'local_errors': result.get('errors', []),
            'local_exit_code': result.get('exit_code', -1),
            'execution_success': result['success'],
            'workflow_status': 'executed',
            'found_tests': found_tests,
            'test_command': result.get('command', '')
        }
        
    except Exception as e:
        print(f"   ❌ Local execution failed: {str(e)}")
        
        if debug_logger:
            debug_logger.log_error(e, "Local Executor")
            debug_logger.stage_end("Local Executor", "ERROR")
        
        return {
            **state,
            'local_output': '',
            'local_errors': [str(e)],
            'local_exit_code': -1,
            'execution_success': False,
            'workflow_status': 'executed'
        }