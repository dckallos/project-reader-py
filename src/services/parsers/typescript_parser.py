"""
TypeScript code parser.
"""
import re
from typing import List

from ...types.file_types import CodeDefinition
from .javascript_parser import JavaScriptParser
from .registry import ParserRegistry


class TypeScriptParser(JavaScriptParser):
    """
    Parser for TypeScript code.
    """

    def __init__(self):
        """Initialize the TypeScript parser."""
        super().__init__()
        self.interface_pattern = re.compile(r"interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*{")
        self.type_pattern = re.compile(r"type\s+(\w+)\s*=\s*")
        self.enum_pattern = re.compile(r"enum\s+(\w+)\s*{")

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse TypeScript code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        # Get JavaScript definitions first
        definitions = super().parse(content, file_path)
        
        # Add TypeScript-specific definitions
        definitions.extend(self._find_interfaces(content, file_path))
        definitions.extend(self._find_types(content, file_path))
        definitions.extend(self._find_enums(content, file_path))
        
        return definitions

    def _find_interfaces(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all interfaces in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of interface definitions.
        """
        definitions = []
        
        for match in self.interface_pattern.finditer(content):
            interface_name = match.group(1)
            interface_start = match.start()
            interface_line = self.find_line_number(content, interface_start)
            
            # Find the end of the interface (matching braces)
            interface_end = self.find_block_end(content, interface_start)
            interface_content = content[interface_start:interface_end]
            interface_end_line = interface_line + interface_content.count("\n")
            
            # Extract JSDoc
            jsdoc = None
            jsdoc_match = self.jsdoc_pattern.search(content[:interface_start])
            if jsdoc_match and jsdoc_match.end() == interface_start - 1:
                jsdoc = jsdoc_match.group(1).strip()
            
            # Create interface definition
            interface_def = CodeDefinition(
                name=interface_name,
                type="interface",
                file_path=file_path,
                line_number=interface_line,
                end_line_number=interface_end_line,
                signature=match.group(0),
                docstring=jsdoc
            )
            
            definitions.append(interface_def)
        
        return definitions

    def _find_types(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all type aliases in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of type definitions.
        """
        definitions = []
        
        for match in self.type_pattern.finditer(content):
            type_name = match.group(1)
            type_start = match.start()
            type_line = self.find_line_number(content, type_start)
            
            # Find the end of the type (semicolon)
            type_end = content.find(";", type_start)
            if type_end == -1:
                type_end = len(content)
            
            type_content = content[type_start:type_end]
            type_end_line = type_line + type_content.count("\n")
            
            # Extract JSDoc
            jsdoc = None
            jsdoc_match = self.jsdoc_pattern.search(content[:type_start])
            if jsdoc_match and jsdoc_match.end() == type_start - 1:
                jsdoc = jsdoc_match.group(1).strip()
            
            # Create type definition
            type_def = CodeDefinition(
                name=type_name,
                type="type",
                file_path=file_path,
                line_number=type_line,
                end_line_number=type_end_line,
                signature=match.group(0),
                docstring=jsdoc
            )
            
            definitions.append(type_def)
        
        return definitions

    def _find_enums(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all enums in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of enum definitions.
        """
        definitions = []
        
        for match in self.enum_pattern.finditer(content):
            enum_name = match.group(1)
            enum_start = match.start()
            enum_line = self.find_line_number(content, enum_start)
            
            # Find the end of the enum (matching braces)
            enum_end = self.find_block_end(content, enum_start)
            enum_content = content[enum_start:enum_end]
            enum_end_line = enum_line + enum_content.count("\n")
            
            # Extract JSDoc
            jsdoc = None
            jsdoc_match = self.jsdoc_pattern.search(content[:enum_start])
            if jsdoc_match and jsdoc_match.end() == enum_start - 1:
                jsdoc = jsdoc_match.group(1).strip()
            
            # Create enum definition
            enum_def = CodeDefinition(
                name=enum_name,
                type="enum",
                file_path=file_path,
                line_number=enum_line,
                end_line_number=enum_end_line,
                signature=match.group(0),
                docstring=jsdoc
            )
            
            definitions.append(enum_def)
        
        return definitions


# Register the parser
parser_registry = ParserRegistry()
parser_registry.register(["ts", "tsx"], TypeScriptParser)
