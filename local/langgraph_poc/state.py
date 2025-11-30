"""State definitions for the LangGraph workflow."""
from typing import TypedDict, Optional, Dict, List, Any


class FailureAnalysisState(TypedDict):
    """State schema for the failure analysis workflow."""
    
    # Input parameters
    xml_report_path: str
    repo_path: str
    test_name: Optional[str]
    
    # Test report data
    test_results: Optional[Dict[str, Any]]
    failure_details: Optional[Dict[str, Any]]
    
    # Repository data
    code_files: Optional[List[str]]
    
    # Local execution results
    local_execution_logs: Optional[str]
    local_exit_code: Optional[int]
    local_errors: Optional[List[str]]
    execution_success: Optional[bool]
    
    # Analysis results
    collected_data: Optional[Dict[str, Any]]
    root_cause: Optional[str]
    confidence_level: Optional[float]
    recommendations: Optional[List[str]]
    
    # Report
    final_report: Optional[str]
    
    # Metadata
    workflow_status: str
    error_message: Optional[str]
    timestamp: str
