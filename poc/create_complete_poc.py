"""
Complete LangGraph POC File Creation Script - LOCAL VERSION
Uses local XML files and local repository (no Jenkins, no Azure)
Works on Windows, Mac, and Linux
Run with: python create_complete_poc.py
"""

import os
from pathlib import Path

def create_file(filepath, content):
    """Create a file with the given content."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"   ✅ Created {filepath}")

def main():
    print("🚀 Creating Complete LangGraph POC files (LOCAL VERSION)...")
    print("=" * 70)
    print()
    
    # Create directory structure
    print("📁 Creating directories...")
    Path("langgraph_poc/nodes").mkdir(parents=True, exist_ok=True)
    Path("langgraph_poc/clients").mkdir(parents=True, exist_ok=True)
    Path("config").mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("tests").mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")
    print()
    
    print("📝 Creating files...")
    print()
    
    # ==================== MAIN PACKAGE FILES ====================
    
    create_file("langgraph_poc/__init__.py", '''"""LangGraph POC for Test Failure Analysis."""

__version__ = "0.1.0"

from .graph import create_failure_analysis_graph, run_failure_analysis
from .config import Config
from .state import FailureAnalysisState

__all__ = [
    'create_failure_analysis_graph',
    'run_failure_analysis',
    'Config',
    'FailureAnalysisState',
]
''')
    
    create_file("langgraph_poc/state.py", '''"""State definitions for the LangGraph workflow."""
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
''')
    
    create_file("langgraph_poc/config.py", '''"""Configuration management for the POC."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration manager."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        load_dotenv()
        self.config_path = config_path
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Override with environment variables
        config['llm']['api_key'] = os.getenv('OPENAI_API_KEY', config['llm'].get('api_key'))
        config['llm']['model'] = os.getenv('LLM_MODEL', config['llm'].get('model', 'gpt-4'))
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    @property
    def llm(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self._config.get('llm', {})
    
    @property
    def execution(self) -> Dict[str, Any]:
        """Get execution configuration."""
        return self._config.get('execution', {})
''')
    
    create_file("langgraph_poc/graph.py", '''"""LangGraph workflow definition for failure analysis."""
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
''')
    
    create_file("langgraph_poc/main.py", '''"""Main entry point for the LangGraph POC."""
import argparse
import sys
from pathlib import Path
from .config import Config
from .graph import run_failure_analysis


def main():
    """Main function to run the failure analysis POC."""
    parser = argparse.ArgumentParser(
        description='Analyze test failures using LangGraph (Local XML + Local Repo)'
    )
    parser.add_argument(
        '--xml-report',
        required=True,
        help='Path to XML test report file (e.g., test-results.xml)'
    )
    parser.add_argument(
        '--repo-path',
        required=True,
        help='Path to local repository containing the code'
    )
    parser.add_argument(
        '--test-name',
        help='Optional test identifier/name for reference'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        help='Output file for the analysis report'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate paths
        if not Path(args.xml_report).exists():
            print(f"❌ XML report not found: {args.xml_report}")
            sys.exit(1)
        
        if not Path(args.repo_path).exists():
            print(f"❌ Repository path not found: {args.repo_path}")
            sys.exit(1)
        
        # Load configuration
        print("Loading configuration...")
        config = Config(args.config)
        
        # Run the analysis
        final_state = run_failure_analysis(
            xml_report_path=args.xml_report,
            repo_path=args.repo_path,
            test_name=args.test_name,
            config=config
        )
        
        # Print results
        print("\\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80 + "\\n")
        
        if final_state.get('final_report'):
            print(final_state['final_report'])
            
            # Save to file if requested
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(final_state['final_report'])
                print(f"\\n✅ Report saved to: {args.output}")
        else:
            print("❌ No report generated")
            if final_state.get('error_message'):
                print(f"Error: {final_state['error_message']}")
            sys.exit(1)
        
        print("\\n✅ Analysis workflow completed successfully!")
        
    except Exception as e:
        print(f"\\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
''')
    
    # ==================== CLIENT FILES ====================
    
    create_file("langgraph_poc/clients/__init__.py", '''"""API clients for external services."""

from .xml_reader import XMLReportReader
from .local_repo import LocalRepoClient

__all__ = ['XMLReportReader', 'LocalRepoClient']
''')
    
    create_file("langgraph_poc/clients/xml_reader.py", '''"""XML test report reader for local files."""
from typing import Dict, Any, List, Optional
from pathlib import Path
import xml.etree.ElementTree as ET


class XMLReportReader:
    """Client for reading JUnit-style XML test reports."""
    
    def __init__(self, xml_path: str):
        """Initialize XML reader.
        
        Args:
            xml_path: Path to XML test report file
        """
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")
    
    def parse_report(self) -> Dict[str, Any]:
        """Parse XML test report.
        
        Returns:
            Dictionary containing test results
        """
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            
            # Support both JUnit and pytest XML formats
            test_suites = root.findall('.//testsuite')
            if not test_suites:
                test_suites = [root] if root.tag == 'testsuite' else []
            
            failures = []
            errors = []
            total_tests = 0
            failed_tests = 0
            error_tests = 0
            skipped_tests = 0
            
            for suite in test_suites:
                suite_name = suite.get('name', 'Unknown')
                
                # Get test cases
                for testcase in suite.findall('.//testcase'):
                    total_tests += 1
                    classname = testcase.get('classname', '')
                    name = testcase.get('name', '')
                    time = testcase.get('time', '0')
                    
                    # Check for failures
                    failure = testcase.find('failure')
                    if failure is not None:
                        failed_tests += 1
                        failures.append({
                            'type': 'test_failure',
                            'suite': suite_name,
                            'class': classname,
                            'name': name,
                            'time': time,
                            'message': failure.get('message', ''),
                            'text': failure.text or '',
                            'type_attr': failure.get('type', '')
                        })
                    
                    # Check for errors
                    error = testcase.find('error')
                    if error is not None:
                        error_tests += 1
                        errors.append({
                            'type': 'test_error',
                            'suite': suite_name,
                            'class': classname,
                            'name': name,
                            'time': time,
                            'message': error.get('message', ''),
                            'text': error.text or '',
                            'type_attr': error.get('type', '')
                        })
                    
                    # Check for skipped
                    skipped = testcase.find('skipped')
                    if skipped is not None:
                        skipped_tests += 1
            
            return {
                'total_tests': total_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests,
                'skipped_tests': skipped_tests,
                'passed_tests': total_tests - failed_tests - error_tests - skipped_tests,
                'failures': failures,
                'errors': errors,
                'xml_path': str(self.xml_path)
            }
            
        except ET.ParseError as e:
            raise Exception(f"Failed to parse XML: {str(e)}")
    
    def extract_failure_details(self) -> Dict[str, Any]:
        """Extract detailed failure information.
        
        Returns:
            Dictionary with extracted failure details
        """
        report = self.parse_report()
        
        all_failures = report['failures'] + report['errors']
        
        # Extract error messages
        error_lines = []
        for failure in all_failures:
            if failure.get('message'):
                error_lines.append(f"ERROR: {failure['message']}")
            if failure.get('text'):
                error_lines.extend(failure['text'].split('\\n')[:10])
        
        return {
            'result': 'FAILURE' if all_failures else 'SUCCESS',
            'test_failures': all_failures,
            'error_lines': error_lines[:50],
            'failure_count': len(all_failures),
            'total_tests': report['total_tests'],
            'passed_tests': report['passed_tests'],
            'has_compilation_error': any('compilation' in str(f).lower() for f in all_failures),
            'has_timeout': any('timeout' in str(f).lower() for f in all_failures),
        }
''')
    
    create_file("langgraph_poc/clients/local_repo.py", '''"""Local repository handler."""
from typing import List, Optional
from pathlib import Path


class LocalRepoClient:
    """Client for accessing local repository."""
    
    def __init__(self, repo_path: str):
        """Initialize local repo client.
        
        Args:
            repo_path: Path to local repository
        """
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")
        if not self.repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {repo_path}")
    
    def get_repo_path(self) -> str:
        """Get absolute repository path.
        
        Returns:
            Absolute path to repository
        """
        return str(self.repo_path.absolute())
    
    def list_files(self, extensions: Optional[List[str]] = None) -> List[str]:
        """List files in repository.
        
        Args:
            extensions: List of file extensions to filter (e.g., ['.py', '.js'])
            
        Returns:
            List of relative file paths
        """
        files = []
        
        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file():
                # Skip common ignore patterns
                if any(ignore in file_path.parts for ignore in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']):
                    continue
                    
                if extensions is None or file_path.suffix in extensions:
                    files.append(str(file_path.relative_to(self.repo_path)))
        
        return sorted(files)
    
    def get_file_content(self, relative_path: str) -> str:
        """Get content of a file.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            File content as string
        """
        file_path = self.repo_path / relative_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        return file_path.read_text(encoding='utf-8')
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists in repository.
        
        Args:
            relative_path: Relative path to file
            
        Returns:
            True if file exists
        """
        return (self.repo_path / relative_path).exists()
''')
    
    # ==================== NODE FILES ====================
    
    create_file("langgraph_poc/nodes/__init__.py", '''"""Workflow nodes for failure analysis."""

from .xml_fetcher import xml_report_fetcher
from .local_repo_access import local_repo_access
from .local_executor import local_executor
from .results_collector import results_collector
from .root_cause_analyzer import root_cause_analyzer
from .report_generator import report_generator

__all__ = [
    'xml_report_fetcher',
    'local_repo_access',
    'local_executor',
    'results_collector',
    'root_cause_analyzer',
    'report_generator',
]
''')
    
    create_file("langgraph_poc/nodes/xml_fetcher.py", '''"""Node for fetching test results from XML."""
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
''')
    
    create_file("langgraph_poc/nodes/local_repo_access.py", '''"""Node for accessing local repository."""
from typing import Dict, Any
from ..state import FailureAnalysisState
from ..clients.local_repo import LocalRepoClient
from ..config import Config


def local_repo_access(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Access local repository.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("📦 Accessing local repository...")
    
    try:
        # Initialize local repo client
        client = LocalRepoClient(state['repo_path'])
        
        # Get repository path
        repo_path = client.get_repo_path()
        
        # List relevant files
        execution_config = config.execution
        extensions = execution_config.get('file_extensions', ['.py', '.js', '.sh', '.yaml'])
        code_files = client.list_files(extensions=extensions)
        
        print(f"✅ Successfully accessed repository: {repo_path}")
        print(f"   Files found: {len(code_files)}")
        
        return {
            'code_files': code_files,
            'workflow_status': 'repo_accessed'
        }
        
    except Exception as e:
        print(f"❌ Failed to access local repository: {str(e)}")
        return {
            'workflow_status': 'error',
            'error_message': f"Local repo access failed: {str(e)}"
        }
''')
    
    create_file("langgraph_poc/nodes/local_executor.py", '''"""Node for executing code locally."""
import subprocess
import os
from typing import Dict, Any
from pathlib import Path
from ..state import FailureAnalysisState
from ..config import Config


def local_executor(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Execute automation code locally.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("🔧 Executing code locally...")
    
    try:
        execution_config = config.execution
        repo_path = state['repo_path']
        
        # Change to repository directory
        original_dir = os.getcwd()
        os.chdir(repo_path)
        
        errors = []
        logs = []
        exit_code = 0
        
        try:
            # Install dependencies if needed
            if execution_config.get('install_dependencies', True):
                print("   Installing dependencies...")
                if Path('requirements.txt').exists():
                    result = subprocess.run(
                        ['pip', 'install', '-r', 'requirements.txt'],
                        capture_output=True,
                        text=True,
                        timeout=execution_config.get('dependency_timeout', 300)
                    )
                    logs.append(f"Dependency installation:\\n{result.stdout}")
                    if result.returncode != 0:
                        errors.append(f"Dependency installation failed: {result.stderr}")
                
                if Path('package.json').exists():
                    result = subprocess.run(
                        ['npm', 'install'],
                        capture_output=True,
                        text=True,
                        timeout=execution_config.get('dependency_timeout', 300)
                    )
                    logs.append(f"NPM installation:\\n{result.stdout}")
                    if result.returncode != 0:
                        errors.append(f"NPM installation failed: {result.stderr}")
            
            # Execute test command
            test_command = execution_config.get('test_command', 'pytest')
            print(f"   Running: {test_command}")
            
            result = subprocess.run(
                test_command.split(),
                capture_output=True,
                text=True,
                timeout=execution_config.get('execution_timeout', 600)
            )
            
            logs.append(f"Test execution:\\n{result.stdout}\\n{result.stderr}")
            exit_code = result.returncode
            
            if exit_code != 0:
                errors.append(f"Tests failed with exit code {exit_code}")
                errors.append(result.stderr)
            
        finally:
            os.chdir(original_dir)
        
        execution_success = exit_code == 0 and len(errors) == 0
        
        print(f"{'✅' if execution_success else '❌'} Local execution completed")
        print(f"   Exit code: {exit_code}")
        print(f"   Errors: {len(errors)}")
        
        return {
            'local_execution_logs': '\\n'.join(logs),
            'local_exit_code': exit_code,
            'local_errors': errors,
            'execution_success': execution_success,
            'workflow_status': 'executed_locally'
        }
        
    except subprocess.TimeoutExpired:
        print("❌ Local execution timed out")
        return {
            'local_execution_logs': 'Execution timed out',
            'local_exit_code': -1,
            'local_errors': ['Execution timeout'],
            'execution_success': False,
            'workflow_status': 'error',
            'error_message': 'Local execution timed out'
        }
    except Exception as e:
        print(f"❌ Local execution failed: {str(e)}")
        return {
            'local_execution_logs': str(e),
            'local_exit_code': -1,
            'local_errors': [str(e)],
            'execution_success': False,
            'workflow_status': 'error',
            'error_message': f'Local execution failed: {str(e)}'
        }
''')
    
    create_file("langgraph_poc/nodes/results_collector.py", '''"""Node for collecting all results."""
from typing import Dict, Any
from ..state import FailureAnalysisState
from ..config import Config


def results_collector(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Collect all results from previous nodes.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("📊 Collecting results...")
    
    collected_data = {
        'test_report': {
            'xml_path': state['xml_report_path'],
            'test_name': state.get('test_name', 'N/A'),
            'result': state['failure_details']['result'] if state.get('failure_details') else None,
            'failure_details': state.get('failure_details'),
            'total_tests': state.get('test_results', {}).get('total_tests', 0),
        },
        'repository': {
            'path': state.get('repo_path'),
            'file_count': len(state.get('code_files', [])),
        },
        'local_execution': {
            'success': state.get('execution_success'),
            'exit_code': state.get('local_exit_code'),
            'error_count': len(state.get('local_errors', [])),
            'log_length': len(state.get('local_execution_logs', '')),
        },
        'comparison': {
            'xml_failed': state.get('failure_details', {}).get('result') != 'SUCCESS',
            'local_failed': not state.get('execution_success', False),
            'consistent_failure': (
                state.get('failure_details', {}).get('result') != 'SUCCESS' and
                not state.get('execution_success', False)
            ),
        }
    }
    
    print("✅ Results collected")
    print(f"   XML failures: {collected_data['test_report']['failure_details']['failure_count'] if collected_data['test_report']['failure_details'] else 0}")
    print(f"   Local execution: {'Failed' if collected_data['local_execution']['exit_code'] != 0 else 'Passed'}")
    print(f"   Consistent failure: {collected_data['comparison']['consistent_failure']}")
    
    return {
        'collected_data': collected_data,
        'workflow_status': 'results_collected'
    }
''')
    
    create_file("langgraph_poc/nodes/root_cause_analyzer.py", '''"""Node for analyzing root cause using LLM."""
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
        
        error_lines = '\\n'.join(failure_details.get('error_lines', [])[:20])
        local_errors = '\\n'.join(state.get('local_errors', [])[:10])
        
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
        lines = analysis_text.split('\\n')
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
''')
    
    create_file("langgraph_poc/nodes/report_generator.py", '''"""Node for generating final report."""
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
                output.append(f"\\n**Test Failures:** {len(test_failures)}\\n")
                for i, failure in enumerate(test_failures[:5], 1):
                    output.append(f"{i}. **{failure.get('name')}**")
                    output.append(f"   - Class: `{failure.get('class')}`")
                    if failure.get('message'):
                        output.append(f"   - Message: {failure.get('message')[:200]}")
            
            if failure_details.get('has_compilation_error'):
                output.append("\\n⚠️ **Compilation Error Detected**")
            
            if failure_details.get('has_timeout'):
                output.append("\\n⏱️ **Timeout Detected**")
            
            return '\\n'.join(output) if output else "No specific failures identified."
        
        def format_local_errors(errors: list) -> str:
            if not errors:
                return ""
            
            output = ["\\n**Local Error Details:**\\n"]
            for i, error in enumerate(errors[:5], 1):
                output.append(f"{i}. ```\\n{error[:500]}\\n```")
            
            if len(errors) > 5:
                output.append(f"\\n*... and {len(errors) - 5} more errors*")
            
            return '\\n'.join(output)
        
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
            
            return '\\n'.join(output)
        
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
''')
    
    # ==================== CONFIGURATION FILES ====================
    
    create_file("config/config.example.yaml", '''# LLM Configuration
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.3
  max_tokens: 2000

# Execution Configuration
execution:
  install_dependencies: true
  dependency_timeout: 300  # seconds
  execution_timeout: 600  # seconds
  test_command: "pytest -v"  # Default test command
  environment: "sandbox"
  file_extensions:
    - ".py"
    - ".js"
    - ".sh"
    - ".ps1"
    - ".yaml"
    - ".yml"
  
# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
''')
    
    create_file("config/.env.example", '''# LLM API Keys
OPENAI_API_KEY=your-openai-api-key

# Optional: Override LLM model
# LLM_MODEL=gpt-4-turbo
''')
    
    # ==================== DOCUMENTATION ====================
    
    readme_content = """# LangGraph POC: Test Failure Analyzer (Local Version)

## Overview
This POC uses LangGraph to create an automated workflow that:
1. Reads test failures from local XML reports
2. Accesses local repository code
3. Reruns failed tests locally
4. Analyzes results using LLM to determine root cause

## Key Features

- Local XML test report parsing (JUnit/pytest format)
- Local repository access (no cloud dependencies)
- Automated test re-execution
- LLM-powered root cause analysis
- Detailed failure comparison
- Comprehensive markdown reports

## Architecture

Workflow: XML Report Reader → Local Repo Access → Local Executor → Results Collector → Root Cause Analyzer → Report Generator

## Setup

### 1. Install Dependencies

    pip install -r requirements.txt

### 2. Configure Environment

    cp config/.env.example .env

Edit .env with your OpenAI API key.

### 3. Configure Settings

    cp config/config.example.yaml config/config.yaml

Edit config/config.yaml with your preferences.

## Usage

### Basic Command

    python -m langgraph_poc.main --xml-report path/to/test-results.xml --repo-path path/to/your/repo --output reports/analysis.md

### With Test Name

    python -m langgraph_poc.main --xml-report results.xml --repo-path . --test-name "MyTestSuite" --output report.md

### Command-Line Arguments

- --xml-report (required): Path to XML test report file
- --repo-path (required): Path to local repository
- --test-name (optional): Test identifier for reference
- --config (optional): Path to config file (default: config/config.yaml)
- --output (optional): Output file path for the report

## XML Report Format

The tool supports standard JUnit XML format:

    <testsuite name="MyTests" tests="10" failures="2">
      <testcase classname="test.MyTest" name="test_example" time="0.5">
        <failure message="AssertionError">
          Detailed error message here
        </failure>
      </testcase>
    </testsuite>

## Example Workflow

1. Run your tests and generate XML report:

    pytest --junitxml=test-results.xml

2. Analyze failures:

    python -m langgraph_poc.main --xml-report test-results.xml --repo-path . --output analysis.md

3. Review the generated report in analysis.md

## Components

### XML Report Reader
- Parses JUnit/pytest XML format
- Extracts failure details
- Counts test statistics

### Local Repo Client
- Accesses local file system
- Lists relevant code files
- No Git operations required

### Local Executor
- Reruns tests in same environment
- Captures execution logs
- Compares with original failures

### Root Cause Analyzer
- Uses GPT-4 for analysis
- Compares XML vs local results
- Provides confidence scores

### Report Generator
- Creates detailed markdown reports
- Includes actionable recommendations
- Highlights inconsistencies

## Configuration

### LLM Settings (config/config.yaml)

    llm:
      provider: "openai"
      model: "gpt-4"
      temperature: 0.3

### Execution Settings

    execution:
      install_dependencies: true
      test_command: "pytest -v"
      execution_timeout: 600

## Troubleshooting

### XML Parsing Errors
- Verify XML is valid JUnit format
- Check file path is correct
- Ensure XML contains test results

### Execution Failures
- Check dependencies are installed
- Verify test command in config
- Review timeout settings

### LLM Issues
- Verify OpenAI API key in .env
- Check API rate limits
- Ensure sufficient API credits

## Output Report Sections

1. Summary - Test statistics and results
2. Repository Info - Code location and files
3. Failure Details - From XML and local execution
4. Comparison - Consistency analysis
5. Root Cause - LLM-powered analysis with confidence
6. Recommendations - Actionable next steps

## Requirements

- Python 3.8+
- OpenAI API key
- Local test results in XML format
- Access to test repository

## Benefits

- No external service dependencies (Jenkins, Azure, etc.)
- Works completely offline (except LLM calls)
- Easy to test and debug
- Fast iteration cycle
- Privacy-friendly (data stays local)

## Limitations

- Requires valid XML test reports
- LLM analysis needs internet connection
- Local execution must be possible
- Memory usage for large repos

## Future Enhancements

- Support for other XML formats
- Multiple LLM provider support
- Caching for faster re-analysis
- Historical failure tracking
- Integration with CI/CD pipelines

## License

This is a proof-of-concept tool for internal use.
"""
    
    create_file("README_POC.md", readme_content)
    
    # ==================== REQUIREMENTS ====================
    
    requirements_content = '''# LangGraph POC Dependencies (Local Version)
langgraph>=0.2.0
langchain>=0.1.0
langchain-openai>=0.0.5
pyyaml>=6.0
python-dotenv>=1.0.0
pydantic>=2.5.0
'''
    
    req_path = Path("requirements.txt")
    if req_path.exists():
        existing = req_path.read_text()
        if "langgraph" not in existing:
            with open("requirements.txt", "a") as f:
                f.write("\n" + requirements_content)
            print("   ✅ Updated existing requirements.txt")
        else:
            print("   ℹ️  requirements.txt already contains LangGraph dependencies")
    else:
        req_path.write_text(requirements_content.strip())
        print("   ✅ Created requirements.txt")
    
    # ==================== GITIGNORE ====================
    
    gitignore_additions = '''
# LangGraph POC
config/config.yaml
.env
reports/
*.xml
langgraph_poc/**/__pycache__/
*.pyc
__pycache__/
.pytest_cache/
'''
    
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        if "LangGraph POC" not in existing:
            with open(".gitignore", "a") as f:
                f.write(gitignore_additions)
            print("   ✅ Updated .gitignore")
        else:
            print("   ℹ️  .gitignore already contains POC entries")
    else:
        gitignore_path.write_text(gitignore_additions.strip())
        print("   ✅ Created .gitignore")
    
    # ==================== SAMPLE TEST XML ====================
    
    sample_xml = '''<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="2" skipped="0" tests="5" time="1.234">
  <testcase classname="tests.test_example" name="test_success" time="0.123"/>
  <testcase classname="tests.test_example" name="test_another_success" time="0.234"/>
  <testcase classname="tests.test_example" name="test_failure_one" time="0.345">
    <failure message="AssertionError: Expected 5 but got 3">
AssertionError: Expected 5 but got 3
    at test_example.py:15
    </failure>
  </testcase>
  <testcase classname="tests.test_example" name="test_failure_two" time="0.456">
    <failure message="ValueError: Invalid input">
ValueError: Invalid input
    at test_example.py:23
    </failure>
  </testcase>
  <testcase classname="tests.test_example" name="test_yet_another_success" time="0.076"/>
</testsuite>
'''
    
    create_file("tests/sample-test-results.xml", sample_xml)
    
    # ==================== COMPLETION MESSAGE ====================
    
    print()
    print("=" * 70)
    print("✅ ALL FILES CREATED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("📋 Created Files:")
    print()
    print("Core Files:")
    print("  ✅ langgraph_poc/__init__.py")
    print("  ✅ langgraph_poc/state.py")
    print("  ✅ langgraph_poc/config.py")
    print("  ✅ langgraph_poc/graph.py")
    print("  ✅ langgraph_poc/main.py")
    print()
    print("Client Files:")
    print("  ✅ langgraph_poc/clients/__init__.py")
    print("  ✅ langgraph_poc/clients/xml_reader.py")
    print("  ✅ langgraph_poc/clients/local_repo.py")
    print()
    print("Node Files:")
    print("  ✅ langgraph_poc/nodes/__init__.py")
    print("  ✅ langgraph_poc/nodes/xml_fetcher.py")
    print("  ✅ langgraph_poc/nodes/local_repo_access.py")
    print("  ✅ langgraph_poc/nodes/local_executor.py")
    print("  ✅ langgraph_poc/nodes/results_collector.py")
    print("  ✅ langgraph_poc/nodes/root_cause_analyzer.py")
    print("  ✅ langgraph_poc/nodes/report_generator.py")
    print()
    print("Configuration:")
    print("  ✅ config/config.example.yaml")
    print("  ✅ config/.env.example")
    print()
    print("Documentation:")
    print("  ✅ README_POC.md")
    print("  ✅ requirements.txt")
    print("  ✅ .gitignore")
    print()
    print("Sample Data:")
    print("  ✅ tests/sample-test-results.xml")
    print()
    print("=" * 70)
    print("📋 NEXT STEPS:")
    print("=" * 70)
    print()
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("2. Configure your credentials:")
    print("   cp config/.env.example .env")
    print("   # Edit .env with your OpenAI API key")
    print()
    print("3. Configure settings:")
    print("   cp config/config.example.yaml config/config.yaml")
    print("   # Edit config/config.yaml if needed")
    print()
    print("4. Test the setup:")
    print("   python -m langgraph_poc.main --help")
    print()
    print("5. Try with sample data:")
    print("   python -m langgraph_poc.main \\")
    print("     --xml-report tests/sample-test-results.xml \\")
    print("     --repo-path . \\")
    print("     --test-name 'Sample Test' \\")
    print("     --output reports/sample-analysis.md")
    print()
    print("=" * 70)
    print("🎉 SETUP COMPLETE! Happy analyzing!")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()