# LangGraph POC: Test Failure Analyzer (Local Version)

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
