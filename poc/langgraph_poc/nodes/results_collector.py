"""Node for collecting and comparing results."""
from typing import Dict, Any
from .. state import FailureAnalysisState
from ..config import Config


def results_collector(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Collect and compare XML vs local execution results. 
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    debug_logger = state.get('_debug_logger')
    
    if debug_logger:
        debug_logger. stage_start("Results Collector")
    
    print("Collecting results...")
    
    try:
        # Get XML paths
        xml_paths = state. get('xml_report_paths', [])
        
        # Collect test report summary
        test_results = state.get('test_results', {})
        failure_details = state.get('failure_details', {})
        
        test_report = {
            'xml_paths': xml_paths,
            'test_name': state.get('test_name', 'N/A'),
            'total_tests': test_results.get('total_tests', 0),
            'passed_tests': test_results.get('passed_tests', 0),
            'failed_tests': test_results.get('failed_tests', 0),
            'error_tests': test_results.get('error_tests', 0),
            'skipped_tests': test_results. get('skipped_tests', 0),
            'result': failure_details.get('result', 'UNKNOWN')
        }
        
        # Collect local execution summary
        local_execution = {
            'exit_code': state.get('local_exit_code', -1),
            'success': state.get('execution_success', False),
            'output_length': len(state.get('local_output') or ''),
            'error_count': len(state.get('local_errors') or [])
        }
        
        # Compare results
        xml_failed = test_report['failed_tests'] > 0 or test_report['error_tests'] > 0
        local_failed = not local_execution['success']
        consistent_failure = xml_failed == local_failed
        
        comparison = {
            'xml_failed': xml_failed,
            'local_failed': local_failed,
            'consistent_failure': consistent_failure,
            'reproducible': consistent_failure and xml_failed
        }
        
        # Collect all data
        collected_data = {
            'test_report': test_report,
            'local_execution': local_execution,
            'comparison': comparison
        }
        
        if debug_logger:
            debug_logger.log_section("Collected Data")
            debug_logger.log_data("Test Report", test_report)
            debug_logger. log_data("Local Execution", local_execution)
            debug_logger.log_data("Comparison", comparison)
        
        print(f"Results collected")
        print(f"   XML failures: {test_report['failed_tests']}")
        print(f"   Local execution: {'Passed' if local_execution['success'] else 'Failed'}")
        print(f"   Consistent failure: {'Yes' if consistent_failure else 'No'}")
        
        if debug_logger:
            debug_logger.stage_end("Results Collector", "SUCCESS")
        
        return {
            'collected_data': collected_data,
            'workflow_status': 'results_collected'
        }
        
    except Exception as e:
        if debug_logger:
            debug_logger.log_error(e, "Results Collector")
            debug_logger.stage_end("Results Collector", "ERROR")
        
        print(f"Failed to collect results: {str(e)}")
        return {
            'workflow_status': 'error',
            'error_message': f"Results collection failed: {str(e)}"
        }