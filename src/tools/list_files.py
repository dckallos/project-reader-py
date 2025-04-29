"""
Tool for listing files in a directory.
"""
import os
from typing import Dict, List, Optional

from ..services.file_system import FileSystemService
from ..types.file_types import DirectoryInfo, FileInfo


class ListFilesTool:
    """
    Tool for listing files in a directory.
    """

    def __init__(self, file_system_service: Optional[FileSystemService] = None):
        """
        Initialize the ListFilesTool.

        Args:
            file_system_service: The FileSystemService to use. If None, a new instance will be created.
        """
        self._file_system_service = file_system_service or FileSystemService()

    def execute(
        self,
        directory: str,
        recursive: bool = False,
        include_hidden: bool = False,
        respect_gitignore: bool = True,
        file_extensions: Optional[List[str]] = None,
        max_depth: int = -1
    ) -> Dict:
        """
        List files in a directory.

        Args:
            directory: The directory to list files from.
            recursive: Whether to list files recursively.
            include_hidden: Whether to include hidden files.
            respect_gitignore: Whether to respect .gitignore patterns.
            file_extensions: List of file extensions to include (e.g., ["py", "txt"]).
            max_depth: Maximum recursion depth (-1 for unlimited).

        Returns:
            Dict: A dictionary containing the list of files and directories.
        """
        # Normalize the directory path
        directory = os.path.abspath(directory)

        # Check if the directory exists
        if not os.path.isdir(directory):
            return {
                "error": f"Directory '{directory}' does not exist",
                "files": [],
                "directories": []
            }

        # Get directory info
        dir_info = self._file_system_service.get_directory_info(
            directory,
            recursive=recursive,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            max_depth=max_depth
        )

        if not dir_info:
            return {
                "error": f"Failed to get directory info for '{directory}'",
                "files": [],
                "directories": []
            }

        # Convert to a simpler format
        result = self._format_directory_info(dir_info)
        result["path"] = directory
        result["error"] = None

        # Filter by extension if needed
        if file_extensions:
            result["files"] = [
                f for f in result["files"]
                if os.path.splitext(f["name"])[1].lstrip(".").lower() in file_extensions
            ]

        return result

    def _format_directory_info(self, dir_info: DirectoryInfo) -> Dict:
        """
        Format DirectoryInfo into a simpler dictionary.

        Args:
            dir_info: The DirectoryInfo to format.

        Returns:
            Dict: A dictionary containing the formatted directory info.
        """
        result = {
            "name": dir_info.name,
            "path": dir_info.path,
            "is_hidden": dir_info.is_hidden,
            "files": [],
            "directories": []
        }

        # Format files
        for file_info in dir_info.files:
            result["files"].append(self._format_file_info(file_info))

        # Format subdirectories
        for subdir_info in dir_info.directories:
            result["directories"].append(self._format_directory_info(subdir_info))

        return result

    def _format_file_info(self, file_info: FileInfo) -> Dict:
        """
        Format FileInfo into a simpler dictionary.

        Args:
            file_info: The FileInfo to format.

        Returns:
            Dict: A dictionary containing the formatted file info.
        """
        return {
            "name": file_info.name,
            "path": file_info.path,
            "type": file_info.type.value,
            "size": file_info.size,
            "modified_time": file_info.modified_time.isoformat(),
            "is_hidden": file_info.is_hidden,
            "extension": file_info.extension,
            "mime_type": file_info.mime_type
        }
