"""Node for executing code locally."""
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
                    logs.append(f"Dependency installation:\n{result.stdout}")
                    if result.returncode != 0:
                        errors.append(f"Dependency installation failed: {result.stderr}")
                
                if Path('package.json').exists():
                    result = subprocess.run(
                        ['npm', 'install'],
                        capture_output=True,
                        text=True,
                        timeout=execution_config.get('dependency_timeout', 300)
                    )
                    logs.append(f"NPM installation:\n{result.stdout}")
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
            
            logs.append(f"Test execution:\n{result.stdout}\n{result.stderr}")
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
            'local_execution_logs': '\n'.join(logs),
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
