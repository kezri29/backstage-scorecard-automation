import os
import requests
import base64
from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import urlparse
import json

class RepoLoaderAgent:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.github_token}" if self.github_token else {},
            "Accept": "application/vnd.github.v3+json"
        }
        
        # File extensions to analyze
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', 
            '.go', '.rb', '.php', '.swift', '.kt', '.rs', '.scala', '.sh',
            '.yml', '.yaml', '.json', '.xml', '.dockerfile', '.tf'
        }
        
        # Config files to prioritize
        self.config_files = {
            'package.json', 'requirements.txt', 'pom.xml', 'build.gradle',
            'Dockerfile', 'docker-compose.yml', 'catalog-info.yaml',
            '.github/workflows', 'terraform', 'k8s', 'kubernetes'
        }

    def parse_github_url(self, repo_url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract owner and repo name from GitHub URL."""
        try:
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1].replace('.git', '')
                return owner, repo
            
            return None, None
        except Exception as e:
            print(f"Error parsing GitHub URL: {str(e)}")
            return None, None

    def get_repo_contents(self, owner: str, repo: str, path: str = "") -> List[Dict[str, Any]]:
        """Get repository contents from GitHub API."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch contents: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching repo contents: {str(e)}")
            return []

    def get_file_content(self, owner: str, repo: str, file_path: str) -> Optional[str]:
        """Get content of a specific file."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                file_data = response.json()
                
                if file_data.get('encoding') == 'base64':
                    content = base64.b64decode(file_data['content']).decode('utf-8')
                    return content
                    
            return None
            
        except Exception as e:
            print(f"Error fetching file content: {str(e)}")
            return None

    def is_relevant_file(self, file_name: str, file_path: str) -> bool:
        """Check if file is relevant for analysis."""
        # Check file extension
        _, ext = os.path.splitext(file_name.lower())
        if ext in self.code_extensions:
            return True
            
        # Check config files
        if any(config in file_path.lower() for config in self.config_files):
            return True
            
        # Check specific important files
        important_files = {
            'readme.md', 'readme.txt', 'license', 'changelog.md',
            'contributing.md', 'security.md', 'makefile'
        }
        
        if file_name.lower() in important_files:
            return True
            
        return False

    def traverse_repository(self, owner: str, repo: str, path: str = "", max_depth: int = 10) -> List[Dict[str, Any]]:
        """Recursively traverse repository and collect relevant files."""
        if max_depth <= 0:
            return []
            
        files_data = []
        contents = self.get_repo_contents(owner, repo, path)
        
        for item in contents:
            item_path = item['path']
            item_name = item['name']
            
            if item['type'] == 'file':
                if self.is_relevant_file(item_name, item_path):
                    file_content = self.get_file_content(owner, repo, item_path)
                    
                    if file_content:
                        files_data.append({
                            'path': item_path,
                            'name': item_name,
                            'type': item['type'],
                            'size': item['size'],
                            'content': file_content,
                            'extension': os.path.splitext(item_name)[1].lower()
                        })
                        
            elif item['type'] == 'dir':
                # Skip certain directories
                skip_dirs = {'.git', 'node_modules', '__pycache__', '.pytest_cache', 
                           'venv', 'env', 'target', 'build', 'dist', '.next'}
                
                if item_name not in skip_dirs:
                    subdir_files = self.traverse_repository(
                        owner, repo, item_path, max_depth - 1
                    )
                    files_data.extend(subdir_files)
        
        return files_data

    def get_repo_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository metadata."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                repo_data = response.json()
                return {
                    'name': repo_data.get('name'),
                    'full_name': repo_data.get('full_name'),
                    'description': repo_data.get('description'),
                    'language': repo_data.get('language'),
                    'languages_url': repo_data.get('languages_url'),
                    'created_at': repo_data.get('created_at'),
                    'updated_at': repo_data.get('updated_at'),
                    'size': repo_data.get('size'),
                    'stargazers_count': repo_data.get('stargazers_count'),
                    'forks_count': repo_data.get('forks_count'),
                    'open_issues_count': repo_data.get('open_issues_count'),
                    'topics': repo_data.get('topics', []),
                    'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None
                }
                
            return {}
            
        except Exception as e:
            print(f"Error fetching repo metadata: {str(e)}")
            return {}

    def get_repo_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get programming languages used in the repository."""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/languages"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
                
            return {}
            
        except Exception as e:
            print(f"Error fetching repo languages: {str(e)}")
            return {}

    def load_repository(self, repo_url: str) -> Tuple[Dict[str, Any], str]:
        """Main method to load repository data."""
        print(f"🔄 Loading repository: {repo_url}")
        
        try:
            # Parse GitHub URL
            owner, repo = self.parse_github_url(repo_url)
            
            if not owner or not repo:
                return {}, "Invalid GitHub repository URL"
            
            print(f"📁 Repository: {owner}/{repo}")
            
            # Get repository metadata
            repo_metadata = self.get_repo_metadata(owner, repo)
            if not repo_metadata:
                return {}, "Failed to fetch repository metadata"
            
            # Get programming languages
            languages = self.get_repo_languages(owner, repo)
            
            # Traverse and load files
            print("📂 Scanning repository files...")
            files_data = self.traverse_repository(owner, repo)
            
            if not files_data:
                return {}, "No relevant files found in repository"
            
            # Organize files by type
            organized_files = self._organize_files_by_type(files_data)
            
            result = {
                'repo_metadata': repo_metadata,
                'languages': languages,
                'files_data': files_data,
                'organized_files': organized_files,
                'total_files': len(files_data),
                'owner': owner,
                'repo_name': repo
            }
            
            print(f"✅ Successfully loaded {len(files_data)} files from repository")
            return result, "Repository loaded successfully"
            
        except Exception as e:
            error_msg = f"Error loading repository: {str(e)}"
            print(f"❌ {error_msg}")
            return {}, error_msg

    def _organize_files_by_type(self, files_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize files by their type/category."""
        organized = {
            'source_code': [],
            'config_files': [],
            'documentation': [],
            'build_files': [],
            'ci_cd': [],
            'other': []
        }
        
        for file_data in files_data:
            file_path = file_data['path'].lower()
            file_name = file_data['name'].lower()
            extension = file_data['extension']
            
            # Source code files
            if extension in {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.rs', '.scala'}:
                organized['source_code'].append(file_data)
            
            # Configuration files
            elif extension in {'.json', '.yml', '.yaml', '.xml', '.toml', '.ini', '.conf'} or file_name in {'dockerfile', 'makefile'}:
                organized['config_files'].append(file_data)
            
            # Documentation
            elif extension in {'.md', '.txt', '.rst'} or 'readme' in file_name:
                organized['documentation'].append(file_data)
            
            # Build files
            elif file_name in {'package.json', 'requirements.txt', 'pom.xml', 'build.gradle', 'setup.py', 'cargo.toml'}:
                organized['build_files'].append(file_data)
            
            # CI/CD files
            elif '.github/workflows' in file_path or 'jenkins' in file_path or file_name.startswith('.gitlab-ci'):
                organized['ci_cd'].append(file_data)
            
            # Other files
            else:
                organized['other'].append(file_data)
        
        return organized
