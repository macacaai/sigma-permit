# IAM Models Package
# Import all existing models from models.py
import sys
from pathlib import Path
import importlib.util

# Load the models.py file from the parent directory
parent_dir = Path(__file__).parent.parent
models_file = parent_dir / 'models.py'

if models_file.exists():
    spec = importlib.util.spec_from_file_location("models", models_file)
    models_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models_module)

    # Import all attributes from the models module
    for attr in dir(models_module):
        if not attr.startswith('_'):
            globals()[attr] = getattr(models_module, attr)

# Import IAM models with extend_existing to avoid conflicts
try:
    from .oauth import *
    from .rbac import *
except:
    # During migration, models might already be defined
    pass