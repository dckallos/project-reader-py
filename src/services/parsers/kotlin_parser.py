"""
Kotlin code parser.
"""
import re
from typing import List, Match, Optional, Tuple

from ...types.file_types import CodeDefinition
from .base import BaseParser


class KotlinParser(BaseParser):
    """
    Parser for Kotlin code.
    """

    def __init__(self):
        """Initialize the Kotlin parser."""
        super().__init__()
        self.class_pattern = re.compile(r"(?:public|private|protected|internal)?\s*(?:abstract|final|sealed|open)?\s*(?:data)?\s*class\s+(\w+)(?:<[^>]+>)?(?:\s*\([^)]*\))?(?:\s*:\s*([^{]+))?")
        self.interface_pattern = re.compile(r"(?:public|private|protected|internal)?\s*interface\s+(\w+)(?:<[^>]+>)?(?:\s*:\s*([^{]+))?")
        self.object_pattern = re.compile(r"(?:public|private|protected|internal)?\s*object\s+(\w+)(?:\s*:\s*([^{]+))?")
        self.enum_pattern = re.compile(r"(?:public|private|protected|internal)?\s*enum\s+class\s+(\w+)(?:\s*\([^)]*\))?(?:\s*:\s*([^{]+))?")
        self.function_pattern = re.compile(r"(?:public|private|protected|internal)?\s*(?:inline|suspend)?\s*fun\s+(?:<[^>]+>\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*[^{]+)?")
        self.property_pattern = re.compile(r"(?:public|private|protected|internal)?\s*(?:val|var)\s+(\w+)\s*(?::\s*[^=]+)?(?:\s*=\s*[^{;]+)?")
        self.companion_pattern = re.compile(r"companion\s+object(?:\s+(\w+))?")
        self.extension_function_pattern = re.compile(r"(?:public|private|protected|internal)?\s*(?:inline|suspend)?\s*fun\s+([^.]+)\.(\w+)\s*\(([^)]*)\)(?:\s*:\s*[^{]+)?")
        self.typealias_pattern = re.compile(r"(?:public|private|protected|internal)?\s*typealias\s+(\w+)(?:<[^>]+>)?\s*=")
        self.docstring_pattern = re.compile(r'\/\*\*(.*?)\*\/', re.DOTALL)
        self.kdoc_pattern = re.compile(r'\/\*\*(.*?)\*\/', re.DOTALL)
        self.inline_comment_pattern = re.compile(r'//\s*(.*?)$', re.MULTILINE)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse Kotlin code and extract definitions.

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
        
        # Find all objects
        definitions.extend(self._find_objects(content, file_path))
        
        # Find all enums
        definitions.extend(self._find_enums(content, file_path))
        
        # Find all functions (not methods)
        definitions.extend(self._find_functions(content, file_path))
        
        # Find all extension functions
        definitions.extend(self._find_extension_functions(content, file_path))
        
        # Find all top-level properties
        definitions.extend(self._find_properties(content, file_path))
        
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
            docstring = self._extract_kotlin_docstring(content, class_start)
            
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
            properties = self._find_class_properties(class_content, file_path, class_name, class_start)
            for prop in properties:
                class_def.children.append(prop.name)
                definitions.append(prop)
            
            # Find companion objects in the class
            companions = self._find_companion_objects(class_content, file_path, class_name, class_start)
            for companion in companions:
                class_def.children.append(companion.name)
                definitions.append(companion)
            
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
            
            # Find the opening brace
            opening_brace = content.find("{", interface_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the interface (matching braces)
            interface_end = self.find_block_end(content, opening_brace, "{", "}")
            interface_content = content[interface_start:interface_end]
            interface_end_line = interface_line + interface_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_kotlin_docstring(content, interface_start)
            
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
            
            # Find all methods in the interface
            methods = self._find_methods(interface_content, file_path, interface_name, interface_start)
            for method in methods:
                interface_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the interface
            properties = self._find_class_properties(interface_content, file_path, interface_name, interface_start)
            for prop in properties:
                interface_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(interface_def)
        
        return definitions

    def _find_objects(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all objects in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of object definitions.
        """
        definitions = []
        
        for match in self.object_pattern.finditer(content):
            object_name = match.group(1)
            object_start = match.start()
            object_line = self.find_line_number(content, object_start)
            
            # Find the opening brace
            opening_brace = content.find("{", object_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the object (matching braces)
            object_end = self.find_block_end(content, opening_brace, "{", "}")
            object_content = content[object_start:object_end]
            object_end_line = object_line + object_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_kotlin_docstring(content, object_start)
            
            # Create object definition
            object_def = CodeDefinition(
                name=object_name,
                type="object",
                file_path=file_path,
                line_number=object_line,
                end_line_number=object_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all methods in the object
            methods = self._find_methods(object_content, file_path, object_name, object_start)
            for method in methods:
                object_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the object
            properties = self._find_class_properties(object_content, file_path, object_name, object_start)
            for prop in properties:
                object_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(object_def)
        
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
            docstring = self._extract_kotlin_docstring(content, enum_start)
            
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
            properties = self._find_class_properties(enum_content, file_path, enum_name, enum_start)
            for prop in properties:
                enum_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(enum_def)
        
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
            # Check if this function is inside a class, interface, etc.
            function_start = match.start()
            
            # Skip if inside a class, interface, etc.
            if self._is_inside_block(content, function_start):
                continue
            
            function_name = match.group(1)
            function_line = self.find_line_number(content, function_start)
            
            # Find the opening brace
            opening_brace = content.find("{", function_start)
            if opening_brace == -1:
                # This might be a function declaration without a body
                function_end = content.find(";", function_start)
                if function_end == -1:
                    continue
                function_content = content[function_start:function_end+1]
                function_end_line = function_line + function_content.count("\n")
            else:
                # Function with a body
                function_end = self.find_block_end(content, opening_brace, "{", "}")
                function_content = content[function_start:function_end]
                function_end_line = function_line + function_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_kotlin_docstring(content, function_start)
            
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

    def _find_extension_functions(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all extension functions in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of extension function definitions.
        """
        definitions = []
        
        for match in self.extension_function_pattern.finditer(content):
            # Check if this function is inside a class, interface, etc.
            function_start = match.start()
            
            # Skip if inside a class, interface, etc.
            if self._is_inside_block(content, function_start):
                continue
            
            receiver_type = match.group(1)
            function_name = match.group(2)
            function_line = self.find_line_number(content, function_start)
            
            # Find the opening brace
            opening_brace = content.find("{", function_start)
            if opening_brace == -1:
                # This might be a function declaration without a body
                function_end = content.find(";", function_start)
                if function_end == -1:
                    continue
                function_content = content[function_start:function_end+1]
                function_end_line = function_line + function_content.count("\n")
            else:
                # Function with a body
                function_end = self.find_block_end(content, opening_brace, "{", "}")
                function_content = content[function_start:function_end]
                function_end_line = function_line + function_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_kotlin_docstring(content, function_start)
            
            # Create extension function definition
            function_def = CodeDefinition(
                name=function_name,
                type="extension_function",
                file_path=file_path,
                line_number=function_line,
                end_line_number=function_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=receiver_type
            )
            
            definitions.append(function_def)
        
        return definitions

    def _find_properties(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all top-level properties in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of property definitions.
        """
        definitions = []
        
        for match in self.property_pattern.finditer(content):
            # Check if this property is inside a class, interface, etc.
            property_start = match.start()
            
            # Skip if inside a class, interface, etc.
            if self._is_inside_block(content, property_start):
                continue
            
            property_name = match.group(1)
            property_line = self.find_line_number(content, property_start)
            
            # Find the end of the property (semicolon or newline)
            semicolon = content.find(";", property_start)
            newline = content.find("\n", property_start)
            opening_brace = content.find("{", property_start)
            
            if semicolon != -1 and (newline == -1 or semicolon < newline) and (opening_brace == -1 or semicolon < opening_brace):
                property_end = semicolon + 1
            elif opening_brace != -1 and (newline == -1 or opening_brace < newline):
                # Property with a getter/setter block
                property_end = self.find_block_end(content, opening_brace, "{", "}")
            elif newline != -1:
                property_end = newline
            else:
                property_end = len(content)
            
            property_content = content[property_start:property_end]
            property_end_line = property_line + property_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_kotlin_docstring(content, property_start)
            
            # Create property definition
            property_def = CodeDefinition(
                name=property_name,
                type="property",
                file_path=file_path,
                line_number=property_line,
                end_line_number=property_end_line,
                signature=property_content.strip(),
                docstring=docstring
            )
            
            definitions.append(property_def)
        
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
            # Check if this typealias is inside a class, interface, etc.
            typealias_start = match.start()
            
            # Skip if inside a class, interface, etc.
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
            typealias_end_line = typealias_line + typealias_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_kotlin_docstring(content, typealias_start)
            
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
        Find all methods in a container (class, interface, object, enum).

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
                # This might be a method declaration without a body (in an interface)
                method_end_in_container = container_content.find(";", method_start_in_container)
                if method_end_in_container == -1:
                    continue
                method_content = container_content[method_start_in_container:method_end_in_container+1]
                method_end_line = method_line + method_content.count("\n")
            else:
                # Method with a body
                method_end_in_container = self.find_block_end(container_content, opening_brace, "{", "}")
                method_content = container_content[method_start_in_container:method_end_in_container]
                method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_kotlin_docstring(container_content, method_start_in_container)
            
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

    def _find_class_properties(self, container_content: str, file_path: str, container_name: str, container_start: int) -> List[CodeDefinition]:
        """
        Find all properties in a container (class, interface, object, enum).

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
            docstring = self._extract_kotlin_docstring(container_content, property_start_in_container)
            
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

    def _find_companion_objects(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
        """
        Find all companion objects in a class.

        Args:
            class_content: The content of the class.
            file_path: The path to the file.
            class_name: The name of the class.
            class_start: The start position of the class in the original content.

        Returns:
            List[CodeDefinition]: A list of companion object definitions.
        """
        definitions = []
        
        for match in self.companion_pattern.finditer(class_content):
            companion_name = match.group(1) if match.group(1) else "Companion"
            companion_start_in_class = match.start()
            companion_start = class_start + companion_start_in_class
            companion_line = self.find_line_number(class_content, companion_start_in_class)
            
            # Find the opening brace
            opening_brace = class_content.find("{", companion_start_in_class)
            if opening_brace == -1:
                continue
            
            # Find the end of the companion object (matching braces)
            companion_end_in_class = self.find_block_end(class_content, opening_brace, "{", "}")
            companion_content = class_content[companion_start_in_class:companion_end_in_class]
            companion_end_line = companion_line + companion_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_kotlin_docstring(class_content, companion_start_in_class)
            
            # Create companion object definition
            companion_def = CodeDefinition(
                name=companion_name,
                type="companion_object",
                file_path=file_path,
                line_number=companion_line,
                end_line_number=companion_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=class_name
            )
            
            # Find all methods in the companion object
            methods = self._find_methods(companion_content, file_path, f"{class_name}.{companion_name}", companion_start)
            for method in methods:
                companion_def.children.append(method.name)
                definitions.append(method)
            
            # Find all properties in the companion object
            properties = self._find_class_properties(companion_content, file_path, f"{class_name}.{companion_name}", companion_start)
            for prop in properties:
                companion_def.children.append(prop.name)
                definitions.append(prop)
            
            definitions.append(companion_def)
        
        return definitions

    def _is_inside_block(self, content: str, position: int) -> bool:
        """
        Check if a position is inside a block (class, interface, etc.).

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

    def _extract_kotlin_docstring(self, content: str, start_pos: int) -> Optional[str]:
        """
        Extract a Kotlin docstring (KDoc or comment) before a definition.

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
        
        # Look for KDoc comments before the definition
        kdoc_match = self.kdoc_pattern.search(content[:start_pos], re.DOTALL)
        if kdoc_match and kdoc_match.end() > line_start - 10:  # Allow some whitespace
            return kdoc_match.group(1).strip()
        
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
