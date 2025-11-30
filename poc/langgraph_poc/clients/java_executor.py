"""Execute Java tests using Maven or Gradle."""
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any


class JavaTestExecutor:
    """Execute Java tests with Maven or Gradle."""
    
    def __init__(self, repo_path: str, build_system: str):
        """Initialize the executor.
        
        Args:
            repo_path: Path to the Java project root
            build_system: 'maven' or 'gradle'
        """
        self.repo_path = Path(repo_path)
        self.build_system = build_system
    
    def run_specific_tests(self, test_infos: List[Dict[str, Any]], timeout: int = 300) -> Dict[str, Any]:
        """Run specific tests. 
        
        Args:
            test_infos: List of test information dictionaries
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        if not test_infos:
            return {
                'success': False,
                'output': '',
                'errors': ['No tests to run'],
                'exit_code': -1
            }
        
        # Build the test command
        if self.build_system == 'maven':
            return self._run_maven_tests(test_infos, timeout)
        elif self.build_system == 'gradle':
            return self._run_gradle_tests(test_infos, timeout)
        else:
            return {
                'success': False,
                'output': '',
                'errors': [f'Unsupported build system: {self.build_system}'],
                'exit_code': -1
            }
    
    def _run_maven_tests(self, test_infos: List[Dict[str, Any]], timeout: int) -> Dict[str, Any]:
        """Run tests using Maven. 
        
        Args:
            test_infos: List of test information dictionaries
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        # Build Maven test command
        # mvn test -Dtest=ClassName#methodName,ClassName2#methodName2
        test_specs = []
        for test_info in test_infos:
            class_name = test_info.get('full_class_name') or test_info.get('class_name')
            method_name = test_info.get('method_name')
            
            if class_name and method_name:
                test_specs.append(f"{class_name}#{method_name}")
            elif class_name:
                test_specs.append(class_name)
        
        if not test_specs:
            return {
                'success': False,
                'output': '',
                'errors': ['Could not build test specification'],
                'exit_code': -1
            }
        
        test_param = ','.join(test_specs)
        command = ['mvn', 'test', f'-Dtest={test_param}', '-DfailIfNoTests=false']
        
        try:
            result = subprocess.run(
                command,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result. returncode == 0,
                'output': result.stdout,
                'errors': [result.stderr] if result.stderr else [],
                'exit_code': result.returncode,
                'command': ' '.join(command)
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'errors': [f'Test execution timed out after {timeout} seconds'],
                'exit_code': -1,
                'command': ' '.join(command)
            }
        except FileNotFoundError:
            return {
                'success': False,
                'output': '',
                'errors': ['Maven (mvn) command not found.  Make sure Maven is installed and in PATH.'],
                'exit_code': -1,
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'errors': [f'Test execution failed: {str(e)}'],
                'exit_code': -1,
                'command': ' '.join(command)
            }
    
    def _run_gradle_tests(self, test_infos: List[Dict[str, Any]], timeout: int) -> Dict[str, Any]:
        """Run tests using Gradle. 
        
        Args:
            test_infos: List of test information dictionaries
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        # Build Gradle test command
        # gradle test --tests ClassName.methodName --tests ClassName2.methodName2
        command = ['gradle', 'test']
        
        for test_info in test_infos:
            class_name = test_info.get('full_class_name') or test_info.get('class_name')
            method_name = test_info.get('method_name')
            
            if class_name and method_name:
                command.extend(['--tests', f"{class_name}. {method_name}"])
            elif class_name:
                command.extend(['--tests', class_name])
        
        if len(command) == 2:  # Only 'gradle test'
            return {
                'success': False,
                'output': '',
                'errors': ['Could not build test specification'],
                'exit_code': -1
            }
        
        try:
            result = subprocess.run(
                command,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': [result. stderr] if result.stderr else [],
                'exit_code': result.returncode,
                'command': ' '.join(command)
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'errors': [f'Test execution timed out after {timeout} seconds'],
                'exit_code': -1,
                'command': ' '.join(command)
            }
        except FileNotFoundError:
            return {
                'success': False,
                'output': '',
                'errors': ['Gradle command not found. Make sure Gradle is installed and in PATH.'],
                'exit_code': -1,
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'errors': [f'Test execution failed: {str(e)}'],
                'exit_code': -1,
                'command': ' '.join(command)
            }