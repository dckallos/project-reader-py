"""
Scala code parser.
"""
import re
from typing import List, Match, Optional, Tuple

from ...types.file_types import CodeDefinition
from .base import BaseParser


class ScalaParser(BaseParser):
    """
    Parser for Scala code.
    """

    def __init__(self):
        """Initialize the Scala parser."""
        super().__init__()
        self.class_pattern = re.compile(r"(?:abstract|final)?\s*class\s+(\w+)(?:\[[\w\s,<>]*\])?(?:\s*\([^)]*\))?(?:\s+extends\s+[^{]+)?")
        self.object_pattern = re.compile(r"object\s+(\w+)(?:\s+extends\s+[^{]+)?")
        self.trait_pattern = re.compile(r"trait\s+(\w+)(?:\[[\w\s,<>]*\])?(?:\s+extends\s+[^{]+)?")
        self.case_class_pattern = re.compile(r"case\s+class\s+(\w+)(?:\[[\w\s,<>]*\])?(?:\s*\([^)]*\))?(?:\s+extends\s+[^{]+)?")
        self.case_object_pattern = re.compile(r"case\s+object\s+(\w+)(?:\s+extends\s+[^{]+)?")
        self.def_pattern = re.compile(r"(?:private|protected|override)?\s*def\s+(\w+)(?:\[[\w\s,<>]*\])?(?:\s*\([^)]*\))?(?:\s*:\s*[^=]+)?")
        self.val_pattern = re.compile(r"(?:private|protected|override)?\s*val\s+(\w+)(?:\s*:\s*[^=]+)?")
        self.var_pattern = re.compile(r"(?:private|protected|override)?\s*var\s+(\w+)(?:\s*:\s*[^=]+)?")
        self.type_pattern = re.compile(r"type\s+(\w+)(?:\[[\w\s,<>]*\])?\s*=")
        self.package_pattern = re.compile(r"package\s+([^\s{]+)")
        self.import_pattern = re.compile(r"import\s+([^\s]+)")
        self.docstring_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
        self.scaladoc_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
        self.inline_comment_pattern = re.compile(r'//\s*(.*?)$', re.MULTILINE)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse Scala code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find package
        package = self._find_package(content)
        
        # Find all classes
        definitions.extend(self._find_classes(content, file_path, package))
        
        # Find all objects
        definitions.extend(self._find_objects(content, file_path, package))
        
        # Find all traits
        definitions.extend(self._find_traits(content, file_path, package))
        
        # Find all case classes
        definitions.extend(self._find_case_classes(content, file_path, package))
        
        # Find all case objects
        definitions.extend(self._find_case_objects(content, file_path, package))
        
        # Find all top-level defs
        definitions.extend(self._find_defs(content, file_path, package))
        
        # Find all top-level vals
        definitions.extend(self._find_vals(content, file_path, package))
        
        # Find all top-level vars
        definitions.extend(self._find_vars(content, file_path, package))
        
        # Find all type aliases
        definitions.extend(self._find_types(content, file_path, package))
        
        return definitions

    def _find_package(self, content: str) -> Optional[str]:
        """
        Find the package declaration in the content.

        Args:
            content: The content of the file.

        Returns:
            Optional[str]: The package name, or None if not found.
        """
        match = self.package_pattern.search(content)
        if match:
            return match.group(1)
        return None

    def _find_classes(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all classes in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

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
            docstring = self._extract_scala_docstring(content, class_start)
            
            # Create class definition
            full_name = f"{package}.{class_name}" if package else class_name
            class_def = CodeDefinition(
                name=full_name,
                type="class",
                file_path=file_path,
                line_number=class_line,
                end_line_number=class_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all defs in the class
            defs = self._find_class_defs(class_content, file_path, full_name, class_start)
            for def_def in defs:
                class_def.children.append(def_def.name)
                definitions.append(def_def)
            
            # Find all vals in the class
            vals = self._find_class_vals(class_content, file_path, full_name, class_start)
            for val_def in vals:
                class_def.children.append(val_def.name)
                definitions.append(val_def)
            
            # Find all vars in the class
            vars_defs = self._find_class_vars(class_content, file_path, full_name, class_start)
            for var_def in vars_defs:
                class_def.children.append(var_def.name)
                definitions.append(var_def)
            
            definitions.append(class_def)
        
        return definitions

    def _find_objects(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all objects in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

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
            docstring = self._extract_scala_docstring(content, object_start)
            
            # Create object definition
            full_name = f"{package}.{object_name}" if package else object_name
            object_def = CodeDefinition(
                name=full_name,
                type="object",
                file_path=file_path,
                line_number=object_line,
                end_line_number=object_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all defs in the object
            defs = self._find_class_defs(object_content, file_path, full_name, object_start)
            for def_def in defs:
                object_def.children.append(def_def.name)
                definitions.append(def_def)
            
            # Find all vals in the object
            vals = self._find_class_vals(object_content, file_path, full_name, object_start)
            for val_def in vals:
                object_def.children.append(val_def.name)
                definitions.append(val_def)
            
            # Find all vars in the object
            vars_defs = self._find_class_vars(object_content, file_path, full_name, object_start)
            for var_def in vars_defs:
                object_def.children.append(var_def.name)
                definitions.append(var_def)
            
            definitions.append(object_def)
        
        return definitions

    def _find_traits(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all traits in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

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
            docstring = self._extract_scala_docstring(content, trait_start)
            
            # Create trait definition
            full_name = f"{package}.{trait_name}" if package else trait_name
            trait_def = CodeDefinition(
                name=full_name,
                type="trait",
                file_path=file_path,
                line_number=trait_line,
                end_line_number=trait_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all defs in the trait
            defs = self._find_class_defs(trait_content, file_path, full_name, trait_start)
            for def_def in defs:
                trait_def.children.append(def_def.name)
                definitions.append(def_def)
            
            # Find all vals in the trait
            vals = self._find_class_vals(trait_content, file_path, full_name, trait_start)
            for val_def in vals:
                trait_def.children.append(val_def.name)
                definitions.append(val_def)
            
            # Find all vars in the trait
            vars_defs = self._find_class_vars(trait_content, file_path, full_name, trait_start)
            for var_def in vars_defs:
                trait_def.children.append(var_def.name)
                definitions.append(var_def)
            
            definitions.append(trait_def)
        
        return definitions

    def _find_case_classes(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all case classes in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

        Returns:
            List[CodeDefinition]: A list of case class definitions.
        """
        definitions = []
        
        for match in self.case_class_pattern.finditer(content):
            class_name = match.group(1)
            class_start = match.start()
            class_line = self.find_line_number(content, class_start)
            
            # Find the end of the case class (semicolon or opening brace)
            semicolon = content.find(";", class_start)
            opening_brace = content.find("{", class_start)
            
            if semicolon != -1 and (opening_brace == -1 or semicolon < opening_brace):
                # Case class without a body
                class_end = semicolon + 1
                class_content = content[class_start:class_end]
                class_end_line = class_line + class_content.count("\n")
            elif opening_brace != -1:
                # Case class with a body
                class_end = self.find_block_end(content, opening_brace, "{", "}")
                class_content = content[class_start:class_end]
                class_end_line = class_line + class_content.count("\n")
            else:
                # No semicolon or opening brace found, skip
                continue
            
            # Extract docstring
            docstring = self._extract_scala_docstring(content, class_start)
            
            # Create case class definition
            full_name = f"{package}.{class_name}" if package else class_name
            class_def = CodeDefinition(
                name=full_name,
                type="case_class",
                file_path=file_path,
                line_number=class_line,
                end_line_number=class_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # If the case class has a body, find all defs, vals, and vars
            if opening_brace != -1:
                # Find all defs in the case class
                defs = self._find_class_defs(class_content, file_path, full_name, class_start)
                for def_def in defs:
                    class_def.children.append(def_def.name)
                    definitions.append(def_def)
                
                # Find all vals in the case class
                vals = self._find_class_vals(class_content, file_path, full_name, class_start)
                for val_def in vals:
                    class_def.children.append(val_def.name)
                    definitions.append(val_def)
                
                # Find all vars in the case class
                vars_defs = self._find_class_vars(class_content, file_path, full_name, class_start)
                for var_def in vars_defs:
                    class_def.children.append(var_def.name)
                    definitions.append(var_def)
            
            definitions.append(class_def)
        
        return definitions

    def _find_case_objects(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all case objects in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

        Returns:
            List[CodeDefinition]: A list of case object definitions.
        """
        definitions = []
        
        for match in self.case_object_pattern.finditer(content):
            object_name = match.group(1)
            object_start = match.start()
            object_line = self.find_line_number(content, object_start)
            
            # Find the opening brace
            opening_brace = content.find("{", object_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the case object (matching braces)
            object_end = self.find_block_end(content, opening_brace, "{", "}")
            object_content = content[object_start:object_end]
            object_end_line = object_line + object_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_scala_docstring(content, object_start)
            
            # Create case object definition
            full_name = f"{package}.{object_name}" if package else object_name
            object_def = CodeDefinition(
                name=full_name,
                type="case_object",
                file_path=file_path,
                line_number=object_line,
                end_line_number=object_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all defs in the case object
            defs = self._find_class_defs(object_content, file_path, full_name, object_start)
            for def_def in defs:
                object_def.children.append(def_def.name)
                definitions.append(def_def)
            
            # Find all vals in the case object
            vals = self._find_class_vals(object_content, file_path, full_name, object_start)
            for val_def in vals:
                object_def.children.append(val_def.name)
                definitions.append(val_def)
            
            # Find all vars in the case object
            vars_defs = self._find_class_vars(object_content, file_path, full_name, object_start)
            for var_def in vars_defs:
                object_def.children.append(var_def.name)
                definitions.append(var_def)
            
            definitions.append(object_def)
        
        return definitions

    def _find_defs(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all top-level defs in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

        Returns:
            List[CodeDefinition]: A list of def definitions.
        """
        definitions = []
        
        for match in self.def_pattern.finditer(content):
            # Check if this def is inside a class, trait, object, etc.
            def_start = match.start()
            
            # Skip if inside a class, trait, object, etc.
            if self._is_inside_block(content, def_start):
                continue
            
            def_name = match.group(1)
            def_line = self.find_line_number(content, def_start)
            
            # Find the opening brace or equals sign
            opening_brace = content.find("{", def_start)
            equals_sign = content.find("=", def_start)
            
            if opening_brace != -1 and (equals_sign == -1 or opening_brace < equals_sign):
                # Def with a body
                def_end = self.find_block_end(content, opening_brace, "{", "}")
            elif equals_sign != -1:
                # Def with an expression
                def_end = self._find_expression_end(content, equals_sign)
            else:
                # No body or expression found, skip
                continue
            
            def_content = content[def_start:def_end]
            def_end_line = def_line + def_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_scala_docstring(content, def_start)
            
            # Create def definition
            full_name = f"{package}.{def_name}" if package else def_name
            def_def = CodeDefinition(
                name=full_name,
                type="function",
                file_path=file_path,
                line_number=def_line,
                end_line_number=def_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            definitions.append(def_def)
        
        return definitions

    def _find_vals(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all top-level vals in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

        Returns:
            List[CodeDefinition]: A list of val definitions.
        """
        definitions = []
        
        for match in self.val_pattern.finditer(content):
            # Check if this val is inside a class, trait, object, etc.
            val_start = match.start()
            
            # Skip if inside a class, trait, object, etc.
            if self._is_inside_block(content, val_start):
                continue
            
            val_name = match.group(1)
            val_line = self.find_line_number(content, val_start)
            
            # Find the equals sign
            equals_sign = content.find("=", val_start)
            if equals_sign == -1:
                continue
            
            # Find the end of the val (semicolon or newline)
            val_end = self._find_expression_end(content, equals_sign)
            val_content = content[val_start:val_end]
            val_end_line = val_line + val_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_scala_docstring(content, val_start)
            
            # Create val definition
            full_name = f"{package}.{val_name}" if package else val_name
            val_def = CodeDefinition(
                name=full_name,
                type="val",
                file_path=file_path,
                line_number=val_line,
                end_line_number=val_end_line,
                signature=val_content.strip(),
                docstring=docstring
            )
            
            definitions.append(val_def)
        
        return definitions

    def _find_vars(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all top-level vars in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

        Returns:
            List[CodeDefinition]: A list of var definitions.
        """
        definitions = []
        
        for match in self.var_pattern.finditer(content):
            # Check if this var is inside a class, trait, object, etc.
            var_start = match.start()
            
            # Skip if inside a class, trait, object, etc.
            if self._is_inside_block(content, var_start):
                continue
            
            var_name = match.group(1)
            var_line = self.find_line_number(content, var_start)
            
            # Find the equals sign
            equals_sign = content.find("=", var_start)
            if equals_sign == -1:
                continue
            
            # Find the end of the var (semicolon or newline)
            var_end = self._find_expression_end(content, equals_sign)
            var_content = content[var_start:var_end]
            var_end_line = var_line + var_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_scala_docstring(content, var_start)
            
            # Create var definition
            full_name = f"{package}.{var_name}" if package else var_name
            var_def = CodeDefinition(
                name=full_name,
                type="var",
                file_path=file_path,
                line_number=var_line,
                end_line_number=var_end_line,
                signature=var_content.strip(),
                docstring=docstring
            )
            
            definitions.append(var_def)
        
        return definitions

    def _find_types(self, content: str, file_path: str, package: Optional[str]) -> List[CodeDefinition]:
        """
        Find all type aliases in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            package: The package name.

        Returns:
            List[CodeDefinition]: A list of type alias definitions.
        """
        definitions = []
        
        for match in self.type_pattern.finditer(content):
            # Check if this type is inside a class, trait, object, etc.
            type_start = match.start()
            
            # Skip if inside a class, trait, object, etc.
            if self._is_inside_block(content, type_start):
                continue
            
            type_name = match.group(1)
            type_line = self.find_line_number(content, type_start)
            
            # Find the end of the type (semicolon or newline)
            semicolon = content.find(";", type_start)
            newline = content.find("\n", type_start)
            
            if semicolon != -1 and (newline == -1 or semicolon < newline):
                type_end = semicolon + 1
            elif newline != -1:
                type_end = newline
            else:
                type_end = len(content)
            
            type_content = content[type_start:type_end]
            type_end_line = type_line + type_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_scala_docstring(content, type_start)
            
            # Create type definition
            full_name = f"{package}.{type_name}" if package else type_name
            type_def = CodeDefinition(
                name=full_name,
                type="type",
                file_path=file_path,
                line_number=type_line,
                end_line_number=type_end_line,
                signature=type_content.strip(),
                docstring=docstring
            )
            
            definitions.append(type_def)
        
        return definitions

    def _find_class_defs(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
        """
        Find all defs in a class, trait, or object.

        Args:
            class_content: The content of the class, trait, or object.
            file_path: The path to the file.
            class_name: The name of the class, trait, or object.
            class_start: The start position of the class, trait, or object in the original content.

        Returns:
            List[CodeDefinition]: A list of def definitions.
        """
        definitions = []
        
        for match in self.def_pattern.finditer(class_content):
            def_name = match.group(1)
            def_start_in_class = match.start()
            def_start = class_start + def_start_in_class
            def_line = self.find_line_number(class_content, def_start_in_class)
            
            # Find the opening brace or equals sign
            opening_brace = class_content.find("{", def_start_in_class)
            equals_sign = class_content.find("=", def_start_in_class)
            
            if opening_brace != -1 and (equals_sign == -1 or opening_brace < equals_sign):
                # Def with a body
                def_end_in_class = self.find_block_end(class_content, opening_brace, "{", "}")
            elif equals_sign != -1:
                # Def with an expression
                def_end_in_class = self._find_expression_end(class_content, equals_sign)
            else:
                # No body or expression found, skip
                continue
            
            def_content = class_content[def_start_in_class:def_end_in_class]
            def_end_line = def_line + def_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_scala_docstring(class_content, def_start_in_class)
            
            # Create def definition
            def_def = CodeDefinition(
                name=def_name,
                type="method",
                file_path=file_path,
                line_number=def_line,
                end_line_number=def_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=class_name
            )
            
            definitions.append(def_def)
        
        return definitions

    def _find_class_vals(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
        """
        Find all vals in a class, trait, or object.

        Args:
            class_content: The content of the class, trait, or object.
            file_path: The path to the file.
            class_name: The name of the class, trait, or object.
            class_start: The start position of the class, trait, or object in the original content.

        Returns:
            List[CodeDefinition]: A list of val definitions.
        """
        definitions = []
        
        for match in self.val_pattern.finditer(class_content):
            val_name = match.group(1)
            val_start_in_class = match.start()
            val_start = class_start + val_start_in_class
            val_line = self.find_line_number(class_content, val_start_in_class)
            
            # Find the equals sign
            equals_sign = class_content.find("=", val_start_in_class)
            if equals_sign == -1:
                continue
            
            # Find the end of the val (semicolon or newline)
            val_end_in_class = self._find_expression_end(class_content, equals_sign)
            val_content = class_content[val_start_in_class:val_end_in_class]
            val_end_line = val_line + val_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_scala_docstring(class_content, val_start_in_class)
            
            # Create val definition
            val_def = CodeDefinition(
                name=val_name,
                type="val",
                file_path=file_path,
                line_number=val_line,
                end_line_number=val_end_line,
                signature=val_content.strip(),
                docstring=docstring,
                parent=class_name
            )
            
            definitions.append(val_def)
        
        return definitions

    def _find_class_vars(self, class_content: str, file_path: str, class_name: str, class_start: int) -> List[CodeDefinition]:
        """
        Find all vars in a class, trait, or object.

        Args:
            class_content: The content of the class, trait, or object.
            file_path: The path to the file.
            class_name: The name of the class, trait, or object.
            class_start: The start position of the class, trait, or object in the original content.

        Returns:
            List[CodeDefinition]: A list of var definitions.
        """
        definitions = []
        
        for match in self.var_pattern.finditer(class_content):
            var_name = match.group(1)
            var_start_in_class = match.start()
            var_start = class_start + var_start_in_class
            var_line = self.find_line_number(class_content, var_start_in_class)
            
            # Find the equals sign
            equals_sign = class_content.find("=", var_start_in_class)
            if equals_sign == -1:
                continue
            
            # Find the end of the var (semicolon or newline)
            var_end_in_class = self._find_expression_end(class_content, equals_sign)
            var_content = class_content[var_start_in_class:var_end_in_class]
            var_end_line = var_line + var_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_scala_docstring(class_content, var_start_in_class)
            
            # Create var definition
            var_def = CodeDefinition(
                name=var_name,
                type="var",
                file_path=file_path,
                line_number=var_line,
                end_line_number=var_end_line,
                signature=var_content.strip(),
                docstring=docstring,
                parent=class_name
            )
            
            definitions.append(var_def)
        
        return definitions
    
    def _is_inside_block(self, content: str, position: int) -> bool:
        """
        Check if a position is inside a block (class, trait, object, etc.).

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
    
    def _extract_scala_docstring(self, content: str, start_pos: int) -> Optional[str]:
        """
        Extract a Scala docstring (ScalaDoc or comment) before a definition.

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
        
        # Look for ScalaDoc comments before the definition
        scaladoc_match = self.scaladoc_pattern.search(content[:start_pos], re.DOTALL)
        if scaladoc_match and scaladoc_match.end() > line_start - 10:  # Allow some whitespace
            return scaladoc_match.group(1).strip()
        
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
    
    def _find_expression_end(self, content: str, equals_sign: int) -> int:
        """
        Find the end of an expression (after an equals sign).

        Args:
            content: The content of the file.
            equals_sign: The position of the equals sign.

        Returns:
            int: The position of the end of the expression.
        """
        # Skip the equals sign and any whitespace
        pos = equals_sign + 1
        while pos < len(content) and content[pos].isspace():
            pos += 1
        
        # Check if the expression is a block
        if pos < len(content) and content[pos] == "{":
            return self.find_block_end(content, pos, "{", "}")
        
        # Otherwise, find the end of the expression (semicolon or newline)
        semicolon = content.find(";", pos)
        newline = content.find("\n", pos)
        
        if semicolon != -1 and (newline == -1 or semicolon < newline):
            return semicolon + 1
        elif newline != -1:
            return newline
        else:
            return len(content)
