"""Node for accessing local repository."""
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
