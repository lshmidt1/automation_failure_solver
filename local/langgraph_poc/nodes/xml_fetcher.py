"""Node for fetching test results from XML."""
from typing import Dict, Any
from ..state import FailureAnalysisState
from ..clients.xml_reader import XMLReportReader
from ..config import Config


def xml_report_fetcher(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Fetch test results from XML file.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("📥 Reading XML test report...")
    
    try:
        # Initialize XML reader
        reader = XMLReportReader(state['xml_report_path'])
        
        # Parse report
        test_results = reader.parse_report()
        
        # Extract failure details
        failure_details = reader.extract_failure_details()
        
        print(f"✅ Successfully parsed XML report")
        print(f"   Total tests: {test_results['total_tests']}")
        print(f"   Failures: {failure_details['failure_count']}")
        print(f"   Result: {failure_details['result']}")
        
        return {
            'test_results': test_results,
            'failure_details': failure_details,
            'workflow_status': 'xml_fetched'
        }
        
    except Exception as e:
        print(f"❌ Failed to read XML report: {str(e)}")
        return {
            'workflow_status': 'error',
            'error_message': f"XML parsing failed: {str(e)}"
        }
