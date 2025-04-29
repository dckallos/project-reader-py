"""
Swift code parser.
"""
import re
from typing import List, Match, Optional, Tuple

from ...types.file_types import CodeDefinition
from .base import BaseParser


class SwiftParser(BaseParser):
    """
    Parser for Swift code.
    """

    def __init__(self):
        """Initialize the Swift parser."""
        super().__init__()
        self.class_pattern = re.compile(r"(?:public|private|internal|fileprivate|open)?\s*(?:final)?\s*class\s+(\w+)(?:\s*:\s*([^{]+))?")
        self.struct_pattern = re.compile(r"(?:public|private|internal|fileprivate|open)?\s*struct\s+(\w+)(?:\s*:\s*([^{]+))?")
        self.enum_pattern = re.compile(r"(?:public|private|internal|fileprivate|open)?\s*enum\s+(\w+)(?:\s*:\s*([^{]+))?")
        self.protocol_pattern = re.compile(r"(?:public|private|internal|fileprivate|open)?\s*protocol\s+(\w+)(?:\s*:\s*([^{]+))?")
        self.extension_pattern = re.compile(r"(?:public|private|internal|fileprivate|open)?\s*extension\s+(\w+)(?:\s*:\s*([^{]+))?")
        self.function_pattern = re.compile(r"(?:public|private|internal|fileprivate|open)?\s*(?:static|class)?\s*func\s+(\w+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)(?:\s*->\s*[^{]+)?")
        self.property_pattern = re.compile(r"(?:public|private|internal|fileprivate|open)?\s*(?:static|class)?\s*(?:let|var)\s+(\w+)\s*:")
        self.typealias_pattern = re.compile(r"(?:public|private|internal|fileprivate|open)?\s*typealias\s+(\w+)\s*=")
        self.docstring_pattern = re.compile(r'///\s*(.*?)$|/\*\*(.*?)\*/', re.MULTILINE | re.DOTALL)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse Swift code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find all classes
        definitions.extend(self._find_classes(content, file_path))
        
        # Find all structs
        definitions.extend(self._find_structs(content, file_path))
        
        # Find all enums
        definitions.extend(self._find_enums(content, file_path))
        
        # Find all protocols
        definitions.extend(self._find_protocols(content, file_path))
        
        # Find all extensions
        definitions.extend(self._find_extensions(content, file_path))
        
        # Find all functions (not methods)
        definitions.extend(self._find_functions(content, file_path))
        
        # Find all typealiases
        definitions.extend(self._find_typealiases(content, file_path))
        
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
            
            # Find the opening brace
            opening_brace = content.find("{", class_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the class (matching braces)
            class_end = self.find_block_end(content, opening_brace, "{", "}")
            class_content = content[class_start:class_end]
            class_end_line = class_line + class_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_swift_docstring(content, class_start)
            
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
            
            # Find all properties in the class
            properties = self._find_properties(class_content, file_path, class_name, class_start)
            for prop in properties:
                class_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(class_def)
        
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
            
            # Find the opening brace
            opening_brace = content.find("{", struct_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the struct (matching braces)
            struct_end = self.find_block_end(content, opening_brace, "{", "}")
            struct_content = content[struct_start:struct_end]
            struct_end_line = struct_line + struct_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_swift_docstring(content, struct_start)
            
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
            
            # Find all methods in the struct
            methods = self._find_methods(struct_content, file_path, struct_name, struct_start)
            for method in methods:
                struct_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the struct
            properties = self._find_properties(struct_content, file_path, struct_name, struct_start)
            for prop in properties:
                struct_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(struct_def)
        
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
            
            # Find the opening brace
            opening_brace = content.find("{", enum_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the enum (matching braces)
            enum_end = self.find_block_end(content, opening_brace, "{", "}")
            enum_content = content[enum_start:enum_end]
            enum_end_line = enum_line + enum_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_swift_docstring(content, enum_start)
            
            # Create enum definition
            enum_def = CodeDefinition(
                name=enum_name,
                type="enum",
                file_path=file_path,
                line_number=enum_line,
                end_line_number=enum_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all methods in the enum
            methods = self._find_methods(enum_content, file_path, enum_name, enum_start)
            for method in methods:
                enum_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the enum
            properties = self._find_properties(enum_content, file_path, enum_name, enum_start)
            for prop in properties:
                enum_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(enum_def)
        
        return definitions

    def _find_protocols(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all protocols in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of protocol definitions.
        """
        definitions = []
        
        for match in self.protocol_pattern.finditer(content):
            protocol_name = match.group(1)
            protocol_start = match.start()
            protocol_line = self.find_line_number(content, protocol_start)
            
            # Find the opening brace
            opening_brace = content.find("{", protocol_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the protocol (matching braces)
            protocol_end = self.find_block_end(content, opening_brace, "{", "}")
            protocol_content = content[protocol_start:protocol_end]
            protocol_end_line = protocol_line + protocol_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_swift_docstring(content, protocol_start)
            
            # Create protocol definition
            protocol_def = CodeDefinition(
                name=protocol_name,
                type="protocol",
                file_path=file_path,
                line_number=protocol_line,
                end_line_number=protocol_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all methods in the protocol
            methods = self._find_methods(protocol_content, file_path, protocol_name, protocol_start)
            for method in methods:
                protocol_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the protocol
            properties = self._find_properties(protocol_content, file_path, protocol_name, protocol_start)
            for prop in properties:
                protocol_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(protocol_def)
        
        return definitions

    def _find_extensions(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all extensions in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of extension definitions.
        """
        definitions = []
        
        for match in self.extension_pattern.finditer(content):
            extended_type = match.group(1)
            extension_start = match.start()
            extension_line = self.find_line_number(content, extension_start)
            
            # Find the opening brace
            opening_brace = content.find("{", extension_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the extension (matching braces)
            extension_end = self.find_block_end(content, opening_brace, "{", "}")
            extension_content = content[extension_start:extension_end]
            extension_end_line = extension_line + extension_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_swift_docstring(content, extension_start)
            
            # Create extension definition
            extension_def = CodeDefinition(
                name=f"extension {extended_type}",
                type="extension",
                file_path=file_path,
                line_number=extension_line,
                end_line_number=extension_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=extended_type
            )
            
            # Find all methods in the extension
            methods = self._find_methods(extension_content, file_path, extended_type, extension_start)
            for method in methods:
                extension_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the extension
            properties = self._find_properties(extension_content, file_path, extended_type, extension_start)
            for prop in properties:
                extension_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(extension_def)
        
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
            # Check if this function is inside a class, struct, etc.
            function_start = match.start()
            
            # Skip if inside a class, struct, etc.
            if self._is_inside_block(content, function_start):
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
            docstring = self._extract_swift_docstring(content, function_start)
            
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

    def _find_typealiases(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all type aliases in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of type alias definitions.
        """
        definitions = []
        
        for match in self.typealias_pattern.finditer(content):
            # Check if this typealias is inside a class, struct, etc.
            typealias_start = match.start()
            
            # Skip if inside a class, struct, etc.
            if self._is_inside_block(content, typealias_start):
                continue
            
            typealias_name = match.group(1)
            typealias_line = self.find_line_number(content, typealias_start)
            
            # Find the end of the typealias (semicolon or newline)
            semicolon = content.find(";", typealias_start)
            newline = content.find("\n", typealias_start)
            
            if semicolon != -1 and (newline == -1 or semicolon < newline):
                typealias_end = semicolon + 1
            elif newline != -1:
                typealias_end = newline
            else:
                typealias_end = len(content)
            
            typealias_content = content[typealias_start:typealias_end]
            typealias_end_line = typealias_line
            
            # Extract docstring
            docstring = self._extract_swift_docstring(content, typealias_start)
            
            # Create typealias definition
            typealias_def = CodeDefinition(
                name=typealias_name,
                type="typealias",
                file_path=file_path,
                line_number=typealias_line,
                end_line_number=typealias_end_line,
                signature=typealias_content.strip(),
                docstring=docstring
            )
            
            definitions.append(typealias_def)
        
        return definitions

    def _find_methods(self, container_content: str, file_path: str, container_name: str, container_start: int) -> List[CodeDefinition]:
        """
        Find all methods in a container (class, struct, enum, protocol, extension).

        Args:
            container_content: The content of the container.
            file_path: The path to the file.
            container_name: The name of the container.
            container_start: The start position of the container in the original content.

        Returns:
            List[CodeDefinition]: A list of method definitions.
        """
        definitions = []
        
        for match in self.function_pattern.finditer(container_content):
            method_name = match.group(1)
            method_start_in_container = match.start()
            method_start = container_start + method_start_in_container
            method_line = self.find_line_number(container_content, method_start_in_container)
            
            # Find the opening brace
            opening_brace = container_content.find("{", method_start_in_container)
            if opening_brace == -1:
                continue
            
            # Find the end of the method (matching braces)
            method_end_in_container = self.find_block_end(container_content, opening_brace, "{", "}")
            method_content = container_content[method_start_in_container:method_end_in_container]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_swift_docstring(container_content, method_start_in_container)
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=container_name
            )
            
            definitions.append(method_def)
        
        return definitions

    def _find_properties(self, container_content: str, file_path: str, container_name: str, container_start: int) -> List[CodeDefinition]:
        """
        Find all properties in a container (class, struct, enum, protocol, extension).

        Args:
            container_content: The content of the container.
            file_path: The path to the file.
            container_name: The name of the container.
            container_start: The start position of the container in the original content.

        Returns:
            List[CodeDefinition]: A list of property definitions.
        """
        definitions = []
        
        for match in self.property_pattern.finditer(container_content):
            property_name = match.group(1)
            property_start_in_container = match.start()
            property_line = self.find_line_number(container_content, property_start_in_container)
            
            # Find the end of the property (semicolon or newline)
            semicolon = container_content.find(";", property_start_in_container)
            newline = container_content.find("\n", property_start_in_container)
            opening_brace = container_content.find("{", property_start_in_container)
            
            if semicolon != -1 and (newline == -1 or semicolon < newline) and (opening_brace == -1 or semicolon < opening_brace):
                property_end_in_container = semicolon + 1
            elif opening_brace != -1 and (newline == -1 or opening_brace < newline):
                # Property with a getter/setter block
                property_end_in_container = self.find_block_end(container_content, opening_brace, "{", "}")
            elif newline != -1:
                property_end_in_container = newline
            else:
                property_end_in_container = len(container_content)
            
            property_content = container_content[property_start_in_container:property_end_in_container]
            property_end_line = property_line + property_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_swift_docstring(container_content, property_start_in_container)
            
            # Create property definition
            property_def = CodeDefinition(
                name=property_name,
                type="property",
                file_path=file_path,
                line_number=property_line,
                end_line_number=property_end_line,
                signature=property_content.strip(),
                docstring=docstring,
                parent=container_name
            )
            
            definitions.append(property_def)
        
        return definitions

    def _is_inside_block(self, content: str, position: int) -> bool:
        """
        Check if a position is inside a block (class, struct, etc.).

        Args:
            content: The content of the file.
            position: The position to check.

        Returns:
            bool: True if the position is inside a block, False otherwise.
        """
        # Count the number of opening and closing braces before the position
        open_braces = content[:position].count("{")
        close_braces = content[:position].count("}")
        
        # If there are more opening braces than closing braces, it's inside a block
        return open_braces > close_braces

    def _extract_swift_docstring(self, content: str, start_pos: int) -> Optional[str]:
        """
        Extract a Swift docstring (comment) before a definition.

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
            # Check which group matched (/// or /** */)
            if docblock_match.group(1) is not None:
                return docblock_match.group(1).strip()
            else:
                return docblock_match.group(2).strip()
        
        # Look for multiple /// comments before the definition
        comment_block = []
        current_pos = line_start
        
        # Go backward to find comments
        while current_pos > 0:
            prev_line_end = content[:current_pos-1].rfind("\n")
            if prev_line_end < 0:
                prev_line_end = 0
            
            prev_line = content[prev_line_end:current_pos-1].strip()
            
            # Check if the previous line is a /// comment
            if prev_line.startswith("///"):
                comment_block.insert(0, prev_line[3:].strip())
                current_pos = prev_line_end + 1
            else:
                break
        
        if comment_block:
            return "\n".join(comment_block)
        
        return None
