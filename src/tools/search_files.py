"""
Tool for searching files for patterns.
"""
import os
import re
from typing import Dict, List, Optional, Union

from ..services.file_system import FileSystemService
from ..types.file_types import SearchResult


class SearchFilesTool:
    """
    Tool for searching files for patterns.
    """

    def __init__(self, file_system_service: Optional[FileSystemService] = None):
        """
        Initialize the SearchFilesTool.

        Args:
            file_system_service: The FileSystemService to use. If None, a new instance will be created.
        """
        self._file_system_service = file_system_service or FileSystemService()

    def execute(
        self,
        directory: str,
        pattern: str,
        file_extensions: Optional[List[str]] = None,
        recursive: bool = True,
        include_hidden: bool = False,
        respect_gitignore: bool = True,
        context_lines: int = 2,
        max_results: int = 1000
    ) -> Dict:
        """
        Search files for a pattern.

        Args:
            directory: The directory to search in.
            pattern: The regex pattern to search for.
            file_extensions: List of file extensions to include (e.g., ["py", "txt"]).
            recursive: Whether to search recursively.
            include_hidden: Whether to include hidden files.
            respect_gitignore: Whether to respect .gitignore patterns.
            context_lines: Number of context lines to include before and after matches.
            max_results: Maximum number of results to return.

        Returns:
            Dict: A dictionary containing the search results.
        """
        # Normalize the directory path
        directory = os.path.abspath(directory)

        # Check if the directory exists
        if not os.path.isdir(directory):
            return {
                "error": f"Directory '{directory}' does not exist",
                "results": []
            }

        # Compile the regex pattern
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return {
                "error": f"Invalid regex pattern: {e}",
                "results": []
            }

        # Get the list of files to search
        files = self._file_system_service.list_files(
            directory,
            recursive=recursive,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            file_extensions=file_extensions
        )

        results = []
        result_count = 0

        # Search each file
        for file_path in files:
            # Skip binary files
            file_info = self._file_system_service.get_file_info(file_path)
            if not file_info or file_info.type != "text":
                continue

            # Read the file
            content = self._file_system_service.read_file(file_path)
            if not content:
                continue

            # Search for matches
            file_results = self._search_file(file_path, content, regex, context_lines)
            
            # Add results
            for result in file_results:
                results.append(self._format_search_result(result))
                result_count += 1
                if result_count >= max_results:
                    break
            
            if result_count >= max_results:
                break

        return {
            "error": None,
            "results": results,
            "total_results": result_count,
            "pattern": pattern
        }

    def _search_file(
        self,
        file_path: str,
        content: str,
        regex: re.Pattern,
        context_lines: int
    ) -> List[SearchResult]:
        """
        Search a file for matches.

        Args:
            file_path: The path to the file.
            content: The content of the file.
            regex: The compiled regex pattern.
            context_lines: Number of context lines to include.

        Returns:
            List[SearchResult]: A list of search results.
        """
        results = []
        lines = content.splitlines()

        for match in regex.finditer(content):
            # Get the line number and content
            line_start = content[:match.start()].count('\n')
            line_end = line_start + content[match.start():match.end()].count('\n')
            
            # If the match spans multiple lines, we'll just use the first line
            line_number = line_start + 1  # 1-based line number
            line_content = lines[line_start] if line_start < len(lines) else ""
            
            # Calculate match positions within the line
            if line_start == line_end:
                # Match is on a single line
                line_start_pos = match.start() - content[:match.start()].rfind('\n') - 1
                if line_start_pos < 0:
                    line_start_pos = match.start()
                line_end_pos = line_start_pos + (match.end() - match.start())
            else:
                # Match spans multiple lines, just highlight to the end of the first line
                line_start_pos = match.start() - content[:match.start()].rfind('\n') - 1
                if line_start_pos < 0:
                    line_start_pos = match.start()
                line_end_pos = len(line_content)
            
            # Get context lines
            context_before = []
            for i in range(max(0, line_start - context_lines), line_start):
                context_before.append(lines[i])
            
            context_after = []
            for i in range(line_start + 1, min(len(lines), line_start + context_lines + 1)):
                context_after.append(lines[i])
            
            # Create search result
            result = SearchResult(
                file_path=file_path,
                line_number=line_number,
                line_content=line_content,
                match_start=line_start_pos,
                match_end=line_end_pos,
                context_before=context_before,
                context_after=context_after
            )
            
            results.append(result)
        
        return results

    def _format_search_result(self, result: SearchResult) -> Dict:
        """
        Format SearchResult into a simpler dictionary.

        Args:
            result: The SearchResult to format.

        Returns:
            Dict: A dictionary containing the formatted search result.
        """
        return {
            "file_path": result.file_path,
            "line_number": result.line_number,
            "line_content": result.line_content,
            "match_start": result.match_start,
            "match_end": result.match_end,
            "context_before": result.context_before,
            "context_after": result.context_after
        }
