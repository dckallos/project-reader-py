"""
Python code parser.
"""
import re
from typing import List, Match, Optional, Tuple

from ...types.file_types import CodeDefinition
from .base import BaseParser
from .registry import ParserRegistry


class PythonParser(BaseParser):
    """
    Parser for Python code.
    """

    def __init__(self):
        """Initialize the Python parser."""
        super().__init__()
        self.class_pattern = re.compile(r"class\s+(\w+)(?:\s*\(([^)]*)\))?\s*:")
        self.function_pattern = re.compile(r"def\s+(\w+)\s*\(([^)]*)\)\s*(?:->.*?)?:")
        self.docstring_pattern = re.compile(r'"""(.*?)"""', re.DOTALL)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse Python code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find all classes
        definitions.extend(self._find_classes(content, file_path))
        
        # Find all top-level functions (not methods)
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
            
            # Find the end of the class
            class_end = len(content)
            next_class_match = self.class_pattern.search(content[class_start + 1:])
            if next_class_match:
                class_end = class_start + 1 + next_class_match.start()
            
            class_content = content[class_start:class_end]
            class_end_line = class_line + class_content.count("\n")
            
            # Extract docstring
            docstring = self.extract_docstring(class_content, self.docstring_pattern, 0)
            
            # Create class definition
            class_def = CodeDefinition(
                name=class_name,
                type="class",
                file_path=file_path,
                line_number=class_line,
                end_line_number=class_end_line,
                signature=match.group(0),
                docstring=docstring
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
        
        # Determine the indentation level of the class
        first_line_end = class_content.find("\n")
        if first_line_end == -1:
            return []
        
        first_line = class_content[:first_line_end]
        class_indent = len(first_line) - len(first_line.lstrip())
        
        # Create a pattern for methods with the correct indentation
        method_indent = class_indent + 4  # Python standard is 4 spaces
        method_pattern = re.compile(r"^( {" + str(method_indent) + r"}|\t)def\s+(\w+)\s*\(([^)]*)\)\s*(?:->.*?)?:", re.MULTILINE)
        
        for match in method_pattern.finditer(class_content):
            method_name = match.group(2)
            method_start_in_class = match.start()
            method_start = class_start + method_start_in_class
            method_line = self.find_line_number(class_content, method_start_in_class)
            
            # Find the end of the method
            next_method_match = method_pattern.search(class_content[method_start_in_class + 1:])
            if next_method_match:
                method_end_in_class = method_start_in_class + 1 + next_method_match.start()
                method_content = class_content[method_start_in_class:method_end_in_class]
            else:
                method_content = class_content[method_start_in_class:]
            
            method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self.extract_docstring(method_content, self.docstring_pattern, 0)
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0).strip(),
                docstring=docstring,
                parent=class_name
            )
            
            definitions.append(method_def)
        
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
            # Check if this is a method (indented)
            line_start = content[:match.start()].rfind("\n") + 1
            if line_start >= 0 and content[line_start:match.start()].strip():
                continue
            
            function_name = match.group(1)
            function_start = match.start()
            function_line = self.find_line_number(content, function_start)
            
            # Find the end of the function
            function_end = len(content)
            next_function_match = self.function_pattern.search(content[function_start + 1:])
            if next_function_match:
                # Check if the next function is at the same indentation level
                next_function_start = function_start + 1 + next_function_match.start()
                next_line_start = content[:next_function_start].rfind("\n") + 1
                if next_line_start >= 0 and not content[next_line_start:next_function_start].strip():
                    function_end = next_function_start
            
            function_content = content[function_start:function_end]
            function_end_line = function_line + function_content.count("\n")
            
            # Extract docstring
            docstring = self.extract_docstring(function_content, self.docstring_pattern, 0)
            
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


# Register the parser
parser_registry = ParserRegistry()
parser_registry.register(["py"], PythonParser)
