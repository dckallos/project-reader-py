"""
Registry for code parsers.
"""
from typing import Dict, List, Optional, Type

from .base import BaseParser


class ParserRegistry:
    """
    Registry for code parsers.
    """

    def __init__(self):
        """Initialize the parser registry."""
        self._parsers: Dict[str, Type[BaseParser]] = {}
        self._instances: Dict[str, BaseParser] = {}

    def register(self, extensions: List[str], parser_class: Type[BaseParser]) -> None:
        """
        Register a parser for the given file extensions.

        Args:
            extensions: List of file extensions (without the dot).
            parser_class: The parser class to register.
        """
        for ext in extensions:
            self._parsers[ext.lower()] = parser_class

    def get_parser(self, file_extension: str) -> Optional[BaseParser]:
        """
        Get a parser for the given file extension.

        Args:
            file_extension: The file extension (without the dot).

        Returns:
            Optional[BaseParser]: The parser for the given file extension, or None if not found.
        """
        ext = file_extension.lower()
        if ext not in self._parsers:
            return None

        # Lazy instantiation of parsers
        if ext not in self._instances:
            self._instances[ext] = self._parsers[ext]()

        return self._instances[ext]

    def get_supported_extensions(self) -> List[str]:
        """
        Get a list of supported file extensions.

        Returns:
            List[str]: A list of supported file extensions.
        """
        return list(self._parsers.keys())
