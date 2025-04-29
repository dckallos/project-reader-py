"""
Java code parser.
"""
import re
from typing import List

from ...types.file_types import CodeDefinition
from .base import BaseParser
from .registry import ParserRegistry


class JavaParser(BaseParser):
    """
    Parser for Java code.
    """

    def __init__(self):
        """Initialize the Java parser."""
        super().__init__()
        self.class_pattern = re.compile(
            r"(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)"
            r"(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*{"
        )
        self.interface_pattern = re.compile(
            r"(?:public|private|protected)?\s*interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*{"
        )
        self.method_pattern = re.compile(
            r"(?:public|private|protected)?\s*(?:static|final|abstract)?\s*"
            r"(?:<[^>]+>\s*)?(\w+)\s+(\w+)\s*\([^)]*\)(?:\s+throws\s+[^{]+)?\s*{"
        )
        self.javadoc_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse Java code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find all classes
        definitions.extend(self._find_classes(content, file_path))
        
        # Find all interfaces
        definitions.extend(self._find_interfaces(content, file_path))
        
        return definitions

    def _find_classes(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all classes in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of class definitions.
        """
        definitions = []
        
        for match in self.class_pattern.finditer(content):
            class_name = match.group(1)
            class_start = match.start()
            class_line = self.find_line_number(content, class_start)
            
            # Find the end of the class (matching braces)
            class_end = self.find_block_end(content, class_start)
            class_content = content[class_start:class_end]
            class_end_line = class_line + class_content.count("\n")
            
            # Extract Javadoc
            javadoc = None
            javadoc_match = self.javadoc_pattern.search(content[:class_start])
            if javadoc_match and javadoc_match.end() == class_start - 1:
                javadoc = javadoc_match.group(1).strip()
            
            # Create class definition
            class_def = CodeDefinition(
                name=class_name,
                type="class",
                file_path=file_path,
                line_number=class_line,
                end_line_number=class_end_line,
                signature=match.group(0),
                docstring=javadoc
            )
            
            # Find all methods in the class
            methods = self._find_methods(class_content, file_path, class_name, class_start)
            for method in methods:
                class_def.children.append(method.name)
                definitions.append(method)
            
            definitions.append(class_def)
        
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
            
            # Extract Javadoc
            javadoc = None
            javadoc_match = self.javadoc_pattern.search(content[:interface_start])
            if javadoc_match and javadoc_match.end() == interface_start - 1:
                javadoc = javadoc_match.group(1).strip()
            
            # Create interface definition
            interface_def = CodeDefinition(
                name=interface_name,
                type="interface",
                file_path=file_path,
                line_number=interface_line,
                end_line_number=interface_end_line,
                signature=match.group(0),
                docstring=javadoc
            )
            
            # Find all methods in the interface
            methods = self._find_methods(interface_content, file_path, interface_name, interface_start)
            for method in methods:
                interface_def.children.append(method.name)
                definitions.append(method)
            
            definitions.append(interface_def)
        
        return definitions

    def _find_methods(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
        """
        Find all methods in a class or interface.

        Args:
            class_content: The content of the class or interface.
            file_path: The path to the file.
            class_name: The name of the class or interface.
            class_start: The start position of the class or interface in the original content.

        Returns:
            List[CodeDefinition]: A list of method definitions.
        """
        definitions = []
        
        for match in self.method_pattern.finditer(class_content):
            return_type = match.group(1)
            method_name = match.group(2)
            method_start_in_class = match.start()
            method_start = class_start + method_start_in_class
            method_line = self.find_line_number(class_content, method_start_in_class)
            
            # Find the end of the method (matching braces)
            method_end_in_class = self.find_block_end(class_content, method_start_in_class)
            method_content = class_content[method_start_in_class:method_end_in_class]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract Javadoc
            javadoc = None
            javadoc_match = self.javadoc_pattern.search(class_content[:method_start_in_class])
            if javadoc_match and javadoc_match.end() == method_start_in_class - 1:
                javadoc = javadoc_match.group(1).strip()
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=javadoc,
                parent=class_name
            )
            
            definitions.append(method_def)
        
        return definitions


# Register the parser
parser_registry = ParserRegistry()
parser_registry.register(["java"], JavaParser)
