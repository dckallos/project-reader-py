"""
Base parser class for code parsing.
"""
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Pattern, Tuple

from ...types.file_types import CodeDefinition


class BaseParser(ABC):
    """
    Base class for all language parsers.
    """

    def __init__(self):
        """Initialize the parser."""
        pass

    @abstractmethod
    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse code content and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        pass

    @staticmethod
    def find_line_number(content: str, position: int) -> int:
        """
        Find the line number for a position in the content.

        Args:
            content: The content of the file.
            position: The position in the content.

        Returns:
            int: The line number (1-based).
        """
        return content[:position].count("\n") + 1

    @staticmethod
    def extract_docstring(content: str, pattern: Pattern[str], start_pos: int) -> Optional[str]:
        """
        Extract a docstring using a regex pattern.

        Args:
            content: The content of the file.
            pattern: The regex pattern for the docstring.
            start_pos: The position to start searching from.

        Returns:
            Optional[str]: The extracted docstring, or None if not found.
        """
        match = pattern.search(content[start_pos:])
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def find_block_end(content: str, start_pos: int, open_char: str = "{", close_char: str = "}") -> int:
        """
        Find the end of a block (e.g., a function or class body).

        Args:
            content: The content of the file.
            start_pos: The position to start searching from.
            open_char: The character that opens a block.
            close_char: The character that closes a block.

        Returns:
            int: The position of the end of the block.
        """
        count = 0
        for i in range(start_pos, len(content)):
            if content[i] == open_char:
                count += 1
            elif content[i] == close_char:
                count -= 1
                if count == 0:
                    return i + 1
        return len(content)

    @staticmethod
    def find_next_definition(content: str, start_pos: int, pattern: Pattern[str]) -> Tuple[int, Optional[re.Match]]:
        """
        Find the next definition in the content.

        Args:
            content: The content of the file.
            start_pos: The position to start searching from.
            pattern: The regex pattern for the definition.

        Returns:
            Tuple[int, Optional[re.Match]]: The position and match of the next definition.
        """
        match = pattern.search(content[start_pos:])
        if match:
            return start_pos + match.start(), match
        return len(content), None
