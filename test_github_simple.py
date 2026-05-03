"""
Simple GitHub connection test without UI dependencies
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("GitHub Connection Test")
print("=" * 60)
print()

github_token = os.getenv('GITHUB_TOKEN')
github_repo = os.getenv('GITHUB_REPO')

if not github_token or not github_repo:
    print("[ERROR] GitHub not configured in .env file")
    sys.exit(1)

print(f"Repository: {github_repo}")
print(f"Token: {github_token[:10]}... (length: {len(github_token)})")
print()

try:
    import requests
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    print("Testing GitHub API connection...")
    response = requests.get(
        f"https://api.github.com/repos/{github_repo}",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        repo_data = response.json()
        print("[OK] Connection successful!")
        print(f"[OK] Repository: {repo_data['full_name']}")
        print(f"[OK] Default branch: {repo_data['default_branch']}")
        print(f"[OK] Private: {repo_data['private']}")
        print()
        print("=" * 60)
        print("GitHub is configured correctly!")
        print("=" * 60)
    elif response.status_code == 404:
        print(f"[ERROR] Repository '{github_repo}' not found or no access")
    elif response.status_code == 401:
        print("[ERROR] Invalid GitHub token")
    else:
        print(f"[ERROR] GitHub API error: {response.status_code}")
        print(f"Response: {response.text}")
        
except ImportError:
    print("[ERROR] 'requests' library not installed")
except Exception as e:
    print(f"[ERROR] Connection failed: {str(e)}")

# Made with Bob
