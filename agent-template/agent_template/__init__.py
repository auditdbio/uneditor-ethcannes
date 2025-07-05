from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Setup Jinja2 environment to load templates from the 'prompts' directory
TEMPLATES_PATH = Path(__file__).parent / "prompts"
TEMPLATES = Environment(loader=FileSystemLoader(TEMPLATES_PATH)) 