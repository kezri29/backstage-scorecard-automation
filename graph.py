import os
import argparse
from typing import Optional, List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()

# Agent imports
from agents.A1_repo_loader_agent import RepoLoaderAgent
from agents.A2_scoring_agent import ScoringAgent
from agents.A3_commit_agent import CommitAgent

# Agent State
class ScorecardAgentState(TypedDict, total=False):
    # Input data
    repo_url: Optional[str]
    
    # Agent outputs
    repo_data: Optional[Dict[str, Any]]
    scorecard_json: Optional[Dict[str, Any]]
    commit_result: Optional[str]
    commit_sha: Optional[str]
    
    # Status tracking
    processing_status: str
    errors: List[str]

# Node Functions
def repo_loader_node(state: ScorecardAgentState) -> ScorecardAgentState:
    """Load repository data from GitHub."""
    print("🔄 Starting repository loading...")
    
    try:
        repo_url = state.get("repo_url")
        
        if not repo_url:
            return {
                **state,
                "processing_status": "failed",
                "errors": state.get("errors", []) + ["No repository URL provided"]
            }
        
        loader_agent = RepoLoaderAgent()
        repo_data, status = loader_agent.load_repository(repo_url)
        
        if "successfully" in status:
            print("✅ Repository loading successful")
            return {
                **state,
                "repo_data": repo_data,
                "processing_status": "repo_loaded"
            }
        else:
            print(f"❌ Repository loading failed: {status}")
            return {
                **state,
                "processing_status": "failed",
                "errors": state.get("errors", []) + [status]
            }
            
    except Exception as e:
        print(f"❌ Error in repository loading: {str(e)}")
        return {
            **state,
            "processing_status": "failed",
            "errors": state.get("errors", []) + [f"Repository loading error: {str(e)}"]
        }

def scoring_agent_node(state: ScorecardAgentState) -> ScorecardAgentState:
    """Generate scoring analysis using GenAI."""
    print("🔄 Starting scoring analysis...")
    
    try:
        repo_data = state.get("repo_data")
        
        if not repo_data:
            return {
                **state,
                "processing_status": "failed",
                "errors": state.get("errors", []) + ["No repository data available for scoring"]
            }
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {
                **state,
                "processing_status": "failed",
                "errors": state.get("errors", []) + ["GOOGLE_API_KEY not found in environment variables"]
            }
        
        scoring_agent = ScoringAgent(api_key)
        scorecard_json = scoring_agent.analyze_repository(repo_data)
        
        print("✅ Scoring analysis completed")
        return {
            **state,
            "scorecard_json": scorecard_json,
            "processing_status": "scoring_complete"
        }
        
    except Exception as e:
        print(f"❌ Error in scoring analysis: {str(e)}")
        return {
            **state,
            "processing_status": "failed",
            "errors": state.get("errors", []) + [f"Scoring analysis error: {str(e)}"]
        }

def commit_agent_node(state: ScorecardAgentState) -> ScorecardAgentState:
    """Commit scorecard JSON to GitHub repository."""
    print("🔄 Starting commit process...")
    
    try:
        scorecard_json = state.get("scorecard_json")
        repo_data = state.get("repo_data")
        
        if not scorecard_json or not repo_data:
            return {
                **state,
                "processing_status": "failed",
                "errors": state.get("errors", []) + ["Missing scorecard JSON or repository data for commit"]
            }
        
        commit_agent = CommitAgent()
        commit_sha, commit_result = commit_agent.commit_scorecard(repo_data, scorecard_json)
        
        print("✅ Commit process completed")
        return {
            **state,
            "commit_result": commit_result,
            "commit_sha": commit_sha,
            "processing_status": "complete"
        }
        
    except Exception as e:
        print(f"❌ Error in commit process: {str(e)}")
        return {
            **state,
            "processing_status": "failed",
            "errors": state.get("errors", []) + [f"Commit error: {str(e)}"]
        }

# Routing Functions
def check_success(state: ScorecardAgentState) -> str:
    """Check processing status and route accordingly."""
    status = state.get("processing_status", "")
    
    if status == "failed" or state.get("errors"):
        return "END"
    
    routing_map = {
        "repo_loaded": "scoring_agent",
        "scoring_complete": "commit_agent",
        "complete": "END"
    }
    
    return routing_map.get(status, "END")

# Graph Definition
def create_scorecard_graph():
    """Creates and returns the compiled LangGraph workflow."""
    print("🔧 Building scorecard generation workflow...")
    
    # Initialize the graph
    graph = StateGraph(ScorecardAgentState)
    
    # Add all processing nodes
    graph.add_node("repo_loader", repo_loader_node)
    graph.add_node("scoring_agent", scoring_agent_node)
    graph.add_node("commit_agent", commit_agent_node)
    
    # Define routing - start with repo loader
    graph.add_edge(START, "repo_loader")
    
    # Sequential processing with error handling
    graph.add_conditional_edges(
        "repo_loader",
        check_success,
        {
            "scoring_agent": "scoring_agent",
            "END": END
        }
    )
    
    graph.add_conditional_edges(
        "scoring_agent",
        check_success,
        {
            "commit_agent": "commit_agent",
            "END": END
        }
    )
    
    graph.add_conditional_edges(
        "commit_agent",
        check_success,
        {
            "END": END
        }
    )
    
    print("✅ Workflow graph construction complete")
    return graph.compile()

# Main Workflow Function
def process_scorecard(repo_url: str) -> Dict[str, Any]:
    """
    Main function to process repository scorecard through the entire workflow.
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Dictionary containing all processing results
    """
    print("🚀 Starting scorecard generation workflow...")
    
    # Validate inputs
    if not repo_url:
        return {
            "error": "No repository URL provided",
            "processing_status": "input_validation_failed"
        }
    
    # Initialize state
    initial_state = ScorecardAgentState(
        repo_url=repo_url,
        processing_status="initialized",
        errors=[]
    )
    
    try:
        # Create and run the workflow
        workflow = create_scorecard_graph()
        
        print("⚡ Executing workflow...")
        final_state = workflow.invoke(initial_state)
        
        # Extract results
        result = {
            "processing_status": final_state.get("processing_status"),
            "repo_data": final_state.get("repo_data"),
            "scorecard_json": final_state.get("scorecard_json"),
            "commit_result": final_state.get("commit_result"),
            "commit_sha": final_state.get("commit_sha"),
            "errors": final_state.get("errors", [])
        }
        
        if final_state.get("processing_status") == "complete":
            print("🎉 Scorecard generation completed successfully!")
        else:
            print(f"⚠️ Workflow completed with status: {final_state.get('processing_status')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Critical workflow error: {str(e)}")
        return {
            "error": f"Critical workflow error: {str(e)}",
            "processing_status": "critical_error",
            "errors": [str(e)]
        }

# Testing the graph
if __name__ == "__main__":
    # Test with a sample GitHub repository
    #test_repo_url = os.environ.get("REPO_URL")
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-url', required=True, help='GitHub repository URL')
    args = parser.parse_args()

    print("🧪 Testing workflow with sample repository...")
    result = process_scorecard(args.repo_url)
    
    if result.get("processing_status") in ["repo_loaded", "scoring_complete", "complete"]:
        print(f"✅ Test passed! Status: {result.get('processing_status')}")
        repo_data = result.get("repo_data", {})
        print(f"📊 Loaded {repo_data.get('total_files', 0)} files")
        print(f"📁 Repository: {repo_data.get('repo_metadata', {}).get('full_name', 'Unknown')}")
        print(f"🔤 Languages: {list(repo_data.get('languages', {}).keys())}")
        
        # Show scoring results if available
        scorecard_json = result.get("scorecard_json")
        if scorecard_json:
            print(f"🎯 Overall Score: {scorecard_json.get('scorePercent', 'N/A')}")
            print(f"📝 Score Status: {scorecard_json.get('scoreSuccess', 'N/A')}")
        
        # Show commit results if available
        commit_result = result.get("commit_result")
        commit_sha = result.get("commit_sha")
        if commit_result:
            print(f"📤 Commit Status: {commit_result}")
        if commit_sha:
            print(f"🔗 Commit SHA: {commit_sha}")
    else:
        print(f"❌ Test failed: {result.get('error', 'Unknown error')}")
        if result.get("errors"):
            for error in result["errors"]:
                print(f"   - {error}")
