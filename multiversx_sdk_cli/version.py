import importlib.metadata
import logging
from pathlib import Path

import toml


def get_version():
    try:
        return _get_version_from_pyproject()
    except Exception as error:
        try:
            return _get_version_from_metadata()
        except Exception as error:
            logging.exception(f"Failed to get version: {error}")
            return "unknown"


def _get_version_from_pyproject() -> str:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    return toml.load(pyproject_path)["project"]["version"]


def _get_version_from_metadata() -> str:
    return importlib.metadata.version("multiversx_sdk_cli")
