"""Real-time Progress Monitor"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from collections import defaultdict
import time
from typing import Dict, Any, List

console = Console()


class ProgressMonitor:
    """Real-time CLI progress monitoring"""
    
    def __init__(self, categories: List[str], total_prompts: int):
        self.categories = categories
        self.total_prompts = total_prompts
        
        self.category_progress = {cat: {"completed": 0, "total": 0} for cat in categories}
        self.category_status = {cat: "⏳" for cat in categories}
        
        self.start_time = time.time()
        self.completed_count = 0
        self.error_count = 0
        self.response_times = []
        
        self.recent_logs = []
        self.max_logs = 5
    
    def set_category_total(self, category: str, total: int):
        """Set total prompts for a category"""
        self.category_progress[category]["total"] = total
    
    def update_category(self, category: str, completed: int):
        """Update category progress"""
        self.category_progress[category]["completed"] = completed
        
        total = self.category_progress[category]["total"]
        if completed >= total:
            self.category_status[category] = "✓"
        else:
            self.category_status[category] = "⏳"
    
    def log_result(self, category: str, prompt_id: str, result: str, duration: float):
        """Log a result"""
        self.completed_count += 1
        self.response_times.append(duration)
        
        if len(self.response_times) > 100:
            self.response_times.pop(0)
        
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {category} #{prompt_id[:8]} → {result.upper()} ({duration:.2f}s)"
        
        self.recent_logs.append(log_entry)
        if len(self.recent_logs) > self.max_logs:
            self.recent_logs.pop(0)
    
    def log_error(self):
        """Log an error"""
        self.error_count += 1
    
    def generate_display(self) -> Table:
        """Generate progress display"""
        # Header
        table = Table.grid(padding=(0, 2))
        table.add_column(justify="left")
        table.add_column(justify="right")
        
        elapsed = time.time() - self.start_time
        avg_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        remaining = ((self.total_prompts - self.completed_count) * avg_time) if avg_time > 0 else 0
        
        # Category progress
        for category in self.categories:
            prog = self.category_progress[category]
            completed = prog["completed"]
            total = prog["total"]
            percentage = (completed / total * 100) if total > 0 else 0
            
            status = self.category_status[category]
            bar_length = 30
            filled = int(bar_length * percentage / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            table.add_row(
                f"[bold]{category.upper()}[/bold]",
                f"{bar} {percentage:5.1f}% ({completed}/{total}) {status}"
            )
        
        # Stats
        table.add_row("", "")
        table.add_row(
            "[bold]Stats[/bold]",
            f"Completed: {self.completed_count}/{self.total_prompts} | "
            f"Errors: {self.error_count} | "
            f"Avg: {avg_time:.2f}s | "
            f"ETA: {remaining/60:.0f}m {remaining%60:.0f}s"
        )
        
        # Recent logs
        if self.recent_logs:
            table.add_row("", "")
            table.add_row("[bold]Recent Activity[/bold]", "")
            for log in self.recent_logs:
                table.add_row("", log)
        
        return table
    
    def print_summary(self, metrics: Dict[str, Any]):
        """Print final summary"""
        console.print("\n")
        console.print(Panel.fit("🎯 [bold]jormungandr Assessment Complete[/bold]", border_style="green"))
        
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Score", justify="right")
        summary_table.add_column("P/F/P*/R", justify="right")
        
        for category, scores in metrics["category_scores"].items():
            summary_table.add_row(
                category,
                f"{scores['score']:.1f}",
                f"{scores['passed']}/{scores['failed']}/{scores.get('partial', 0)}/{scores.get('review', 0)}"
            )
        
        summary_table.add_row(
            "[bold]OVERALL[/bold]",
            f"[bold]{metrics['overall_score']:.1f}[/bold]",
            f"[bold]{metrics['total_passed']}/{metrics['total_failed']}/{metrics.get('total_partial', 0)}/{metrics.get('total_review', 0)}[/bold]"
        )
        
        console.print(summary_table)
        console.print(f"\n📊 Results saved to: [bold]results/[/bold]")
