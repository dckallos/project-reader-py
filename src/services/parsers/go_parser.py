"""
Go code parser.
"""
import re
from typing import List, Match, Optional, Tuple

from ...types.file_types import CodeDefinition
from .base import BaseParser


class GoParser(BaseParser):
    """
    Parser for Go code.
    """

    def __init__(self):
        """Initialize the Go parser."""
        super().__init__()
        self.struct_pattern = re.compile(r"type\s+(\w+)\s+struct\s*{")
        self.interface_pattern = re.compile(r"type\s+(\w+)\s+interface\s*{")
        self.function_pattern = re.compile(r"func\s+(\w+)\s*\(([^)]*)\)\s*(?:\(([^)]*)\)|[^{]*)\s*{")
        self.method_pattern = re.compile(r"func\s+\(([^)]*)\)\s+(\w+)\s*\(([^)]*)\)\s*(?:\(([^)]*)\)|[^{]*)\s*{")
        self.docstring_pattern = re.compile(r'\/\/\s*(.*?)$|\/\*\s*(.*?)\s*\*\/', re.MULTILINE)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse Go code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find all structs
        definitions.extend(self._find_structs(content, file_path))
        
        # Find all interfaces
        definitions.extend(self._find_interfaces(content, file_path))
        
        # Find all functions (not methods)
        definitions.extend(self._find_functions(content, file_path))
        
        # Find all methods
        definitions.extend(self._find_methods(content, file_path))
        
        return definitions

    def _find_structs(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all structs in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of struct definitions.
        """
        definitions = []
        
        for match in self.struct_pattern.finditer(content):
            struct_name = match.group(1)
            struct_start = match.start()
            struct_line = self.find_line_number(content, struct_start)
            
            # Find the end of the struct
            struct_end = self.find_block_end(content, struct_start, "{", "}")
            struct_content = content[struct_start:struct_end]
            struct_end_line = struct_line + struct_content.count("\n")
            
            # Extract docstring (Go uses // or /* */ comments)
            docstring = self._extract_go_docstring(content, struct_start)
            
            # Create struct definition
            struct_def = CodeDefinition(
                name=struct_name,
                type="struct",
                file_path=file_path,
                line_number=struct_line,
                end_line_number=struct_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            definitions.append(struct_def)
        
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
            
            # Find the end of the interface
            interface_end = self.find_block_end(content, interface_start, "{", "}")
            interface_content = content[interface_start:interface_end]
            interface_end_line = interface_line + interface_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_go_docstring(content, interface_start)
            
            # Create interface definition
            interface_def = CodeDefinition(
                name=interface_name,
                type="interface",
                file_path=file_path,
                line_number=interface_line,
                end_line_number=interface_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            definitions.append(interface_def)
        
        return definitions

    def _find_functions(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all top-level functions in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of function definitions.
        """
        definitions = []
        
        for match in self.function_pattern.finditer(content):
            function_name = match.group(1)
            function_start = match.start()
            function_line = self.find_line_number(content, function_start)
            
            # Find the end of the function
            function_end = self.find_block_end(content, function_start, "{", "}")
            function_content = content[function_start:function_end]
            function_end_line = function_line + function_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_go_docstring(content, function_start)
            
            # Create function definition
            function_def = CodeDefinition(
                name=function_name,
                type="function",
                file_path=file_path,
                line_number=function_line,
                end_line_number=function_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            definitions.append(function_def)
        
        return definitions

    def _find_methods(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all methods in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of method definitions.
        """
        definitions = []
        
        for match in self.method_pattern.finditer(content):
            receiver = match.group(1).strip()
            method_name = match.group(2)
            method_start = match.start()
            method_line = self.find_line_number(content, method_start)
            
            # Extract the receiver type
            receiver_type = receiver.split()[-1].strip("*")
            
            # Find the end of the method
            method_end = self.find_block_end(content, method_start, "{", "}")
            method_content = content[method_start:method_end]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_go_docstring(content, method_start)
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=receiver_type
            )
            
            definitions.append(method_def)
        
        return definitions

    def _extract_go_docstring(self, content: str, start_pos: int) -> Optional[str]:
        """
        Extract a Go docstring (comment) before a definition.

        Args:
            content: The content of the file.
            start_pos: The position of the definition.

        Returns:
            Optional[str]: The extracted docstring, or None if not found.
        """
        # Find the line start
        line_start = content[:start_pos].rfind("\n") + 1
        if line_start < 0:
            line_start = 0
        
        # Look for comments before the definition
        comment_block = []
        current_pos = line_start
        
        # Go backward to find comments
        while current_pos > 0:
            prev_line_end = content[:current_pos-1].rfind("\n")
            if prev_line_end < 0:
                prev_line_end = 0
            
            prev_line = content[prev_line_end:current_pos-1].strip()
            
            # Check if the previous line is a comment
            if prev_line.startswith("//"):
                comment_block.insert(0, prev_line[2:].strip())
                current_pos = prev_line_end + 1
            elif prev_line.startswith("/*") and prev_line.endswith("*/"):
                comment_block.insert(0, prev_line[2:-2].strip())
                break
            else:
                break
        
        if comment_block:
            return "\n".join(comment_block)
        
        return None
