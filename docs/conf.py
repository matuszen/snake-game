"""Configuration file for the Sphinx documentation builder."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Snake Game"
title = "Technical Documentation"
author = "Mateusz Nowak"
copyright = "2026"
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
    "papersize": "a4paper",
    "pointsize": "11pt",
    "preamble": r"""
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{mathptmx}
\usepackage[scaled=.92]{helvet}
\usepackage{courier}

\makeatletter
\renewcommand{\maketitle}{
  \begin{titlepage}
    \centering
    \vspace*{2cm}

    \rule{\linewidth}{1.5pt}
    \vspace{0.5cm}
    {\textsc{\Large Technical Documentation} \par}
    \vspace{0.5cm}
    \rule{\linewidth}{0.5pt}

    \vspace{2.5cm}

    {\Huge \bfseries \sffamily \@title \par}

    \vspace{1cm}

    {\large \itshape Version \@release \par}

    \vfill

    \rule{\linewidth}{0.5pt}
    \vspace{0.5cm}
    \begin{flushright}
        {\footnotesize \textbf{Project Team:}} \\
        \vspace{0.2cm}
        {\scriptsize \@author \par}
        \vspace{0.5cm}
        {\scriptsize \itshape \@date \par}
    \end{flushright}
  \end{titlepage}
}
\makeatother
""",
    "fncychap": "\\usepackage[Sonny]{fncychap}",
    "printindex": "\\footnotesize\\raggedright\\printindex",
}

latex_documents = [
    (
        "index",
        "SnakeGame.tex",
        title,
        author,
        "manual",
    ),
]

latex_show_urls = "False"
latex_show_pagerefs = True
