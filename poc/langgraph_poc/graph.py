"""LangGraph workflow definition."""
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from . state import FailureAnalysisState
from .config import Config
from .nodes. xml_fetcher import xml_report_fetcher
from .nodes. local_repo_access import local_repo_access
from .nodes.local_executor import local_executor
from .nodes.results_collector import results_collector
from .nodes.root_cause_analyzer import root_cause_analyzer
from .nodes.report_generator import report_generator


def create_failure_analysis_graph(config: Config) -> StateGraph:
    """Create the failure analysis workflow graph. 
    
    Args:
        config: Configuration object
        
    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(FailureAnalysisState)
    
    # Add nodes
    workflow.add_node("fetch_xml", lambda state: xml_report_fetcher(state, config))
    workflow.add_node("access_repo", lambda state: local_repo_access(state, config))
    workflow.add_node("execute_local", lambda state: local_executor(state, config))
    workflow.add_node("collect_results", lambda state: results_collector(state, config))
    workflow.add_node("analyze_root_cause", lambda state: root_cause_analyzer(state, config))
    workflow.add_node("generate_report", lambda state: report_generator(state, config))
    
    # Define edges
    workflow.set_entry_point("fetch_xml")
    workflow.add_edge("fetch_xml", "access_repo")
    workflow.add_edge("access_repo", "execute_local")
    workflow.add_edge("execute_local", "collect_results")
    workflow. add_edge("collect_results", "analyze_root_cause")
    workflow.add_edge("analyze_root_cause", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow. compile()


def run_failure_analysis(
    xml_report_paths: list,
    repo_path: str,
    test_name: str = None,
    config: Config = None,
    verbose: bool = False,
    debug: bool = False
) -> Dict[str, Any]:
    """Run the failure analysis workflow.
    
    Args:
        xml_report_paths: List of paths to XML test report files
        repo_path: Path to local repository
        test_name: Name of the test run (optional)
        config: Configuration object (optional)
        verbose: Enable verbose output
        debug: Enable debug mode
        
    Returns:
        Final state dictionary
    """
    # Load config if not provided
    if config is None:
        config = Config()
    
    # Create initial state
    initial_state = {
        'xml_report_paths': xml_report_paths,
        'repo_path': repo_path,
        'test_name': test_name,
        'verbose': verbose,
        'debug': debug,
        'test_results': None,
        'failure_details': None,
        'repo_files': None,
        'local_output': None,
        'local_errors': None,
        'local_exit_code': None,
        'execution_success': None,
        'collected_data': None,
        'root_cause': None,
        'confidence_level': None,
        'recommendations': None,
        'final_report': None,
        'workflow_status': 'initialized',
        'error_message': None,
        '_debug_logger': None
    }
    
    # Initialize debug logger if needed
    if debug:
        from .debug_logger import DebugLogger
        debug_logger = DebugLogger(config._config, verbose)
        initial_state['_debug_logger'] = debug_logger
    
    # Create and run graph
    graph = create_failure_analysis_graph(config)
    
    # Print workflow info
    print("Starting failure analysis workflow...")
    if len(xml_report_paths) == 1:
        print(f"   XML Report: {xml_report_paths[0]}")
    else:
        print(f"   XML Reports: {len(xml_report_paths)} files")
        for path in xml_report_paths:
            print(f"     - {path}")
    print(f"   Repository: {repo_path}")
    print(f"   Test Name: {test_name or 'N/A'}")
    print()
    
    # Execute workflow
    final_state = graph.invoke(initial_state)
    
    return final_state