"""Jormungandr Dataset Loader"""

from datasets import load_dataset
from typing import List, Dict, Any
from jormungandr.utils.logger import get_logger
import json

logger = get_logger(__name__)


class JormungandrLoader:
    """Load and manage Jormungandr dataset"""
    
    # Mapping of categories to Jormungandr dataset configs
    CATEGORY_CONFIG_MAP = {
        "hallucination": [
            "hallucination_tools_basic",
            "hallucination_tools_knowledge",
            "hallucination_debunking",
            "hallucination_factuality",
            "hallucination_satirical"
        ],
        "harmful_content": [
            "harmful_vulnerable_misguidance"
        ],
        "bias_and_stereotypes": [
            "biases"
        ],
        "bias": [
            "biases"
        ],
        "jailbreak": [
            "jailbreak_encoding",
            "jailbreak_framing",
            "jailbreak_injection"
        ]
    }
    
    def __init__(self, jormungandr_config: Dict[str, Any]):
        self.config = jormungandr_config
        self.dataset_id = jormungandr_config.get("dataset_id", "giskardai/Jormungandr")
        self.split = jormungandr_config.get("split", "public")
        self.languages = jormungandr_config.get("languages", ["en"])
        self.selected_categories = jormungandr_config.get("categories", [])
        
        self.dataset = None
        self.prompts = []
    
    def load(self):
        """Load dataset from HuggingFace"""
        logger.info(f"Loading Jormungandr dataset: {self.dataset_id}")
        
        try:
            all_samples = []
            
            # Determine which configs to load
            configs_to_load = []
            
            if not self.selected_categories:
                for configs in self.CATEGORY_CONFIG_MAP.values():
                    configs_to_load.extend(configs)
            else:
                for category in self.selected_categories:
                    if category in self.CATEGORY_CONFIG_MAP:
                        configs_to_load.extend(self.CATEGORY_CONFIG_MAP[category])
            
            configs_to_load = list(set(configs_to_load))
            logger.info(f"Loading {len(configs_to_load)} Jormungandr configurations")
            
            # Load each config
            for config_name in configs_to_load:
                try:
                    logger.info(f"Loading config: {config_name}")
                    dataset = load_dataset(self.dataset_id, config_name, split=self.split)
                    category = self._get_category_from_config(config_name)
                    
                    extracted_count = 0
                    
                    for idx in range(len(dataset)):
                        try:
                            sample = dataset[idx]
                            prompt_text = None
                            
                            # Parse generations field (it's JSON stored as string)
                            if 'generations' in sample and isinstance(sample['generations'], str):
                                try:
                                    generations_data = json.loads(sample['generations'])
                                    
                                    if isinstance(generations_data, list) and len(generations_data) > 0:
                                        first_gen = generations_data[0]
                                        
                                        if isinstance(first_gen, dict) and 'messages' in first_gen:
                                            messages = first_gen['messages']
                                            if isinstance(messages, list):
                                                for msg in messages:
                                                    if isinstance(msg, dict):
                                                        if msg.get('role') == 'user' and 'content' in msg:
                                                            prompt_text = msg['content']
                                                            break
                                        
                                        if not prompt_text and isinstance(first_gen, dict):
                                            prompt_text = first_gen.get('prompt') or first_gen.get('input')
                                
                                except json.JSONDecodeError:
                                    continue
                            
                            if not prompt_text or len(str(prompt_text).strip()) < 5:
                                continue
                            
                            # Extract evaluation criteria
                            evaluation_criteria = self._extract_evaluation_criteria(sample)
                            
                            # Create sample
                            sample_data = {
                                "id": sample.get('id', f"{config_name}_{idx}"),
                                "category": category,
                                "subcategory": config_name,
                                "language": sample.get('language', 'en'),
                                "prompt": str(prompt_text).strip(),
                                "expected_behavior": "safe_response",
                                "evaluation_criteria": evaluation_criteria,  # NEW: Add criteria
                                "metadata": {
                                    "config": config_name,
                                    "task": sample.get('task', ''),
                                    "module": sample.get('module', '')
                                }
                            }
                            all_samples.append(sample_data)
                            extracted_count += 1
                        
                        except Exception as e:
                            continue
                    
                    logger.info(f"Extracted {extracted_count} prompts from {config_name}")
                
                except Exception as e:
                    logger.error(f"Failed to load {config_name}: {e}")
            
            self.prompts = all_samples
            logger.info(f"Total samples loaded: {len(self.prompts)}")
            
            if len(self.prompts) == 0:
                raise ValueError("No samples extracted from jormungandr dataset")
            
            # Apply sampling
            sampling_config = self.config.get("sampling", {})
            if sampling_config.get("enabled"):
                self._apply_sampling(sampling_config)
        
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    def _extract_evaluation_criteria(self, sample: Dict[str, Any]) -> str:
        """Extract evaluation criteria from the evaluation field"""
        
        try:
            # Parse evaluation field (also JSON string)
            if 'evaluation' in sample and isinstance(sample['evaluation'], str):
                eval_data = json.loads(sample['evaluation'])
                
                if isinstance(eval_data, dict):
                    # Extract context or criterion
                    if 'data' in eval_data:
                        data = eval_data['data']
                        if isinstance(data, dict):
                            # Try multiple field names
                            criteria = (
                                data.get('context') or 
                                data.get('criterion') or
                                data.get('description') or
                                data.get('criteria')
                            )
                            if criteria:
                                return str(criteria)
                    
                    # Fallback: use scorer name
                    scorer = eval_data.get('scorer', '')
                    if scorer:
                        return f"Evaluation method: {scorer}"
        
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not extract evaluation criteria: {e}")
        
        return ""
    
    def _get_category_from_config(self, config_name: str) -> str:
        """Map config to category"""
        if config_name.startswith("hallucination"):
            return "hallucination"
        elif config_name.startswith("harmful"):
            return "harmful_content"
        elif config_name.startswith("bias"):
            return "bias_and_stereotypes"
        elif config_name.startswith("jailbreak"):
            return "jailbreak"
        return "unknown"
    
    def _apply_sampling(self, sampling_config: Dict[str, Any]):
        """Apply sampling"""
        samples_per_category = sampling_config.get("samples_per_category", 100)
        
        category_samples = {}
        for prompt in self.prompts:
            category = prompt["category"]
            if category not in category_samples:
                category_samples[category] = []
            category_samples[category].append(prompt)
        
        sampled_prompts = []
        for category, samples in category_samples.items():
            sampled_count = min(samples_per_category, len(samples))
            sampled_prompts.extend(samples[:sampled_count])
            logger.info(f"Sampled {sampled_count} from {category}")
        
        self.prompts = sampled_prompts
        logger.info(f"Final count: {len(self.prompts)} prompts")
    
    def get_prompts(self) -> List[Dict[str, Any]]:
        return self.prompts
    
    def get_categories(self) -> List[str]:
        return list(set(p["category"] for p in self.prompts))
    
    def get_prompts_by_category(self, category: str) -> List[Dict[str, Any]]:
        return [p for p in self.prompts if p["category"] == category]
