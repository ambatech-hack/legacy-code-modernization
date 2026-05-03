"""
Startup script for the Streamlit UI.

Usage:
    python scripts/run_ui.py
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the Streamlit application."""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Path to the Streamlit app
    app_path = project_root / "ui" / "app.py"
    
    if not app_path.exists():
        print(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)
    
    print("🚀 Starting Legacy Code Modernization Squad UI...")
    print(f"📂 Project root: {project_root}")
    print(f"📄 App path: {app_path}")
    print("\n" + "="*60)
    print("The UI will open in your default browser.")
    print("Press Ctrl+C to stop the server.")
    print("="*60 + "\n")
    
    # Run streamlit
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.port=8501",
                "--server.address=localhost",
                "--browser.gatherUsageStats=false"
            ],
            cwd=str(project_root),
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down UI server...")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running Streamlit: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

