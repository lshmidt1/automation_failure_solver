"""XML report reader that supports both JUnit and TestNG formats."""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class XMLReportReader:
    """Read and parse XML test reports in JUnit or TestNG format."""
    
    def __init__(self, xml_path: str):
        """Initialize the XML reader. 
        
        Args:
            xml_path: Path to the XML test report file
        """
        self.xml_path = Path(xml_path)
        self.tree = None
        self.root = None
        self.format = None  # 'junit' or 'testng'
        
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")
        
        try:
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()
            self._detect_format()
        except ET. ParseError as e:
            raise ValueError(f"Invalid XML file: {e}")
    
    def _detect_format(self):
        """Detect if the XML is JUnit or TestNG format."""
        if self.root. tag == 'testng-results':
            self.format = 'testng'
        elif self.root.tag == 'testsuites' or self.root.tag == 'testsuite':
            self. format = 'junit'
        else:
            # Try to detect by looking for child elements
            if self.root.find('. //test-method') is not None:
                self. format = 'testng'
            elif self.root.find('.//testcase') is not None:
                self.format = 'junit'
            else:
                raise ValueError(f"Unknown XML format.  Root tag: {self.root.tag}")
    
    def parse_report(self) -> Dict[str, Any]:
        """Parse the test report and extract summary statistics.
        
        Returns:
            Dictionary with test statistics
        """
        if self.format == 'testng':
            return self._parse_testng()
        else:
            return self._parse_junit()
    
    def _parse_testng(self) -> Dict[str, Any]:
        """Parse TestNG format XML. 
        
        Returns:
            Dictionary with test statistics
        """
        # Get summary from root attributes
        total = int(self.root.get('total', 0))
        passed = int(self.root.get('passed', 0))
        failed = int(self.root. get('failed', 0))
        skipped = int(self.root. get('skipped', 0))
        ignored = int(self.root.get('ignored', 0))
        
        # Calculate duration
        duration = 0.0
        for suite in self.root.findall('. //suite'):
            suite_duration = suite.get('duration-ms', '0')
            try:
                duration += float(suite_duration) / 1000.0  # Convert ms to seconds
            except (ValueError, TypeError):
                pass
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': failed,
            'error_tests': 0,  # TestNG doesn't distinguish errors from failures
            'skipped_tests': skipped + ignored,
            'duration_seconds': duration,
            'format': 'testng'
        }
    
    def _parse_junit(self) -> Dict[str, Any]:
        """Parse JUnit format XML.
        
        Returns:
            Dictionary with test statistics
        """
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        skipped_tests = 0
        duration = 0.0
        
        # Find all test suites
        testsuites = self.root.findall('.//testsuite')
        if not testsuites and self.root.tag == 'testsuite':
            testsuites = [self.root]
        
        for suite in testsuites:
            tests = int(suite.get('tests', 0))
            failures = int(suite.get('failures', 0))
            errors = int(suite.get('errors', 0))
            skipped = int(suite.get('skipped', 0))
            time = float(suite.get('time', 0))
            
            total_tests += tests
            failed_tests += failures
            error_tests += errors
            skipped_tests += skipped
            duration += time
            
            # Count passed tests (total - failures - errors - skipped)
            passed_tests += (tests - failures - errors - skipped)
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'skipped_tests': skipped_tests,
            'duration_seconds': duration,
            'format': 'junit'
        }
    
    def extract_failure_details(self) -> Dict[str, Any]:
        """Extract detailed information about test failures.
        
        Returns:
            Dictionary with failure details
        """
        if self.format == 'testng':
            return self._extract_testng_failures()
        else:
            return self._extract_junit_failures()
    
    def _extract_testng_failures(self) -> Dict[str, Any]:
        """Extract failure details from TestNG format.
        
        Returns:
            Dictionary with failure details
        """
        failures = []
        error_lines = []
        
        # Find all test methods with status="FAIL"
        for test_method in self. root.findall('.//test-method[@status="FAIL"]'):
            method_name = test_method.get('name', 'Unknown')
            signature = test_method.get('signature', '')
            duration_ms = test_method.get('duration-ms', '0')
            
            # Extract class name from signature
            # signature format: "methodName(params)[pri:0, instance:com. crb.mcsend.testers. ClassName@hash]"
            class_name = ''
            if 'instance:' in signature:
                # Extract class name from instance field
                instance_match = re.search(r'instance:([^@]+)@', signature)
                if instance_match:
                    class_name = instance_match.group(1)
            
            # Get exception details
            exception = test_method.find('. //exception')
            error_message = ''
            error_type = ''
            stack_trace = ''
            
            if exception is not None:
                error_type = exception.get('class', 'Exception')
                
                message_elem = exception.find('message')
                if message_elem is not None and message_elem.text:
                    error_message = message_elem.text. strip()
                
                # Get full stack trace
                full_stacktrace = exception.find('full-stacktrace')
                if full_stacktrace is not None and full_stacktrace.text:
                    stack_trace = full_stacktrace.text. strip()
                else:
                    # Try short-stacktrace as fallback
                    short_trace = exception. find('short-stacktrace')
                    if short_trace is not None and short_trace.text:
                        stack_trace = short_trace.text.strip()
            
            # Get test parameters if available
            params = []
            params_elem = test_method.find('.//params')
            if params_elem is not None:
                for param in params_elem.findall('. //param'):
                    value_elem = param.find('.//value')
                    if value_elem is not None and value_elem. text:
                        params.append(value_elem.text.strip())
            
            failure_info = {
                'test_name': method_name,
                'class_name': class_name,
                'method_signature': signature,
                'error_type': error_type,
                'error_message': error_message,
                'stack_trace': stack_trace,
                'duration_ms': duration_ms,
                'params': params
            }
            
            failures.append(failure_info)
            
            # Add to error lines
            error_summary = f"{class_name}. {method_name}"
            if params:
                error_summary += f"({', '.join(params)})"
            error_summary += f": {error_type}"
            
            if error_message:
                error_lines.append(f"{error_summary}")
                error_lines.append(f"  Message: {error_message}")
            
            if stack_trace:
                # Add first few lines of stack trace
                stack_lines = stack_trace.split('\n')[:10]
                for line in stack_lines:
                    if line.strip():
                        error_lines.append(f"  {line. strip()}")
        
        # Determine overall result
        failed_count = len(failures)
        total = int(self.root. get('total', 0))
        
        if failed_count == 0:
            result = 'SUCCESS'
        elif failed_count == total:
            result = 'FAILURE'
        else:
            result = 'PARTIAL_FAILURE'
        
        # Check for specific error types
        has_compilation_error = any('CompilationError' in f. get('error_type', '') for f in failures)
        has_timeout = any('timeout' in f.get('error_message', '').lower() for f in failures)
        has_assertion_error = any('AssertionError' in f.get('error_type', '') or 'Assert' in f.get('error_type', '') for f in failures)
        
        return {
            'failure_count': failed_count,
            'result': result,
            'test_failures': failures,
            'error_lines': error_lines,
            'has_compilation_error': has_compilation_error,
            'has_timeout': has_timeout,
            'has_assertion_error': has_assertion_error,
            'format': 'testng'
        }
    
    def _extract_junit_failures(self) -> Dict[str, Any]:
        """Extract failure details from JUnit format.
        
        Returns:
            Dictionary with failure details
        """
        failures = []
        error_lines = []
        
        # Find all testcases
        for testcase in self.root.findall('.//testcase'):
            # Check for failure
            failure = testcase.find('failure')
            error = testcase.find('error')
            
            if failure is not None or error is not None:
                elem = failure if failure is not None else error
                
                test_name = testcase.get('name', 'Unknown')
                class_name = testcase.get('classname', '')
                error_type = elem.get('type', 'Error')
                error_message = elem.get('message', '')
                stack_trace = elem.text or ''
                
                failure_info = {
                    'test_name': test_name,
                    'class_name': class_name,
                    'error_type': error_type,
                    'error_message': error_message,
                    'stack_trace': stack_trace
                }
                
                failures.append(failure_info)
                
                # Add to error lines
                if error_message:
                    error_lines. append(f"{class_name}.{test_name}: {error_message}")
                if stack_trace:
                    stack_lines = stack_trace.split('\n')[:5]
                    error_lines.extend(stack_lines)
        
        # Determine overall result
        failed_count = len(failures)
        test_results = self.parse_report()
        total = test_results['total_tests']
        
        if failed_count == 0:
            result = 'SUCCESS'
        elif failed_count == total:
            result = 'FAILURE'
        else:
            result = 'PARTIAL_FAILURE'
        
        # Check for specific error types
        has_compilation_error = any('CompilationError' in f.get('error_type', '') for f in failures)
        has_timeout = any('timeout' in f.get('error_message', '').lower() for f in failures)
        has_assertion_error = any('AssertionError' in f.get('error_type', '') for f in failures)
        
        return {
            'failure_count': failed_count,
            'result': result,
            'test_failures': failures,
            'error_lines': error_lines,
            'has_compilation_error': has_compilation_error,
            'has_timeout': has_timeout,
            'has_assertion_error': has_assertion_error,
            'format': 'junit'
        }
    
    @staticmethod
    def merge_reports(xml_paths: List[str]) -> Dict[str, Any]:
        """Merge multiple XML reports into a single summary.
        
        Args:
            xml_paths: List of paths to XML files
            
        Returns:
            Merged test results
        """
        merged = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'skipped_tests': 0,
            'duration_seconds': 0.0,
            'test_failures': [],
            'error_lines': [],
            'failure_count': 0,
            'formats': []
        }
        
        for xml_path in xml_paths:
            try:
                reader = XMLReportReader(xml_path)
                results = reader.parse_report()
                failures = reader.extract_failure_details()
                
                # Merge statistics
                merged['total_tests'] += results['total_tests']
                merged['passed_tests'] += results['passed_tests']
                merged['failed_tests'] += results['failed_tests']
                merged['error_tests'] += results. get('error_tests', 0)
                merged['skipped_tests'] += results['skipped_tests']
                merged['duration_seconds'] += results['duration_seconds']
                
                # Merge failures
                merged['failure_count'] += failures['failure_count']
                merged['test_failures']. extend(failures['test_failures'])
                merged['error_lines']. extend(failures['error_lines'])
                
                # Track formats
                if results['format'] not in merged['formats']:
                    merged['formats'].append(results['format'])
                
            except Exception as e:
                print(f"Warning: Failed to parse {xml_path}: {e}")
                continue
        
        # Determine overall result
        if merged['failure_count'] == 0:
            merged['result'] = 'SUCCESS'
        elif merged['failure_count'] == merged['total_tests']:
            merged['result'] = 'FAILURE'
        else:
            merged['result'] = 'PARTIAL_FAILURE'
        
        # Check for specific error types
        merged['has_compilation_error'] = any('CompilationError' in f.get('error_type', '') for f in merged['test_failures'])
        merged['has_timeout'] = any('timeout' in f.get('error_message', '').lower() for f in merged['test_failures'])
        merged['has_assertion_error'] = any('AssertionError' in f.get('error_type', '') or 'Assert' in f.get('error_type', '') for f in merged['test_failures'])
        
        return merged