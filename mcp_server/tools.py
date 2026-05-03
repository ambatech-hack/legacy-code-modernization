"""
MCP Server Tools Implementation

This module implements all MCP tools exposed to agents:
1. read_file - Safely read file contents
2. write_file - Safely write content to files
3. run_tests - Execute pytest in specified directory
4. create_pull_request - Create GitHub pull request
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from loguru import logger
from github import Github, GithubException

from .config import get_config


class SecurityError(Exception):
    """Raised when a security validation fails"""
    pass


class ToolExecutionError(Exception):
    """Raised when a tool execution fails"""
    pass


def validate_path(path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Validate that a path is safe and within the allowed workspace.
    
    Args:
        path: The path to validate
        base_dir: Base directory to validate against (defaults to workspace)
    
    Returns:
        Path: The validated absolute path
    
    Raises:
        SecurityError: If path validation fails
    """
    config = get_config()
    
    if not config.enable_path_validation:
        return Path(path).resolve()
    
    if base_dir is None:
        base_dir = config.get_workspace_path()
    
    try:
        # Convert to absolute path and resolve
        abs_path = Path(path).resolve()
        base_dir = base_dir.resolve()
        
        # Check if path is within base directory
        try:
            abs_path.relative_to(base_dir)
        except ValueError:
            raise SecurityError(
                f"Path '{path}' is outside workspace directory '{base_dir}'"
            )
        
        # Check for path traversal attempts
        if ".." in path or path.startswith("/") or (os.name == 'nt' and ":" in path[1:]):
            raise SecurityError(f"Path contains invalid characters: {path}")
        
        return abs_path
        
    except Exception as e:
        if isinstance(e, SecurityError):
            raise
        raise SecurityError(f"Path validation failed: {str(e)}")


def validate_file_size(file_path: Path) -> None:
    """
    Validate that a file size is within limits.
    
    Args:
        file_path: Path to the file
    
    Raises:
        SecurityError: If file size exceeds limit
    """
    config = get_config()
    
    if file_path.exists():
        size = file_path.stat().st_size
        max_size = config.max_file_size_bytes
        
        if size > max_size:
            raise SecurityError(
                f"File size {size} bytes exceeds maximum {max_size} bytes"
            )


def sanitize_content(content: str) -> str:
    """
    Sanitize content to remove potentially harmful patterns.
    
    Args:
        content: The content to sanitize
    
    Returns:
        str: Sanitized content
    """
    config = get_config()
    
    if not config.enable_content_sanitization:
        return content
    
    # Remove null bytes
    content = content.replace('\x00', '')
    
    # Ensure content is valid UTF-8
    try:
        content.encode('utf-8')
    except UnicodeEncodeError:
        logger.warning("Content contains invalid UTF-8 characters, attempting to fix")
        content = content.encode('utf-8', errors='ignore').decode('utf-8')
    
    return content


def create_backup(file_path: Path) -> Optional[Path]:
    """
    Create a backup of a file before modification.
    
    Args:
        file_path: Path to the file to backup
    
    Returns:
        Optional[Path]: Path to backup file, or None if backup disabled
    """
    config = get_config()
    
    if not config.backup_enabled or not file_path.exists():
        return None
    
    try:
        backup_dir = config.get_backup_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return None


# Tool 1: read_file
def read_file(path: str) -> Dict[str, Any]:
    """
    Safely read file contents.
    
    Args:
        path: Relative path to file (validated against workspace)
    
    Returns:
        dict: {
            "success": bool,
            "content": str (file contents if successful),
            "path": str (absolute path),
            "size": int (file size in bytes),
            "error": str (error message if failed)
        }
    
    Example:
        >>> result = read_file("src/main.py")
        >>> if result["success"]:
        ...     print(result["content"])
    """
    try:
        logger.info(f"Reading file: {path}")
        
        # Validate path
        file_path = validate_path(path)
        
        # Check file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        # Validate file size
        validate_file_size(file_path)
        
        # Check file extension
        config = get_config()
        if not config.is_allowed_extension(file_path.name):
            raise ValueError(
                f"File extension not allowed: {file_path.suffix}. "
                f"Allowed: {config.allowed_extensions}"
            )
        
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with different encoding
            content = file_path.read_text(encoding='latin-1')
            logger.warning(f"File read with latin-1 encoding: {path}")
        
        logger.info(f"Successfully read file: {path} ({len(content)} chars)")
        
        return {
            "success": True,
            "content": content,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "error": None
        }
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        return {
            "success": False,
            "content": None,
            "path": path,
            "size": 0,
            "error": f"FileNotFoundError: {str(e)}"
        }
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        return {
            "success": False,
            "content": None,
            "path": path,
            "size": 0,
            "error": f"PermissionError: {str(e)}"
        }
    except SecurityError as e:
        logger.error(f"Security error: {str(e)}")
        return {
            "success": False,
            "content": None,
            "path": path,
            "size": 0,
            "error": f"SecurityError: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error reading file: {str(e)}")
        return {
            "success": False,
            "content": None,
            "path": path,
            "size": 0,
            "error": f"Error: {str(e)}"
        }


# Tool 2: write_file
def write_file(path: str, content: str) -> Dict[str, Any]:
    """
    Safely write content to file.
    
    Args:
        path: Relative path to file
        content: File content to write
    
    Returns:
        dict: {
            "success": bool,
            "path": str (absolute path of written file),
            "size": int (file size in bytes),
            "backup_path": str (path to backup if created),
            "error": str (error message if failed)
        }
    
    Example:
        >>> result = write_file("output/result.txt", "Hello, World!")
        >>> if result["success"]:
        ...     print(f"File written to: {result['path']}")
    """
    backup_path = None
    
    try:
        logger.info(f"Writing file: {path}")
        
        # Validate path
        file_path = validate_path(path)
        
        # Check file extension
        config = get_config()
        if not config.is_allowed_extension(file_path.name):
            raise ValueError(
                f"File extension not allowed: {file_path.suffix}. "
                f"Allowed: {config.allowed_extensions}"
            )
        
        # Sanitize content
        content = sanitize_content(content)
        
        # Check content size
        content_size = len(content.encode('utf-8'))
        if content_size > config.max_file_size_bytes:
            raise SecurityError(
                f"Content size {content_size} bytes exceeds maximum "
                f"{config.max_file_size_bytes} bytes"
            )
        
        # Create backup if file exists
        backup_path = create_backup(file_path)
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first (atomic operation)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp"
        )
        
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Move temporary file to target (atomic on most systems)
            shutil.move(temp_path, file_path)
            
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise
        
        file_size = file_path.stat().st_size
        logger.info(f"Successfully wrote file: {path} ({file_size} bytes)")
        
        return {
            "success": True,
            "path": str(file_path),
            "size": file_size,
            "backup_path": str(backup_path) if backup_path else None,
            "error": None
        }
        
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        return {
            "success": False,
            "path": path,
            "size": 0,
            "backup_path": str(backup_path) if backup_path else None,
            "error": f"PermissionError: {str(e)}"
        }
    except SecurityError as e:
        logger.error(f"Security error: {str(e)}")
        return {
            "success": False,
            "path": path,
            "size": 0,
            "backup_path": str(backup_path) if backup_path else None,
            "error": f"SecurityError: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error writing file: {str(e)}")
        return {
            "success": False,
            "path": path,
            "size": 0,
            "backup_path": str(backup_path) if backup_path else None,
            "error": f"Error: {str(e)}"
        }


# Tool 3: run_tests
def run_tests(test_directory: str) -> Dict[str, Any]:
    """
    Execute pytest in specified directory.
    
    Args:
        test_directory: Path to test directory
    
    Returns:
        dict: {
            "success": bool,
            "passed": int (number of passed tests),
            "failed": int (number of failed tests),
            "errors": int (number of errors),
            "skipped": int (number of skipped tests),
            "total": int (total number of tests),
            "duration": float (execution time in seconds),
            "output": str (test execution output),
            "error": str (error message if failed)
        }
    
    Example:
        >>> result = run_tests("tests/")
        >>> print(f"Tests passed: {result['passed']}/{result['total']}")
    """
    try:
        logger.info(f"Running tests in: {test_directory}")
        
        # Validate path
        test_path = validate_path(test_directory)
        
        # Check directory exists
        if not test_path.exists():
            raise FileNotFoundError(f"Test directory not found: {test_directory}")
        
        if not test_path.is_dir():
            raise ValueError(f"Path is not a directory: {test_directory}")
        
        # Get configuration
        config = get_config()
        
        # Build pytest command
        cmd = ["pytest", str(test_path)] + config.pytest_args
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Execute pytest with timeout
        start_time = datetime.now()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.test_timeout_seconds,
                cwd=config.workspace_directory
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse pytest output
            output = result.stdout + result.stderr
            
            # Extract test counts from output
            passed = failed = errors = skipped = 0
            
            # Look for pytest summary line
            summary_pattern = r'(\d+) passed|(\d+) failed|(\d+) error|(\d+) skipped'
            matches = re.findall(summary_pattern, output)
            
            for match in matches:
                if match[0]:  # passed
                    passed = int(match[0])
                elif match[1]:  # failed
                    failed = int(match[1])
                elif match[2]:  # errors
                    errors = int(match[2])
                elif match[3]:  # skipped
                    skipped = int(match[3])
            
            total = passed + failed + errors + skipped
            
            # Determine success (pytest returns 0 if all tests pass)
            success = result.returncode == 0
            
            logger.info(
                f"Tests completed: {passed} passed, {failed} failed, "
                f"{errors} errors, {skipped} skipped (duration: {duration:.2f}s)"
            )
            
            return {
                "success": success,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "total": total,
                "duration": duration,
                "output": output,
                "error": None if success else "Some tests failed"
            }
            
        except subprocess.TimeoutExpired:
            duration = config.test_timeout_seconds
            raise TimeoutError(
                f"Test execution exceeded timeout of {duration} seconds"
            )
        
    except FileNotFoundError as e:
        logger.error(f"Test directory not found: {str(e)}")
        return {
            "success": False,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "total": 0,
            "duration": 0.0,
            "output": "",
            "error": f"FileNotFoundError: {str(e)}"
        }
    except TimeoutError as e:
        logger.error(f"Test execution timeout: {str(e)}")
        config = get_config()
        return {
            "success": False,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "total": 0,
            "duration": config.test_timeout_seconds,
            "output": "",
            "error": f"TimeoutError: {str(e)}"
        }
    except SecurityError as e:
        logger.error(f"Security error: {str(e)}")
        return {
            "success": False,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "total": 0,
            "duration": 0.0,
            "output": "",
            "error": f"SecurityError: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error running tests: {str(e)}")
        return {
            "success": False,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "total": 0,
            "duration": 0.0,
            "output": "",
            "error": f"Error: {str(e)}"
        }


# Tool 4: create_pull_request
def create_pull_request(
    title: str,
    branch: str,
    files: List[str],
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create GitHub pull request.
    
    Args:
        title: PR title
        branch: Source branch name
        files: List of file paths to include
        description: Optional PR description
    
    Returns:
        dict: {
            "success": bool,
            "pr_url": str (GitHub PR URL if successful),
            "pr_number": int (PR number if successful),
            "branch": str (branch name),
            "files_committed": int (number of files committed),
            "fallback_used": bool (True if GitHub unavailable),
            "error": str (error message if failed)
        }
    
    Example:
        >>> result = create_pull_request(
        ...     title="Refactor legacy code",
        ...     branch="refactor/cobol-modernization",
        ...     files=["src/main.py", "tests/test_main.py"]
        ... )
        >>> if result["success"]:
        ...     print(f"PR created: {result['pr_url']}")
    """
    try:
        logger.info(f"Creating pull request: {title}")
        
        config = get_config()
        
        # Validate files
        validated_files = []
        for file_path in files:
            try:
                validated_path = validate_path(file_path)
                if not validated_path.exists():
                    logger.warning(f"File not found, skipping: {file_path}")
                    continue
                validated_files.append(validated_path)
            except SecurityError as e:
                logger.warning(f"Invalid file path, skipping: {file_path} - {e}")
                continue
        
        if not validated_files:
            raise ValueError("No valid files to commit")
        
        # Check if GitHub is enabled
        if not config.github_enabled:
            logger.warning("GitHub integration not enabled, using fallback")
            return _create_pr_fallback(title, branch, validated_files, description)
        
        try:
            # Initialize GitHub client
            github_client = Github(config.github_token)
            repo = github_client.get_repo(config.github_repo)
            
            # Get default branch
            default_branch = repo.default_branch or config.github_default_branch
            
            # Create new branch from default branch
            source_branch = repo.get_branch(default_branch)
            
            try:
                # Try to create new branch
                repo.create_git_ref(
                    ref=f"refs/heads/{branch}",
                    sha=source_branch.commit.sha
                )
                logger.info(f"Created branch: {branch}")
            except GithubException as e:
                if e.status == 422:  # Branch already exists
                    logger.info(f"Branch already exists: {branch}")
                else:
                    raise
            
            # Commit files to the branch
            committed_files = []
            for file_path in validated_files:
                try:
                    # Read file content
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Get relative path from workspace
                    rel_path = file_path.relative_to(config.get_workspace_path())
                    
                    # Try to get existing file
                    try:
                        existing_file = repo.get_contents(str(rel_path), ref=branch)
                        # Update existing file
                        repo.update_file(
                            path=str(rel_path),
                            message=f"Update {rel_path}",
                            content=content,
                            sha=existing_file.sha,
                            branch=branch
                        )
                    except GithubException:
                        # Create new file
                        repo.create_file(
                            path=str(rel_path),
                            message=f"Add {rel_path}",
                            content=content,
                            branch=branch
                        )
                    
                    committed_files.append(str(rel_path))
                    logger.info(f"Committed file: {rel_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to commit file {file_path}: {str(e)}")
            
            if not committed_files:
                raise RuntimeError("No files were successfully committed")
            
            # Create pull request
            pr_body = description or f"Automated PR created by MCP Server\n\nFiles modified:\n" + \
                      "\n".join(f"- {f}" for f in committed_files)
            
            pr = repo.create_pull(
                title=title,
                body=pr_body,
                head=branch,
                base=default_branch
            )
            
            logger.info(f"Pull request created: {pr.html_url}")
            
            return {
                "success": True,
                "pr_url": pr.html_url,
                "pr_number": pr.number,
                "branch": branch,
                "files_committed": len(committed_files),
                "fallback_used": False,
                "error": None
            }
            
        except GithubException as e:
            logger.error(f"GitHub API error: {str(e)}")
            # Fallback to local branch
            return _create_pr_fallback(title, branch, validated_files, description)
        
    except ValueError as e:
        logger.error(f"Invalid parameters: {str(e)}")
        return {
            "success": False,
            "pr_url": None,
            "pr_number": None,
            "branch": branch,
            "files_committed": 0,
            "fallback_used": False,
            "error": f"ValueError: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error creating pull request: {str(e)}")
        return {
            "success": False,
            "pr_url": None,
            "pr_number": None,
            "branch": branch,
            "files_committed": 0,
            "fallback_used": False,
            "error": f"Error: {str(e)}"
        }


def _create_pr_fallback(
    title: str,
    branch: str,
    files: List[Path],
    description: Optional[str]
) -> Dict[str, Any]:
    """
    Fallback method when GitHub is unavailable.
    Creates a local branch and saves PR information.
    
    Args:
        title: PR title
        branch: Branch name
        files: List of file paths
        description: Optional description
    
    Returns:
        dict: Result dictionary with fallback_used=True
    """
    try:
        config = get_config()
        output_dir = config.get_output_path()
        
        # Create PR info file
        pr_info = {
            "title": title,
            "branch": branch,
            "description": description,
            "files": [str(f) for f in files],
            "created_at": datetime.now().isoformat(),
            "status": "pending_github_sync"
        }
        
        pr_file = output_dir / f"pr_{branch.replace('/', '_')}.json"
        pr_file.write_text(json.dumps(pr_info, indent=2))
        
        logger.info(f"Created PR info file (fallback): {pr_file}")
        
        return {
            "success": True,
            "pr_url": None,
            "pr_number": None,
            "branch": branch,
            "files_committed": len(files),
            "fallback_used": True,
            "error": None,
            "fallback_file": str(pr_file)
        }
        
    except Exception as e:
        logger.error(f"Fallback failed: {str(e)}")
        return {
            "success": False,
            "pr_url": None,
            "pr_number": None,
            "branch": branch,
            "files_committed": 0,
            "fallback_used": True,
            "error": f"Fallback error: {str(e)}"
        }


# Export all tools
__all__ = [
    'read_file',
    'write_file',
    'run_tests',
    'create_pull_request',
    'validate_path',
    'validate_file_size',
    'sanitize_content',
    'SecurityError',
    'ToolExecutionError'
]

# Made with Bob
