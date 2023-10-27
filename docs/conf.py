import os
import sys

sys.path.insert(0, os.path.abspath(".."))

from model_bakery import __about__  # noqa

project = "Model Bakery"
copyright = "2023, Rust Saiargaliev"
author = "Rust Saiargaliev"
version = release = __about__.__version__

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
