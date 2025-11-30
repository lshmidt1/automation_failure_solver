"""
Complete LangGraph POC File Creation Script
Works on Windows, Mac, and Linux
Run with: python create_all_files.py
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
    print("🚀 Creating LangGraph POC files...")
    print("=" * 60)
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
    
    # ========== Main Package Files ==========
    
    create_file("langgraph_poc/__init__.py", '''"""LangGraph POC for Jenkins Automation Failure Analysis."""

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
from datetime import datetime


class FailureAnalysisState(TypedDict):
    """State schema for the failure analysis workflow."""
    
    # Input parameters
    jenkins_url: str
    jenkins_job: str
    build_number: int
    azure_repo_url: str
    azure_project: str
    
    # Jenkins data
    jenkins_logs: Optional[str]
    build_info: Optional[Dict[str, Any]]
    failure_details: Optional[Dict[str, Any]]
    
    # Azure repository data
    repo_path: Optional[str]
    commit_sha: Optional[str]
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
        config['jenkins']['username'] = os.getenv('JENKINS_USERNAME', config['jenkins'].get('username'))
        config['jenkins']['api_token'] = os.getenv('JENKINS_API_TOKEN', config['jenkins'].get('api_token'))
        config['jenkins']['base_url'] = os.getenv('JENKINS_URL', config['jenkins'].get('base_url'))
        
        config['azure']['pat_token'] = os.getenv('AZURE_PAT_TOKEN', config['azure'].get('pat_token'))
        config['azure']['organization'] = os.getenv('AZURE_ORG', config['azure'].get('organization'))
        
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
    def jenkins(self) -> Dict[str, Any]:
        """Get Jenkins configuration."""
        return self._config.get('jenkins', {})
    
    @property
    def azure(self) -> Dict[str, Any]:
        """Get Azure configuration."""
        return self._config.get('azure', {})
    
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
from .nodes.jenkins_fetcher import jenkins_log_fetcher
from .nodes.azure_repo import azure_repo_access
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
    workflow.add_node("jenkins_fetcher", lambda state: jenkins_log_fetcher(state, config))
    workflow.add_node("azure_repo", lambda state: azure_repo_access(state, config))
    workflow.add_node("local_executor", lambda state: local_executor(state, config))
    workflow.add_node("results_collector", lambda state: results_collector(state, config))
    workflow.add_node("root_cause_analyzer", lambda state: root_cause_analyzer(state, config))
    workflow.add_node("report_generator", lambda state: report_generator(state, config))
    
    # Define the workflow edges
    workflow.set_entry_point("jenkins_fetcher")
    
    # Add conditional routing based on workflow status
    workflow.add_conditional_edges(
        "jenkins_fetcher",
        lambda state: "error" if state.get("workflow_status") == "error" else "continue",
        {
            "continue": "azure_repo",
            "error": END
        }
    )
    
    workflow.add_conditional_edges(
        "azure_repo",
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
            "error": "results_collector"  # Still collect partial results even on error
        }
    )
    
    workflow.add_edge("results_collector", "root_cause_analyzer")
    workflow.add_edge("root_cause_analyzer", "report_generator")
    workflow.add_edge("report_generator", END)
    
    # Compile the graph
    return workflow.compile()


def run_failure_analysis(
    jenkins_url: str,
    jenkins_job: str,
    build_number: int,
    azure_repo_url: str,
    azure_project: str,
    config: Config
) -> Dict[str, Any]:
    """Run the complete failure analysis workflow.
    
    Args:
        jenkins_url: Jenkins server URL
        jenkins_job: Jenkins job name
        build_number: Build number to analyze
        azure_repo_url: Azure DevOps repository URL
        azure_project: Azure DevOps project name
        config: Configuration object
        
    Returns:
        Final state with analysis results
    """
    from datetime import datetime
    
    # Create initial state
    initial_state = {
        'jenkins_url': jenkins_url,
        'jenkins_job': jenkins_job,
        'build_number': build_number,
        'azure_repo_url': azure_repo_url,
        'azure_project': azure_project,
        'jenkins_logs': None,
        'build_info': None,
        'failure_details': None,
        'repo_path': None,
        'commit_sha': None,
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
    print(f"   Jenkins Job: {jenkins_job}")
    print(f"   Build: #{build_number}")
    print(f"   Azure Project: {azure_project}")
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
from .clients.azure_client import AzureDevOpsClient


def main():
    """Main function to run the failure analysis POC."""
    parser = argparse.ArgumentParser(
        description='Analyze Jenkins automation failures using LangGraph'
    )
    parser.add_argument(
        '--jenkins-job',
        required=True,
        help='Jenkins job name'
    )
    parser.add_argument(
        '--build-number',
        type=int,
        required=True,
        help='Jenkins build number to analyze'
    )
    parser.add_argument(
        '--jenkins-url',
        help='Jenkins server URL (optional, uses config default)'
    )
    parser.add_argument(
        '--azure-project',
        required=True,
        help='Azure DevOps project name'
    )
    parser.add_argument(
        '--azure-repo-url',
        help='Azure DevOps repository URL (optional)'
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
        # Load configuration
        print("Loading configuration...")
        config = Config(args.config)
        
        # Use config defaults if not provided
        jenkins_url = args.jenkins_url or config.jenkins['base_url']
        azure_repo_url = args.azure_repo_url or config.azure.get('repository_url', '')
        
        # Run the analysis
        final_state = run_failure_analysis(
            jenkins_url=jenkins_url,
            jenkins_job=args.jenkins_job,
            build_number=args.build_number,
            azure_repo_url=azure_repo_url,
            azure_project=args.azure_project,
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
        
        # Cleanup
        if final_state.get('repo_path'):
            print(f"\\nCleaning up repository: {final_state['repo_path']}")
            AzureDevOpsClient.cleanup_repo(final_state['repo_path'])
        
        print("\\n✅ Analysis workflow completed successfully!")
        
    except Exception as e:
        print(f"\\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
''')
    
    # ========== Client Files ==========
    
    create_file("langgraph_poc/clients/__init__.py", '''"""API clients for external services."""

from .jenkins_client import JenkinsClient
from .azure_client import AzureDevOpsClient

__all__ = ['JenkinsClient', 'AzureDevOpsClient']
''')
    
    create_file("langgraph_poc/clients/jenkins_client.py", '''"""Jenkins API client for fetching build logs and information."""
import jenkins
from typing import Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth


class JenkinsClient:
    """Client for interacting with Jenkins API."""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        """Initialize Jenkins client.
        
        Args:
            base_url: Jenkins server URL
            username: Jenkins username
            api_token: Jenkins API token
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.server = jenkins.Jenkins(base_url, username=username, password=api_token)
        
    def get_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """Get build information.
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number
            
        Returns:
            Dictionary containing build information
        """
        try:
            build_info = self.server.get_build_info(job_name, build_number)
            return {
                'number': build_info['number'],
                'result': build_info['result'],
                'duration': build_info['duration'],
                'timestamp': build_info['timestamp'],
                'url': build_info['url'],
                'building': build_info['building'],
                'actions': build_info.get('actions', []),
                'changeSet': build_info.get('changeSet', {}),
            }
        except jenkins.JenkinsException as e:
            raise Exception(f"Failed to get build info: {str(e)}")
    
    def get_console_log(self, job_name: str, build_number: int) -> str:
        """Get console log for a build.
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number
            
        Returns:
            Console log as string
        """
        try:
            return self.server.get_build_console_output(job_name, build_number)
        except jenkins.JenkinsException as e:
            raise Exception(f"Failed to get console log: {str(e)}")
    
    def get_test_report(self, job_name: str, build_number: int) -> Optional[Dict[str, Any]]:
        """Get test report for a build.
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number
            
        Returns:
            Test report dictionary or None if not available
        """
        try:
            url = f"{self.base_url}/job/{job_name}/{build_number}/testReport/api/json"
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.username, self.api_token)
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    def extract_failure_details(self, build_info: Dict[str, Any], 
                               console_log: str,
                               test_report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract failure details from build data.
        
        Args:
            build_info: Build information
            console_log: Console log
            test_report: Test report
            
        Returns:
            Dictionary with extracted failure details
        """
        failures = []
        
        # Extract from test report
        if test_report:
            for suite in test_report.get('suites', []):
                for case in suite.get('cases', []):
                    if case.get('status') in ['FAILED', 'REGRESSION']:
                        failures.append({
                            'type': 'test_failure',
                            'name': case.get('name'),
                            'class': case.get('className'),
                            'message': case.get('errorDetails'),
                            'stackTrace': case.get('errorStackTrace')
                        })
        
        # Extract errors from console log
        error_patterns = ['ERROR', 'FAILED', 'Exception', 'Error:']
        log_lines = console_log.split('\\n')
        error_lines = [line for line in log_lines if any(pattern in line for pattern in error_patterns)]
        
        return {
            'result': build_info.get('result'),
            'test_failures': failures,
            'error_lines': error_lines[:50],  # Limit to first 50 error lines
            'failure_count': len(failures),
            'has_compilation_error': 'compilation' in console_log.lower(),
            'has_timeout': 'timeout' in console_log.lower(),
        }
''')
    
    create_file("langgraph_poc/clients/azure_client.py", '''"""Azure DevOps client for accessing repositories."""
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from typing import Optional, List
import git
import tempfile
import shutil
from pathlib import Path


class AzureDevOpsClient:
    """Client for interacting with Azure DevOps."""
    
    def __init__(self, organization_url: str, pat_token: str):
        """Initialize Azure DevOps client.
        
        Args:
            organization_url: Azure DevOps organization URL
            pat_token: Personal Access Token
        """
        self.organization_url = organization_url
        self.pat_token = pat_token
        credentials = BasicAuthentication('', pat_token)
        self.connection = Connection(base_url=organization_url, creds=credentials)
        self.git_client = self.connection.clients.get_git_client()
        
    def clone_repository(self, project: str, repo_name: str, 
                        branch: Optional[str] = None,
                        target_dir: Optional[str] = None) -> str:
        """Clone a repository from Azure DevOps.
        
        Args:
            project: Project name
            repo_name: Repository name
            branch: Branch name (default: main/master)
            target_dir: Target directory for cloning
            
        Returns:
            Path to cloned repository
        """
        try:
            # Get repository info
            repo = self.git_client.get_repository(project=project, repository_id=repo_name)
            
            # Construct clone URL with PAT
            clone_url = repo.remote_url
            clone_url_with_auth = clone_url.replace('https://', f'https://{self.pat_token}@')
            
            # Create temp directory if not provided
            if target_dir is None:
                target_dir = tempfile.mkdtemp(prefix='azure_repo_')
            else:
                Path(target_dir).mkdir(parents=True, exist_ok=True)
            
            # Clone repository
            repo_obj = git.Repo.clone_from(clone_url_with_auth, target_dir)
            
            # Checkout specific branch if provided
            if branch and branch != repo_obj.active_branch.name:
                repo_obj.git.checkout(branch)
            
            return target_dir
            
        except Exception as e:
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    def get_commit_info(self, project: str, repo_name: str, commit_id: str):
        """Get commit information.
        
        Args:
            project: Project name
            repo_name: Repository name
            commit_id: Commit SHA
            
        Returns:
            Commit information
        """
        try:
            commit = self.git_client.get_commit(
                commit_id=commit_id,
                repository_id=repo_name,
                project=project
            )
            return {
                'commit_id': commit.commit_id,
                'author': commit.author.name,
                'message': commit.comment,
                'date': commit.author.date,
                'changes': len(commit.changes) if hasattr(commit, 'changes') else 0
            }
        except Exception as e:
            raise Exception(f"Failed to get commit info: {str(e)}")
    
    def list_files(self, repo_path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """List files in cloned repository.
        
        Args:
            repo_path: Path to cloned repository
            extensions: List of file extensions to filter (e.g., ['.py', '.js'])
            
        Returns:
            List of file paths
        """
        files = []
        repo_path_obj = Path(repo_path)
        
        for file_path in repo_path_obj.rglob('*'):
            if file_path.is_file():
                # Skip .git directory
                if '.git' in file_path.parts:
                    continue
                    
                if extensions is None or file_path.suffix in extensions:
                    files.append(str(file_path.relative_to(repo_path_obj)))
        
        return files
    
    @staticmethod
    def cleanup_repo(repo_path: str):
        """Clean up cloned repository.
        
        Args:
            repo_path: Path to repository to clean up
        """
        if Path(repo_path).exists():
            shutil.rmtree(repo_path)
''')
    
    # ========== Node Files ==========
    
    create_file("langgraph_poc/nodes/__init__.py", '''"""Workflow nodes for failure analysis."""

from .jenkins_fetcher import jenkins_log_fetcher
from .azure_repo import azure_repo_access
from .local_executor import local_executor
from .results_collector import results_collector
from .root_cause_analyzer import root_cause_analyzer
from .report_generator import report_generator

__all__ = [
    'jenkins_log_fetcher',
    'azure_repo_access',
    'local_executor',
    'results_collector',
    'root_cause_analyzer',
    'report_generator',
]
''')
    
    create_file("langgraph_poc/nodes/jenkins_fetcher.py", '''"""Node for fetching Jenkins logs and build information."""
from typing import Dict, Any
from ..state import FailureAnalysisState
from ..clients.jenkins_client import JenkinsClient
from ..config import Config


def jenkins_log_fetcher(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Fetch logs and information from Jenkins.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("📥 Fetching Jenkins build logs...")
    
    try:
        # Initialize Jenkins client
        jenkins_config = config.jenkins
        client = JenkinsClient(
            base_url=state['jenkins_url'] or jenkins_config['base_url'],
            username=jenkins_config['username'],
            api_token=jenkins_config['api_token']
        )
        
        # Get build information
        build_info = client.get_build_info(
            state['jenkins_job'],
            state['build_number']
        )
        
        # Get console log
        console_log = client.get_console_log(
            state['jenkins_job'],
            state['build_number']
        )
        
        # Get test report if available
        test_report = client.get_test_report(
            state['jenkins_job'],
            state['build_number']
        )
        
        # Extract failure details
        failure_details = client.extract_failure_details(
            build_info,
            console_log,
            test_report
        )
        
        print(f"✅ Successfully fetched build #{state['build_number']}")
        print(f"   Result: {build_info['result']}")
        print(f"   Failures: {failure_details['failure_count']}")
        
        return {
            'jenkins_logs': console_log,
            'build_info': build_info,
            'failure_details': failure_details,
            'workflow_status': 'jenkins_fetched'
        }
        
    except Exception as e:
        print(f"❌ Failed to fetch Jenkins data: {str(e)}")
        return {
            'workflow_status': 'error',
            'error_message': f"Jenkins fetch failed: {str(e)}"
        }
''')
    
    create_file("langgraph_poc/nodes/azure_repo.py", '''"""Node for accessing Azure DevOps repository."""
from typing import Dict, Any
from ..state import FailureAnalysisState
from ..clients.azure_client import AzureDevOpsClient
from ..config import Config


def azure_repo_access(state: FailureAnalysisState, config: Config) -> Dict[str, Any]:
    """Access and clone Azure DevOps repository.
    
    Args:
        state: Current workflow state
        config: Configuration object
        
    Returns:
        Updated state dictionary
    """
    print("📦 Accessing Azure DevOps repository...")
    
    try:
        # Initialize Azure client
        azure_config = config.azure
        client = AzureDevOpsClient(
            organization_url=azure_config['organization_url'],
            pat_token=azure_config['pat_token']
        )
        
        # Extract commit SHA from Jenkins build if available
        commit_sha = None
        if state.get('build_info'):
            change_set = state['build_info'].get('changeSet', {})
            if change_set and 'items' in change_set and len(change_set['items']) > 0:
                commit_sha = change_set['items'][0].get('commitId')
        
        # Clone repository
        repo_path = client.clone_repository(
            project=state['azure_project'],
            repo_name=azure_config['repository'],
            branch=azure_config.get('default_branch')
        )
        
        # List relevant files
        code_files = client.list_files(
            repo_path,
            extensions=azure_config.get('file_extensions')
        )
        
        print(f"✅ Successfully cloned repository to: {repo_path}")
        print(f"   Files found: {len(code_files)}")
        if commit_sha:
            print(f"   Commit: {commit_sha[:8]}")
        
        return {
            'repo_path': repo_path,
            'commit_sha': commit_sha,
            'code_files': code_files,
            'workflow_status': 'repo_accessed'
        }
        
    except Exception as e:
        print(f"❌ Failed to access Azure repository: {str(e)}")
        return {
            'workflow_status': 'error',
            'error_message': f"Azure repo access failed: {str(e)}"
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
        'jenkins': {
            'job': state['jenkins_job'],
            'build_number': state['build_number'],
            'result': state['build_info']['result'] if state.get('build_info') else None,
            'failure_details': state.get('failure_details'),
            'console_log_length': len(state.get('jenkins_logs', '')),
        },
        'repository': {
            'path': state.get('repo_path'),
            'commit_sha': state.get('commit_sha'),
            'file_count': len(state.get('code_files', [])),
        },
        'local_execution': {
            'success': state.get('execution_success'),
            'exit_code': state.get('local_exit_code'),
            'error_count': len(state.get('local_errors', [])),
            'log_length': len(state.get('local_execution_logs', '')),
        },
        'comparison': {
            'jenkins_failed': state.get('failure_details', {}).get('result') != 'SUCCESS',
            'local_failed': not state.get('execution_success', False),
            'consistent_failure': (
                state.get('failure_details', {}).get('result') != 'SUCCESS' and
                not state.get('execution_success', False)
            ),
        }
    }
    
    print("✅ Results collected")
    print(f"   Jenkins failures: {collected_data['jenkins']['failure_details']['failure_count'] if collected_data['jenkins']['failure_details'] else 0}")
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
Your task is to identify the root cause of failures by comparing Jenkins logs with local execution results.
Provide a detailed analysis with:
1. Root cause identification
2. Confidence level (0-1)
3. Specific recommendations for fixing the issue
4. Whether the issue is environment-related, code-related, or infrastructure-related
"""),
            ("user", """Analyze this test failure:

JENKINS BUILD INFO:
Job: {jenkins_job}
Build: #{build_number}
Result: {result}
Failure Count: {failure_count}

JENKINS FAILURE DETAILS:
{failure_details}

JENKINS ERROR LINES (first 20):
{jenkins_errors}

LOCAL EXECUTION:
Exit Code: {local_exit_code}
Success: {local_success}
Error Count: {local_error_count}

LOCAL ERRORS:
{local_errors}

COMPARISON:
- Jenkins Failed: {jenkins_failed}
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
        
        jenkins_errors = '\\n'.join(failure_details.get('error_lines', [])[:20])
        local_errors = '\\n'.join(state.get('local_errors', [])[:10])
        
        # Get analysis from LLM
        chain = prompt | llm
        response = chain.invoke({
            'jenkins_job': state['jenkins_job'],
            'build_number': state['build_number'],
            'result': collected_data['jenkins']['result'],
            'failure_count': failure_details.get('failure_count', 0),
            'failure_details': str(failure_details.get('test_failures', [])[:5]),
            'jenkins_errors': jenkins_errors,
            'local_exit_code': state.get('local_exit_code'),
            'local_success': state.get('execution_success'),
            'local_error_count': len(state.get('local_errors', [])),
            'local_errors': local_errors,
            'jenkins_failed': collected_data['comparison']['jenkins_failed'],
            'local_failed': collected_data['comparison']['local_failed'],
            'consistent_failure': collected_data['comparison']['consistent_failure'],
        })
        
        analysis_text = response.content
        
        # Parse response (simplified - in production, use structured output)
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
                # Try to extract confidence value
                try:
                    conf_str = line.split(':')[1].strip()
                    confidence = float(conf_str.replace('%', '').strip()) / 100 if '%' in conf_str else float(conf_str)
                except:
                    pass
            elif 'recommendation' in line.lower() and ':' in line:
                current_section = 'recommendations'
            elif current_section == 'recommendations' and line.startswith(('-', '•', '*')):
                recommendations.append(line.lstrip('-•* '))
        
        # Use full analysis as root cause for now
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
    
    # Create report_generator.py - Part 1
    report_gen_code = '''"""Node for generating final report."""
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
The failure is **consistent** between Jenkins and local execution. This suggests:
- The issue is in the code itself, not environment-specific
- The failure is reproducible
- Fix should work in both environments
"""
            elif comparison['jenkins_failed'] and not comparison['local_failed']:
                return """
### Analysis
The failure occurs **only in Jenkins**, not locally. This suggests:
- Environment-specific issue (dependencies, configuration, resources)
- Possible infrastructure problem
- Timing or concurrency issue
"""
            elif not comparison['jenkins_failed'] and comparison['local_failed']:
                return """
### Analysis
The failure occurs **only locally**, not in Jenkins. This suggests:
- Local environment configuration issue
- Missing dependencies locally
- Different test data or setup
"""
            else:
                return """
### Analysis
Both Jenkins and local execution succeeded. The original failure may have been:
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
# Jenkins Automation Failure Analysis Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Summary

- **Jenkins Job:** {state['jenkins_job']}
- **Build Number:** #{state['build_number']}
- **Build Result:** {collected_data['jenkins']['result']}
- **Failure Count:** {collected_data['jenkins']['failure_details']['failure_count'] if collected_data['jenkins'].get('failure_details') else 0}

## Build Information

- **URL:** {state.get('build_info', {}).get('url', 'N/A')}
- **Duration:** {state.get('build_info', {}).get('duration', 0) / 1000:.1f}s
- **Timestamp:** {datetime.fromtimestamp(state.get('build_info', {}).get('timestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S') if state.get('build_info', {}).get('timestamp') else 'N/A'}

## Repository Information

- **Commit SHA:** {state.get('commit_sha', 'N/A')}
- **Files Analyzed:** {collected_data['repository']['file_count']}
- **Local Path:** {collected_data['repository']['path']}

## Failure Details

### Jenkins Failures
{format_failure_details(state.get('failure_details', {}))}

### Local Execution Results
- **Exit Code:** {state.get('local_exit_code', 'N/A')}
- **Status:** {'✅ Passed' if state.get('execution_success') else '❌ Failed'}
- **Errors:** {len(state.get('local_errors', []))}

{format_local_errors(state.get('local_errors', []))}

## Comparison

- **Jenkins Failed:** {'Yes' if collected_data['comparison']['jenkins_failed'] else 'No'}
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
4. Push fixes and monitor Jenkins build
5. Update test suite if needed to prevent recurrence

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
'''
    
    create_file("langgraph_poc/nodes/report_generator.py", report_gen_code)
    
    # ========== Configuration Files ==========
    
    create_file("config/config.example.yaml", '''# Jenkins Configuration
jenkins:
  base_url: "https://jenkins.example.com"
  username: "your-username"
  api_token: "${JENKINS_API_TOKEN}"  # Use environment variable
  
# Azure DevOps Configuration
azure:
  organization_url: "https://dev.azure.com/your-org"
  pat_token: "${AZURE_PAT_TOKEN}"  # Use environment variable
  organization: "your-org"
  project: "your-project"
  repository: "automation-repo"
  default_branch: "main"
  file_extensions:
    - ".py"
    - ".js"
    - ".sh"
    - ".ps1"
    - ".yaml"
    - ".yml"

# LLM Configuration
llm:
  provider: "openai"  # or "anthropic"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"  # Use environment variable
  temperature: 0.3
  max_tokens: 2000

# Execution Configuration
execution:
  install_dependencies: true
  dependency_timeout: 300  # seconds
  execution_timeout: 600  # seconds
  test_command: "pytest -v"  # Default test command
  environment: "sandbox"
  
# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
''')
    
    create_file("config/.env.example", '''# Jenkins Credentials
JENKINS_URL=https://jenkins.example.com
JENKINS_USERNAME=your-username
JENKINS_API_TOKEN=your-jenkins-api-token

# Azure DevOps Credentials
AZURE_ORG=your-org
AZURE_PAT_TOKEN=your-azure-pat-token

# LLM API Keys
OPENAI_API_KEY=your-openai-api-key
# ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional: Override LLM model
# LLM_MODEL=gpt-4-turbo
''')
    
    # ========== Documentation ==========
    
    readme_content = """# LangGraph POC: Jenkins Automation Failure Analyzer

## Overview
This POC uses LangGraph to create an automated workflow that:
1. Fetches logs from Jenkins builds
2. Accesses automation code from Azure DevOps repositories
3. Reruns failed tests locally
4. Analyzes results to determine root cause of failures

## Architecture

Workflow: Start → Jenkins Log Fetcher → Azure Repo Access → Local Executor → Results Collector → Root Cause Analyzer → Report Generator → End

## Setup

### 1. Install Dependencies

    pip install -r requirements.txt

### 2. Configure Environment

    cp config/.env.example .env

Edit .env with your actual credentials.

### 3. Configure Settings

    cp config/config.example.yaml config/config.yaml

Edit config/config.yaml with your Jenkins, Azure, and LLM settings.

## Usage

    python -m langgraph_poc.main --jenkins-job "my-automation-tests" --build-number 123 --azure-project "MyProject" --output reports/analysis.md

### Command-Line Arguments

- --jenkins-job (required): Name of the Jenkins job
- --build-number (required): Build number to analyze
- --jenkins-url (optional): Jenkins server URL
- --azure-project (required): Azure DevOps project name
- --azure-repo-url (optional): Azure repository URL
- --config (optional): Path to config file
- --output (optional): Output file path for the report

## Components

### Workflow Nodes

- JenkinsLogFetcher: Retrieves build logs and failure information from Jenkins
- AzureRepoAccess: Clones relevant automation code from Azure DevOps
- LocalExecutor: Reruns failed tests in isolated environment
- ResultsCollector: Aggregates all execution data
- RootCauseAnalyzer: Uses LLM to analyze failures and identify root causes
- ReportGenerator: Creates comprehensive failure analysis report

### API Clients

- JenkinsClient: Handles Jenkins API interactions
- AzureDevOpsClient: Manages Azure DevOps repository access

## Example Output

The tool generates a detailed markdown report including:
- Build summary and information
- Repository details
- Failure analysis
- Comparison between Jenkins and local execution
- Root cause analysis with confidence level
- Actionable recommendations

## Troubleshooting

### Authentication Issues
1. Verify your credentials in .env
2. Check that Jenkins API token has sufficient permissions
3. Ensure Azure PAT token has Code (Read) permissions

### Execution Failures
1. Check that all dependencies are installed
2. Verify test command in config matches your project
3. Review execution timeout settings

### LLM Issues
1. Verify OpenAI API key is valid
2. Check API rate limits
3. Ensure sufficient API credits

## Requirements

- Python 3.8+
- Jenkins with API access
- Azure DevOps with PAT token
- OpenAI API key (or other LLM provider)

## License

This is a proof-of-concept tool for internal use.
"""

    create_file("README_POC.md", readme_content)