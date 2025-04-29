"""
Rust code parser.
"""
import re
from typing import List, Match, Optional, Tuple

from ...types.file_types import CodeDefinition
from .base import BaseParser


class RustParser(BaseParser):
    """
    Parser for Rust code.
    """

    def __init__(self):
        """Initialize the Rust parser."""
        super().__init__()
        self.struct_pattern = re.compile(r"(?:pub\s+)?struct\s+(\w+)(?:<[^>]+>)?")
        self.enum_pattern = re.compile(r"(?:pub\s+)?enum\s+(\w+)(?:<[^>]+>)?")
        self.trait_pattern = re.compile(r"(?:pub\s+)?trait\s+(\w+)(?:<[^>]+>)?")
        self.impl_pattern = re.compile(r"impl(?:<[^>]+>)?\s+(?:(?:\w+::)*(\w+)(?:<[^>]+>)?|(\w+)(?:<[^>]+>)?\s+for\s+(?:\w+::)*(\w+)(?:<[^>]+>)?)")
        self.function_pattern = re.compile(r"(?:pub\s+)?fn\s+(\w+)(?:<[^>]+>)?\s*\(([^)]*)\)(?:\s*->\s*[^{]+)?")
        self.mod_pattern = re.compile(r"(?:pub\s+)?mod\s+(\w+)")
        self.const_pattern = re.compile(r"(?:pub\s+)?const\s+(\w+)\s*:\s*[^=]+=")
        self.static_pattern = re.compile(r"(?:pub\s+)?static\s+(?:mut\s+)?(\w+)\s*:\s*[^=]+=")
        self.type_pattern = re.compile(r"(?:pub\s+)?type\s+(\w+)(?:<[^>]+>)?\s*=")
        self.docstring_pattern = re.compile(r'///\s*(.*?)$|/\*\*(.*?)\*/', re.MULTILINE | re.DOTALL)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse Rust code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find all modules
        definitions.extend(self._find_modules(content, file_path))
        
        # Find all structs
        definitions.extend(self._find_structs(content, file_path))
        
        # Find all enums
        definitions.extend(self._find_enums(content, file_path))
        
        # Find all traits
        definitions.extend(self._find_traits(content, file_path))
        
        # Find all implementations
        definitions.extend(self._find_impls(content, file_path))
        
        # Find all functions (not methods)
        definitions.extend(self._find_functions(content, file_path))
        
        # Find all constants
        definitions.extend(self._find_constants(content, file_path))
        
        # Find all static variables
        definitions.extend(self._find_statics(content, file_path))
        
        # Find all type aliases
        definitions.extend(self._find_types(content, file_path))
        
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
        
        for match in self.mod_pattern.finditer(content):
            mod_name = match.group(1)
            mod_start = match.start()
            mod_line = self.find_line_number(content, mod_start)
            
            # Check if this is an inline module or a declaration
            if content.find("{", mod_start, mod_start + 100) != -1:
                # Inline module
                opening_brace = content.find("{", mod_start)
                mod_end = self.find_block_end(content, opening_brace, "{", "}")
                mod_content = content[mod_start:mod_end]
                mod_end_line = mod_line + mod_content.count("\n")
            else:
                # Module declaration (no content)
                mod_end = content.find(";", mod_start)
                if mod_end == -1:
                    mod_end = len(content)
                mod_content = content[mod_start:mod_end+1]
                mod_end_line = mod_line
            
            # Extract docstring
            docstring = self._extract_rust_docstring(content, mod_start)
            
            # Create module definition
            mod_def = CodeDefinition(
                name=mod_name,
                type="module",
                file_path=file_path,
                line_number=mod_line,
                end_line_number=mod_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            definitions.append(mod_def)
        
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
            # Rust structs can be defined in three ways:
            # 1. struct Name { ... }
            # 2. struct Name(Type1, Type2, ...);
            # 3. struct Name;
            
            # Check for opening brace (case 1)
            opening_brace = content.find("{", struct_start, struct_start + 100)
            if opening_brace != -1:
                struct_end = self.find_block_end(content, opening_brace, "{", "}")
            else:
                # Check for tuple struct (case 2) or unit struct (case 3)
                struct_end = content.find(";", struct_start)
                if struct_end == -1:
                    struct_end = len(content)
            
            struct_content = content[struct_start:struct_end]
            struct_end_line = struct_line + struct_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(content, struct_start)
            
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
            
            # Find the end of the enum
            enum_end = self.find_block_end(content, opening_brace, "{", "}")
            enum_content = content[enum_start:enum_end]
            enum_end_line = enum_line + enum_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(content, enum_start)
            
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
            
            definitions.append(enum_def)
        
        return definitions

    def _find_traits(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all traits in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

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
            
            # Find the end of the trait
            trait_end = self.find_block_end(content, opening_brace, "{", "}")
            trait_content = content[trait_start:trait_end]
            trait_end_line = trait_line + trait_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(content, trait_start)
            
            # Create trait definition
            trait_def = CodeDefinition(
                name=trait_name,
                type="trait",
                file_path=file_path,
                line_number=trait_line,
                end_line_number=trait_end_line,
                signature=match.group(0),
                docstring=docstring
            )
            
            # Find all methods in the trait
            methods = self._find_trait_methods(trait_content, file_path, trait_name, trait_start)
            for method in methods:
                trait_def.children.append(method.name)
                definitions.append(method)
            
            definitions.append(trait_def)
        
        return definitions

    def _find_impls(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all implementations in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of implementation definitions.
        """
        definitions = []
        
        for match in self.impl_pattern.finditer(content):
            # Extract the type name and trait name (if any)
            type_name = match.group(1) or match.group(3)
            trait_name = match.group(2)
            
            impl_start = match.start()
            impl_line = self.find_line_number(content, impl_start)
            
            # Find the opening brace
            opening_brace = content.find("{", impl_start)
            if opening_brace == -1:
                continue
            
            # Find the end of the implementation
            impl_end = self.find_block_end(content, opening_brace, "{", "}")
            impl_content = content[impl_start:impl_end]
            impl_end_line = impl_line + impl_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(content, impl_start)
            
            # Create implementation definition
            impl_name = f"{type_name}"
            if trait_name:
                impl_name = f"{trait_name} for {type_name}"
            
            impl_def = CodeDefinition(
                name=impl_name,
                type="implementation",
                file_path=file_path,
                line_number=impl_line,
                end_line_number=impl_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=type_name
            )
            
            # Find all methods in the implementation
            methods = self._find_impl_methods(impl_content, file_path, type_name, impl_start)
            for method in methods:
                impl_def.children.append(method.name)
                definitions.append(method)
            
            definitions.append(impl_def)
        
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
            # Check if this function is inside an impl, trait, etc.
            function_start = match.start()
            
            # Skip if inside an impl, trait, etc.
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
            docstring = self._extract_rust_docstring(content, function_start)
            
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

    def _find_trait_methods(self, trait_content: str, file_path: str, trait_name: str, trait_start: int) -> List[CodeDefinition]:
        """
        Find all methods in a trait.

        Args:
            trait_content: The content of the trait.
            file_path: The path to the file.
            trait_name: The name of the trait.
            trait_start: The start position of the trait in the original content.

        Returns:
            List[CodeDefinition]: A list of method definitions.
        """
        definitions = []
        
        for match in self.function_pattern.finditer(trait_content):
            method_name = match.group(1)
            method_start_in_trait = match.start()
            method_start = trait_start + method_start_in_trait
            method_line = self.find_line_number(trait_content, method_start_in_trait)
            
            # Find the end of the method (semicolon or block)
            opening_brace = trait_content.find("{", method_start_in_trait)
            semicolon = trait_content.find(";", method_start_in_trait)
            
            if opening_brace != -1 and (semicolon == -1 or opening_brace < semicolon):
                # Method with a body
                method_end_in_trait = self.find_block_end(trait_content, opening_brace, "{", "}")
            else:
                # Method declaration without a body
                method_end_in_trait = semicolon + 1 if semicolon != -1 else len(trait_content)
            
            method_content = trait_content[method_start_in_trait:method_end_in_trait]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(trait_content, method_start_in_trait)
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=trait_name
            )
            
            definitions.append(method_def)
        
        return definitions

    def _find_impl_methods(self, impl_content: str, file_path: str, type_name: str, impl_start: int) -> List[CodeDefinition]:
        """
        Find all methods in an implementation.

        Args:
            impl_content: The content of the implementation.
            file_path: The path to the file.
            type_name: The name of the type being implemented.
            impl_start: The start position of the implementation in the original content.

        Returns:
            List[CodeDefinition]: A list of method definitions.
        """
        definitions = []
        
        for match in self.function_pattern.finditer(impl_content):
            method_name = match.group(1)
            method_start_in_impl = match.start()
            method_start = impl_start + method_start_in_impl
            method_line = self.find_line_number(impl_content, method_start_in_impl)
            
            # Find the opening brace
            opening_brace = impl_content.find("{", method_start_in_impl)
            if opening_brace == -1:
                continue
            
            # Find the end of the method
            method_end_in_impl = self.find_block_end(impl_content, opening_brace, "{", "}")
            method_content = impl_content[method_start_in_impl:method_end_in_impl]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(impl_content, method_start_in_impl)
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=docstring,
                parent=type_name
            )
            
            definitions.append(method_def)
        
        return definitions

    def _find_constants(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all constants in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of constant definitions.
        """
        definitions = []
        
        for match in self.const_pattern.finditer(content):
            # Check if this constant is inside a block
            const_start = match.start()
            
            # Skip if inside a block
            if self._is_inside_block(content, const_start):
                continue
            
            const_name = match.group(1)
            const_line = self.find_line_number(content, const_start)
            
            # Find the end of the constant (semicolon)
            const_end = content.find(";", const_start)
            if const_end == -1:
                const_end = len(content)
            
            const_content = content[const_start:const_end+1]
            const_end_line = const_line + const_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(content, const_start)
            
            # Create constant definition
            const_def = CodeDefinition(
                name=const_name,
                type="constant",
                file_path=file_path,
                line_number=const_line,
                end_line_number=const_end_line,
                signature=const_content.strip(),
                docstring=docstring
            )
            
            definitions.append(const_def)
        
        return definitions

    def _find_statics(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all static variables in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of static variable definitions.
        """
        definitions = []
        
        for match in self.static_pattern.finditer(content):
            # Check if this static is inside a block
            static_start = match.start()
            
            # Skip if inside a block
            if self._is_inside_block(content, static_start):
                continue
            
            static_name = match.group(1)
            static_line = self.find_line_number(content, static_start)
            
            # Find the end of the static (semicolon)
            static_end = content.find(";", static_start)
            if static_end == -1:
                static_end = len(content)
            
            static_content = content[static_start:static_end+1]
            static_end_line = static_line + static_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(content, static_start)
            
            # Create static definition
            static_def = CodeDefinition(
                name=static_name,
                type="static",
                file_path=file_path,
                line_number=static_line,
                end_line_number=static_end_line,
                signature=static_content.strip(),
                docstring=docstring
            )
            
            definitions.append(static_def)
        
        return definitions

    def _find_types(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all type aliases in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of type alias definitions.
        """
        definitions = []
        
        for match in self.type_pattern.finditer(content):
            # Check if this type is inside a block
            type_start = match.start()
            
            # Skip if inside a block
            if self._is_inside_block(content, type_start):
                continue
            
            type_name = match.group(1)
            type_line = self.find_line_number(content, type_start)
            
            # Find the end of the type (semicolon)
            type_end = content.find(";", type_start)
            if type_end == -1:
                type_end = len(content)
            
            type_content = content[type_start:type_end+1]
            type_end_line = type_line + type_content.count("\n")
            
            # Extract docstring
            docstring = self._extract_rust_docstring(content, type_start)
            
            # Create type definition
            type_def = CodeDefinition(
                name=type_name,
                type="type",
                file_path=file_path,
                line_number=type_line,
                end_line_number=type_end_line,
                signature=type_content.strip(),
                docstring=docstring
            )
            
            definitions.append(type_def)
        
        return definitions

    def _is_inside_block(self, content: str, position: int) -> bool:
        """
        Check if a position is inside a block (impl, trait, etc.).

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

    def _extract_rust_docstring(self, content: str, start_pos: int) -> Optional[str]:
        """
        Extract a Rust docstring (comment) before a definition.

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
