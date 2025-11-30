"""Node for analyzing root cause using LLM."""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..state import FailureAnalysisState
from ..config import Config


def root_cause_analyzer(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Analyze root cause of failure using LLM.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("🔍 Analyzing root cause...")
    
    try:
        # Initialize LLM
        llm_config = config.llm
        llm = ChatOpenAI(
            model=llm_config['model'],
            api_key=llm_config['api_key'],
            temperature=0.3
        )
        
        # Prepare analysis prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert automation engineer analyzing test failures.
Your task is to identify the root cause of failures by comparing XML test reports with local execution results.
Provide a detailed analysis with:
1. Root cause identification
2. Confidence level (0-1)
3. Specific recommendations for fixing the issue
4. Whether the issue is environment-related, code-related, or infrastructure-related
"""),
            ("user", """Analyze this test failure:

XML TEST REPORT:
Path: {xml_path}
Test Name: {test_name}
Result: {result}
Total Tests: {total_tests}
Failure Count: {failure_count}

TEST FAILURE DETAILS:
{failure_details}

ERROR LINES (first 20):
{error_lines}

LOCAL EXECUTION:
Exit Code: {local_exit_code}
Success: {local_success}
Error Count: {local_error_count}

LOCAL ERRORS:
{local_errors}

COMPARISON:
- XML Report Failed: {xml_failed}
- Local Failed: {local_failed}
- Consistent Failure: {consistent_failure}

Please provide:
1. Root Cause (detailed explanation)
2. Confidence Level (0.0 to 1.0)
3. Recommendations (list of actionable steps)
4. Failure Category (environment/code/infrastructure/other)
""")
        ])
        
        # Prepare data for prompt
        collected_data = state.get('collected_data', {})
        failure_details = state.get('failure_details', {})
        
        error_lines = '\n'.join(failure_details.get('error_lines', [])[:20])
        local_errors = '\n'.join(state.get('local_errors', [])[:10])
        
        # Get analysis from LLM
        chain = prompt | llm
        response = chain.invoke({
            'xml_path': state['xml_report_path'],
            'test_name': state.get('test_name', 'N/A'),
            'result': collected_data['test_report']['result'],
            'total_tests': collected_data['test_report']['total_tests'],
            'failure_count': failure_details.get('failure_count', 0),
            'failure_details': str(failure_details.get('test_failures', [])[:5]),
            'error_lines': error_lines,
            'local_exit_code': state.get('local_exit_code'),
            'local_success': state.get('execution_success'),
            'local_error_count': len(state.get('local_errors', [])),
            'local_errors': local_errors,
            'xml_failed': collected_data['comparison']['xml_failed'],
            'local_failed': collected_data['comparison']['local_failed'],
            'consistent_failure': collected_data['comparison']['consistent_failure'],
        })
        
        analysis_text = response.content
        
        # Parse response (simplified)
        lines = analysis_text.split('\n')
        root_cause = "See full analysis"
        confidence = 0.7
        recommendations = []
        
        # Extract sections from response
        current_section = None
        for line in lines:
            line = line.strip()
            if 'root cause' in line.lower() and ':' in line:
                current_section = 'root_cause'
            elif 'confidence' in line.lower() and ':' in line:
                current_section = 'confidence'
                try:
                    conf_str = line.split(':')[1].strip()
                    confidence = float(conf_str.replace('%', '').strip()) / 100 if '%' in conf_str else float(conf_str)
                except:
                    pass
            elif 'recommendation' in line.lower() and ':' in line:
                current_section = 'recommendations'
            elif current_section == 'recommendations' and line.startswith(('-', '•', '*')):
                recommendations.append(line.lstrip('-•* '))
        
        # Use full analysis as root cause
        root_cause = analysis_text
        
        print("✅ Root cause analysis completed")
        print(f"   Confidence: {confidence:.2%}")
        print(f"   Recommendations: {len(recommendations)}")
        
        return {
            'root_cause': root_cause,
            'confidence_level': confidence,
            'recommendations': recommendations if recommendations else ["See detailed analysis for recommendations"],
            'workflow_status': 'analyzed'
        }
        
    except Exception as e:
        print(f"❌ Root cause analysis failed: {str(e)}")
        return {
            'root_cause': f"Analysis failed: {str(e)}",
            'confidence_level': 0.0,
            'recommendations': ["Manual investigation required"],
            'workflow_status': 'error',
            'error_message': f"Analysis failed: {str(e)}"
        }
