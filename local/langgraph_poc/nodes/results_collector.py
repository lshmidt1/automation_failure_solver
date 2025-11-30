"""Node for collecting all results."""
from typing import Dict, Any
from ..state import FailureAnalysisState
from ..config import Config


def results_collector(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Collect all results from previous nodes.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("📊 Collecting results...")
    
    collected_data = {
        'test_report': {
            'xml_path': state['xml_report_path'],
            'test_name': state.get('test_name', 'N/A'),
            'result': state['failure_details']['result'] if state.get('failure_details') else None,
            'failure_details': state.get('failure_details'),
            'total_tests': state.get('test_results', {}).get('total_tests', 0),
        },
        'repository': {
            'path': state.get('repo_path'),
            'file_count': len(state.get('code_files', [])),
        },
        'local_execution': {
            'success': state.get('execution_success'),
            'exit_code': state.get('local_exit_code'),
            'error_count': len(state.get('local_errors', [])),
            'log_length': len(state.get('local_execution_logs', '')),
        },
        'comparison': {
            'xml_failed': state.get('failure_details', {}).get('result') != 'SUCCESS',
            'local_failed': not state.get('execution_success', False),
            'consistent_failure': (
                state.get('failure_details', {}).get('result') != 'SUCCESS' and
                not state.get('execution_success', False)
            ),
        }
    }
    
    print("✅ Results collected")
    print(f"   XML failures: {collected_data['test_report']['failure_details']['failure_count'] if collected_data['test_report']['failure_details'] else 0}")
    print(f"   Local execution: {'Failed' if collected_data['local_execution']['exit_code'] != 0 else 'Passed'}")
    print(f"   Consistent failure: {collected_data['comparison']['consistent_failure']}")
    
    return {
        'collected_data': collected_data,
        'workflow_status': 'results_collected'
    }
