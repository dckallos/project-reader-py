"""
Service for parsing code and extracting definitions.
"""
import os
from typing import Dict, List, Optional

from ..types.file_types import CodeDefinition
from .parsers.registry import ParserRegistry


class CodeParserService:
    """
    Service for parsing code and extracting definitions.
    """

    def __init__(self, parser_registry: Optional[ParserRegistry] = None):
        """
        Initialize the CodeParserService.

        Args:
            parser_registry: The parser registry to use. If None, a new instance will be created.
        """
        self._parser_registry = parser_registry or ParserRegistry()

    def extract_definitions(self, file_path: str) -> List[CodeDefinition]:
        """
        Extract code definitions from a file.

        Args:
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        if not os.path.isfile(file_path):
            return []

        # Get the file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lstrip(".").lower()

        # Get the parser for the file extension
        parser = self._parser_registry.get_parser(ext)
        if not parser:
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return parser.parse(content, file_path)
        except UnicodeDecodeError:
            try:
                # Try with a different encoding
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
                
                return parser.parse(content, file_path)
            except Exception as e:
                print(f"Error extracting definitions from {file_path}: {e}")
                return []
        except Exception as e:
            print(f"Error extracting definitions from {file_path}: {e}")
            return []

    def get_supported_extensions(self) -> List[str]:
        """
        Get a list of supported file extensions.

        Returns:
            List[str]: A list of supported file extensions.
        """
        return self._parser_registry.get_supported_extensions()
