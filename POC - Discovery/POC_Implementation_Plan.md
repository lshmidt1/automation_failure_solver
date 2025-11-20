# Test Failure Classification POC - Implementation Plan

## Deliverable
Create a Jupyter notebook `test_failure_classifier_poc.ipynb` that demonstrates two approaches for AI-powered test failure classification:
1. **Basic Approach**: Direct Claude API call via AWS Bedrock
2. **LangGraph Approach**: Multi-node agent workflow (3-4 nodes)

## Implementation Steps

### Part 1: Setup & Dependencies
- Install required Python packages in .venv:
  - `boto3`, `botocore` (AWS Bedrock)
  - `langgraph`, `langchain`, `langchain-aws` (LangGraph)
  - `lxml` (XML parsing)
  - `pandas` (data handling)
- Configure AWS SSO authentication (use existing 'claude-code' profile)
- Verify Bedrock connection

**Status**: ✅ COMPLETED

### Part 2: Data Extraction
- Parse `docs/testng-results.xml` (2.4MB, 62K lines)
- Extract all 3 failed tests with:
  - Test name and signature
  - Exception type and message
  - Full stack trace
  - Duration and timestamps
  - Reporter logs (if relevant)
- Display failed tests in structured format
- **Select one test** for detailed analysis (e.g., `reportFileGlobalValidation`)

**Status**: Pending

### Part 3: Create Dummy Test Code
- Since actual test code is unavailable, create realistic dummy test code that:
  - Matches the failure signature from XML (`VisaDirectReportTester.reportFileGlobalValidation`)
  - References MCSend domain concepts (payment processing, reports, etc.)
  - Shows plausible code that would produce the actual failure
- Create 2-3 supporting method stubs for context

**Status**: Pending

### Part 4: Basic Approach Implementation
- Format prompt with:
  - Test failure details
  - Dummy test source code
  - Stack trace
- Send to Claude 3 Sonnet via Bedrock
- Parse response for:
  - **Root cause classification** (code bug, flaky test, infrastructure, etc.)
  - **Confidence level**
  - **Suggested fix** (code changes or action items)
- Display results with timing and token usage

**Status**: Pending

### Part 5: LangGraph Approach Implementation

**Graph Nodes (3-4 max):**
1. **Analyze Error Node**: Parse exception, understand what went wrong
2. **Review Code Node**: Examine test code to understand intent
3. **Classify & Fix Node**: Determine root cause + suggest solution

**Graph Flow:**
```
Input → Analyze Error → Review Code → Classify & Fix → Output
```

**Implementation:**
- Implement StateGraph with defined schema
- Each node calls Claude with focused sub-task
- Track reasoning steps through the graph
- Display full workflow output with intermediate results

**Status**: Pending

### Part 6: Comparison & Evaluation
Create comparison table:

| Metric | Basic Approach | LangGraph Approach |
|--------|----------------|-------------------|
| Root Cause | ... | ... |
| Suggested Fix | ... | ... |
| Response Time | ... | ... |
| Tokens Used | ... | ... |
| Reasoning Clarity | ... | ... |

Add qualitative assessment section

**Status**: Pending

### Part 7: Documentation
- Add markdown cells explaining each section
- Include observations about accuracy
- Note limitations (dummy test code vs real code)
- List next steps for full implementation

**Status**: Pending

## Files to Create/Modify
- **NEW**: `test_failure_classifier_poc.ipynb` - Main POC notebook
- **UPDATE**: `README.md` - Update "Current Progress" checklist

## Success Criteria
- ✅ Both approaches successfully classify the test failure
- ✅ Both provide actionable suggested fixes
- ✅ Clear comparison shows trade-offs between approaches
- ✅ POC runs end-to-end without errors
- ✅ Results demonstrate feasibility (or lack thereof) of AI classification

## Technical Details

### Test Failure Example
From `testng-results.xml`:
- **Test**: `reportFileGlobalValidation` in `VisaDirectReportTester`
- **Exception**: `java.lang.AssertionError`
- **Message**: "who is left out? Expected: is <lambda> but: was <[]>"
- **Location**: `VisaDirectReportTester.java:296` → `verifyNumberOdRecordsInReport`
- **Duration**: 5666ms

### Root Cause Categories
The AI should classify failures into:
- **Test Code Bug**: Bug in the test itself (bad assertion, wrong test setup, incorrect mocking, invalid test logic)
- **Production Code Bug**: Bug in the application code being tested (logic errors, NPEs, incorrect implementations)
- **Environmental Issues**: Missing dependencies, configuration problems, file system issues
- **Flaky Tests**: Timing issues, non-deterministic behavior, race conditions
- **Infrastructure**: Network failures, service unavailability, database timeouts
- **Data Issues**: Invalid test data, database state problems, missing test fixtures
- **Breaking Changes**: API changes, deprecated functionality, interface changes

**Note**: Splitting CODE_BUG into TEST_CODE_BUG and PRODUCTION_CODE_BUG provides clearer actionability:
- Test bugs → QA fixes the test
- Production bugs → Developer fixes the code
- Enables better metrics on test quality vs code quality

### LangGraph State Schema
```python
class FailureAnalysisState(TypedDict):
    test_name: str
    error_message: str
    stack_trace: str
    test_code: str
    error_analysis: str  # From Analyze Error node
    code_review: str     # From Review Code node
    root_cause: str      # Final classification
    suggested_fix: str   # Recommended solution
    confidence: str      # Confidence level
```

### Prompt Engineering Considerations
- Include full context: test name, exception type, message, stack trace
- Provide test source code for accurate analysis
- Ask for structured output: category, confidence, explanation, suggested fix
- Consider including domain knowledge about payment processing tests

## Next Steps After POC
1. Evaluate results with real test failures
2. Test with actual test source code (when available)
3. Expand to all 3 failed tests
4. Add metrics tracking (accuracy, precision, recall)
5. Implement feedback loop for prompt refinement
6. Consider integration with CI/CD pipeline
7. Explore cost optimization strategies

## Notes
- Real test code is currently unavailable; using realistic dummy code
- MCSend code is available locally for domain context
- Future versions will access test code from GitHub/Azure DevOps
- AWS SSO profile 'claude-code' is pre-configured for Bedrock access
