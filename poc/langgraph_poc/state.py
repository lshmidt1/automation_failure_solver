"""State definition for failure analysis workflow."""
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import add_messages
from typing_extensions import Annotated


class FailureAnalysisState(TypedDict, total=False):
    """State for failure analysis workflow."""
    
    # Input data - these must persist throughout
    xml_report_paths: List[str]
    repo_path: str
    test_name: Optional[str]
    
    # Configuration
    verbose: Optional[bool]
    debug: Optional[bool]
    
    # Test results from XML
    test_results: Optional[Dict[str, Any]]
    failure_details: Optional[Dict[str, Any]]
    
    # Repository data
    repo_files: Optional[List[str]]
    
    # Local execution results
    local_output: Optional[str]
    local_errors: Optional[List[str]]
    local_exit_code: Optional[int]
    execution_success: Optional[bool]
    
    # Collected data
    collected_data: Optional[Dict[str, Any]]
    
    # Analysis results
    root_cause: Optional[str]
    confidence_level: Optional[float]
    recommendations: Optional[List[str]]
    llm_full_response: Optional[str]
    
    # Final report
    final_report: Optional[str]
    
    # Workflow metadata
    workflow_status: Optional[str]
    error_message: Optional[str]
    
    # Internal
    _debug_logger: Optional[Any]