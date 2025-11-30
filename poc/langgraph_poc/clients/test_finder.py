"""Find Java test files in a repository."""
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
import re


class JavaTestFinder:
    """Find Java test files by test name or class name."""
    
    def __init__(self, repo_path: str):
        """Initialize the test finder.
        
        Args:
            repo_path: Path to the Java project root
        """
        self.repo_path = Path(repo_path)
        
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository not found: {repo_path}")
    
    def find_test_by_signature(self, signature: str, test_dirs: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Find a test file by method signature.
        
        Args:
            signature: Test method signature like "com.crb.mcsend.testers.TestClass.testMethod()"
            test_dirs: List of directories to search in (optional)
            
        Returns:
            Dictionary with test file info or None if not found
        """
        # Parse the signature to extract class name and method
        # Example: "com.crb.mcsend.testers.MCSendTester.testSomething()"
        match = re.match(r'(. +)\.([^.]+)\(.*\)$', signature)
        
        if not match:
            return None
        
        full_class_name = match.group(1)
        method_name = match.group(2)
        
        # Extract just the class name (last part)
        class_name = full_class_name.split('.')[-1]
        
        # Convert package to path
        # com.crb.mcsend. testers. MCSendTester -> com/crb/mcsend/testers/MCSendTester. java
        relative_path = full_class_name.replace('.', os.sep) + '.java'
        
        # Search for the file
        if test_dirs:
            search_paths = [self.repo_path / d for d in test_dirs]
        else:
            # Default Java test locations
            search_paths = [
                self.repo_path / 'src' / 'test' / 'java',
                self.repo_path / 'src' / 'main' / 'java',
                self.repo_path
            ]
        
        for search_path in search_paths:
            test_file = search_path / relative_path
            
            if test_file.exists():
                return {
                    'file_path': str(test_file),
                    'class_name': class_name,
                    'full_class_name': full_class_name,
                    'method_name': method_name,
                    'package': '. '.join(full_class_name.split('.')[:-1]),
                    'relative_path': relative_path
                }
            
            # Also try just searching for the class name in the search path
            found_files = list(search_path.rglob(f'{class_name}.java'))
            if found_files:
                test_file = found_files[0]
                return {
                    'file_path': str(test_file),
                    'class_name': class_name,
                    'full_class_name': full_class_name,
                    'method_name': method_name,
                    'package': '.'.join(full_class_name.split('.')[:-1]),
                    'relative_path': str(test_file. relative_to(search_path))
                }
        
        return None
    
    def find_tests_for_failures(self, failure_details: Dict[str, Any], test_dirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Find all test files for failed tests.
        
        Args:
            failure_details: Dictionary with test failure information
            test_dirs: List of directories to search in (optional)
            
        Returns:
            List of test file information dictionaries
        """
        found_tests = []
        
        test_failures = failure_details.get('test_failures', [])
        
        for failure in test_failures:
            # Try to find by signature first
            signature = failure.get('method_signature', '')
            
            if signature:
                test_info = self.find_test_by_signature(signature, test_dirs)
                
                if test_info:
                    test_info['failure_info'] = failure
                    found_tests.append(test_info)
                else:
                    # Try to construct from class name and method name
                    class_name = failure.get('class_name', '')
                    method_name = failure.get('test_name', '')
                    
                    if class_name and method_name:
                        # Try to find just by class name
                        simple_class = class_name.split('.')[-1]
                        found_files = self._search_by_class_name(simple_class, test_dirs)
                        
                        if found_files:
                            test_info = {
                                'file_path': found_files[0],
                                'class_name': simple_class,
                                'full_class_name': class_name,
                                'method_name': method_name,
                                'failure_info': failure
                            }
                            found_tests.append(test_info)
        
        return found_tests
    
    def _search_by_class_name(self, class_name: str, test_dirs: Optional[List[str]] = None) -> List[str]:
        """Search for Java files by class name.
        
        Args:
            class_name: Simple class name (e.g., "MCSendTester")
            test_dirs: List of directories to search in (optional)
            
        Returns:
            List of file paths matching the class name
        """
        if test_dirs:
            search_paths = [self.repo_path / d for d in test_dirs]
        else:
            search_paths = [
                self.repo_path / 'src' / 'test' / 'java',
                self.repo_path / 'src' / 'main' / 'java',
                self.repo_path
            ]
        
        found = []
        for search_path in search_paths:
            if search_path.exists():
                files = list(search_path.rglob(f'{class_name}.java'))
                found.extend([str(f) for f in files])
        
        return found
    
    def detect_build_system(self) -> Optional[str]:
        """Detect the build system used (Maven or Gradle).
        
        Returns:
            'maven', 'gradle', or None
        """
        if (self.repo_path / 'pom.xml').exists():
            return 'maven'
        elif (self.repo_path / 'build.gradle').exists() or (self.repo_path / 'build.gradle.kts').exists():
            return 'gradle'
        return None