"""Node for generating final report."""
from typing import Dict, Any
from datetime import datetime
from ..state import FailureAnalysisState
from ..config import Config


def report_generator(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Generate comprehensive failure analysis report.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("📝 Generating report...")
    
    try:
        collected_data = state.get('collected_data', {})
        
        # Helper functions
        def format_failure_details(failure_details: Dict[str, Any]) -> str:
            if not failure_details:
                return "No failure details available."
            
            output = []
            test_failures = failure_details.get('test_failures', [])
            
            if test_failures:
                output.append(f"\n**Test Failures:** {len(test_failures)}\n")
                for i, failure in enumerate(test_failures[:5], 1):
                    output.append(f"{i}. **{failure.get('name')}**")
                    output.append(f"   - Class: `{failure.get('class')}`")
                    if failure.get('message'):
                        output.append(f"   - Message: {failure.get('message')[:200]}")
            
            if failure_details.get('has_compilation_error'):
                output.append("\n⚠️ **Compilation Error Detected**")
            
            if failure_details.get('has_timeout'):
                output.append("\n⏱️ **Timeout Detected**")
            
            return '\n'.join(output) if output else "No specific failures identified."
        
        def format_local_errors(errors: list) -> str:
            if not errors:
                return ""
            
            output = ["\n**Local Error Details:**\n"]
            for i, error in enumerate(errors[:5], 1):
                output.append(f"{i}. ```\n{error[:500]}\n```")
            
            if len(errors) > 5:
                output.append(f"\n*... and {len(errors) - 5} more errors*")
            
            return '\n'.join(output)
        
        def format_consistency_analysis(comparison: Dict[str, Any]) -> str:
            if comparison['consistent_failure']:
                return """
### Analysis
The failure is **consistent** between XML report and local execution. This suggests:
- The issue is in the code itself, not environment-specific
- The failure is reproducible
- Fix should work in both environments
"""
            elif comparison['xml_failed'] and not comparison['local_failed']:
                return """
### Analysis
The failure occurs **only in original test**, not locally. This suggests:
- Environment-specific issue (dependencies, configuration, resources)
- Possible infrastructure problem
- Timing or concurrency issue
"""
            elif not comparison['xml_failed'] and comparison['local_failed']:
                return """
### Analysis
The failure occurs **only locally**, not in original test. This suggests:
- Local environment configuration issue
- Missing dependencies locally
- Different test data or setup
"""
            else:
                return """
### Analysis
Both original and local execution succeeded. The original failure may have been:
- Transient/intermittent issue
- Already fixed in current code
- Environment-specific and resolved
"""
        
        def format_recommendations(recommendations: list) -> str:
            if not recommendations:
                return "No specific recommendations available."
            
            output = []
            for i, rec in enumerate(recommendations, 1):
                output.append(f"{i}. {rec}")
            
            return '\n'.join(output)
        
        report = f"""
# Test Failure Analysis Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Summary

- **Test Name:** {state.get('test_name', 'N/A')}
- **XML Report:** {state['xml_report_path']}
- **Test Result:** {collected_data['test_report']['result']}
- **Total Tests:** {collected_data['test_report']['total_tests']}
- **Failure Count:** {collected_data['test_report']['failure_details']['failure_count'] if collected_data['test_report']['failure_details'] else 0}

## Repository Information

- **Path:** {collected_data['repository']['path']}
- **Files Analyzed:** {collected_data['repository']['file_count']}

## Failure Details

### XML Report Failures
{format_failure_details(state.get('failure_details', {}))}

### Local Execution Results
- **Exit Code:** {state.get('local_exit_code', 'N/A')}
- **Status:** {'✅ Passed' if state.get('execution_success') else '❌ Failed'}
- **Errors:** {len(state.get('local_errors', []))}

{format_local_errors(state.get('local_errors', []))}

## Comparison

- **XML Report Failed:** {'Yes' if collected_data['comparison']['xml_failed'] else 'No'}
- **Local Failed:** {'Yes' if collected_data['comparison']['local_failed'] else 'No'}
- **Consistent Failure:** {'Yes ⚠️' if collected_data['comparison']['consistent_failure'] else 'No'}

{format_consistency_analysis(collected_data['comparison'])}

## Root Cause Analysis

**Confidence Level:** {state.get('confidence_level', 0):.1%}

{state.get('root_cause', 'No analysis available')}

## Recommendations

{format_recommendations(state.get('recommendations', []))}

## Next Steps

1. Review the root cause analysis above
2. Implement recommended fixes
3. Rerun tests locally to verify
4. Update test suite if needed to prevent recurrence

---

*This report was generated automatically using LangGraph POC for failure analysis.*
"""
        
        print("✅ Report generated successfully")
        
        return {
            'final_report': report,
            'workflow_status': 'completed'
        }
        
    except Exception as e:
        print(f"❌ Report generation failed: {str(e)}")
        return {
            'final_report': f"Report generation failed: {str(e)}",
            'workflow_status': 'error',
            'error_message': f"Report generation failed: {str(e)}"
        }
