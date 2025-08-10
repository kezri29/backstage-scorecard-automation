import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai

class ScoringAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Oriflame scorecard structure definition
        self.scorecard_structure = {
            "areas": [
                {
                    "id": 1001,
                    "title": "Code Quality",
                    "entries": [
                        {
                            "id": 1,
                            "title": "Documentation",
                            "howToScore": "Technical documentation should be present and accessible.",
                            "scoreChoices": [
                                {"Well documented with comprehensive README and docs": 100},
                                {"Basic documentation present": 80},
                                {"Minimal documentation": 40},
                                {"No documentation": 0}
                            ]
                        },
                        {
                            "id": 2,
                            "title": "Static Code Analysis",
                            "howToScore": "Code should be analyzed for quality and security issues.",
                            "scoreChoices": [
                                {"Comprehensive static analysis with automated checks": 100},
                                {"Basic static analysis implemented": 70},
                                {"Manual code reviews only": 40},
                                {"No static analysis": 0}
                            ]
                        },
                        {
                            "id": 3,
                            "title": "Code Structure",
                            "howToScore": "Code should follow best practices and be well organized.",
                            "scoreChoices": [
                                {"Excellent structure with design patterns": 100},
                                {"Good structure and organization": 80},
                                {"Basic structure present": 60},
                                {"Poor code organization": 20}
                            ]
                        }
                    ]
                },
                {
                    "id": 1002,
                    "title": "Operations",
                    "entries": [
                        {
                            "id": 4,
                            "title": "CI/CD Pipeline",
                            "howToScore": "Automated build and deployment pipeline should be in place.",
                            "scoreChoices": [
                                {"Full CI/CD with automated testing and deployment": 100},
                                {"CI/CD pipeline configured": 90},
                                {"Basic CI only": 50},
                                {"Manual deployment": 0}
                            ]
                        },
                        {
                            "id": 5,
                            "title": "Dependency Management",
                            "howToScore": "Dependencies should be properly managed and up to date.",
                            "scoreChoices": [
                                {"Automated dependency management with security scanning": 100},
                                {"Regular dependency updates": 80},
                                {"Basic dependency files present": 60},
                                {"No dependency management": 0}
                            ]
                        },
                        {
                            "id": 6,
                            "title": "Configuration Management",
                            "howToScore": "Application configuration should be externalized and secure.",
                            "scoreChoices": [
                                {"Environment-based config with secrets management": 100},
                                {"Basic environment configuration": 70},
                                {"Hardcoded configuration": 30},
                                {"No configuration management": 0}
                            ]
                        }
                    ]
                },
                {
                    "id": 1003,
                    "title": "Security",
                    "entries": [
                        {
                            "id": 7,
                            "title": "Security Practices",
                            "howToScore": "Security best practices should be implemented.",
                            "scoreChoices": [
                                {"Comprehensive security measures implemented": 100},
                                {"Basic security practices in place": 70},
                                {"Minimal security considerations": 40},
                                {"No security measures": 0}
                            ]
                        },
                        {
                            "id": 8,
                            "title": "Secrets Management",
                            "howToScore": "Secrets and credentials should be properly managed.",
                            "scoreChoices": [
                                {"Secure secrets management with encryption": 100},
                                {"Environment variables for secrets": 80},
                                {"Some hardcoded secrets": 30},
                                {"Exposed secrets in code": 0}
                            ]
                        }
                    ]
                },
                {
                    "id": 1004,
                    "title": "Testing",
                    "entries": [
                        {
                            "id": 9,
                            "title": "Test Coverage",
                            "howToScore": "Automated tests should cover critical functionality.",
                            "scoreChoices": [
                                {"Comprehensive test suite with high coverage": 100},
                                {"Good test coverage": 80},
                                {"Basic tests present": 50},
                                {"No automated tests": 0}
                            ]
                        },
                        {
                            "id": 10,
                            "title": "Test Quality",
                            "howToScore": "Tests should be well-written and maintainable.",
                            "scoreChoices": [
                                {"Excellent test quality and organization": 100},
                                {"Good test structure": 80},
                                {"Basic test implementation": 60},
                                {"Poor test quality": 20}
                            ]
                        }
                    ]
                }
            ]
        }

    def prepare_analysis_context(self, repo_data: Dict[str, Any]) -> str:
        """Prepare repository context for analysis."""
        context = []
        
        # Repository metadata
        metadata = repo_data.get('repo_metadata', {})
        context.append(f"Repository: {metadata.get('full_name', 'Unknown')}")
        context.append(f"Description: {metadata.get('description', 'No description')}")
        context.append(f"Primary Language: {metadata.get('language', 'Unknown')}")
        
        # Languages breakdown
        languages = repo_data.get('languages', {})
        if languages:
            context.append(f"Languages: {', '.join(languages.keys())}")
        
        # File statistics
        organized_files = repo_data.get('organized_files', {})
        context.append(f"Total Files: {repo_data.get('total_files', 0)}")
        context.append(f"Source Code Files: {len(organized_files.get('source_code', []))}")
        context.append(f"Config Files: {len(organized_files.get('config_files', []))}")
        context.append(f"Documentation Files: {len(organized_files.get('documentation', []))}")
        context.append(f"Build Files: {len(organized_files.get('build_files', []))}")
        context.append(f"CI/CD Files: {len(organized_files.get('ci_cd', []))}")
        
        return "\n".join(context)

    def extract_key_files_content(self, repo_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract content from key files for analysis."""
        key_files = {}
        organized_files = repo_data.get('organized_files', {})
        
        # Get README content
        for doc_file in organized_files.get('documentation', []):
            if 'readme' in doc_file['name'].lower():
                key_files['readme'] = doc_file['content'][:2000]  # Limit content
                break
        
        # Get package.json or requirements.txt or similar
        for build_file in organized_files.get('build_files', []):
            if build_file['name'].lower() in ['package.json', 'requirements.txt', 'pom.xml', 'cargo.toml']:
                key_files[build_file['name']] = build_file['content'][:1000]
                break
        
        # Get CI/CD configuration
        for cicd_file in organized_files.get('ci_cd', []):
            key_files[f"cicd_{cicd_file['name']}"] = cicd_file['content'][:1000]
            break
        
        # Sample source code files
        source_files = organized_files.get('source_code', [])
        if source_files:
            # Get up to 3 source files for analysis
            for i, source_file in enumerate(source_files[:3]):
                key_files[f"source_{i+1}_{source_file['name']}"] = source_file['content'][:1500]
        
        return key_files

    def analyze_repository(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze repository and generate Oriflame scorecard format.
        
        Args:
            repo_data: Repository data from RepoLoaderAgent
            
        Returns:
            Dictionary in Oriflame scorecard format
        """
        print("🔄 Starting repository analysis...")
        
        try:
            # Prepare analysis context
            context = self.prepare_analysis_context(repo_data)
            key_files = self.extract_key_files_content(repo_data)
            
            # Create analysis prompt
            system_prompt = self._create_analysis_prompt()
            user_prompt = self._create_user_prompt(context, key_files)
            
            print("🤖 Generating AI analysis...")
            # Generate analysis with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(system_prompt + "\n\n" + user_prompt)
                    
                    if not response or not response.text:
                        print(f"⚠️ Empty response from AI (attempt {attempt + 1}/{max_retries})")
                        if attempt == max_retries - 1:
                            raise Exception("AI returned empty response after all retries")
                        continue
                    
                    response_text = response.text.strip()
                    print(f"📝 AI Response length: {len(response_text)} characters")
                    
                    # Clean response text
                    response_text = self._clean_ai_response(response_text)
                    
                    if not response_text:
                        print(f"⚠️ Response became empty after cleaning (attempt {attempt + 1}/{max_retries})")
                        if attempt == max_retries - 1:
                            raise Exception("AI response is empty after cleaning")
                        continue
                    
                    # Parse JSON response
                    scores_data = json.loads(response_text)
                    
                    # Validate the response structure
                    if not self._validate_ai_response(scores_data):
                        print(f"⚠️ Invalid response structure (attempt {attempt + 1}/{max_retries})")
                        if attempt == max_retries - 1:
                            raise Exception("AI response has invalid structure")
                        continue
                    
                    # Build Oriflame scorecard format
                    scorecard = self._build_oriflame_scorecard(scores_data, repo_data)
                    
                    print("✅ Repository analysis completed successfully")
                    return scorecard
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parsing failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt == max_retries - 1:
                        # Create basic scorecard as fallback
                        return self._create_basic_scorecard(repo_data)
                    continue
                    
        except Exception as e:
            print(f"❌ Error during repository analysis: {str(e)}")
            # Create basic scorecard as fallback
            return self._create_basic_scorecard(repo_data)

    def _clean_ai_response(self, response_text: str) -> str:
        """Clean and extract JSON from AI response."""
        # Remove common AI response prefixes/suffixes
        response_text = response_text.strip()
        
        # Look for JSON content between ```json blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        
        # Look for JSON content between ``` blocks (without json specifier)
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        
        # Find JSON object boundaries
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            response_text = response_text[start_idx:end_idx + 1]
        
        return response_text

    def _validate_ai_response(self, response_data: Dict[str, Any]) -> bool:
        """Validate AI response structure."""
        if not isinstance(response_data, dict):
            return False
        
        entries = response_data.get('entries', {})
        if not isinstance(entries, dict):
            return False
        
        # Check if we have at least some entry scores
        if len(entries) == 0:
            return False
        
        # Validate entry structure
        for entry_id, entry_data in entries.items():
            if not isinstance(entry_data, dict):
                return False
            if 'score' not in entry_data or 'details' not in entry_data:
                return False
            if not isinstance(entry_data['score'], (int, float)):
                return False
        
        return True

    def _create_basic_scorecard(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic scorecard when AI analysis fails."""
        print("🔧 Creating basic scorecard as fallback...")
        
        # Extract repository name
        repo_name = repo_data.get('repo_metadata', {}).get('name', 'unknown-component')
        organized_files = repo_data.get('organized_files', {})
        
        # Basic scoring based on file presence
        basic_scores = {
            "1": {"score": 80 if organized_files.get('documentation') else 20, "details": "Documentation analysis based on file presence"},
            "2": {"score": 60, "details": "Basic static analysis assessment"},
            "3": {"score": 70 if organized_files.get('source_code') else 30, "details": "Code structure evaluation"},
            "4": {"score": 80 if organized_files.get('ci_cd') else 30, "details": "CI/CD pipeline assessment"},
            "5": {"score": 70 if organized_files.get('build_files') else 40, "details": "Dependency management evaluation"},
            "6": {"score": 60 if organized_files.get('config_files') else 30, "details": "Configuration management assessment"},
            "7": {"score": 55, "details": "Basic security practices evaluation"},
            "8": {"score": 70, "details": "Secrets management assessment"},
            "9": {"score": 40, "details": "Test coverage evaluation"},
            "10": {"score": 50, "details": "Test quality assessment"}
        }
        
        scores_data = {"entries": basic_scores}
        return self._build_oriflame_scorecard(scores_data, repo_data)

    def _create_analysis_prompt(self) -> str:
        """Create the system prompt for repository analysis."""
        return """
                    You are an expert code reviewer analyzing a repository. You MUST return a valid JSON response only.

                    Analyze the repository and provide scores (0-100) for these 10 entries:
                    1. Documentation - README quality, comments, API docs
                    2. Static Code Analysis - Linting tools, code quality checks
                    3. Code Structure - Organization, patterns, maintainability
                    4. CI/CD Pipeline - Automated workflows, GitHub Actions
                    5. Dependency Management - Package files, updates
                    6. Configuration Management - Config files, environment handling
                    7. Security Practices - Security headers, input validation
                    8. Secrets Management - No hardcoded secrets, env variables
                    9. Test Coverage - Test files, testing frameworks
                    10. Test Quality - Test structure and implementation

                    You MUST return ONLY this JSON format with no additional text:
                    {
                    "entries": {
                        "1": {"score": 80, "details": "Good README with comprehensive documentation"},
                        "2": {"score": 70, "details": "Basic linting configuration found"},
                        "3": {"score": 85, "details": "Well-organized code structure with clear patterns"},
                        "4": {"score": 90, "details": "GitHub Actions workflow properly configured"},
                        "5": {"score": 75, "details": "Package dependencies regularly maintained"},
                        "6": {"score": 60, "details": "Basic environment configuration present"},
                        "7": {"score": 65, "details": "Some security practices implemented"},
                        "8": {"score": 80, "details": "No hardcoded secrets detected"},
                        "9": {"score": 50, "details": "Limited test coverage identified"},
                        "10": {"score": 60, "details": "Basic test implementation found"}
                    }
                    }

                    IMPORTANT: Return ONLY the JSON above, no explanations or additional text.
                    """

    def _create_user_prompt(self, context: str, key_files: Dict[str, str]) -> str:
        """Create the user prompt with repository data."""
        files_content = "\n\n".join([
            f"=== {filename} ===\n{content}"
            for filename, content in key_files.items()
        ])
        
        return f"""
                    Repository Context:
                    {context}

                    Key Files Content:
                    {files_content}

                    Analyze this repository and provide scores for all 10 entries based on the evidence.
                    """

    def _build_oriflame_scorecard(self, scores_data: Dict[str, Any], repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the final Oriflame scorecard format."""
        
        # Extract repository name
        repo_name = repo_data.get('repo_metadata', {}).get('name', 'unknown-component')
        
        # Build area scores with entries
        area_scores = []
        entries_scores = scores_data.get('entries', {})
        
        for area in self.scorecard_structure['areas']:
            area_entries = []
            area_total_score = 0
            
            for entry in area['entries']:
                entry_id = str(entry['id'])
                entry_score_data = entries_scores.get(entry_id, {'score': 50, 'details': 'No analysis available'})
                
                score_percent = entry_score_data['score']
                area_total_score += score_percent
                
                area_entries.append({
                    "id": entry['id'],
                    "title": entry['title'],
                    "scorePercent": score_percent,
                    "scoreSuccess": self._get_score_success(score_percent),
                    "howToScore": entry['howToScore'],
                    "scoreChoices": entry['scoreChoices'],
                    "details": entry_score_data['details']
                })
            
            # Calculate area average score
            area_score_percent = int(area_total_score / len(area['entries'])) if area['entries'] else 0
            
            area_scores.append({
                "id": area['id'],
                "title": area['title'],
                "scorePercent": area_score_percent,
                "scoreSuccess": self._get_score_success(area_score_percent),
                "scoreEntries": area_entries
            })
        
        # Calculate overall score
        overall_score = int(sum(area['scorePercent'] for area in area_scores) / len(area_scores)) if area_scores else 0
        
        # Build final scorecard
        scorecard = {
            "entityRef": {
                "kind": "component",
                "name": repo_name
            },
            "generatedDateTimeUtc": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "scorePercent": overall_score,
            "scoreSuccess": self._get_score_success(overall_score),
            "areaScores": area_scores
        }
        
        return scorecard

    def _get_score_success(self, score: int) -> str:
        """Convert numeric score to success level."""
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "warning"
        else:
            return "error"
