"""Configuration file for the Sphinx documentation builder."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Snake Game"
copyright = "2026, Mateusz"
author = "Mateusz"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "breathe",
]

# Mock external dependencies imports to avoid installing them in CI environment
autodoc_mock_imports = [
    "numpy",
    "ray",
    "posix_ipc",
    "matplotlib",
    "pygame",
    "py.snake_lib",  # Mock the C++ binding module
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

breathe_projects = {"Snake Game": "./doxygen_output/xml"}
breathe_default_project = "Snake Game"
