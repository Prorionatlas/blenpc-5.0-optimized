import json
import os
import time
from typing import List, Dict, Optional
from .. import config

class ModelRegistry:
    """Save and recall building models with semantic metadata."""
    
    @staticmethod
    def save_model(name: str, spec: Dict, result: Dict, tags: List[str] = None):
        """Register a generated model with metadata."""
        if tags is None:
            tags = []
            
        registry_file = os.path.join(config.REGISTRY_DIR, "model_registry.json")
        os.makedirs(config.REGISTRY_DIR, exist_ok=True)
        
        data = {"models": {}}
        if os.path.exists(registry_file):
            with open(registry_file, "r") as f:
                data = json.load(f)
        
        model_entry = {
            "name": name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "spec": spec,
            "result": result,
            "tags": tags
        }
        
        data["models"][name] = model_entry
        
        with open(registry_file, "w") as f:
            json.dump(data, f, indent=2)
            
        return model_entry

    @staticmethod
    def list_models(tags: List[str] = None) -> Dict:
        """List models with optional tag filtering."""
        registry_file = os.path.join(config.REGISTRY_DIR, "model_registry.json")
        if not os.path.exists(registry_file):
            return {}
            
        with open(registry_file, "r") as f:
            data = json.load(f)
            
        if not tags:
            return data.get("models", {})
            
        filtered = {}
        for name, model in data.get("models", {}).items():
            if all(t in model.get("tags", []) for t in tags):
                filtered[name] = model
        return filtered

    @staticmethod
    def recall_model(name: str) -> Optional[Dict]:
        """Retrieve a specific model by name."""
        registry_file = os.path.join(config.REGISTRY_DIR, "model_registry.json")
        if not os.path.exists(registry_file):
            return None
            
        with open(registry_file, "r") as f:
            data = json.load(f)
            
        return data.get("models", {}).get(name)
