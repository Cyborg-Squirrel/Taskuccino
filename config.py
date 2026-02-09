import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_FILE = Path(__file__).parent / 'config.json'

@dataclass
class Model:
    """Represents an AI model with its capabilities."""
    name: str
    capabilities: List[str] = field(default_factory=list)


@dataclass
class ModelsConfig:
    """Configuration for primary and backup AI models."""
    primary_model: Model
    backup_models: List[Model] = field(default_factory=list)

@dataclass
class RemindMeConfig:
    """Configuration for the RemindMe Discord bot."""
    token: str
    api_url: str
    models: Optional[ModelsConfig]
    reaction_emoji: str
    react_to_messages: bool

DEFAULT_CONFIG = RemindMeConfig('', 'http://localhost:11434', None, '👋', True)

def load_config() -> RemindMeConfig:
    """Load configuration from config.json as a dictionary."""
    if not CONFIG_FILE.exists():
        print(f'Config file does not exist, falling back to defaults. Please create a config.json file with your settings.')
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
        
        models = _load_models(config_data.get('models', DEFAULT_CONFIG.models))
        config = RemindMeConfig(
            token=config_data.get('token', DEFAULT_CONFIG.token),
            api_url=config_data.get('api_url', DEFAULT_CONFIG.api_url),
            models=models,
            reaction_emoji=config_data.get('reaction_emoji', DEFAULT_CONFIG.reaction_emoji),
            react_to_messages=config_data.get('react_to_messages', DEFAULT_CONFIG.react_to_messages)
        )

        return config
    
    except json.JSONDecodeError:
        print(f'Error: config.json is not valid JSON. Using defaults.')
        return DEFAULT_CONFIG
    except Exception as e:
        print(f'Error loading config: {e}. Using defaults.')
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to config.json."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f'Error saving config: {e}')
        return False

def _load_models(model_config: dict) -> Optional[ModelsConfig]:
    """Load models from config and return a ModelsConfig object."""
    
    if model_config is None:
        return None
    
    primary_model = None
    other_models = []
    
    for model_data in model_config:
        model = Model(
            name=model_data.get('name'),
            capabilities=model_data.get('capabilities', [])
        )
        
        is_primary = model_data.get('primary', False)
        
        if is_primary and primary_model is None:
            primary_model = model
        else:
            other_models.append(model)
    
    if primary_model is None:
        if other_models:
            primary_model = other_models.pop(0)
        else:
            raise ValueError('At least one model must be configured')
    
    return ModelsConfig(primary_model=primary_model, backup_models=other_models)
