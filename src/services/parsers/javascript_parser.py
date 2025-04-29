"""
JavaScript code parser.
"""
import re
from typing import List, Optional

from ...types.file_types import CodeDefinition
from .base import BaseParser
from .registry import ParserRegistry


class JavaScriptParser(BaseParser):
    """
    Parser for JavaScript code.
    """

    def __init__(self):
        """Initialize the JavaScript parser."""
        super().__init__()
        self.class_pattern = re.compile(r"class\s+(\w+)(?:\s+extends\s+(\w+))?\s*{")
        self.function_pattern = re.compile(
            r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|"
            r"let\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|"
            r"var\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)"
        )
        self.method_pattern = re.compile(
            r"(?:(\w+)\s*\([^)]*\)|get\s+(\w+)\s*\(\)|"
            r"set\s+(\w+)\s*\([^)]*\)|async\s+(\w+)\s*\([^)]*\))\s*{"
        )
        self.jsdoc_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse JavaScript code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find all classes
        definitions.extend(self._find_classes(content, file_path))
        
        # Find all functions (not methods)
        definitions.extend(self._find_functions(content, file_path))
        
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
            
            # Extract JSDoc
            jsdoc = None
            jsdoc_match = self.jsdoc_pattern.search(content[:class_start])
            if jsdoc_match and jsdoc_match.end() == class_start - 1:
                jsdoc = jsdoc_match.group(1).strip()
            
            # Create class definition
            class_def = CodeDefinition(
                name=class_name,
                type="class",
                file_path=file_path,
                line_number=class_line,
                end_line_number=class_end_line,
                signature=match.group(0),
                docstring=jsdoc
            )
            
            # Find all methods in the class
            methods = self._find_methods(class_content, file_path, class_name, class_start)
            for method in methods:
                class_def.children.append(method.name)
                definitions.append(method)
            
            definitions.append(class_def)
        
        return definitions

    def _find_methods(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
        """
        Find all methods in a class.

        Args:
            class_content: The content of the class.
            file_path: The path to the file.
            class_name: The name of the class.
            class_start: The start position of the class in the original content.

        Returns:
            List[CodeDefinition]: A list of method definitions.
        """
        definitions = []
        
        for match in self.method_pattern.finditer(class_content):
            # Get the method name from the first non-None group
            method_name = next((name for name in match.groups() if name), "anonymous")
            method_start_in_class = match.start()
            method_start = class_start + method_start_in_class
            method_line = self.find_line_number(class_content, method_start_in_class)
            
            # Find the end of the method (matching braces)
            method_end_in_class = self.find_block_end(class_content, method_start_in_class)
            method_content = class_content[method_start_in_class:method_end_in_class]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract JSDoc
            jsdoc = None
            # Look for JSDoc before the method
            jsdoc_match = self.jsdoc_pattern.search(class_content[:method_start_in_class])
            if jsdoc_match and jsdoc_match.end() == method_start_in_class - 1:
                jsdoc = jsdoc_match.group(1).strip()
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=jsdoc,
                parent=class_name
            )
            
            definitions.append(method_def)
        
        return definitions

    def _find_functions(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all functions in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of function definitions.
        """
        definitions = []
        
        for match in self.function_pattern.finditer(content):
            # Get the function name from the first non-None group
            function_name = next((name for name in match.groups() if name), "anonymous")
            function_start = match.start()
            function_line = self.find_line_number(content, function_start)
            
            # Find the end of the function
            if "=>" in match.group(0):
                # Arrow function
                function_end = content.find(";", function_start)
                if function_end == -1:
                    function_end = len(content)
            else:
                # Regular function
                function_end = self.find_block_end(content, function_start)
            
            function_content = content[function_start:function_end]
            function_end_line = function_line + function_content.count("\n")
            
            # Extract JSDoc
            jsdoc = None
            jsdoc_match = self.jsdoc_pattern.search(content[:function_start])
            if jsdoc_match and jsdoc_match.end() == function_start - 1:
                jsdoc = jsdoc_match.group(1).strip()
            
            # Create function definition
            function_def = CodeDefinition(
                name=function_name,
                type="function",
                file_path=file_path,
                line_number=function_line,
                end_line_number=function_end_line,
                signature=match.group(0),
                docstring=jsdoc
            )
            
            definitions.append(function_def)
        
        return definitions


# Register the parser
parser_registry = ParserRegistry()
parser_registry.register(["js", "jsx"], JavaScriptParser)
