"""Node for generating the final analysis report."""
from typing import Dict, Any
from datetime import datetime
from ..  state import FailureAnalysisState
from ..config import Config


def report_generator(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Generate final analysis report in markdown format. 
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary with final report
    """
    debug_logger = state.get('_debug_logger')
    
    if debug_logger:
        debug_logger.stage_start("Report Generator")
    
    print("Generating report...")
    
    try:
        # Safely extract all data with defaults
        xml_paths = state.get('xml_report_paths') or []
        test_name = state.get('test_name') or 'Test Analysis'
        test_results = state.get('test_results') or {}
        failure_details = state.get('failure_details') or {}
        collected_data = state.get('collected_data') or {}
        root_cause = state.get('root_cause') or 'Unable to determine root cause'
        confidence_level = state.get('confidence_level') or 0.0
        recommendations = state.get('recommendations') or ['No recommendations available']
        llm_response = state.get('llm_full_response') or ''
        
        # Extract test report data
        test_report = collected_data.get('test_report') or {}
        local_execution = collected_data.get('local_execution') or {}
        comparison = collected_data.get('comparison') or {}
        
        # Build the report
        report_lines = []
        
        # Header
        report_lines.append("# Test Failure Analysis Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Test Name:** {test_name}")
        report_lines.append("")
        
        # XML Report Information
        report_lines.append("## XML Test Report")
        report_lines. append("")
        if len(xml_paths) == 1:
            report_lines.append(f"**File:** `{xml_paths[0]}`")
        else:
            report_lines.append(f"**Files:** {len(xml_paths)} XML reports")
            for i, path in enumerate(xml_paths, 1):
                report_lines. append(f"  {i}. `{path}`")
        report_lines.append("")
        
        # Test Statistics
        report_lines.append("### Test Statistics")
        report_lines.append("")
        report_lines.append(f"- **Total Tests:** {test_results.get('total_tests', 0)}")
        report_lines. append(f"- **Passed:** {test_results.get('passed_tests', 0)}")
        report_lines.append(f"- **Failed:** {test_results.get('failed_tests', 0)}")
        report_lines.append(f"- **Errors:** {test_results.get('error_tests', 0)}")
        report_lines.append(f"- **Skipped:** {test_results.get('skipped_tests', 0)}")
        report_lines.append(f"- **Duration:** {test_results.get('duration_seconds', 0):.2f}s")
        report_lines.append(f"- **Format:** {test_results.get('format', 'Unknown'). upper()}")
        report_lines.append(f"- **Result:** {test_report.get('result', 'UNKNOWN')}")
        report_lines.append("")
        
        # Failure Details
        if failure_details. get('failure_count', 0) > 0:
            report_lines.append("### Failure Details")
            report_lines.append("")
            report_lines.append(f"**Failed Test Count:** {failure_details['failure_count']}")
            report_lines.append("")
            
            # List failed tests
            test_failures = failure_details.get('test_failures', [])
            if test_failures:
                report_lines.append("**Failed Tests:**")
                report_lines.append("")
                for i, failure in enumerate(test_failures[:10], 1):  # Limit to first 10
                    test_name_str = failure.get('test_name', 'Unknown')
                    class_name = failure.get('class_name', '')
                    error_type = failure.get('error_type', 'Error')
                    error_msg = failure.get('error_message', 'No message')
                    
                    report_lines.append(f"{i}. **{class_name}. {test_name_str}**")
                    report_lines. append(f"   - **Type:** `{error_type}`")
                    report_lines.append(f"   - **Message:** {error_msg}")
                    report_lines.append("")
                
                if len(test_failures) > 10:
                    report_lines.append(f"*... and {len(test_failures) - 10} more failures*")
                    report_lines.append("")
            
            # Error indicators
            report_lines.append("**Error Indicators:**")
            report_lines.append("")
            report_lines.append(f"- Compilation Error: {'Yes' if failure_details.get('has_compilation_error') else 'No'}")
            report_lines.append(f"- Timeout: {'Yes' if failure_details.get('has_timeout') else 'No'}")
            report_lines.append(f"- Assertion Error: {'Yes' if failure_details.get('has_assertion_error') else 'No'}")
            report_lines.append("")
        
        # Local Execution Results
        report_lines.append("## Local Execution Results")
        report_lines.append("")
        report_lines.append(f"- **Exit Code:** {local_execution.get('exit_code', 'N/A')}")
        report_lines.append(f"- **Success:** {'Yes' if local_execution.get('success') else 'No'}")
        report_lines.append(f"- **Output Length:** {local_execution. get('output_length', 0)} characters")
        report_lines. append(f"- **Error Count:** {local_execution.get('error_count', 0)}")
        report_lines.append("")
        
        # Comparison Analysis
        report_lines.append("## Comparison Analysis")
        report_lines.append("")
        report_lines.append(f"- **XML Reports Failure:** {'Yes' if comparison.get('xml_failed') else 'No'}")
        report_lines.append(f"- **Local Execution Failed:** {'Yes' if comparison.get('local_failed') else 'No'}")
        report_lines.append(f"- **Consistent Failure:** {'Yes' if comparison.get('consistent_failure') else 'No'}")
        report_lines.append(f"- **Reproducible:** {'Yes' if comparison.get('reproducible') else 'No'}")
        report_lines.append("")
        
        # Root Cause Analysis
        report_lines.append("## Root Cause Analysis")
        report_lines.append("")
        report_lines.append(f"**Confidence Level:** {confidence_level:.0%}")
        report_lines. append("")
        report_lines.append("### Analysis")
        report_lines.append("")
        report_lines.append(root_cause)
        report_lines.append("")
        
        # Recommendations
        report_lines.append("## Recommendations")
        report_lines.append("")
        for i, rec in enumerate(recommendations, 1):
            report_lines. append(f"{i}. {rec}")
        report_lines. append("")
        
        # Error Messages (if available)
        error_lines = failure_details.get('error_lines', [])
        if error_lines:
            report_lines.append("## Error Messages")
            report_lines.append("")
            report_lines.append("```")
            for line in error_lines[:50]:  # Limit to first 50 lines
                report_lines.append(line)
            if len(error_lines) > 50:
                report_lines. append(f"... and {len(error_lines) - 50} more lines")
            report_lines. append("```")
            report_lines.append("")
        
        # Footer
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("*Report generated by Automation Failure Solver POC*")
        
        # Join all lines
        final_report = '\n'.join(report_lines)
        
        if debug_logger:
            debug_logger.log_section("Report Generated")
            debug_logger.log_data("Report Stats", {
                "Total Lines": len(report_lines),
                "Report Length": len(final_report),
                "Sections": 7
            })
            debug_logger.stage_end("Report Generator", "SUCCESS")
        
        print("Report generated successfully")
        print(f"   Report length: {len(final_report)} characters")
        print(f"   Sections: Test Stats, Failures, Local Exec, Comparison, Root Cause, Recommendations")
        
        return {
            **state,
            'final_report': final_report,
            'workflow_status': 'completed'
        }
        
    except Exception as e:
        if debug_logger:
            debug_logger.log_error(e, "Report Generator")
            debug_logger.stage_end("Report Generator", "ERROR")
        
        print(f"Report generation failed: {str(e)}")
        
        # Generate a minimal error report
        error_report = f"""# Test Failure Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Error

Report generation failed: {str(e)}

### Available Data
- XML Paths: {state.get('xml_report_paths', [])}
- Test Results: {state.get('test_results', 'N/A')}
- Workflow Status: {state.get('workflow_status', 'Unknown')}

---
*Report generation encountered an error*
"""
        
        return {
            **state,
            'final_report': error_report,
            'workflow_status': 'error',
            'error_message': f"Report generation failed: {str(e)}"
        }