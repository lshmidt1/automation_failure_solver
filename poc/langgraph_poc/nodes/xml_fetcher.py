"""Node for fetching test results from XML."""
from typing import Dict, Any
from .. state import FailureAnalysisState
from ..clients.xml_reader import XMLReportReader
from ..config import Config


def xml_report_fetcher(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Fetch test results from XML file(s).  
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    debug_logger = state.get('_debug_logger')
    
    if debug_logger:
        debug_logger. stage_start("XML Report Fetcher")
    
    xml_paths = state.get('xml_report_paths', [])
    
    if not xml_paths:
        print("ERROR: No XML paths found in state")
        return {
            **state,
            'workflow_status': 'error',
            'error_message': 'No XML paths provided'
        }
    
    if debug_logger:
        debug_logger.log_detail("XML Files", len(xml_paths))
    
    if len(xml_paths) == 1:
        print("Reading XML test report...")
        if debug_logger:
            debug_logger.log_detail("File Path", xml_paths[0])
        
        try:
            reader = XMLReportReader(xml_paths[0])
            test_results = reader.parse_report()
            failure_details = reader. extract_failure_details()
            
            if debug_logger:
                debug_logger.log_data("Test Results", {
                    "Total Tests": test_results['total_tests'],
                    "Failures": test_results['failed_tests'],
                    "Errors": test_results['error_tests'],
                    "Passed": test_results['passed_tests']
                })
                
                debug_logger.log_section("Failure Details")
                debug_logger.log_data("Failures", {
                    "Count": failure_details['failure_count'],
                    "Has Compilation Error": failure_details. get('has_compilation_error'),
                    "Has Timeout": failure_details.get('has_timeout')
                })
            
            print(f"Successfully parsed XML report")
            print(f"   Total tests: {test_results['total_tests']}")
            print(f"   Failures: {failure_details['failure_count']}")
            print(f"   Result: {failure_details['result']}")
            
            if debug_logger:
                debug_logger.stage_end("XML Report Fetcher", "SUCCESS")
            
            return {
                **state,
                'test_results': test_results,
                'failure_details': failure_details,
                'workflow_status': 'xml_fetched'
            }
        except Exception as e:
            if debug_logger:
                debug_logger.log_error(e, "XML Report Fetcher")
                debug_logger.stage_end("XML Report Fetcher", "ERROR")
            
            print(f"Failed to read XML report: {str(e)}")
            return {
                **state,
                'workflow_status': 'error',
                'error_message': f"XML parsing failed: {str(e)}"
            }
    else:
        print(f"Reading {len(xml_paths)} XML test reports...")
        if debug_logger:
            for i, path in enumerate(xml_paths, 1):
                debug_logger.log_detail(f"File {i}", path)
        
        try:
            # Merge all reports
            merged_results = XMLReportReader.merge_reports(xml_paths)
            
            if debug_logger:
                debug_logger.log_data("Merged Test Results", {
                    "Total Tests": merged_results['total_tests'],
                    "Failures": merged_results['failed_tests'],
                    "Errors": merged_results['error_tests'],
                    "Passed": merged_results['passed_tests'],
                    "Source Files": len(xml_paths)
                })
            
            print(f"Successfully parsed {len(xml_paths)} XML reports")
            print(f"   Total tests: {merged_results['total_tests']}")
            print(f"   Failures: {merged_results['failure_count']}")
            print(f"   Result: {merged_results['result']}")
            
            if debug_logger:
                debug_logger.stage_end("XML Report Fetcher", "SUCCESS")
            
            return {
                **state,
                'test_results': merged_results,
                'failure_details': merged_results,
                'workflow_status': 'xml_fetched'
            }
        except Exception as e:
            if debug_logger:
                debug_logger.log_error(e, "XML Report Fetcher (Multiple Files)")
                debug_logger. stage_end("XML Report Fetcher", "ERROR")
            
            print(f"Failed to read XML reports: {str(e)}")
            return {
                **state,
                'workflow_status': 'error',
                'error_message': f"XML parsing failed: {str(e)}"
            }