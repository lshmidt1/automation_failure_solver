"""XML test report reader for local files."""
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
                    failure = testcase.find('exception') or testcase.find('failure')
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
                error_lines.extend(failure['text'].split('\n')[:10])
        
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