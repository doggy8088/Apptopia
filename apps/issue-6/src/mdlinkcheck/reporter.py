"""Report generation for link checking results."""

import json
import sys
from typing import Dict

from .checker import FileResult


class Reporter:
    """Generate reports for link checking results."""
    
    def __init__(self, format: str = "text"):
        self.format = format
    
    def report(self, results: Dict[str, FileResult], source_name: str):
        """Generate and print report."""
        if self.format == "json":
            self._report_json(results, source_name)
        else:
            self._report_text(results, source_name)
    
    def _report_text(self, results: Dict[str, FileResult], source_name: str):
        """Generate text format report."""
        total_files = len(results)
        
        print(f"\n🔍 Scanning: {source_name} ({total_files} markdown files found)\n")
        
        total_links = 0
        total_ok = 0
        total_broken = 0
        total_warning = 0
        
        for file_path, file_result in results.items():
            total_links += len(file_result.results)
            total_ok += file_result.ok_count
            total_broken += file_result.broken_count
            total_warning += file_result.warning_count
            
            print(f"{file_path}")
            
            # Group results by status
            broken_results = [r for r in file_result.results if r.status == "broken"]
            warning_results = [r for r in file_result.results if r.status == "warning"]
            
            # Print broken links
            for result in broken_results:
                icon = "❌"
                if result.status_code:
                    msg = f"[{result.status_code}]"
                else:
                    msg = f"[{result.message}]"
                
                print(f"  {icon} {msg} {result.link.url} (line {result.link.line_number})")
                
                if result.suggestion:
                    print(f"     {result.suggestion}")
            
            # Print warnings
            for result in warning_results:
                icon = "⚠️"
                msg = f"[{result.message}]"
                print(f"  {icon} {msg} {result.link.url} (line {result.link.line_number})")
            
            # Print OK summary
            if file_result.ok_count > 0:
                if broken_results or warning_results:
                    print(f"  ✅ {file_result.ok_count} links OK")
                else:
                    print(f"  ✅ {file_result.ok_count} links OK — all good!")
            
            print()
        
        # Print summary
        print("─" * 40)
        print("📊 Summary")
        print(f"  Files scanned:  {total_files}")
        print(f"  Links checked:  {total_links}")
        print(f"  ✅ Healthy:     {total_ok}")
        print(f"  ❌ Broken:      {total_broken}")
        print(f"  ⚠️ Warning:     {total_warning}")
        print()
    
    def _report_json(self, results: Dict[str, FileResult], source_name: str):
        """Generate JSON format report."""
        output = {
            "source": source_name,
            "summary": {
                "files_scanned": len(results),
                "links_checked": sum(len(r.results) for r in results.values()),
                "healthy": sum(r.ok_count for r in results.values()),
                "broken": sum(r.broken_count for r in results.values()),
                "warning": sum(r.warning_count for r in results.values()),
            },
            "files": {}
        }
        
        for file_path, file_result in results.items():
            output["files"][file_path] = {
                "ok_count": file_result.ok_count,
                "broken_count": file_result.broken_count,
                "warning_count": file_result.warning_count,
                "links": []
            }
            
            for result in file_result.results:
                link_data = {
                    "url": result.link.url,
                    "line": result.link.line_number,
                    "type": result.link.link_type,
                    "status": result.status,
                }
                
                if result.status_code:
                    link_data["status_code"] = result.status_code
                
                if result.message:
                    link_data["message"] = result.message
                
                if result.suggestion:
                    link_data["suggestion"] = result.suggestion
                
                output["files"][file_path]["links"].append(link_data)
        
        print(json.dumps(output, indent=2))
