# Advanced LangGraph Workflow Design for Test Failure Analysis

## Overview

This document outlines a comprehensive LangGraph agent design that models the real human workflow for analyzing test failures. Unlike the simple 3-node POC, this design handles the complexity of production test failure scenarios.

## Human Workflow Analysis

From the actual developer workflow, we identified these key stages:

### 1. **Initial Assessment**
- Developer sees multiple failed tests
- Looks at test logs to understand context
- Checks if sanity tests are failing (these are basic smoke tests)

### 2. **Pattern Detection & Prioritization**
- Are 80 tests failing or just 4? (volume matters)
- Is it a deployment issue?
- Is it one thing vs. widespread?
- Is it environment-specific (Locust, Falconnet, env variables)?

### 3. **Deep Investigation**
- Open Jenkins for more detailed results
- Check if automation threw an exception → look at test code/fixtures
- Check if production code threw an exception → look at elastic logs

### 4. **Root Cause Classification**
- Configuration issue (something changed)
- Third party problem (check change logs)
- Bug with the test code
- Bug with production code

### 5. **Action Decision**
- Open a bug
- Fix immediately
- Follow up accordingly

---

## Proposed LangGraph Structure

```
                    START
                      ↓
              ┌───────────────┐
              │  Node 1:      │
              │ Parse All     │
              │ Failed Tests  │
              └───────┬───────┘
                      ↓
              ┌───────────────┐
              │  Node 2:      │
              │ Sanity Check  │
              │ Analysis      │
              └───────┬───────┘
                      ↓
                   DECISION 1: Are sanity tests failing?
                      ↓
              ┌───────┴───────┐
              │               │
         YES  │               │  NO
              ↓               ↓
    ┌─────────────┐   ┌─────────────┐
    │ Node 3a:    │   │ Node 3b:    │
    │ Deployment  │   │ Pattern     │
    │ Issue Check │   │ Analysis    │
    └──────┬──────┘   └──────┬──────┘
           │                 │
           └────────┬────────┘
                    ↓
              ┌───────────────┐
              │  Node 4:      │
              │ Volume &      │
              │ Scope Triage  │
              └───────┬───────┘
                      ↓
                DECISION 2: Failure pattern?
                      ↓
        ┌─────────────┼─────────────┐
        │             │             │
    Single Issue   Multiple     Widespread
        │          Related         │
        ↓             ↓             ↓
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Node 5a: │  │ Node 5b: │  │ Node 5c: │
  │ Focused  │  │ Common   │  │ System   │
  │ Analysis │  │ Root     │  │ Issue    │
  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │             │             │
       └─────────────┼─────────────┘
                     ↓
              ┌───────────────┐
              │  Node 6:      │
              │ Stack Trace   │
              │ Analysis      │
              └───────┬───────┘
                      ↓
              DECISION 3: Exception source?
                      ↓
           ┌──────────┴──────────┐
           │                     │
    Test Code                Production Code
           │                     │
           ↓                     ↓
    ┌─────────────┐      ┌─────────────┐
    │ Node 7a:    │      │ Node 7b:    │
    │ Test Code   │      │ Check       │
    │ Review      │      │ Elastic     │
    │             │      │ Logs        │
    └──────┬──────┘      └──────┬──────┘
           │                     │
           └──────────┬──────────┘
                      ↓
              ┌───────────────┐
              │  Node 8:      │
              │ Environment   │
              │ & Config      │
              │ Check         │
              └───────┬───────┘
                      ↓
              DECISION 4: Root cause category?
                      ↓
      ┌───────────────┼───────────────┐
      │               │               │
   Config        3rd Party       Code Bug
      │               │               │
      ↓               ↓               ↓
  ┌────────┐    ┌────────┐    ┌────────┐
  │Node 9a:│    │Node 9b:│    │Node 9c:│
  │Config  │    │3rd Pty │    │ Code   │
  │Details │    │ Check  │    │Analysis│
  └───┬────┘    └───┬────┘    └───┬────┘
      │             │             │
      └─────────────┼─────────────┘
                    ↓
              ┌───────────────┐
              │  Node 10:     │
              │ Action        │
              │ Recommender   │
              └───────┬───────┘
                      ↓
              DECISION 5: Urgency?
                      ↓
      ┌───────────────┼───────────────┐
      │               │               │
   Critical      Investigate       Track
      │               │               │
      ↓               ↓               ↓
   Fix Now       Open Bug        Deprioritize
      │               │               │
      └───────────────┴───────────────┘
                      ↓
                     END
```

---

## Detailed Node Descriptions

### **Node 1: Parse All Failed Tests**
**Purpose**: Extract and structure all test failure data

**Inputs**:
- Test results XML/JSON
- Test run metadata

**Processing**:
- Extract all failures from test results
- Count total failures
- Extract basic metadata (test names, types, duration)
- Group by test suite/class

**Outputs**:
- List of failed test objects
- Total failure count
- Failure distribution by suite

**LLM Task**: Structure and summarize the failure data

---

### **Node 2: Sanity Check Analysis**
**Purpose**: Identify if basic smoke tests are failing (critical system indicator)

**Inputs**:
- Failed tests list from Node 1
- Sanity test identifier patterns

**Processing**:
- Identify which tests are "sanity tests" (basic smoke tests)
- Check if sanity tests are failing
- Analyze sanity test failure patterns

**Outputs**:
- Boolean: Are sanity tests failing?
- List of failing sanity tests
- Sanity failure rate

**LLM Task**: Determine if this is a system-wide deployment issue

---

### **DECISION 1: Are sanity tests failing?**
**Routing Logic**:
- **YES** → Route to Node 3a (Deployment Issue Check)
  - Rationale: Sanity test failures indicate system-wide problems
- **NO** → Route to Node 3b (Pattern Analysis)
  - Rationale: More targeted, feature-specific issues

---

### **Node 3a: Deployment Issue Check**
**Purpose**: Investigate if failures correlate with recent deployment

**Inputs**:
- Failure timestamps
- Deployment history
- Test history

**Processing**:
- Check if failures correlate with recent deployment
- Look for timing patterns (all failed after deployment)
- Compare with previous successful runs

**Outputs**:
- Deployment correlation score (0-1)
- Deployment timestamp vs failure timestamp
- Changes in recent deployment

**LLM Task**: Analyze temporal correlation with deployment events

---

### **Node 3b: Pattern Analysis**
**Purpose**: Find patterns in non-sanity test failures

**Inputs**:
- Failed tests (excluding sanity tests)
- Test metadata

**Processing**:
- Analyze test names/types for patterns
- Group failures by similarity (package, class, method patterns)
- Identify common characteristics

**Outputs**:
- Failure clusters/groups
- Pattern descriptions
- Commonality analysis

**LLM Task**: Identify patterns and group related failures

---

### **Node 4: Volume & Scope Triage**
**Purpose**: Assess the scale and scope of the failure

**Inputs**:
- All failure data
- Environment information
- Historical failure rates

**Processing**:
- Assess scope: 4 failures vs 80 failures vs 1000 failures
- Check if related to specific environment (Locust, Falconnet)
- Check environment variables
- Compare with historical baseline

**Outputs**:
- Scope category (Isolated / Related / Widespread)
- Environment specificity
- Volume severity (Low / Medium / High)

**LLM Task**: Categorize the failure scope and severity

---

### **DECISION 2: Failure pattern?**
**Routing Logic**:
- **Single Issue** → Node 5a (Focused Analysis)
  - 1-5 failures, likely related to one feature
- **Multiple Related** → Node 5b (Common Root)
  - 5-20 failures, common pattern identified
- **Widespread** → Node 5c (System Issue)
  - 20+ failures, system-level problem

---

### **Node 5a: Focused Analysis**
**Purpose**: Deep dive on isolated failures

**Inputs**:
- Single or small cluster of failures
- Full test context

**Processing**:
- Detailed analysis of each failure
- Compare with similar passing tests
- Analyze recent changes to affected area

**Outputs**:
- Detailed failure breakdown
- Likely root cause candidates
- Affected code areas

**LLM Task**: Perform detailed analysis on specific failures

---

### **Node 5b: Common Root Analysis**
**Purpose**: Find common root cause across related failures

**Inputs**:
- Related failure cluster
- Common patterns identified

**Processing**:
- Identify shared dependencies
- Find common code paths
- Analyze shared configuration

**Outputs**:
- Common root cause hypothesis
- Shared dependencies list
- Impact scope

**LLM Task**: Identify the common denominator causing multiple failures

---

### **Node 5c: System Issue Analysis**
**Purpose**: Investigate system-level problems

**Inputs**:
- All failures
- System metrics
- Infrastructure status

**Processing**:
- System-wide dependency analysis
- Infrastructure health check
- Configuration validation

**Outputs**:
- System-level issues identified
- Infrastructure status
- Configuration problems

**LLM Task**: Analyze system-level factors affecting all tests

---

### **Node 6: Stack Trace Analysis**
**Purpose**: Parse and analyze exception stack traces

**Inputs**:
- Stack traces from all failures
- Source code context

**Processing**:
- Parse stack traces from all failures
- Identify where exceptions originate
- Map to source code locations
- Categorize exception types

**Outputs**:
- Exception source location (test code vs production code)
- Exception type classification
- Common stack trace patterns

**LLM Task**: Interpret stack traces and identify exception origins

---

### **DECISION 3: Exception source?**
**Routing Logic**:
- **Test Automation Code** → Node 7a (Test Code Review)
  - Exception originates in test fixtures, setup, or assertions
- **Production Code** → Node 7b (Check Elastic Logs)
  - Exception originates in application code being tested

---

### **Node 7a: Test Code Review**
**Purpose**: Investigate issues in test automation code

**Inputs**:
- Test source code
- Test fixtures
- Stack trace pointing to test code

**Processing**:
- Examine test fixtures
- Check test setup/teardown
- Look for test code bugs
- Analyze test data providers

**Outputs**:
- Test code issues identified
- Problematic test fixtures
- Fix recommendations for test code

**LLM Task**: Review test code for bugs or incorrect setup

---

### **Node 7b: Check Elastic Logs**
**Purpose**: Query production logs for detailed error information

**Inputs**:
- Test failure timestamps
- Elastic log access
- Exception details

**Processing**:
- Query elastic logs for production errors
- Get full call stack from production
- Correlate with test failures
- Extract relevant log context

**Outputs**:
- Production error logs
- Full production stack traces
- Log correlation with test failures

**LLM Task**: Analyze production logs and correlate with test failures

---

### **Node 8: Environment & Config Check**
**Purpose**: Validate environment and configuration

**Inputs**:
- Environment variables
- Configuration files
- Deployment configurations

**Processing**:
- Check for configuration changes
- Compare environment variables across environments
- Look for deployment config differences
- Validate dependencies and versions

**Outputs**:
- Configuration differences
- Environment variable mismatches
- Dependency version conflicts

**LLM Task**: Identify configuration or environment discrepancies

---

### **DECISION 4: Root cause category?**
**Routing Logic**:
- **Configuration Issue** → Node 9a (Config Details)
  - Environment vars, config files, settings changes
- **Third Party Problem** → Node 9b (3rd Party Check)
  - External API, library, or service issues
- **Code Bug** → Node 9c (Code Analysis)
  - Actual bug in test or production code

---

### **Node 9a: Config Details**
**Purpose**: Deep dive on configuration issues

**Inputs**:
- Configuration diffs
- Environment comparisons

**Processing**:
- Identify specific config that changed
- Determine impact of config change
- Validate config correctness

**Outputs**:
- Specific config issue
- Recommended config fix
- Config rollback option

**LLM Task**: Diagnose configuration problems and suggest fixes

---

### **Node 9b: Third Party Check**
**Purpose**: Investigate third-party dependencies

**Inputs**:
- Third-party service logs
- API change logs
- Library versions

**Processing**:
- Check third party change logs
- Validate API versions
- Review third-party service status
- Analyze integration points

**Outputs**:
- Third-party issue identified
- API/library version problems
- Service status

**LLM Task**: Assess third-party dependency issues

---

### **Node 9c: Code Analysis**
**Purpose**: Detailed analysis of code bugs

**Inputs**:
- Source code
- Stack traces
- Test results

**Processing**:
- Detailed code analysis
- Logic error identification
- Race condition detection
- Null pointer analysis

**Outputs**:
- Specific code bug identified
- Bug location
- Fix recommendation with code changes

**LLM Task**: Perform detailed code analysis and suggest fixes

---

### **Node 10: Action Recommender**
**Purpose**: Synthesize all analysis and recommend actions

**Inputs**:
- All previous node outputs
- Root cause determination
- Impact assessment

**Processing**:
- Synthesize all previous analysis
- Determine action priority
- Create action plan
- Provide specific fix recommendations

**Outputs**:
- Action priority (Critical / Investigate / Track)
- Specific action items
- Fix recommendations
- Owner assignment suggestion

**LLM Task**: Create comprehensive action plan with priorities

---

### **DECISION 5: Urgency?**
**Routing Logic**:
- **Critical** → Fix Now
  - Blocking production, sanity tests failing, major outage
- **Investigate** → Open Bug
  - Needs deeper investigation, moderate impact
- **Track** → Deprioritize
  - Known issue, low impact, can be deferred

**Final Outputs**:
- Urgency level
- Recommended action
- Assignee recommendation
- Timeline suggestion

---

## Key Decision Points & Routing Logic

### 1. Sanity Test Decision
**Purpose**: Differentiate between system-wide vs targeted issues

**Logic**:
```python
if sanity_tests_failing:
    return "deployment_check"  # Node 3a
else:
    return "pattern_analysis"  # Node 3b
```

### 2. Pattern Decision
**Purpose**: Route to appropriate analysis depth

**Logic**:
```python
if failure_count <= 5:
    return "focused_analysis"  # Node 5a
elif failure_count <= 20 and has_pattern:
    return "common_root"  # Node 5b
else:
    return "system_issue"  # Node 5c
```

### 3. Exception Source Decision
**Purpose**: Determine investigation path

**Logic**:
```python
if exception_in_test_code:
    return "test_code_review"  # Node 7a
else:
    return "elastic_logs"  # Node 7b
```

### 4. Root Cause Decision
**Purpose**: Categorize for proper handling

**Logic**:
```python
if config_mismatch or env_var_issue:
    return "config_details"  # Node 9a
elif third_party_error or api_change:
    return "third_party_check"  # Node 9b
else:
    return "code_analysis"  # Node 9c
```

### 5. Urgency Decision
**Purpose**: Determine final action priority

**Logic**:
```python
if sanity_failing or production_blocked:
    return "fix_now"  # Critical
elif needs_investigation:
    return "open_bug"  # Investigate
else:
    return "track"  # Deprioritize
```

---

## Additional Nodes We Could Add

### **Historical Analysis Node**
- Check if this test has failed before
- Analyze failure frequency
- Identify flaky tests

### **Flakiness Detector Node**
- Re-run failed tests
- Analyze determinism
- Calculate flakiness score

### **Regression Detector Node**
- Compare with previous passing runs
- Identify when test started failing
- Git blame for changes

### **Merge Analysis Node**
- Check what changed in recent merges
- Identify recent code changes
- Blame analysis

### **Cross-Environment Validator Node**
- Compare same test across environments
- Identify environment-specific issues
- Configuration comparison

### **Impact Analysis Node**
- Determine user impact
- Assess business criticality
- Calculate risk score

### **Notification Router Node**
- Determine who to notify
- Format notifications
- Create tickets automatically

---

## State Schema for Advanced Workflow

```python
from typing import TypedDict, List, Optional

class FailureAnalysisState(TypedDict):
    # Input data
    all_failed_tests: List[dict]
    test_run_metadata: dict

    # Node 1 outputs
    total_failure_count: int
    failure_distribution: dict

    # Node 2 outputs
    sanity_tests_failing: bool
    sanity_failure_list: List[str]

    # Node 3 outputs
    deployment_correlation: float
    deployment_timestamp: str
    failure_pattern: str

    # Node 4 outputs
    scope_category: str  # Isolated / Related / Widespread
    environment_specificity: dict
    volume_severity: str  # Low / Medium / High

    # Node 5 outputs
    detailed_analysis: str
    common_root_hypothesis: str
    system_issues: List[str]

    # Node 6 outputs
    exception_source: str  # test_code / production_code
    exception_types: List[str]
    stack_trace_patterns: dict

    # Node 7 outputs
    test_code_issues: List[str]
    production_logs: List[dict]

    # Node 8 outputs
    config_diffs: dict
    env_var_mismatches: List[dict]

    # Node 9 outputs
    root_cause_category: str  # Config / ThirdParty / CodeBug
    specific_issue: str
    fix_recommendation: str

    # Node 10 outputs
    action_priority: str  # Critical / Investigate / Track
    action_items: List[str]
    owner_suggestion: str

    # Tracking
    steps_completed: List[str]
    decisions_made: dict
    total_tokens: int
    elapsed_time: float
```

---

## Implementation Considerations

### 1. **Conditional Edges**
Use LangGraph's conditional edges for decision points:
```python
workflow.add_conditional_edges(
    "sanity_check",
    lambda state: "deployment_check" if state["sanity_tests_failing"] else "pattern_analysis"
)
```

### 2. **Parallel Execution**
Some nodes can run in parallel:
- Node 7a and Node 7b could run in parallel if both test and production code involved
- Node 8 could run in parallel with Node 6

### 3. **Human-in-the-Loop**
Add human confirmation points:
- Before critical action decisions
- When confidence is low
- For production deployments

### 4. **Caching & Optimization**
- Cache environment configs
- Cache historical test data
- Reuse analysis across similar failures

### 5. **Error Handling**
- Each node should handle API failures gracefully
- Fallback to simpler analysis if advanced tools unavailable
- Timeout handling for long-running operations

---

## Open Questions

1. **Data Access**: Will the agent have access to:
   - Jenkins API?
   - Elastic logs?
   - Git history?
   - Environment configurations?

2. **Complexity**: Should we:
   - Start with 5-6 core nodes?
   - Build the full 10+ node graph?
   - Iterate and add nodes progressively?

3. **Human-in-Loop**: Which decisions need human confirmation?
   - Critical actions only?
   - All classification decisions?
   - Final recommendations only?

4. **Historical Data**: Do you have:
   - Historical test results?
   - Flakiness metrics?
   - Past incident data?

5. **Priority**: Which aspects are most critical:
   - Speed of analysis?
   - Accuracy of classification?
   - Actionability of recommendations?
   - Explanation quality?

---

## Next Steps

1. **Prioritize Nodes**: Determine which 5-7 nodes to implement first
2. **Define Data Sources**: Identify what data is available and how to access it
3. **Build MVP**: Implement core workflow with essential nodes
4. **Test & Iterate**: Run on real failure data and refine
5. **Add Complexity**: Progressively add more nodes and decision points
6. **Optimize**: Improve performance and accuracy based on feedback

---

## Comparison: Simple POC vs Advanced Workflow

| Aspect | Simple POC (3 nodes) | Advanced Workflow (10+ nodes) |
|--------|---------------------|-------------------------------|
| **Nodes** | 3 sequential nodes | 10+ nodes with branching |
| **Decisions** | None | 5 major decision points |
| **Scope** | Single test analysis | Multi-test triage & analysis |
| **Context** | Test code + error | Full system context |
| **Output** | Classification only | Action plan with priority |
| **Routing** | Linear flow | Conditional branching |
| **Use Case** | POC/Demo | Production-ready |
| **Complexity** | Low | High |
| **Value** | Proof of concept | Actionable insights |

The advanced workflow mirrors the actual human debugging process and provides production-ready analysis capabilities.
