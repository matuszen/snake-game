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

breathe_projects = {"Snake Game": "./doxygen_output/xml"}
breathe_default_project = "Snake Game"

autodoc_mock_imports = [
    "numpy",
    "ray",
    "posix_ipc",
    "matplotlib",
    "pygame",
    "py.snake_lib",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = []

latex_engine = "pdflatex"
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "11pt",
    "preamble": r"""
\usepackage[utf8]{inputenc}
\usepackage{hyperref}
""",
    "fncychap": "\\usepackage[Bjornstrup]{fncychap}",
    "printindex": "\\footnotesize\\raggedright\\printindex",
    "makeindex": "",
}

latex_documents = [
    (
        "index",
        "SnakeGame.tex",
        "Snake Game Documentation",
        "Mateusz",
        "manual",
    ),
]

latex_show_urls = "False"
latex_show_pagerefs = True
latex_use_modindex = False
