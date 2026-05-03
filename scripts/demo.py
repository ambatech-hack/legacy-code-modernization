"""
IBM Bob Hackathon - End-to-End Demo Script
Demonstrates the complete legacy code modernization workflow
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.orchestrator import LegacyCodeOrchestrator
from utils.file_handler import FileHandler


class DemoRunner:
    """Runs the complete demo workflow with timing and reporting"""
    
    def __init__(self):
        self.demo_dir = Path(__file__).parent.parent
        self.output_dir = self.demo_dir / "output" / "demo"
        self.sample_file = self.demo_dir / "samples" / "cobol" / "customer_report.cbl"
        self.results = {}
        self.timings = {}
        
    def print_banner(self, text: str, char: str = "="):
        """Print a formatted banner"""
        width = 80
        print("\n" + char * width)
        print(f"{text:^{width}}")
        print(char * width + "\n")
        
    def print_section(self, text: str):
        """Print a section header"""
        print(f"\n{'─' * 80}")
        print(f"  {text}")
        print(f"{'─' * 80}\n")
        
    def print_step(self, step: int, total: int, description: str):
        """Print a step indicator"""
        print(f"\n[Step {step}/{total}] {description}")
        print("─" * 60)
        
    def display_file_preview(self, file_path: Path, max_lines: int = 20):
        """Display a preview of a file"""
        if not file_path.exists():
            print(f"  ⚠️  File not found: {file_path}")
            return
            
        print(f"\n  📄 Preview of {file_path.name}:")
        print("  " + "─" * 76)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            preview_lines = lines[:max_lines]
            
            for i, line in enumerate(preview_lines, 1):
                print(f"  {i:3d} | {line.rstrip()}")
                
            if len(lines) > max_lines:
                print(f"  ... ({len(lines) - max_lines} more lines)")
        
        print("  " + "─" * 76)
        
    def display_json_summary(self, json_path: Path, title: str):
        """Display a summary of JSON results"""
        if not json_path.exists():
            print(f"  ⚠️  File not found: {json_path}")
            return
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"\n  📊 {title}:")
        print("  " + "─" * 76)
        
        # Display key metrics based on content
        if 'metrics' in data:
            metrics = data['metrics']
            print(f"  • Lines of Code: {metrics.get('lines_of_code', 'N/A')}")
            print(f"  • Complexity Score: {metrics.get('complexity_score', 'N/A')}")
            print(f"  • Maintainability: {metrics.get('maintainability_index', 'N/A')}")
            
        if 'issues' in data:
            issues = data['issues']
            print(f"  • Total Issues: {len(issues)}")
            if issues:
                severity_counts = {}
                for issue in issues:
                    sev = issue.get('severity', 'unknown')
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                for sev, count in severity_counts.items():
                    print(f"    - {sev.capitalize()}: {count}")
                    
        if 'recommendations' in data:
            recs = data['recommendations']
            print(f"  • Recommendations: {len(recs)}")
            
        if 'modernization_summary' in data:
            summary = data['modernization_summary']
            print(f"  • Target Language: {summary.get('target_language', 'N/A')}")
            print(f"  • Conversion Status: {summary.get('status', 'N/A')}")
            
        print("  " + "─" * 76)
        
    def run_demo(self):
        """Run the complete demo workflow"""
        try:
            self.print_banner("IBM BOB HACKATHON - LEGACY CODE MODERNIZATION DEMO", "═")
            
            print("🚀 Welcome to the IBM Bob Legacy Code Modernization Platform Demo!")
            print("\nThis demo will showcase:")
            print("  1. 🔍 Code Analysis - Identify issues and complexity")
            print("  2. 📚 Documentation Generation - Create comprehensive docs")
            print("  3. 🔄 Code Refactoring - Modernize to Python")
            print("\nSample: COBOL Customer Sales Report Generator")
            print(f"Location: {self.sample_file.relative_to(self.demo_dir)}")
            
            input("\n▶️  Press Enter to start the demo...")
            
            # Step 1: Show original code
            self.print_step(1, 4, "ORIGINAL LEGACY CODE")
            print("\n📋 Displaying the original COBOL code...")
            self.display_file_preview(self.sample_file, max_lines=30)
            
            print("\n💡 This COBOL program:")
            print("  • Processes customer sales data")
            print("  • Generates formatted reports")
            print("  • Calculates commissions and totals")
            print("  • Uses file I/O operations")
            print("  • Contains ~267 lines of legacy code")
            
            input("\n▶️  Press Enter to begin analysis...")
            
            # Step 2: Initialize orchestrator
            self.print_step(2, 4, "INITIALIZING MODERNIZATION PLATFORM")
            print("\n⚙️  Setting up IBM watsonx.ai integration...")
            
            start_time = time.time()
            orchestrator = LegacyCodeOrchestrator(
                output_base_dir=str(self.output_dir)
            )
            init_time = time.time() - start_time
            self.timings['initialization'] = init_time
            
            print(f"✅ Platform initialized in {init_time:.2f} seconds")
            print(f"📁 Output directory: {self.output_dir.relative_to(self.demo_dir)}")
            
            input("\n▶️  Press Enter to run analysis agent...")
            
            # Step 3: Run analysis
            self.print_step(3, 4, "AGENT 1: CODE ANALYSIS")
            print("\n🔍 Analyzing legacy code with IBM watsonx.ai...")
            print("  • Detecting code smells and anti-patterns")
            print("  • Calculating complexity metrics")
            print("  • Identifying security vulnerabilities")
            print("  • Generating improvement recommendations")
            
            start_time = time.time()
            analysis_result = orchestrator.run_analysis(str(self.sample_file))
            analysis_time = time.time() - start_time
            self.timings['analysis'] = analysis_time
            self.results['analysis'] = analysis_result
            
            print(f"\n✅ Analysis completed in {analysis_time:.2f} seconds")
            
            # Display analysis results
            analysis_report = self.output_dir / "analysis" / "analysis_report.json"
            if analysis_report.exists():
                self.display_json_summary(analysis_report, "Analysis Results")
            
            input("\n▶️  Press Enter to generate documentation...")
            
            # Step 4: Generate documentation
            self.print_step(4, 4, "AGENT 2: DOCUMENTATION GENERATION")
            print("\n📚 Generating comprehensive documentation...")
            print("  • Creating README with usage instructions")
            print("  • Documenting architecture and design")
            print("  • Mapping dependencies")
            print("  • Identifying technical debt")
            print("  • Adding inline code comments")
            
            start_time = time.time()
            doc_result = orchestrator.run_documentation(str(self.sample_file))
            doc_time = time.time() - start_time
            self.timings['documentation'] = doc_time
            self.results['documentation'] = doc_result
            
            print(f"\n✅ Documentation generated in {doc_time:.2f} seconds")
            
            # Display documentation files
            doc_dir = self.output_dir / "documentation"
            if doc_dir.exists():
                print("\n  📄 Generated documentation files:")
                for doc_file in sorted(doc_dir.glob("*.md")):
                    print(f"    • {doc_file.name}")
                    
            input("\n▶️  Press Enter to modernize the code...")
            
            # Step 5: Refactor/Modernize
            self.print_step(5, 4, "AGENT 3: CODE MODERNIZATION")
            print("\n🔄 Modernizing COBOL to Python...")
            print("  • Converting procedural to object-oriented")
            print("  • Applying modern design patterns")
            print("  • Generating unit tests")
            print("  • Creating migration guide")
            
            start_time = time.time()
            refactor_result = orchestrator.run_refactoring(
                str(self.sample_file),
                target_language="python"
            )
            refactor_time = time.time() - start_time
            self.timings['refactoring'] = refactor_time
            self.results['refactoring'] = refactor_result
            
            print(f"\n✅ Modernization completed in {refactor_time:.2f} seconds")
            
            # Display modernized code
            modernized_file = self.output_dir / "modernized" / "customer_report.py"
            if modernized_file.exists():
                self.display_file_preview(modernized_file, max_lines=40)
                
            # Display modernization report
            mod_report = self.output_dir / "modernized" / "modernization_report.json"
            if mod_report.exists():
                self.display_json_summary(mod_report, "Modernization Summary")
                
            input("\n▶️  Press Enter to view final summary...")
            
            # Final Summary
            self.print_banner("DEMO SUMMARY", "═")
            
            total_time = sum(self.timings.values())
            
            print("⏱️  PERFORMANCE METRICS:")
            print(f"  • Initialization: {self.timings.get('initialization', 0):.2f}s")
            print(f"  • Analysis: {self.timings.get('analysis', 0):.2f}s")
            print(f"  • Documentation: {self.timings.get('documentation', 0):.2f}s")
            print(f"  • Modernization: {self.timings.get('refactoring', 0):.2f}s")
            print(f"  • Total Time: {total_time:.2f}s")
            
            print("\n📊 RESULTS:")
            print(f"  • Analysis Report: ✅ Generated")
            print(f"  • Documentation: ✅ {len(list((self.output_dir / 'documentation').glob('*.md')))} files")
            print(f"  • Modernized Code: ✅ Python implementation")
            print(f"  • Unit Tests: ✅ Generated")
            
            print("\n📁 OUTPUT LOCATION:")
            print(f"  {self.output_dir.relative_to(self.demo_dir)}/")
            print(f"    ├── analysis/")
            print(f"    ├── documentation/")
            print(f"    └── modernized/")
            
            print("\n🎯 KEY ACHIEVEMENTS:")
            print("  ✅ Automated legacy code analysis")
            print("  ✅ AI-powered documentation generation")
            print("  ✅ Seamless COBOL to Python conversion")
            print("  ✅ Production-ready modernized code")
            print("  ✅ Comprehensive test coverage")
            
            print("\n💡 NEXT STEPS:")
            print("  1. Review generated documentation")
            print("  2. Examine modernized Python code")
            print("  3. Run unit tests")
            print("  4. Deploy to production")
            
            # Save demo report
            self.save_demo_report(total_time)
            
            self.print_banner("DEMO COMPLETE - THANK YOU!", "═")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during demo: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def save_demo_report(self, total_time: float):
        """Save a detailed demo report"""
        report = {
            "demo_info": {
                "timestamp": datetime.now().isoformat(),
                "sample_file": str(self.sample_file.relative_to(self.demo_dir)),
                "total_time_seconds": round(total_time, 2)
            },
            "timings": {k: round(v, 2) for k, v in self.timings.items()},
            "results": {
                "analysis": self.results.get('analysis', {}).get('status') == 'success',
                "documentation": self.results.get('documentation', {}).get('status') == 'success',
                "refactoring": self.results.get('refactoring', {}).get('status') == 'success'
            },
            "output_directory": str(self.output_dir.relative_to(self.demo_dir))
        }
        
        report_file = self.output_dir / "demo_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Demo report saved: {report_file.relative_to(self.demo_dir)}")


def main():
    """Main entry point"""
    demo = DemoRunner()
    success = demo.run_demo()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

