"""
PHP code parser.
"""
import re
from typing import List, Match, Optional, Tuple

from ...types.file_types import CodeDefinition
from .base import BaseParser


class PHPParser(BaseParser):
    """
    Parser for PHP code.
    """

    def __init__(self):
        """Initialize the PHP parser."""
        super().__init__()
        self.class_pattern = re.compile(r"class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?")
        self.interface_pattern = re.compile(r"interface\s+(\w+)(?:\s+extends\s+([^{]+))?")
        self.trait_pattern = re.compile(r"trait\s+(\w+)")
        self.function_pattern = re.compile(r"function\s+(\w+)\s*\(([^)]*)\)")
        self.method_pattern = re.compile(r"(?:public|private|protected)?\s*(?:static)?\s*function\s+(\w+)\s*\(([^)]*)\)")
        self.property_pattern = re.compile(r"(?:public|private|protected)\s+(?:static)?\s*\$(\w+)")
        self.namespace_pattern = re.compile(r"namespace\s+([^;]+);")
        self.docstring_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
        self.inline_comment_pattern = re.compile(r'//\s*(.*?)$', re.MULTILINE)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse PHP code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find namespace
        namespace = self._find_namespace(content)
        
        # Find all classes
        definitions.extend(self._find_classes(content, file_path, namespace))
        
        # Find all interfaces
        definitions.extend(self._find_interfaces(content, file_path, namespace))
        
        # Find all traits
        definitions.extend(self._find_traits(content, file_path, namespace))
        
        # Find all functions (not methods)
        definitions.extend(self._find_functions(content, file_path, namespace))
        
        return definitions

    def _find_namespace(self, content: str) -> Optional[str]:
        """
        Find the namespace in the content.

        Args:
            content: The content of the file.

        Returns:
            Optional[str]: The namespace, or None if not found.
        """
        match = self.namespace_pattern.search(content)
        if match:
            return match.group(1).strip()
        return None

    def _find_classes(self, content: str, file_path: str, namespace: Optional[str]) -> List[CodeDefinition]:
        """
        Find all classes in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            namespace: The namespace of the file.

        Returns:
            List[CodeDefinition]: A list of class definitions.
        """
        definitions = []
        
        for match in self.class_pattern.finditer(content):
            class_name = match.group(1)
            class_start = match.start()
            class_line = self.find_line_number(content, class_start)
            
            # Find the opening brace
            opening_brace = content.find("{", class_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the class (matching braces)
            class_end = self.find_block_end(content, opening_brace, "{", "}")
            class_content = content[class_start:class_end]
            class_end_line = class_line + class_content.count("\n")
            
            # Extract docstring (PHP uses /** */ or // comments)
            docstring = self._extract_php_docstring(content, class_start)
            
            # Create class definition
            full_name = f"{namespace}\\{class_name}" if namespace else class_name
            class_def = CodeDefinition(
                name=full_name,
                type="class",
                file_path=file_path,
                line_number=class_line,
                end_line_number=class_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all methods in the class
            methods = self._find_class_methods(class_content, file_path, full_name, class_start)
            for method in methods:
                class_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the class
            properties = self._find_class_properties(class_content, file_path, full_name, class_start)
            for prop in properties:
                class_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(class_def)
        
        return definitions

    def _find_interfaces(self, content: str, file_path: str, namespace: Optional[str]) -> List[CodeDefinition]:
        """
        Find all interfaces in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            namespace: The namespace of the file.

        Returns:
            List[CodeDefinition]: A list of interface definitions.
        """
        definitions = []
        
        for match in self.interface_pattern.finditer(content):
            interface_name = match.group(1)
            interface_start = match.start()
            interface_line = self.find_line_number(content, interface_start)
            
            # Find the opening brace
            opening_brace = content.find("{", interface_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the interface (matching braces)
            interface_end = self.find_block_end(content, opening_brace, "{", "}")
            interface_content = content[interface_start:interface_end]
            interface_end_line = interface_line + interface_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_php_docstring(content, interface_start)
            
            # Create interface definition
            full_name = f"{namespace}\\{interface_name}" if namespace else interface_name
            interface_def = CodeDefinition(
                name=full_name,
                type="interface",
                file_path=file_path,
                line_number=interface_line,
                end_line_number=interface_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all methods in the interface
            methods = self._find_class_methods(interface_content, file_path, full_name, interface_start)
            for method in methods:
                interface_def.children.append(method.name)
                definitions.append(method)
            
            definitions.append(interface_def)
        
        return definitions

    def _find_traits(self, content: str, file_path: str, namespace: Optional[str]) -> List[CodeDefinition]:
        """
        Find all traits in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            namespace: The namespace of the file.

        Returns:
            List[CodeDefinition]: A list of trait definitions.
        """
        definitions = []
        
        for match in self.trait_pattern.finditer(content):
            trait_name = match.group(1)
            trait_start = match.start()
            trait_line = self.find_line_number(content, trait_start)
            
            # Find the opening brace
            opening_brace = content.find("{", trait_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the trait (matching braces)
            trait_end = self.find_block_end(content, opening_brace, "{", "}")
            trait_content = content[trait_start:trait_end]
            trait_end_line = trait_line + trait_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_php_docstring(content, trait_start)
            
            # Create trait definition
            full_name = f"{namespace}\\{trait_name}" if namespace else trait_name
            trait_def = CodeDefinition(
                name=full_name,
                type="trait",
                file_path=file_path,
                line_number=trait_line,
                end_line_number=trait_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all methods in the trait
            methods = self._find_class_methods(trait_content, file_path, full_name, trait_start)
            for method in methods:
                trait_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the trait
            properties = self._find_class_properties(trait_content, file_path, full_name, trait_start)
            for prop in properties:
                trait_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(trait_def)
        
        return definitions

    def _find_functions(self, content: str, file_path: str, namespace: Optional[str]) -> List[CodeDefinition]:
        """
        Find all top-level functions in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            namespace: The namespace of the file.

        Returns:
            List[CodeDefinition]: A list of function definitions.
        """
        definitions = []
        
        for match in self.function_pattern.finditer(content):
            # Check if this function is inside a class, interface, or trait
            function_start = match.start()
            
            # Skip if inside a class, interface, or trait
            if self._is_inside_class_or_interface(content, function_start):
                continue
            
            function_name = match.group(1)
            function_line = self.find_line_number(content, function_start)
            
            # Find the opening brace
            opening_brace = content.find("{", function_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the function (matching braces)
            function_end = self.find_block_end(content, opening_brace, "{", "}")
            function_content = content[function_start:function_end]
            function_end_line = function_line + function_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_php_docstring(content, function_start)
            
            # Create function definition
            full_name = f"{namespace}\\{function_name}" if namespace else function_name
            function_def = CodeDefinition(
                name=full_name,
                type="function",
                file_path=file_path,
                line_number=function_line,
                end_line_number=function_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            definitions.append(function_def)
        
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
            
            # Find the opening brace
            opening_brace = class_content.find("{", method_start_in_class)
            if opening_brace == -1:
                continue
            
            # Find the end of the method (matching braces)
            method_end_in_class = self.find_block_end(class_content, opening_brace, "{", "}")
            method_content = class_content[method_start_in_class:method_end_in_class]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_php_docstring(class_content, method_start_in_class)
            
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

    def _find_class_properties(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
        """
        Find all properties in a class.

        Args:
            class_content: The content of the class.
            file_path: The path to the file.
            class_name: The name of the class.
            class_start: The start position of the class in the original content.

        Returns:
            List[CodeDefinition]: A list of property definitions.
        """
        definitions = []
        
        for match in self.property_pattern.finditer(class_content):
            property_name = match.group(1)
            property_start_in_class = match.start()
            property_line = self.find_line_number(class_content, property_start_in_class)
            
            # Find the end of the property (semicolon)
            property_end_in_class = class_content.find(";", property_start_in_class)
            if property_end_in_class == -1:
                property_end_in_class = len(class_content)
            
            property_content = class_content[property_start_in_class:property_end_in_class+1]
            
            # Extract docstring
            docstring = self._extract_php_docstring(class_content, property_start_in_class)
            
            # Create property definition
            property_def = CodeDefinition(
                name=property_name,
                type="property",
                file_path=file_path,
                line_number=property_line,
                end_line_number=property_line,
                signature=property_content.strip(),
                docstring=docstring,
                parent=class_name
            )
            
            definitions.append(property_def)
        
        return definitions

    def _is_inside_class_or_interface(self, content: str, position: int) -> bool:
        """
        Check if a position is inside a class, interface, or trait.

        Args:
            content: The content of the file.
            position: The position to check.

        Returns:
            bool: True if the position is inside a class, interface, or trait, False otherwise.
        """
        # Count the number of opening and closing braces before the position
        open_braces = content[:position].count("{")
        close_braces = content[:position].count("}")
        
        # Check if there are any class, interface, or trait definitions before the position
        class_matches = list(self.class_pattern.finditer(content[:position]))
        interface_matches = list(self.interface_pattern.finditer(content[:position]))
        trait_matches = list(self.trait_pattern.finditer(content[:position]))
        
        # If there are no class, interface, or trait definitions, it's not inside any of them
        if not class_matches and not interface_matches and not trait_matches:
            return False
        
        # If the number of opening braces is greater than the number of closing braces,
        # and there's at least one class, interface, or trait definition, it's inside one of them
        return open_braces > close_braces

    def _extract_php_docstring(self, content: str, start_pos: int) -> Optional[str]:
        """
        Extract a PHP docstring (comment) before a definition.

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
        
        # Look for docblock comments before the definition
        docblock_match = self.docstring_pattern.search(content[:start_pos], re.DOTALL)
        if docblock_match and docblock_match.end() > line_start - 10:  # Allow some whitespace
            return docblock_match.group(1).strip()
        
        # Look for inline comments before the definition
        comment_block = []
        current_pos = line_start
        
        # Go backward to find comments
        while current_pos > 0:
            prev_line_end = content[:current_pos-1].rfind("\n")
            if prev_line_end < 0:
                prev_line_end = 0
            
            prev_line = content[prev_line_end:current_pos-1].strip()
            
            # Check if the previous line is a comment
            inline_match = self.inline_comment_pattern.match(prev_line)
            if inline_match:
                comment_block.insert(0, inline_match.group(1).strip())
                current_pos = prev_line_end + 1
            else:
                break
        
        if comment_block:
            return "\n".join(comment_block)
        
        return None
