import langgraph
from langgraph.graph import Graph
from langgraph.graph.nodes import ToolNode
from langgraph.tools import Tool
from langchain.tools import tool
from langchain_openai import ChatOpenAI

# ----- Step 1: Jenkins Log Ingest -----
@tool
def get_jenkins_logs(build_url: str) -> str:
    """
    Retrieves the Jenkins logs for the provided build URL.
    Make this real using requests/api/password if needed.
    """
    # For POC: just load/build from a text file or mock
    try:
        with open('jenkins.log', 'r') as f:
            log = f.read()
        return log
    except FileNotFoundError:
        return "Mocked Jenkins logs: failure in LoginTest on step XYZ"

# ----- Step 2: Map Log to Azure Repo/Test -----
@tool
def map_log_to_azure_code(log: str) -> dict:
    """
    Given Jenkins log, finds which repo/test/file/line failed in Azure repo.
    """
    # For POC: parse log for a test/class name, and return repo info
    # Here you would use Azure API to query repo/files
    return {
        "repo": "org/project/automation-tests",
        "file": "tests/login_test.py",
        "function": "test_login_invalid",
        "line": 42,
    }

# ----- Step 3: Rerun Test Locally/Simulate -----
@tool
def rerun_test_locally(repo: str, file: str, function: str) -> dict:
    """
    Reruns the failed test locally, returns test result and output.
    """
    # For POC, simulate: in production, run via pytest/subprocess, etc.
    import subprocess
    result = {
        "status": "fail",
        "output": "AssertionError: Login did not fail as expected.",
        "file": file,
        "function": function,
    }
    # You could trigger real pytest, e.g.:
    # completed = subprocess.run(["pytest", f"{file}::${function}"], capture_output=True, text=True)
    # result["status"] = "pass" if completed.returncode == 0 else "fail"
    # result["output"] = completed.stdout + completed.stderr
    return result

# ----- Step 4: LLM Root Cause Analysis -----
@tool
def analyze_root_cause(log: str, code_result: dict) -> str:
    """
    Uses an LLM to analyze the Jenkins log + rerun result and suggests root cause.
    """
    # Use your favorite LangChain LLM, here is default (can use OpenAI/GPT, Azure, Claude, etc.)
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    prompt = (
        f"Jenkins Log:\n{log}\n\n"
        f"Code Test Rerun Output:\n{code_result}\n\n"
        "Analyse and provide the most likely root cause behind the failure, "
        "reference test code, stack trace, and suggest likely fixes."
    )
    analysis = llm.invoke(prompt)
    return analysis.content

# ----- LangGraph Nodes -----
log_node = ToolNode(tool=get_jenkins_logs)
map_node = ToolNode(tool=map_log_to_azure_code)
rerun_node = ToolNode(tool=rerun_test_locally)
analyze_node = ToolNode(tool=analyze_root_cause)

# ----- Build the LangGraph -----
workflow = Graph()
workflow.add_node("logs", log_node)
workflow.add_node("map", map_node)
workflow.add_node("rerun", rerun_node)
workflow.add_node("analyze", analyze_node)

workflow.connect("logs", "map")
workflow.connect("map", "rerun")
workflow.connect("rerun", "analyze")

# Entry point
workflow.set_entry_node("logs")

# ----- Run the Workflow -----
def run_poc(build_url):
    result = workflow.run({"build_url": build_url})
    print("==== Final Root Cause Analysis ====")
    print(result["analyze"])  # Step name or use result dict keys

if __name__ == "__main__":
    run_poc("https://jenkins.example.com/job/abc/123")