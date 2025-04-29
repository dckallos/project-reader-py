"""
Ruby code parser.
"""
import re
from typing import List, Match, Optional, Tuple

from ...types.file_types import CodeDefinition
from .base import BaseParser


class RubyParser(BaseParser):
    """
    Parser for Ruby code.
    """

    def __init__(self):
        """Initialize the Ruby parser."""
        super().__init__()
        self.class_pattern = re.compile(r"class\s+(\w+)(?:\s*<\s*(\w+))?")
        self.module_pattern = re.compile(r"module\s+(\w+)")
        self.method_pattern = re.compile(r"def\s+(?:self\.)?(\w+)(?:\(([^)]*)\))?")
        self.attr_pattern = re.compile(r"attr(?:_reader|_writer|_accessor)\s+:([\w,\s]+)")
        self.docstring_pattern = re.compile(r'#\s*(.*?)$', re.MULTILINE)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse Ruby code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find all classes
        definitions.extend(self._find_classes(content, file_path))
        
        # Find all modules
        definitions.extend(self._find_modules(content, file_path))
        
        # Find all top-level methods (not in classes or modules)
        definitions.extend(self._find_methods(content, file_path))
        
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
            
            # Find the end of the class (end keyword)
            class_end = self._find_ruby_block_end(content, class_start, "class")
            class_content = content[class_start:class_end]
            class_end_line = class_line + class_content.count("\n")
            
            # Extract docstring (Ruby uses # comments)
            docstring = self._extract_ruby_docstring(content, class_start)
            
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
            methods = self._find_class_methods(class_content, file_path, class_name, class_start)
            for method in methods:
                class_def.children.append(method.name)
                definitions.append(method)
            
            # Find all attributes in the class
            attributes = self._find_class_attributes(class_content, file_path, class_name, class_start)
            for attr in attributes:
                class_def.children.append(attr.name)
                definitions.append(attr)
            
            definitions.append(class_def)
        
        return definitions

    def _find_modules(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all modules in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of module definitions.
        """
        definitions = []
        
        for match in self.module_pattern.finditer(content):
            module_name = match.group(1)
            module_start = match.start()
            module_line = self.find_line_number(content, module_start)
            
            # Find the end of the module (end keyword)
            module_end = self._find_ruby_block_end(content, module_start, "module")
            module_content = content[module_start:module_end]
            module_end_line = module_line + module_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_ruby_docstring(content, module_start)
            
            # Create module definition
            module_def = CodeDefinition(
                name=module_name,
                type="module",
                file_path=file_path,
                line_number=module_line,
                end_line_number=module_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all methods in the module
            methods = self._find_class_methods(module_content, file_path, module_name, module_start)
            for method in methods:
                module_def.children.append(method.name)
                definitions.append(method)
            
            definitions.append(module_def)
        
        return definitions

    def _find_methods(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all top-level methods in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of method definitions.
        """
        definitions = []
        
        for match in self.method_pattern.finditer(content):
            # Check if this method is inside a class or module
            method_start = match.start()
            
            # Skip if inside a class or module
            if self._is_inside_class_or_module(content, method_start):
                continue
            
            method_name = match.group(1)
            method_line = self.find_line_number(content, method_start)
            
            # Find the end of the method (end keyword)
            method_end = self._find_ruby_block_end(content, method_start, "def")
            method_content = content[method_start:method_end]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_ruby_docstring(content, method_start)
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="function",  # Top-level methods are considered functions
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            definitions.append(method_def)
        
        return definitions

    def _find_class_methods(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
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
            method_name = match.group(1)
            method_start_in_class = match.start()
            method_start = class_start + method_start_in_class
            method_line = self.find_line_number(class_content, method_start_in_class)
            
            # Find the end of the method (end keyword)
            method_end_in_class = self._find_ruby_block_end(class_content, method_start_in_class, "def")
            method_content = class_content[method_start_in_class:method_end_in_class]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_ruby_docstring(class_content, method_start_in_class)
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=class_name
            )
            
            definitions.append(method_def)
        
        return definitions

    def _find_class_attributes(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
        """
        Find all attributes in a class.

        Args:
            class_content: The content of the class.
            file_path: The path to the file.
            class_name: The name of the class.
            class_start: The start position of the class in the original content.

        Returns:
            List[CodeDefinition]: A list of attribute definitions.
        """
        definitions = []
        
        for match in self.attr_pattern.finditer(class_content):
            attr_list = match.group(1)
            attr_start_in_class = match.start()
            attr_line = self.find_line_number(class_content, attr_start_in_class)
            
            # Split multiple attributes (attr_accessor :name, :age, :email)
            for attr_name in attr_list.split(','):
                attr_name = attr_name.strip()
                
                # Extract docstring
                docstring = self._extract_ruby_docstring(class_content, attr_start_in_class)
                
                # Create attribute definition
                attr_def = CodeDefinition(
                    name=attr_name,
                    type="attribute",
                    file_path=file_path,
                    line_number=attr_line,
                    end_line_number=attr_line,
                    signature=match.group(0),
                    docstring=docstring,
                    parent=class_name
                )
                
                definitions.append(attr_def)
        
        return definitions

    def _is_inside_class_or_module(self, content: str, position: int) -> bool:
        """
        Check if a position is inside a class or module.

        Args:
            content: The content of the file.
            position: The position to check.

        Returns:
            bool: True if the position is inside a class or module, False otherwise.
        """
        # Count the number of class/module and end keywords before the position
        class_module_count = len(re.findall(r"class\s+\w+|module\s+\w+", content[:position]))
        end_count = len(re.findall(r"\bend\b", content[:position]))
        
        return class_module_count > end_count

    def _find_ruby_block_end(self, content: str, start_pos: int, block_type: str) -> int:
        """
        Find the end of a Ruby block (class, module, def, etc.).

        Args:
            content: The content of the file.
            start_pos: The position to start searching from.
            block_type: The type of block (class, module, def, etc.).

        Returns:
            int: The position of the end of the block.
        """
        # Count nested blocks
        block_count = 1
        current_pos = start_pos
        
        # Skip the first line (the block definition)
        line_end = content[current_pos:].find("\n")
        if line_end != -1:
            current_pos += line_end + 1
        
        while current_pos < len(content) and block_count > 0:
            # Check for new blocks
            if re.search(r"\b(class|module|def|if|unless|case|begin|do)\b", content[current_pos:current_pos+20]):
                block_count += 1
            
            # Check for end keyword
            if re.search(r"\bend\b", content[current_pos:current_pos+5]):
                block_count -= 1
                if block_count == 0:
                    # Find the end of the line
                    line_end = content[current_pos:].find("\n")
                    if line_end != -1:
                        return current_pos + line_end
                    else:
                        return len(content)
            
            current_pos += 1
        
        return len(content)

    def _extract_ruby_docstring(self, content: str, start_pos: int) -> Optional[str]:
        """
        Extract a Ruby docstring (comment) before a definition.

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
            if prev_line.startswith("#"):
                comment_block.insert(0, prev_line[1:].strip())
                current_pos = prev_line_end + 1
            else:
                break
        
        if comment_block:
            return "\n".join(comment_block)
        
        return None
