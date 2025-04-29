"""
Service for handling .gitignore patterns.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

import pathspec


class IgnorePatternService:
    """
    Service for handling .gitignore patterns and other ignore files.
    """

    def __init__(self):
        """Initialize the IgnorePatternService."""
        self._ignore_specs: Dict[str, pathspec.PathSpec] = {}
        self._ignore_patterns: Dict[str, List[str]] = {}

    def load_ignore_file(self, path: str, ignore_file_name: str = ".gitignore") -> bool:
        """
        Load an ignore file (e.g., .gitignore) from the specified path.

        Args:
            path: The directory path containing the ignore file.
            ignore_file_name: The name of the ignore file (default: .gitignore).

        Returns:
            bool: True if the ignore file was loaded successfully, False otherwise.
        """
        ignore_file_path = os.path.join(path, ignore_file_name)
        if not os.path.isfile(ignore_file_path):
            return False

        try:
            with open(ignore_file_path, "r", encoding="utf-8") as f:
                patterns = []
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)

                self._ignore_patterns[path] = patterns
                self._ignore_specs[path] = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, patterns
                )
                return True
        except Exception as e:
            print(f"Error loading ignore file {ignore_file_path}: {e}")
            return False

    def is_ignored(self, file_path: str, base_dir: Optional[str] = None) -> bool:
        """
        Check if a file is ignored based on the loaded ignore patterns.

        Args:
            file_path: The path of the file to check.
            base_dir: The base directory to use for relative paths. If None, use the directory of the file.

        Returns:
            bool: True if the file is ignored, False otherwise.
        """
        if not base_dir:
            base_dir = os.path.dirname(file_path)

        # Normalize paths
        base_dir = os.path.abspath(base_dir)
        file_path = os.path.abspath(file_path)

        # Check if the file is in the base directory
        if not file_path.startswith(base_dir):
            return False

        # Get the relative path
        rel_path = os.path.relpath(file_path, base_dir)

        # Check if the file is ignored by any of the loaded ignore specs
        for dir_path, spec in self._ignore_specs.items():
            if base_dir.startswith(dir_path) and spec.match_file(rel_path):
                return True

        return False

    def find_all_ignore_files(self, root_dir: str, ignore_file_name: str = ".gitignore") -> List[str]:
        """
        Find all ignore files in the directory tree.

        Args:
            root_dir: The root directory to search from.
            ignore_file_name: The name of the ignore file (default: .gitignore).

        Returns:
            List[str]: A list of paths to ignore files.
        """
        ignore_files = []
        for dirpath, _, filenames in os.walk(root_dir):
            if ignore_file_name in filenames:
                ignore_files.append(os.path.join(dirpath, ignore_file_name))
        return ignore_files

    def load_all_ignore_files(self, root_dir: str, ignore_file_name: str = ".gitignore") -> int:
        """
        Load all ignore files in the directory tree.

        Args:
            root_dir: The root directory to search from.
            ignore_file_name: The name of the ignore file (default: .gitignore).

        Returns:
            int: The number of ignore files loaded.
        """
        count = 0
        for dirpath, _, filenames in os.walk(root_dir):
            if ignore_file_name in filenames:
                if self.load_ignore_file(dirpath, ignore_file_name):
                    count += 1
        return count

    def get_patterns(self, path: str) -> List[str]:
        """
        Get the ignore patterns for a specific directory.

        Args:
            path: The directory path.

        Returns:
            List[str]: The ignore patterns for the directory.
        """
        return self._ignore_patterns.get(path, [])

    def clear(self) -> None:
        """Clear all loaded ignore patterns."""
        self._ignore_specs.clear()
        self._ignore_patterns.clear()
