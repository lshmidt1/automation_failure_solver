"""LangGraph workflow definition for failure analysis."""
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from .state import FailureAnalysisState
from .config import Config
from .nodes.xml_fetcher import xml_report_fetcher
from .nodes.local_repo_access import local_repo_access
from .nodes.local_executor import local_executor
from .nodes.results_collector import results_collector
from .nodes.root_cause_analyzer import root_cause_analyzer
from .nodes.report_generator import report_generator


def create_failure_analysis_graph(config: Config) -> StateGraph:
    """Create the LangGraph workflow for failure analysis.
    
    Args:
        config: Configuration object
        
    Returns:
        Compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(FailureAnalysisState)
    
    # Add nodes with config binding
    workflow.add_node("xml_fetcher", lambda state: xml_report_fetcher(state, config))
    workflow.add_node("local_repo", lambda state: local_repo_access(state, config))
    workflow.add_node("local_executor", lambda state: local_executor(state, config))
    workflow.add_node("results_collector", lambda state: results_collector(state, config))
    workflow.add_node("root_cause_analyzer", lambda state: root_cause_analyzer(state, config))
    workflow.add_node("report_generator", lambda state: report_generator(state, config))
    
    # Define the workflow edges
    workflow.set_entry_point("xml_fetcher")
    
    # Add conditional routing based on workflow status
    workflow.add_conditional_edges(
        "xml_fetcher",
        lambda state: "error" if state.get("workflow_status") == "error" else "continue",
        {
            "continue": "local_repo",
            "error": END
        }
    )
    
    workflow.add_conditional_edges(
        "local_repo",
        lambda state: "error" if state.get("workflow_status") == "error" else "continue",
        {
            "continue": "local_executor",
            "error": END
        }
    )
    
    workflow.add_conditional_edges(
        "local_executor",
        lambda state: "error" if state.get("workflow_status") == "error" else "continue",
        {
            "continue": "results_collector",
            "error": "results_collector"
        }
    )
    
    workflow.add_edge("results_collector", "root_cause_analyzer")
    workflow.add_edge("root_cause_analyzer", "report_generator")
    workflow.add_edge("report_generator", END)
    
    # Compile the graph
    return workflow.compile()


def run_failure_analysis(
    xml_report_path: str,
    repo_path: str,
    test_name: str = None,
    config: Config = None
) -> Dict[str, Any]:
    """Run the complete failure analysis workflow.
    
    Args:
        xml_report_path: Path to XML test report
        repo_path: Path to local repository
        test_name: Optional test identifier
        config: Configuration object
        
    Returns:
        Final state with analysis results
    """
    from datetime import datetime
    
    # Create initial state
    initial_state = {
        'xml_report_path': xml_report_path,
        'repo_path': repo_path,
        'test_name': test_name,
        'test_results': None,
        'failure_details': None,
        'code_files': None,
        'local_execution_logs': None,
        'local_exit_code': None,
        'local_errors': None,
        'execution_success': None,
        'collected_data': None,
        'root_cause': None,
        'confidence_level': None,
        'recommendations': None,
        'final_report': None,
        'workflow_status': 'started',
        'error_message': None,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Create and run the graph
    graph = create_failure_analysis_graph(config)
    
    print("🚀 Starting failure analysis workflow...")
    print(f"   XML Report: {xml_report_path}")
    print(f"   Repository: {repo_path}")
    if test_name:
        print(f"   Test Name: {test_name}")
    print()
    
    # Execute the workflow
    final_state = graph.invoke(initial_state)
    
    return final_state
