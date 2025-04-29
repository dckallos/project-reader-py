"""
C/C++ code parser.
"""
import re
from typing import List

from ...types.file_types import CodeDefinition
from .base import BaseParser
from .registry import ParserRegistry


class CParser(BaseParser):
    """
    Parser for C code.
    """

    def __init__(self):
        """Initialize the C parser."""
        super().__init__()
        self.function_pattern = re.compile(
            r"(?:static|extern)?\s*(?:const)?\s*(\w+)(?:\s+|\s*\*\s*)(\w+)\s*\(([^)]*)\)\s*{"
        )
        self.struct_pattern = re.compile(r"(?:typedef\s+)?struct\s+(\w*)\s*{")
        self.enum_pattern = re.compile(r"(?:typedef\s+)?enum\s+(\w*)\s*{")
        self.comment_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse C code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        definitions = []
        
        # Find all functions
        definitions.extend(self._find_functions(content, file_path))
        
        # Find all structs
        definitions.extend(self._find_structs(content, file_path))
        
        # Find all enums
        definitions.extend(self._find_enums(content, file_path))
        
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
            return_type = match.group(1)
            function_name = match.group(2)
            function_start = match.start()
            function_line = self.find_line_number(content, function_start)
            
            # Find the end of the function (matching braces)
            function_end = self.find_block_end(content, function_start)
            function_content = content[function_start:function_end]
            function_end_line = function_line + function_content.count("\n")
            
            # Extract comment
            comment = None
            comment_match = self.comment_pattern.search(content[:function_start])
            if comment_match and comment_match.end() == function_start - 1:
                comment = comment_match.group(1).strip()
            
            # Create function definition
            function_def = CodeDefinition(
                name=function_name,
                type="function",
                file_path=file_path,
                line_number=function_line,
                end_line_number=function_end_line,
                signature=match.group(0),
                docstring=comment
            )
            
            definitions.append(function_def)
        
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
            struct_name = match.group(1) or "anonymous"
            struct_start = match.start()
            struct_line = self.find_line_number(content, struct_start)
            
            # Find the end of the struct (matching braces)
            struct_end = self.find_block_end(content, struct_start)
            struct_content = content[struct_start:struct_end]
            struct_end_line = struct_line + struct_content.count("\n")
            
            # Extract comment
            comment = None
            comment_match = self.comment_pattern.search(content[:struct_start])
            if comment_match and comment_match.end() == struct_start - 1:
                comment = comment_match.group(1).strip()
            
            # Create struct definition
            struct_def = CodeDefinition(
                name=struct_name,
                type="struct",
                file_path=file_path,
                line_number=struct_line,
                end_line_number=struct_end_line,
                signature=match.group(0),
                docstring=comment
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
            enum_name = match.group(1) or "anonymous"
            enum_start = match.start()
            enum_line = self.find_line_number(content, enum_start)
            
            # Find the end of the enum (matching braces)
            enum_end = self.find_block_end(content, enum_start)
            enum_content = content[enum_start:enum_end]
            enum_end_line = enum_line + enum_content.count("\n")
            
            # Extract comment
            comment = None
            comment_match = self.comment_pattern.search(content[:enum_start])
            if comment_match and comment_match.end() == enum_start - 1:
                comment = comment_match.group(1).strip()
            
            # Create enum definition
            enum_def = CodeDefinition(
                name=enum_name,
                type="enum",
                file_path=file_path,
                line_number=enum_line,
                end_line_number=enum_end_line,
                signature=match.group(0),
                docstring=comment
            )
            
            definitions.append(enum_def)
        
        return definitions


class CppParser(CParser):
    """
    Parser for C++ code.
    """

    def __init__(self):
        """Initialize the C++ parser."""
        super().__init__()
        self.class_pattern = re.compile(r"(?:class|struct)\s+(\w+)(?:\s*:\s*(?:public|protected|private)\s+(\w+))?\s*{")
        self.method_pattern = re.compile(
            r"(?:virtual|static|inline)?\s*(?:const)?\s*(\w+)(?:\s+|\s*\*\s*)(\w+)::\s*(\w+)\s*\(([^)]*)\)(?:\s+const)?\s*{"
        )
        self.namespace_pattern = re.compile(r"namespace\s+(\w+)\s*{")

    def parse(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Parse C++ code and extract definitions.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of code definitions.
        """
        # Get C definitions first
        definitions = super().parse(content, file_path)
        
        # Add C++-specific definitions
        definitions.extend(self._find_classes(content, file_path))
        definitions.extend(self._find_namespaces(content, file_path))
        
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
            
            # Extract comment
            comment = None
            comment_match = self.comment_pattern.search(content[:class_start])
            if comment_match and comment_match.end() == class_start - 1:
                comment = comment_match.group(1).strip()
            
            # Create class definition
            class_def = CodeDefinition(
                name=class_name,
                type="class",
                file_path=file_path,
                line_number=class_line,
                end_line_number=class_end_line,
                signature=match.group(0),
                docstring=comment
            )
            
            # Find all methods in the class
            methods = self._find_methods(content, file_path, class_name)
            for method in methods:
                class_def.children.append(method.name)
                definitions.append(method)
            
            definitions.append(class_def)
        
        return definitions

    def _find_methods(self, content: str, file_path: str, class_name: str) -> List[CodeDefinition]:
        """
        Find all methods for a class in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.
            class_name: The name of the class.

        Returns:
            List[CodeDefinition]: A list of method definitions.
        """
        definitions = []
        
        # Create a pattern for methods of this class
        class_method_pattern = re.compile(
            r"(?:virtual|static|inline)?\s*(?:const)?\s*(\w+)(?:\s+|\s*\*\s*)" + 
            re.escape(class_name) + r"::\s*(\w+)\s*\(([^)]*)\)(?:\s+const)?\s*{"
        )
        
        for match in class_method_pattern.finditer(content):
            return_type = match.group(1)
            method_name = match.group(2)
            method_start = match.start()
            method_line = self.find_line_number(content, method_start)
            
            # Find the end of the method (matching braces)
            method_end = self.find_block_end(content, method_start)
            method_content = content[method_start:method_end]
            method_end_line = method_line + method_content.count("\n")
            
            # Extract comment
            comment = None
            comment_match = self.comment_pattern.search(content[:method_start])
            if comment_match and comment_match.end() == method_start - 1:
                comment = comment_match.group(1).strip()
            
            # Create method definition
            method_def = CodeDefinition(
                name=method_name,
                type="method",
                file_path=file_path,
                line_number=method_line,
                end_line_number=method_end_line,
                signature=match.group(0),
                docstring=comment,
                parent=class_name
            )
            
            definitions.append(method_def)
        
        return definitions

    def _find_namespaces(self, content: str, file_path: str) -> List[CodeDefinition]:
        """
        Find all namespaces in the content.

        Args:
            content: The content of the file.
            file_path: The path to the file.

        Returns:
            List[CodeDefinition]: A list of namespace definitions.
        """
        definitions = []
        
        for match in self.namespace_pattern.finditer(content):
            namespace_name = match.group(1)
            namespace_start = match.start()
            namespace_line = self.find_line_number(content, namespace_start)
            
            # Find the end of the namespace (matching braces)
            namespace_end = self.find_block_end(content, namespace_start)
            namespace_content = content[namespace_start:namespace_end]
            namespace_end_line = namespace_line + namespace_content.count("\n")
            
            # Extract comment
            comment = None
            comment_match = self.comment_pattern.search(content[:namespace_start])
            if comment_match and comment_match.end() == namespace_start - 1:
                comment = comment_match.group(1).strip()
            
            # Create namespace definition
            namespace_def = CodeDefinition(
                name=namespace_name,
                type="namespace",
                file_path=file_path,
                line_number=namespace_line,
                end_line_number=namespace_end_line,
                signature=match.group(0),
                docstring=comment
            )
            
            definitions.append(namespace_def)
        
        return definitions


# Register the parsers
parser_registry = ParserRegistry()
parser_registry.register(["c", "h"], CParser)
parser_registry.register(["cpp", "hpp", "cc", "cxx"], CppParser)
