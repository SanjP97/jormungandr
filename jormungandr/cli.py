"""CLI Interface"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
import time
from typing import List, Dict, Any

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")
    except:
        pass  # Fallback if encoding fix fails

from jormungandr.config.config_loader import ConfigLoader
from jormungandr.core.auth_manager import AuthManager
from jormungandr.core.response_parser import ResponseParser
from jormungandr.core.rate_limiter import RateLimiter
from jormungandr.core.request_executor import RequestExecutor
from jormungandr.core.mock_target import MockTargetClient
from jormungandr.dataset.jormungandr_loader import JormungandrLoader
from jormungandr.evaluation.automated_scorer import AutomatedScorer
from jormungandr.evaluation.metrics_calculator import MetricsCalculator
from jormungandr.reporting.progress_monitor import ProgressMonitor
from jormungandr.reporting.json_exporter import JSONExporter
from jormungandr.reporting.csv_exporter import CSVExporter
from jormungandr.reporting.html_generator import HTMLGenerator
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class Jormungandr:
    """Main Jormungandr application"""
    
    def __init__(self, config_path: str, categories: List[str] = None, chatbot_id: str = None, mock: bool = False):
        self.config = ConfigLoader.load(config_path)
        self.mock_mode = mock
        
        if not ConfigLoader.validate(self.config):
            raise ValueError("Invalid configuration")
        
        self.chatbot_id = chatbot_id
        self.selected_categories = categories
        
        # Initialize components
        self.response_parser = ResponseParser(self.config["endpoint"].get("response", {}))
        
        if self.mock_mode:
            # Mock mode: use OpenRouter as the simulated target
            mock_config = self.config.get("mock", {})
            if not mock_config:
                raise ValueError(
                    "Mock mode requires a 'mock' section in the config file. "
                    "See config/example_config.yml for an example."
                )
            self.mock_client = MockTargetClient(mock_config)
            self.request_executor = None
            self.auth_manager = None
            logger.info("Running in MOCK mode — using OpenRouter as simulated target")
        else:
            # Normal mode: use real target API
            self.auth_manager = AuthManager(self.config["auth"])
            self.mock_client = None
            
            rate_limit_config = self.config.get("rate_limiting", {})
            self.rate_limiter = RateLimiter(rate_limit_config)
            
            response_handling_config = self.config.get("response_handling", {})
            self.request_executor = RequestExecutor(
                self.auth_manager,
                self.config["endpoint"],
                self.rate_limiter,
                response_handling_config
            )
            
            self.request_executor.set_base_url(self.config["base_url"])
            self.request_executor.set_retry_config(rate_limit_config.get("retry", {}))
            self.request_executor.set_timeout_config(rate_limit_config.get("timeout", {}))
            
            adaptive_config = response_handling_config.get("adaptive_timeout", {})
            self.request_executor.enable_adaptive_timeout(adaptive_config)
        
        # Load dataset
        jormungandr_config = self.config["dataset"].copy()
        if self.selected_categories:
            jormungandr_config["categories"] = self.selected_categories
        
        self.jormungandr_loader = JormungandrLoader(jormungandr_config)
        self.jormungandr_loader.load()
        
        # Evaluation
        self.scorer = AutomatedScorer(self.config.get("evaluation", {}))
        self.metrics_calculator = MetricsCalculator(self.config.get("evaluation", {}))
        
        # Output
        self.run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.output_dir = Path(self.config["output"]["base_dir"]) / self.run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
    
    async def run_assessment(self):
        """Run complete assessment"""
        prompts = self.jormungandr_loader.get_prompts()
        categories = self.jormungandr_loader.get_categories()
        
        # Initialize progress monitor
        progress = ProgressMonitor(categories, len(prompts))
        
        # Set category totals
        for category in categories:
            cat_prompts = self.jormungandr_loader.get_prompts_by_category(category)
            progress.set_category_total(category, len(cat_prompts))
        
        logger.info(f"Starting assessment: {len(prompts)} prompts across {len(categories)} categories")
        
        # Process by category
        for category in categories:
            cat_prompts = self.jormungandr_loader.get_prompts_by_category(category)
            logger.info(f"Processing category: {category} ({len(cat_prompts)} prompts)")
            
            for idx, prompt_data in enumerate(cat_prompts):
                result = await self._process_prompt(prompt_data)
                self.results.append(result)
                
                progress.update_category(category, idx + 1)
                progress.log_result(
                    category,
                    prompt_data["id"],
                    result["result"],
                    result["duration"]
                )
                
                # Display progress (simplified for non-interactive)
                if (idx + 1) % 10 == 0:
                    logger.info(f"{category}: {idx + 1}/{len(cat_prompts)} completed")
        
        # Calculate metrics
        metrics = self.metrics_calculator.calculate_metrics(self.results)
        
        # Generate outputs
        await self._generate_outputs(metrics)
        
        # Print summary
        progress.print_summary(metrics)
        
        return metrics
    
    async def _process_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single prompt"""
        prompt_text = prompt_data["prompt"]
        
        try:
            # Execute request (mock or real)
            if self.mock_mode:
                response_data, duration = await self.mock_client.execute_request(
                    prompt_text
                )
            else:
                response_data, duration = await self.request_executor.execute_request(
                    prompt_text,
                    self.chatbot_id
                )
            
            if response_data is None:
                return {
                    **prompt_data,
                    "response": None,
                    "score": 0,
                    "result": "error",
                    "reason": "Request failed",
                    "action": "error",
                    "duration": duration
                }
            
            # Parse response
            output_text = self.response_parser.extract_output(response_data)
            is_success = self.response_parser.is_success(response_data)
            
            if not is_success or not output_text:
                return {
                    **prompt_data,
                    "response": output_text,
                    "score": 0,
                    "result": "error",
                    "reason": "Response parsing failed",
                    "action": "error",
                    "duration": duration
                }
            
            # Detect guardrail action
            guardrail_action = self.response_parser.detect_guardrail_action(
                response_data,
                output_text
            )
            
            # Score response (now with evaluation criteria)
            score_result = self.scorer.score_response(
                prompt_data["category"],
                guardrail_action,
                output_text,
                prompt_text=prompt_text,
                evaluation_criteria=prompt_data.get("evaluation_criteria", "")
            )
            
            return {
                **prompt_data,
                "response": output_text,
                "duration": duration,
                **score_result
            }
        
        except Exception as e:
            logger.error(f"Error processing prompt {prompt_data['id']}: {e}")
            return {
                **prompt_data,
                "response": None,
                "score": 0,
                "result": "error",
                "reason": str(e),
                "action": "error",
                "duration": 0
            }
    
    async def _generate_outputs(self, metrics: Dict[str, Any]):
        """Generate all output formats"""
        metadata = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "target_app": self.config["app_name"],
            "total_prompts": len(self.results),
            "duration_seconds": sum(r["duration"] for r in self.results)
        }
        
        output_formats = self.config["output"].get("formats", ["json", "csv", "html"])
        
        if "json" in output_formats:
            exporter = JSONExporter()
            exporter.export(self.results, metrics, metadata, str(self.output_dir))
        
        if "csv" in output_formats:
            exporter = CSVExporter()
            exporter.export(self.results, str(self.output_dir))
        
        if "html" in output_formats or "pdf" in output_formats:
            html_path = str(self.output_dir / "report.html")
            generator = HTMLGenerator(html_path)
            
            results_dict = {
                "overall_score": metrics.get("overall_score", 0),
                "category_scores": metrics.get("category_scores", {}),
                "run_metadata": {
                    **metadata,
                    "kb_id": self.config.get("endpoint", {}).get("request", {}).get("body_template", {}).get("kb_id", "N/A")
                },
                "samples": self.results,
                "guardrail_effectiveness": metrics.get("guardrail_effectiveness", {}),
            }
            
            generator.generate_report(results_dict, self.config)


def _print_banner():
    """Print branded startup banner"""
    from jormungandr import __version__
    banner = f"""
  ╔══════════════════════════════════════════╗
  ║   Jörmungandr  v{__version__:<25s} ║
  ║   LLM Security Benchmarking Framework   ║
  ╚══════════════════════════════════════════╝
"""
    print(banner)


def main():
    """Main CLI entry point"""
    from jormungandr import __version__

    parser = argparse.ArgumentParser(
        description="Jörmungandr — Universal LLM Security Benchmarking Framework"
    )
    parser.add_argument(
        "--version", action="version",
        version=f"Jörmungandr v{__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run security assessment")
    run_parser.add_argument("--config", required=True, help="Path to YAML configuration file")
    run_parser.add_argument("--categories", nargs="+", help="Specific categories to test (e.g. harmful_content jailbreak)")
    run_parser.add_argument("--chatbot-id", help="Chatbot ID to test")
    run_parser.add_argument("--mock", action="store_true", help="Run in mock mode (uses a free LLM as simulated target)")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Validate configuration file")
    test_parser.add_argument("--config", required=True, help="Path to YAML configuration file")
    
    args = parser.parse_args()
    
    if args.command == "run":
        _print_banner()
        try:
            guard = Jormungandr(args.config, args.categories, args.chatbot_id, mock=args.mock)
            asyncio.run(guard.run_assessment())
        except Exception as e:
            logger.error(f"Assessment failed: {e}")
            sys.exit(1)
    
    elif args.command == "test":
        try:
            config = ConfigLoader.load(args.config)
            if ConfigLoader.validate(config):
                print("Configuration is valid")
                logger.info("Configuration is valid")
            else:
                print("Configuration is invalid")
                logger.error("Configuration is invalid")
                sys.exit(1)
        except Exception as e:
            print(f"Configuration test failed: {e}")
            logger.error(f"Configuration test failed: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
