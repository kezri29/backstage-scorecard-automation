import os
import json
import base64
import requests
from typing import Dict, Any, Tuple

class CommitAgent:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        self.target_file = "component-score.json"

    def commit_scorecard(self, repo_data: Dict[str, Any], scorecard_json: Dict[str, Any]) -> Tuple[str, str]:
        """
        Commit the scorecard JSON to the repository.
        
        Args:
            repo_data: Repository data from RepoLoaderAgent
            scorecard_json: Scorecard data from ScoringAgent
            
        Returns:
            Tuple of (commit_sha, status_message)
        """
        print(f"🔄 Starting commit process for {self.target_file}...")
        
        try:
            owner = repo_data.get('owner')
            repo_name = repo_data.get('repo_name')
            
            if not owner or not repo_name:
                raise ValueError("Repository owner and name not found in repo_data")
            
            print(f"📂 Repository: {owner}/{repo_name}")
            
            # Get current file content (if exists)
            current_sha = self._get_file_sha(owner, repo_name)
            
            # Prepare JSON content
            json_content = json.dumps(scorecard_json, indent=2)
            
            # Encode content to base64
            encoded_content = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
            
            # Prepare commit data
            commit_data = {
                "message": f"Update {self.target_file} with automated scorecard analysis",
                "content": encoded_content,
                "branch": "main"  # Default to main branch
            }
            
            # Add SHA if file exists (for update)
            if current_sha:
                commit_data["sha"] = current_sha
                print(f"📝 Updating existing {self.target_file}")
            else:
                print(f"🆕 Creating new {self.target_file}")
            
            # Make the commit
            commit_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{self.target_file}"
            response = requests.put(commit_url, headers=self.headers, json=commit_data)
            
            if response.status_code in [200, 201]:
                commit_info = response.json()
                commit_sha = commit_info['commit']['sha']
                
                print(f"✅ Successfully committed {self.target_file}")
                print(f"🔗 Commit SHA: {commit_sha}")
                
                return commit_sha, "Scorecard committed successfully"
            else:
                error_msg = f"Failed to commit file: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Commit operation failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

    def _get_file_sha(self, owner: str, repo_name: str) -> str:
        """Get the SHA of the current file if it exists."""
        try:
            file_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{self.target_file}"
            response = requests.get(file_url, headers=self.headers)
            
            if response.status_code == 200:
                file_data = response.json()
                return file_data['sha']
            elif response.status_code == 404:
                # File doesn't exist yet
                return None
            else:
                print(f"⚠️ Warning: Could not check existing file: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Warning: Error checking existing file: {str(e)}")
            return None

    def verify_commit(self, owner: str, repo_name: str, commit_sha: str) -> bool:
        """Verify that the commit was successful."""
        try:
            commit_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits/{commit_sha}"
            response = requests.get(commit_url, headers=self.headers)
            
            if response.status_code == 200:
                commit_data = response.json()
                print(f"✅ Commit verified: {commit_data['commit']['message']}")
                return True
            else:
                print(f"⚠️ Could not verify commit: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error verifying commit: {str(e)}")
            return False

    def get_file_url(self, owner: str, repo_name: str) -> str:
        """Get the GitHub URL for the committed file."""
        return f"https://github.com/{owner}/{repo_name}/blob/main/{self.target_file}"
