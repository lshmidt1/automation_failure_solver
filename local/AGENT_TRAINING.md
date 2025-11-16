# Agent Training: How to Analyze Test Failures

## 6-Step Analysis Process

### Step 1: Find the Test Name
Identify the test method from the stack trace or error title.

### Step 2: Find Test Entry Point in Stack Trace
Look for the FIRST line with YOUR test code (not framework).
STOP reading stack trace below this point - everything else is framework code.

### Step 3: Go to Repository and Trace Code Flow
- Find the test method in repository
- Read the code to understand what it does
- Follow method calls through the stack trace
- Read each method until the failure point

### Step 4: Find Expected vs Actual Results
- Extract expected result from error message or assertion
- Extract actual result from error message
- Understand what each value means
- Identify the gap between them

### Step 5: Identify Root Cause
Why did the test get the actual result instead of expected?
- Test data issue?
- Timing problem?
- Wrong logic?
- Missing setup?

### Step 6: Provide Key Insights
Output brief, actionable analysis with:
- Root cause (why it failed)
- What to check (specific investigation points)
- Recommended fix (minimal code reference)
- File, line, and issue description

---

## Example: Hamcrest Empty Collection

### Error Message
who is left out? Expected: is org.apache.cxf.common.util.StringUtils$$Lambda$481/0x00000008005f0440@1a899fcd but: was <[]>

Code

### Stack Trace
at org.hamcrest.MatcherAssert.assertThat(MatcherAssert.java:20) at com.crb.p2p.testers.VisaDirectReportTester.verifyNumberOdRecordsInReport(VisaDirectReportTester.java:296) at com.crb.p2p.testers.VisaDirectReportTester.reportFileGlobalValidation(VisaDirectReportTester.java:152) at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method) at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) ...

Code

### Apply the 6 Steps

**Step 1: Test Name**
`reportFileGlobalValidation`

**Step 2: Test Entry Point**
Line 152: `VisaDirectReportTester.reportFileGlobalValidation`
(Stop here - lines below are Java/TestNG framework)

**Step 3: Trace Code Flow**
reportFileGlobalValidation (line 152) ↓ calls verifyNumberOdRecordsInReport (line 296) ↓ applies Lambda filter to records collection ↓ assertion fails

Code

**Step 4: Expected vs Actual**
- Expected: Collection with records matching Lambda predicate
- Actual: `[]` (empty list - no records match)
- Gap: Records exist but NONE have the properties the Lambda checks for

**Step 5: Root Cause**
Lambda filter returns empty because test data doesn't match the filter criteria.
Either:
- Records created with wrong properties
- Lambda checking for wrong values
- Records not yet processed to expected state

**Step 6: Key Insights Output**

🎯 Root Cause
Lambda predicate filter returns empty list when records were expected.

Test applies filter to records collection expecting matches, but gets empty result. Records exist but have properties that don't match the Lambda condition.

🔍 What to Check
What is the Lambda at line 296 checking? (e.g., status equals "COMPLETED"?)
What properties do the created test records actually have?
Is there async processing that changes record state?
💡 Recommended Fix
Add debug logging to identify the mismatch:

Java
// Line 296 - Before assertion
List<Record> allRecords = report.getRecords();
System.out.println("Total records: " + allRecords.size());
allRecords.forEach(r -> System.out.println("Record status: " + r.getStatus()));

List<Record> filtered = allRecords.stream().filter(lambda).collect(Collectors.toList());
System.out.println("Filtered records: " + filtered.size());
🛠️ Specific Changes
File: VisaDirectReportTester.java Line: 296 Issue: Lambda filter criteria doesn't match test data properties

⏱️ Estimated Fix Time: 30-45 minutes
🎯 Confidence: MEDIUM (70%)
📁 Category: TEST_DATA_ISSUE
Code

---

END OF TRAINING
