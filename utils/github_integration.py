"""
GitHub Integration Module

Provides functionality to create Pull Requests with modernized code.
Supports creating branches, committing files, and opening PRs.
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import requests

# Setup logger
logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Handle GitHub operations for code modernization workflow."""
    
    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        """
        Initialize GitHub integration.
        
        Args:
            token: GitHub personal access token
            repo: Repository in format 'owner/repo'
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repo = repo or os.getenv('GITHUB_REPO')
        self.base_branch = os.getenv('GITHUB_DEFAULT_BRANCH', 'main')
        
        if not self.token:
            raise ValueError("GitHub token not provided. Set GITHUB_TOKEN environment variable.")
        
        if not self.repo:
            raise ValueError("GitHub repository not provided. Set GITHUB_REPO environment variable.")
        
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        # Validate credentials
        self._validate_credentials()
    
    def _validate_credentials(self) -> None:
        """Validate GitHub credentials and repository access."""
        try:
            response = requests.get(
                f"{self.api_base}/repos/{self.repo}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 404:
                raise ValueError(f"Repository '{self.repo}' not found or no access")
            elif response.status_code == 401:
                raise ValueError("Invalid GitHub token")
            elif response.status_code != 200:
                raise ValueError(f"GitHub API error: {response.status_code}")
            
            logger.info(f"GitHub credentials validated for repo: {self.repo}")
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to GitHub: {str(e)}")
    
    def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """
        Create a new branch from the base branch.
        
        Args:
            branch_name: Name of the new branch
            
        Returns:
            Dict with branch information
        """
        try:
            # Get the SHA of the base branch
            ref_url = f"{self.api_base}/repos/{self.repo}/git/ref/heads/{self.base_branch}"
            response = requests.get(ref_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get base branch: {response.text}")
            
            base_sha = response.json()['object']['sha']
            
            # Create new branch
            create_url = f"{self.api_base}/repos/{self.repo}/git/refs"
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
            
            response = requests.post(
                create_url,
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 422:
                # Branch already exists
                logger.warning(f"Branch '{branch_name}' already exists")
                return {"branch": branch_name, "sha": base_sha, "exists": True}
            elif response.status_code != 201:
                raise ValueError(f"Failed to create branch: {response.text}")
            
            logger.info(f"Created branch: {branch_name}")
            return {"branch": branch_name, "sha": base_sha, "exists": False}
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to create branch: {str(e)}")
    
    def commit_files(
        self,
        branch_name: str,
        files: List[Dict[str, str]],
        commit_message: str
    ) -> Dict[str, Any]:
        """
        Commit multiple files to a branch.
        
        Args:
            branch_name: Target branch name
            files: List of dicts with 'path' and 'content' keys
            commit_message: Commit message
            
        Returns:
            Dict with commit information
        """
        try:
            committed_files = []
            
            for file_info in files:
                file_path = file_info['path']
                content = file_info['content']
                
                # Encode content to base64
                content_bytes = content.encode('utf-8')
                content_base64 = base64.b64encode(content_bytes).decode('utf-8')
                
                # Check if file exists
                file_url = f"{self.api_base}/repos/{self.repo}/contents/{file_path}"
                params = {"ref": branch_name}
                response = requests.get(file_url, headers=self.headers, params=params, timeout=10)
                
                sha = None
                if response.status_code == 200:
                    sha = response.json()['sha']
                
                # Create or update file
                data = {
                    "message": commit_message,
                    "content": content_base64,
                    "branch": branch_name
                }
                
                if sha:
                    data["sha"] = sha
                
                response = requests.put(
                    file_url,
                    headers=self.headers,
                    json=data,
                    timeout=10
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Failed to commit {file_path}: {response.text}")
                    continue
                
                committed_files.append(file_path)
                logger.info(f"Committed file: {file_path}")
            
            return {
                "success": True,
                "committed_files": committed_files,
                "total": len(committed_files)
            }
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to commit files: {str(e)}")
    
    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            branch_name: Source branch name
            title: PR title
            body: PR description
            labels: Optional list of labels
            
        Returns:
            Dict with PR information including URL
        """
        try:
            pr_url = f"{self.api_base}/repos/{self.repo}/pulls"
            
            data = {
                "title": title,
                "body": body,
                "head": branch_name,
                "base": self.base_branch
            }
            
            response = requests.post(
                pr_url,
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code != 201:
                raise ValueError(f"Failed to create PR: {response.text}")
            
            pr_data = response.json()
            pr_number = pr_data['number']
            pr_html_url = pr_data['html_url']
            
            logger.info(f"Created PR #{pr_number}: {pr_html_url}")
            
            # Add labels if provided
            if labels:
                self._add_labels_to_pr(pr_number, labels)
            
            return {
                "success": True,
                "pr_number": pr_number,
                "pr_url": pr_html_url,
                "branch": branch_name
            }
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to create pull request: {str(e)}")
    
    def _add_labels_to_pr(self, pr_number: int, labels: List[str]) -> None:
        """Add labels to a pull request."""
        try:
            labels_url = f"{self.api_base}/repos/{self.repo}/issues/{pr_number}/labels"
            
            response = requests.post(
                labels_url,
                headers=self.headers,
                json={"labels": labels},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Added labels to PR #{pr_number}: {labels}")
            else:
                logger.warning(f"Failed to add labels: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to add labels: {str(e)}")
    
    def create_modernization_pr(
        self,
        source_file: str,
        modernized_files: List[str],
        analysis_summary: Dict[str, Any],
        output_dir: str = "output"
    ) -> Dict[str, Any]:
        """
        Create a complete PR for code modernization.
        
        Args:
            source_file: Original source file name
            modernized_files: List of modernized file paths
            analysis_summary: Analysis results summary
            output_dir: Output directory containing all files
            
        Returns:
            Dict with PR creation results
        """
        try:
            # Generate branch name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            source_name = Path(source_file).stem
            branch_name = f"modernize/{source_name}-{timestamp}"
            
            # Create branch
            logger.info(f"Creating branch: {branch_name}")
            branch_info = self.create_branch(branch_name)
            
            # Prepare files to commit
            files_to_commit = []
            
            # Add modernized code files
            for file_path in modernized_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Use relative path for GitHub
                    rel_path = os.path.relpath(file_path, '.')
                    files_to_commit.append({
                        "path": rel_path.replace('\\', '/'),
                        "content": content
                    })
            
            # Add documentation files
            docs_dir = os.path.join(output_dir, "documentation")
            if os.path.exists(docs_dir):
                for doc_file in ["README.md", "ARCHITECTURE.md", "DEPENDENCIES.md", "TECHNICAL_DEBT.md"]:
                    doc_path = os.path.join(docs_dir, doc_file)
                    if os.path.exists(doc_path):
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        rel_path = os.path.relpath(doc_path, '.')
                        files_to_commit.append({
                            "path": rel_path.replace('\\', '/'),
                            "content": content
                        })
            
            # Commit files
            commit_message = f"Modernize {source_file} to modern code\n\nAutomated modernization by Legacy Code Modernization Squad"
            logger.info(f"Committing {len(files_to_commit)} files...")
            commit_result = self.commit_files(branch_name, files_to_commit, commit_message)
            
            # Generate PR body
            pr_body = self._generate_pr_body(source_file, analysis_summary, commit_result)
            
            # Create PR
            pr_title = f"🔄 Modernize {source_file}"
            logger.info("Creating pull request...")
            pr_result = self.create_pull_request(
                branch_name=branch_name,
                title=pr_title,
                body=pr_body,
                labels=["modernization", "automated", "ai-generated"]
            )
            
            return {
                "success": True,
                "pr_url": pr_result['pr_url'],
                "pr_number": pr_result['pr_number'],
                "branch": branch_name,
                "files_committed": commit_result['committed_files']
            }
            
        except Exception as e:
            logger.error(f"Failed to create modernization PR: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_pr_body(
        self,
        source_file: str,
        analysis_summary: Dict[str, Any],
        commit_result: Dict[str, Any]
    ) -> str:
        """Generate PR description body."""
        
        metrics = analysis_summary.get('metrics', {})
        
        body = f"""## 🔄 Code Modernization

This PR contains the automated modernization of `{source_file}` using AI-powered analysis and refactoring.

### 📊 Analysis Summary

- **Total Lines:** {metrics.get('total_lines', 'N/A')}
- **Functions:** {metrics.get('total_functions', 'N/A')}
- **Average Complexity:** {metrics.get('avg_complexity', 'N/A')}
- **Dependencies:** {len(analysis_summary.get('dependencies', []))}

### 📝 Changes

This PR includes:

"""
        
        for file_path in commit_result.get('committed_files', []):
            body += f"- ✨ `{file_path}`\n"
        
        body += """
### 🤖 Generated By

**Legacy Code Modernization Squad**
- Powered by IBM watsonx and Granite AI
- Automated analysis, documentation, and refactoring

### ⚠️ Review Notes

This code was automatically generated. Please review carefully:

1. ✅ Verify business logic is preserved
2. ✅ Check error handling
3. ✅ Review test coverage
4. ✅ Validate dependencies

### 📚 Documentation

Complete documentation has been generated and included in this PR:
- README.md - Project overview
- ARCHITECTURE.md - System architecture
- DEPENDENCIES.md - Dependency analysis
- TECHNICAL_DEBT.md - Technical debt report

---

*Generated automatically by Legacy Code Modernization Squad*
"""
        
        return body


def create_github_pr_from_workflow(
    source_file: str,
    output_dir: str = "output",
    token: Optional[str] = None,
    repo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to create PR from workflow output.
    
    Args:
        source_file: Original source file name
        output_dir: Output directory with modernization results
        token: Optional GitHub token (uses env var if not provided)
        repo: Optional repo name (uses env var if not provided)
        
    Returns:
        Dict with PR creation results
    """
    try:
        # Initialize GitHub integration
        gh = GitHubIntegration(token=token, repo=repo)
        
        # Find modernized files
        modernized_dir = os.path.join(output_dir, "modernized")
        modernized_files = []
        
        if os.path.exists(modernized_dir):
            for file in os.listdir(modernized_dir):
                if file.endswith(('.py', '.java')) and not file.startswith('test_'):
                    modernized_files.append(os.path.join(modernized_dir, file))
        
        if not modernized_files:
            return {
                "success": False,
                "error": "No modernized files found"
            }
        
        # Load analysis summary
        analysis_path = os.path.join(output_dir, "analysis", "analysis_report.json")
        analysis_summary = {}
        
        if os.path.exists(analysis_path):
            with open(analysis_path, 'r') as f:
                analysis_summary = json.load(f)
        
        # Create PR
        return gh.create_modernization_pr(
            source_file=source_file,
            modernized_files=modernized_files,
            analysis_summary=analysis_summary,
            output_dir=output_dir
        )
        
    except Exception as e:
        logger.error(f"Failed to create PR: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Made with Bob
