"""
Tool for extracting code definitions from files.
"""
import os
from typing import Dict, List, Optional

from ..services.code_parser import CodeParserService
from ..types.file_types import CodeDefinition


class ExtractDefinitionsTool:
    """
    Tool for extracting code definitions from files.
    """

    def __init__(self, code_parser_service: Optional[CodeParserService] = None):
        """
        Initialize the ExtractDefinitionsTool.

        Args:
            code_parser_service: The CodeParserService to use. If None, a new instance will be created.
        """
        self._code_parser_service = code_parser_service or CodeParserService()

    def execute(
        self,
        file_path: str = None,
        directory: str = None,
        recursive: bool = False,
        include_hidden: bool = False,
        respect_gitignore: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> Dict:
        """
        Extract code definitions from files.

        Args:
            file_path: The path to a specific file to extract definitions from.
            directory: The directory to extract definitions from.
            recursive: Whether to extract definitions recursively.
            include_hidden: Whether to include hidden files.
            respect_gitignore: Whether to respect .gitignore patterns.
            file_extensions: List of file extensions to include (e.g., ["py", "js"]).

        Returns:
            Dict: A dictionary containing the extracted definitions.
        """
        if not file_path and not directory:
            return {
                "error": "Either file_path or directory must be provided",
                "definitions": []
            }

        if file_path:
            # Normalize the file path
            file_path = os.path.abspath(file_path)

            # Check if the file exists
            if not os.path.isfile(file_path):
                return {
                    "error": f"File '{file_path}' does not exist",
                    "definitions": []
                }

            # Extract definitions from the file
            definitions = self._code_parser_service.extract_definitions(file_path)
            
            return {
                "error": None,
                "definitions": [self._format_definition(d) for d in definitions]
            }
        else:
            # Normalize the directory path
            directory = os.path.abspath(directory)

            # Check if the directory exists
            if not os.path.isdir(directory):
                return {
                    "error": f"Directory '{directory}' does not exist",
                    "definitions": []
                }

            # Get supported extensions if not provided
            if not file_extensions:
                file_extensions = self._code_parser_service.get_supported_extensions()

            # Get the list of files to process
            files = []
            for root, _, filenames in os.walk(directory):
                if not recursive and root != directory:
                    continue

                for filename in filenames:
                    # Skip hidden files if needed
                    if not include_hidden and filename.startswith('.'):
                        continue

                    # Check file extension
                    ext = os.path.splitext(filename)[1].lstrip('.')
                    if ext not in file_extensions:
                        continue

                    file_path = os.path.join(root, filename)
                    
                    # Skip ignored files if needed
                    if respect_gitignore and self._is_ignored(file_path, directory):
                        continue

                    files.append(file_path)

            # Extract definitions from each file
            all_definitions = []
            for file_path in files:
                definitions = self._code_parser_service.extract_definitions(file_path)
                all_definitions.extend([self._format_definition(d) for d in definitions])

            return {
                "error": None,
                "definitions": all_definitions
            }

    def _is_ignored(self, file_path: str, base_dir: str) -> bool:
        """
        Check if a file is ignored based on .gitignore patterns.

        Args:
            file_path: The path to the file.
            base_dir: The base directory.

        Returns:
            bool: True if the file is ignored, False otherwise.
        """
        # This is a simplified implementation
        # In a real implementation, we would use the IgnorePatternService
        # But for simplicity, we'll just check if the file is in a .git directory
        return '.git' in file_path.split(os.path.sep)

    def _format_definition(self, definition: CodeDefinition) -> Dict:
        """
        Format CodeDefinition into a simpler dictionary.

        Args:
            definition: The CodeDefinition to format.

        Returns:
            Dict: A dictionary containing the formatted definition.
        """
        return {
            "name": definition.name,
            "type": definition.type,
            "file_path": definition.file_path,
            "line_number": definition.line_number,
            "end_line_number": definition.end_line_number,
            "signature": definition.signature,
            "docstring": definition.docstring,
            "parent": definition.parent,
            "children": definition.children,
            "metadata": definition.metadata
        }
