"""
Test script to verify GitHub configuration is loaded correctly
"""

import os
import sys
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

print("=" * 60)
print("GitHub Configuration Test")
print("=" * 60)
print()

# Check if variables are loaded
github_token = os.getenv('GITHUB_TOKEN')
github_repo = os.getenv('GITHUB_REPO')
github_branch = os.getenv('GITHUB_DEFAULT_BRANCH')

print(f"GITHUB_TOKEN: {'[OK] Set' if github_token else '[X] Not set'}")
if github_token:
    print(f"  Length: {len(github_token)} characters")
    print(f"  Prefix: {github_token[:7]}...")

print()
print(f"GITHUB_REPO: {'[OK] Set' if github_repo else '[X] Not set'}")
if github_repo:
    print(f"  Value: {github_repo}")

print()
print(f"GITHUB_DEFAULT_BRANCH: {'[OK] Set' if github_branch else '[X] Not set'}")
if github_branch:
    print(f"  Value: {github_branch}")

print()
print("=" * 60)

# Test GitHub connection
if github_token and github_repo:
    print("Testing GitHub API connection...")
    print()
    
    try:
        from utils.github_integration import GitHubIntegration
        
        gh = GitHubIntegration(token=github_token, repo=github_repo)
        print("[OK] GitHub integration initialized successfully!")
        print(f"[OK] Repository: {gh.repo}")
        print(f"[OK] Base branch: {gh.base_branch}")
        
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
else:
    print("[WARNING] GitHub not fully configured. Please set GITHUB_TOKEN and GITHUB_REPO in .env file")

print("=" * 60)
