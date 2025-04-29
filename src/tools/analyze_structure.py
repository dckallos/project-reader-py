"""
Tool for analyzing project structure.
"""
import os
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

from ..services.code_parser import CodeParserService
from ..services.file_system import FileSystemService


class AnalyzeStructureTool:
    """
    Tool for analyzing project structure.
    """

    def __init__(
        self,
        file_system_service: Optional[FileSystemService] = None,
        code_parser_service: Optional[CodeParserService] = None
    ):
        """
        Initialize the AnalyzeStructureTool.

        Args:
            file_system_service: The FileSystemService to use. If None, a new instance will be created.
            code_parser_service: The CodeParserService to use. If None, a new instance will be created.
        """
        self._file_system_service = file_system_service or FileSystemService()
        self._code_parser_service = code_parser_service or CodeParserService()

    def execute(
        self,
        directory: str,
        include_hidden: bool = False,
        respect_gitignore: bool = True,
        max_depth: int = -1
    ) -> Dict:
        """
        Analyze project structure.

        Args:
            directory: The directory to analyze.
            include_hidden: Whether to include hidden files and directories.
            respect_gitignore: Whether to respect .gitignore patterns.
            max_depth: Maximum recursion depth (-1 for unlimited).

        Returns:
            Dict: A dictionary containing the analysis results.
        """
        # Normalize the directory path
        directory = os.path.abspath(directory)

        # Check if the directory exists
        if not os.path.isdir(directory):
            return {
                "error": f"Directory '{directory}' does not exist",
                "structure": None
            }

        # Get directory info
        dir_info = self._file_system_service.get_directory_info(
            directory,
            recursive=True,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            max_depth=max_depth
        )

        if not dir_info:
            return {
                "error": f"Failed to get directory info for '{directory}'",
                "structure": None
            }

        # Analyze the structure
        structure = self._analyze_structure(dir_info)

        return {
            "error": None,
            "structure": structure
        }

    def _analyze_structure(self, dir_info) -> Dict:
        """
        Analyze the structure of a directory.

        Args:
            dir_info: The DirectoryInfo to analyze.

        Returns:
            Dict: A dictionary containing the analysis results.
        """
        # Count files by extension
        extensions = Counter()
        
        # Count files by type
        file_types = Counter()
        
        # Count files by directory
        files_by_directory = defaultdict(int)
        
        # Track directories
        directories = set()
        
        # Collect all files
        all_files = []
        
        # Process the directory tree
        self._process_directory(
            dir_info,
            extensions,
            file_types,
            files_by_directory,
            directories,
            all_files
        )
        
        # Calculate directory depth
        max_depth = 0
        for directory in directories:
            depth = directory.count(os.path.sep)
            max_depth = max(max_depth, depth)
        
        # Calculate average files per directory
        avg_files_per_directory = len(all_files) / len(directories) if directories else 0
        
        # Find the largest and smallest directories
        largest_directory = max(files_by_directory.items(), key=lambda x: x[1]) if files_by_directory else (None, 0)
        smallest_directory = min(files_by_directory.items(), key=lambda x: x[1]) if files_by_directory else (None, 0)
        
        # Find the most common file extensions
        most_common_extensions = extensions.most_common(10)
        
        # Find the most common file types
        most_common_types = file_types.most_common(10)
        
        # Create the result
        result = {
            "total_files": len(all_files),
            "total_directories": len(directories),
            "max_directory_depth": max_depth,
            "avg_files_per_directory": avg_files_per_directory,
            "largest_directory": {
                "path": largest_directory[0],
                "file_count": largest_directory[1]
            } if largest_directory[0] else None,
            "smallest_directory": {
                "path": smallest_directory[0],
                "file_count": smallest_directory[1]
            } if smallest_directory[0] else None,
            "file_extensions": [
                {"extension": ext, "count": count}
                for ext, count in most_common_extensions
            ],
            "file_types": [
                {"type": type_, "count": count}
                for type_, count in most_common_types
            ],
            "directory_structure": self._format_directory_structure(dir_info)
        }
        
        return result

    def _process_directory(
        self,
        dir_info,
        extensions: Counter,
        file_types: Counter,
        files_by_directory: Dict[str, int],
        directories: Set[str],
        all_files: List[str]
    ) -> None:
        """
        Process a directory and update the counters.

        Args:
            dir_info: The DirectoryInfo to process.
            extensions: Counter for file extensions.
            file_types: Counter for file types.
            files_by_directory: Dictionary mapping directories to file counts.
            directories: Set of directories.
            all_files: List of all files.
        """
        # Add the directory
        directories.add(dir_info.path)
        
        # Process files
        for file_info in dir_info.files:
            # Update counters
            if file_info.extension:
                extensions[file_info.extension] += 1
            
            file_types[file_info.type.value] += 1
            
            # Update files by directory
            files_by_directory[dir_info.path] += 1
            
            # Add to all files
            all_files.append(file_info.path)
        
        # Process subdirectories
        for subdir_info in dir_info.directories:
            self._process_directory(
                subdir_info,
                extensions,
                file_types,
                files_by_directory,
                directories,
                all_files
            )

    def _format_directory_structure(self, dir_info) -> Dict:
        """
        Format the directory structure.

        Args:
            dir_info: The DirectoryInfo to format.

        Returns:
            Dict: A dictionary representing the directory structure.
        """
        result = {
            "name": dir_info.name,
            "path": dir_info.path,
            "is_hidden": dir_info.is_hidden,
            "file_count": len(dir_info.files),
            "directory_count": len(dir_info.directories),
            "files": [
                {
                    "name": file_info.name,
                    "extension": file_info.extension,
                    "size": file_info.size,
                    "type": file_info.type.value
                }
                for file_info in dir_info.files
            ],
            "directories": [
                self._format_directory_structure(subdir_info)
                for subdir_info in dir_info.directories
            ]
        }
        
        return result
