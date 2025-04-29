"""
Tool for reading file contents.
"""
import os
from typing import Dict, Optional

from ..services.file_system import FileSystemService
from ..types.file_types import FileType


class ReadFileTool:
    """
    Tool for reading file contents.
    """

    def __init__(self, file_system_service: Optional[FileSystemService] = None):
        """
        Initialize the ReadFileTool.

        Args:
            file_system_service: The FileSystemService to use. If None, a new instance will be created.
        """
        self._file_system_service = file_system_service or FileSystemService()

    def execute(self, file_path: str, binary: bool = False) -> Dict:
        """
        Read the contents of a file.

        Args:
            file_path: The path to the file.
            binary: Whether to read the file as binary.

        Returns:
            Dict: A dictionary containing the file contents and metadata.
        """
        # Normalize the file path
        file_path = os.path.abspath(file_path)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return {
                "error": f"File '{file_path}' does not exist",
                "content": None,
                "binary": False,
                "file_info": None
            }

        # Get file info
        file_info = self._file_system_service.get_file_info(file_path)
        if not file_info:
            return {
                "error": f"Failed to get file info for '{file_path}'",
                "content": None,
                "binary": False,
                "file_info": None
            }

        # Check if the file is binary
        is_binary = file_info.type == FileType.BINARY

        # Read the file
        if binary or is_binary:
            content = self._file_system_service.read_binary_file(file_path)
            if content is None:
                return {
                    "error": f"Failed to read binary file '{file_path}'",
                    "content": None,
                    "binary": True,
                    "file_info": self._format_file_info(file_info)
                }
            # Convert binary content to base64 for JSON serialization
            import base64
            content = base64.b64encode(content).decode('utf-8')
            is_binary = True
        else:
            content = self._file_system_service.read_file(file_path)
            if content is None:
                return {
                    "error": f"Failed to read file '{file_path}'",
                    "content": None,
                    "binary": False,
                    "file_info": self._format_file_info(file_info)
                }

        return {
            "error": None,
            "content": content,
            "binary": is_binary,
            "file_info": self._format_file_info(file_info)
        }

    def _format_file_info(self, file_info) -> Dict:
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
