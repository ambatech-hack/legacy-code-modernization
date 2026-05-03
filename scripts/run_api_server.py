"""
Run FastAPI Server for Legacy Code Modernization

This script starts the FastAPI server that provides REST API endpoints
for the orchestration workflow.
"""

import os
import sys
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def main():
    """Run the FastAPI server using uvicorn."""
    print("=" * 70)
    print("  Legacy Code Modernization API Server")
    print("=" * 70)
    print()
    print("Starting FastAPI server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Alternative Docs: http://localhost:8000/redoc")
    print("Health Check: http://localhost:8000/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "integrations.api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\nError starting server: {e}")
        print("\nMake sure FastAPI and uvicorn are installed:")
        print("  pip install fastapi uvicorn[standard]")
        sys.exit(1)


if __name__ == "__main__":
    main()


