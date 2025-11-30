"""Node for analyzing root cause using LLM."""
from typing import Dict, Any
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from ..  state import FailureAnalysisState
from ..config import Config


def root_cause_analyzer(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Analyze root cause of failure using LLM.  
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    debug_logger = state.get('_debug_logger')
    
    if debug_logger:
        debug_logger. stage_start("Root Cause Analyzer")
    
    print("Analyzing root cause...")
    
    try:
        llm_config = config.llm
        
        if debug_logger:
            debug_logger.log_section("LLM Configuration")
            debug_logger.log_data("Config", {
                "Provider": llm_config.get('provider'),
                "Model": llm_config['model'],
                "Region": llm_config.get('region'),
                "Temperature": llm_config.get('temperature', 0.3)
            })
        
        # Initialize LLM
        llm = ChatBedrock(
            model_id=llm_config['model'],
            region_name=llm_config.get('region', 'us-east-1'),
            credentials_profile_name=None,
            model_kwargs={
                "temperature": llm_config.get('temperature', 0.3),
                "max_tokens": llm_config.get('max_tokens', 2000)
            }
        )
        
        if debug_logger:
            debug_logger.log_detail("LLM Initialized", "ChatBedrock")
        
        # Prepare prompt data with safe null handling
        collected_data = state.get('collected_data') or {}
        failure_details = state.get('failure_details') or {}
        
        # Safely extract error lines
        error_lines_list = failure_details.get('error_lines') or []
        error_lines = '\n'.join(error_lines_list[:20]) if error_lines_list else 'No error messages captured'
        
        # Safely extract local errors
        local_errors_list = state.get('local_errors') or []
        local_errors = '\n'.join(local_errors_list[:10]) if local_errors_list else 'No local errors'
        
        # Safely extract test report data
        test_report = collected_data.get('test_report') or {}
        comparison = collected_data.get('comparison') or {}
        
        if debug_logger:
            debug_logger.log_section("Prompt Data")
            debug_logger.log_data("Input Data", {
                "XML Paths": state.get('xml_report_paths', []),
                "Test Name": state.get('test_name', 'N/A'),
                "Total Tests": test_report.get('total_tests', 0),
                "Failure Count": failure_details.get('failure_count', 0),
                "Local Exit Code": state.get('local_exit_code', 'N/A'),
                "Error Lines": len(error_lines.  split('\n'))
            })
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert automation engineer analyzing test failures.
Your task is to identify the root cause of test failures and provide actionable recommendations.  

Analyze the following information carefully:
- Test results from XML report
- Local execution results
- Error messages and stack traces
- Comparison between XML and local execution

Provide your analysis in the following format:

**Root Cause:**
[Detailed explanation of what is causing the failures]

**Confidence:** [X]%
[Explain why you have this confidence level]

**Recommendations:**
1. [First recommendation]
2. [Second recommendation]
3. [Third recommendation]

Be specific, technical, and actionable in your recommendations."""),
            ("user", """
# Test Failure Analysis

## Test Information
- **XML Path:** {xml_path}
- **Test Name:** {test_name}
- **Result:** {result}
- **Total Tests:** {total_tests}
- **Failed Tests:** {failure_count}

## Failure Details
{failure_details}

## Error Messages
{error_lines}


## Local Execution Results
- **Exit Code:** {local_exit_code}
- **Execution Success:** {local_success}
- **Local Error Count:** {local_error_count}

### Local Errors
{local_errors}


## Comparison Analysis
- **XML Reports Failure:** {xml_failed}
- **Local Execution Failed:** {local_failed}
- **Consistent Failure:** {consistent_failure}

Please analyze this information and provide the root cause, confidence level, and recommendations.
""")
        ])
        
        # Prepare prompt variables with safe defaults
        xml_paths = state.get('xml_report_paths') or []
        prompt_vars = {
            'xml_path': ', '.join(xml_paths) if xml_paths else 'N/A',
            'test_name': state.get('test_name') or 'N/A',
            'result': test_report.get('result') or 'UNKNOWN',
            'total_tests': test_report.get('total_tests') or 0,
            'failure_count': failure_details.get('failure_count') or 0,
            'failure_details': str(failure_details. get('test_failures', [])[:5]),
            'error_lines': error_lines,
            'local_exit_code': state.get('local_exit_code') or 'N/A',
            'local_success': state.get('execution_success') or False,
            'local_error_count': len(local_errors_list),
            'local_errors': local_errors,
            'xml_failed': comparison.get('xml_failed') or False,
            'local_failed': comparison.get('local_failed') or False,
            'consistent_failure': comparison.get('consistent_failure') or False,
        }
        
        # Log the full prompt if debug mode
        if debug_logger:
            try:
                prompt_text = prompt.format(**prompt_vars)
                debug_logger.log_llm_prompt(str(prompt_text))
            except Exception as e:
                debug_logger.log_detail("Prompt Format Error", str(e))
        
        # Get analysis from LLM
        chain = prompt | llm
        
        if debug_logger:
            debug_logger.log_detail("Sending to LLM", "In progress...")
        
        response = chain.invoke(prompt_vars)
        
        analysis_text = response.  content
        
        # Log the response
        if debug_logger:
            debug_logger.log_llm_response(analysis_text)
        
        # Parse response
        root_cause = "Unable to determine root cause"
        confidence = 0.0
        recommendations = []
        
        # Extract root cause
        if "**Root Cause:**" in analysis_text:
            parts = analysis_text.split("**Root Cause:**")
            if len(parts) > 1:
                root_cause_section = parts[1].split("**Confidence:**")[0] if "**Confidence:**" in parts[1] else parts[1]. split("**Recommendations:**")[0] if "**Recommendations:**" in parts[1] else parts[1]
                root_cause = root_cause_section.strip()
        
        # Extract confidence
        if "**Confidence:**" in analysis_text:
            parts = analysis_text.split("**Confidence:**")
            if len(parts) > 1:
                conf_section = parts[1].split("**Recommendations:**")[0] if "**Recommendations:**" in parts[1] else parts[1]
                conf_line = conf_section.strip(). split('\n')[0]
                # Extract percentage
                import re
                match = re.search(r'(\d+(? :\.\d+)?)\s*%', conf_line)
                if match:
                    confidence = float(match.group(1)) / 100.0
        
        # Extract recommendations
        if "**Recommendations:**" in analysis_text:
            parts = analysis_text.split("**Recommendations:**")
            if len(parts) > 1:
                rec_section = parts[1].strip()
                # Parse numbered list
                for line in rec_section.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line. startswith('-') or line.startswith('â€¢')):
                        # Remove numbering
                        rec = line.lstrip('0123456789.-â€¢) ').strip()
                        if rec:
                            recommendations.append(rec)
        
        if debug_logger:
            debug_logger.log_section("Analysis Results")
            debug_logger.log_data("Parsed Results", {
                "Confidence": f"{confidence:.2%}",
                "Recommendations": len(recommendations),
                "Root Cause Length": len(root_cause)
            })
        
        print("Root cause analysis completed")
        print(f"   Confidence: {confidence:.2%}")
        print(f"   Recommendations: {len(recommendations)}")
        
        if debug_logger:
            debug_logger.stage_end("Root Cause Analyzer", "SUCCESS")
        
        return {
            **state,
            'root_cause': root_cause,
            'confidence_level': confidence,
            'recommendations': recommendations if recommendations else ["See detailed analysis for recommendations"],
            'llm_full_response': analysis_text,
            'workflow_status': 'analyzed'
        }
        
    except Exception as e:
        if debug_logger:
            debug_logger.log_error(e, "Root Cause Analyzer")
            debug_logger.stage_end("Root Cause Analyzer", "ERROR")
        
        print(f"Root cause analysis failed: {str(e)}")
        
        # Return a fallback analysis
        return {
            **state,
            'root_cause': f"Analysis failed: {str(e)}",
            'confidence_level': 0.0,
            'recommendations': ["Manual investigation required", "Check AWS credentials", "Review error logs"],
            'llm_full_response': f"Error: {str(e)}",
            'workflow_status': 'error',
            'error_message': f"Analysis failed: {str(e)}"
        }