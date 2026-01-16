import os
import sys
from importlib.metadata import version as get_version

sys.path.insert(0, os.path.abspath(".."))

project = "Model Bakery"
copyright = "2023, Rust Saiargaliev"
author = "Rust Saiargaliev"
version = release = get_version("model-bakery")

extensions = [
    "myst_parser",
]

myst_enable_extensions = [
    "colon_fence",
]

source_suffix = [".rst", ".md"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
