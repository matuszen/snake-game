"""Setup script for snake_game Python package."""

from setuptools import setup

setup(
    name="snake-game",
    version="1.0",
    packages=["py", "py.training", "py.interface"],
    package_data={  # type: ignore[arg-type]
        "py": ["*.so", "*.pyi"],
    },
    install_requires=[],
)
