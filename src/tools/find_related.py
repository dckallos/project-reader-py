"""
Tool for finding files related to a given file.
"""
import os
import re
from typing import Dict, List, Optional, Set

from ..services.code_parser import CodeParserService
from ..services.file_system import FileSystemService
from ..types.file_types import CodeDefinition


class FindRelatedTool:
    """
    Tool for finding files related to a given file.
    """

    def __init__(
        self,
        file_system_service: Optional[FileSystemService] = None,
        code_parser_service: Optional[CodeParserService] = None
    ):
        """
        Initialize the FindRelatedTool.

        Args:
            file_system_service: The FileSystemService to use. If None, a new instance will be created.
            code_parser_service: The CodeParserService to use. If None, a new instance will be created.
        """
        self._file_system_service = file_system_service or FileSystemService()
        self._code_parser_service = code_parser_service or CodeParserService()

    def execute(
        self,
        file_path: str,
        search_directory: Optional[str] = None,
        max_results: int = 20,
        include_imports: bool = True,
        include_references: bool = True,
        include_similar_names: bool = True,
        respect_gitignore: bool = True
    ) -> Dict:
        """
        Find files related to a given file.

        Args:
            file_path: The path to the file.
            search_directory: The directory to search in. If None, use the directory of the file.
            max_results: Maximum number of results to return.
            include_imports: Whether to include files imported by the given file.
            include_references: Whether to include files that reference the given file.
            include_similar_names: Whether to include files with similar names.
            respect_gitignore: Whether to respect .gitignore patterns.

        Returns:
            Dict: A dictionary containing the related files.
        """
        # Normalize the file path
        file_path = os.path.abspath(file_path)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return {
                "error": f"File '{file_path}' does not exist",
                "related_files": []
            }

        # Determine the search directory
        if not search_directory:
            search_directory = os.path.dirname(file_path)
        else:
            search_directory = os.path.abspath(search_directory)

        # Check if the search directory exists
        if not os.path.isdir(search_directory):
            return {
                "error": f"Search directory '{search_directory}' does not exist",
                "related_files": []
            }

        # Get the file content
        content = self._file_system_service.read_file(file_path)
        if not content:
            return {
                "error": f"Failed to read file '{file_path}'",
                "related_files": []
            }

        # Get the file name and extension
        file_name = os.path.basename(file_path)
        file_name_without_ext, file_ext = os.path.splitext(file_name)
        file_ext = file_ext.lstrip('.')

        related_files = set()

        # Find imports
        if include_imports:
            imports = self._find_imports(content, file_ext)
            for imp in imports:
                # Try to resolve the import to a file path
                resolved_path = self._resolve_import(imp, file_path, search_directory)
                if resolved_path and os.path.isfile(resolved_path):
                    related_files.add(resolved_path)

        # Find references
        if include_references:
            references = self._find_references(file_path, search_directory, respect_gitignore)
            related_files.update(references)

        # Find files with similar names
        if include_similar_names:
            similar_files = self._find_similar_names(file_name_without_ext, search_directory, respect_gitignore)
            related_files.update(similar_files)

        # Remove the original file from the results
        if file_path in related_files:
            related_files.remove(file_path)

        # Limit the number of results
        related_files = list(related_files)[:max_results]

        return {
            "error": None,
            "related_files": related_files
        }

    def _find_imports(self, content: str, file_ext: str) -> Set[str]:
        """
        Find imports in the file content.

        Args:
            content: The content of the file.
            file_ext: The file extension.

        Returns:
            Set[str]: A set of imported module names.
        """
        imports = set()

        # Python imports
        if file_ext == 'py':
            # import statements
            for match in re.finditer(r'import\s+([\w.]+)', content):
                imports.add(match.group(1))
            
            # from ... import statements
            for match in re.finditer(r'from\s+([\w.]+)\s+import', content):
                imports.add(match.group(1))

        # JavaScript/TypeScript imports
        elif file_ext in ('js', 'jsx', 'ts', 'tsx'):
            # import statements
            for match in re.finditer(r'import.*?from\s+[\'"]([^\'"]*)[\'"]\s*;?', content):
                imports.add(match.group(1))
            
            # require statements
            for match in re.finditer(r'require\s*\(\s*[\'"]([^\'"]*)[\'"]\s*\)', content):
                imports.add(match.group(1))

        # Java imports
        elif file_ext == 'java':
            for match in re.finditer(r'import\s+([\w.]+)(?:\.\*)?;', content):
                imports.add(match.group(1))

        # C/C++ includes
        elif file_ext in ('c', 'cpp', 'h', 'hpp'):
            for match in re.finditer(r'#include\s+[<"]([^>"]*)[>"]', content):
                imports.add(match.group(1))

        return imports

    def _resolve_import(self, import_name: str, file_path: str, search_directory: str) -> Optional[str]:
        """
        Resolve an import to a file path.

        Args:
            import_name: The import name.
            file_path: The path to the file containing the import.
            search_directory: The directory to search in.

        Returns:
            Optional[str]: The resolved file path, or None if not found.
        """
        # This is a simplified implementation
        # In a real implementation, we would handle different import styles and search paths
        
        # For Python imports
        if import_name.startswith('.'):
            # Relative import
            parts = import_name.split('.')
            current_dir = os.path.dirname(file_path)
            for _ in range(len(parts) - 1):
                current_dir = os.path.dirname(current_dir)
            
            module_path = os.path.join(current_dir, parts[-1])
            
            # Try with .py extension
            if os.path.isfile(f"{module_path}.py"):
                return f"{module_path}.py"
            
            # Try as a directory with __init__.py
            if os.path.isdir(module_path) and os.path.isfile(os.path.join(module_path, "__init__.py")):
                return os.path.join(module_path, "__init__.py")
        else:
            # Absolute import
            parts = import_name.split('.')
            
            # Try different possible paths
            for root, _, _ in os.walk(search_directory):
                # Try with .py extension
                module_path = os.path.join(root, *parts)
                if os.path.isfile(f"{module_path}.py"):
                    return f"{module_path}.py"
                
                # Try as a directory with __init__.py
                if os.path.isdir(module_path) and os.path.isfile(os.path.join(module_path, "__init__.py")):
                    return os.path.join(module_path, "__init__.py")
        
        return None

    def _find_references(self, file_path: str, search_directory: str, respect_gitignore: bool) -> Set[str]:
        """
        Find files that reference the given file.

        Args:
            file_path: The path to the file.
            search_directory: The directory to search in.
            respect_gitignore: Whether to respect .gitignore patterns.

        Returns:
            Set[str]: A set of file paths that reference the given file.
        """
        references = set()
        
        # Get the file name and module name
        file_name = os.path.basename(file_path)
        file_name_without_ext, _ = os.path.splitext(file_name)
        
        # Get the module name (last directory + file name without extension)
        dir_name = os.path.basename(os.path.dirname(file_path))
        module_name = f"{dir_name}.{file_name_without_ext}" if dir_name else file_name_without_ext
        
        # Get all files in the search directory
        files = self._file_system_service.list_files(
            search_directory,
            recursive=True,
            include_hidden=False,
            respect_gitignore=respect_gitignore
        )
        
        # Search for references in each file
        for other_file in files:
            if other_file == file_path:
                continue
            
            content = self._file_system_service.read_file(other_file)
            if not content:
                continue
            
            # Check for imports or references to the file
            if (
                re.search(rf'import\s+{file_name_without_ext}', content) or
                re.search(rf'from\s+{module_name}', content) or
                re.search(rf'require\s*\(\s*[\'"].*{file_name_without_ext}', content) or
                re.search(rf'import.*from\s+[\'"].*{file_name_without_ext}', content)
            ):
                references.add(other_file)
        
        return references

    def _find_similar_names(self, file_name_without_ext: str, search_directory: str, respect_gitignore: bool) -> Set[str]:
        """
        Find files with similar names.

        Args:
            file_name_without_ext: The file name without extension.
            search_directory: The directory to search in.
            respect_gitignore: Whether to respect .gitignore patterns.

        Returns:
            Set[str]: A set of file paths with similar names.
        """
        similar_files = set()
        
        # Get all files in the search directory
        files = self._file_system_service.list_files(
            search_directory,
            recursive=True,
            include_hidden=False,
            respect_gitignore=respect_gitignore
        )
        
        # Check for files with similar names
        for other_file in files:
            other_name = os.path.basename(other_file)
            other_name_without_ext, _ = os.path.splitext(other_name)
            
            # Check if the names are similar
            if (
                file_name_without_ext.lower() in other_name_without_ext.lower() or
                other_name_without_ext.lower() in file_name_without_ext.lower()
            ):
                similar_files.add(other_file)
        
        return similar_files
