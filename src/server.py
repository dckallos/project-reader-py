"""
MCP server implementation for project reading.
"""
import json
import os
from typing import Any, Dict, List, Optional

from .services.code_parser import CodeParserService
from .services.file_system import FileSystemService
from .services.git_service import GitService
from .tools.analyze_structure import AnalyzeStructureTool
from .tools.calculate_metrics import CalculateMetricsTool
from .tools.extract_definitions import ExtractDefinitionsTool
from .tools.file_history import FileHistoryTool
from .tools.find_related import FindRelatedTool
from .tools.list_files import ListFilesTool
from .tools.read_file import ReadFileTool
from .tools.search_files import SearchFilesTool


class ProjectReaderServer:
    """
    MCP server for project reading.
    """

    def __init__(self):
        """Initialize the ProjectReaderServer."""
        # Initialize services
        self._file_system_service = FileSystemService()
        self._code_parser_service = CodeParserService()
        self._git_service = GitService()

        # Initialize tools
        self._list_files_tool = ListFilesTool(self._file_system_service)
        self._read_file_tool = ReadFileTool(self._file_system_service)
        self._search_files_tool = SearchFilesTool(self._file_system_service)
        self._extract_definitions_tool = ExtractDefinitionsTool(self._code_parser_service)
        self._file_history_tool = FileHistoryTool(self._git_service)
        self._find_related_tool = FindRelatedTool(self._file_system_service, self._code_parser_service)
        self._analyze_structure_tool = AnalyzeStructureTool(self._file_system_service, self._code_parser_service)
        self._calculate_metrics_tool = CalculateMetricsTool(self._file_system_service, self._code_parser_service)

        # Define tools
        self._tools = {
            "list_files": self._handle_list_files,
            "read_file": self._handle_read_file,
            "search_files": self._handle_search_files,
            "extract_definitions": self._handle_extract_definitions,
            "file_history": self._handle_file_history,
            "find_related": self._handle_find_related,
            "analyze_structure": self._handle_analyze_structure,
            "calculate_metrics": self._handle_calculate_metrics
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP request.

        Args:
            request: The MCP request.

        Returns:
            Dict[str, Any]: The MCP response.
        """
        try:
            # Extract request data
            tool_name = request.get("tool")
            arguments = request.get("arguments", {})

            # Check if the tool exists
            if tool_name not in self._tools:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "result": None
                }

            # Call the tool handler
            handler = self._tools[tool_name]
            result = handler(arguments)

            return {
                "error": None,
                "result": result
            }
        except Exception as e:
            return {
                "error": f"Error handling request: {str(e)}",
                "result": None
            }

    def _handle_list_files(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a list_files request.

        Args:
            arguments: The request arguments.

        Returns:
            Dict[str, Any]: The response.
        """
        directory = arguments.get("directory", os.getcwd())
        recursive = arguments.get("recursive", False)
        include_hidden = arguments.get("include_hidden", False)
        respect_gitignore = arguments.get("respect_gitignore", True)
        file_extensions = arguments.get("file_extensions")
        max_depth = arguments.get("max_depth", -1)

        return self._list_files_tool.execute(
            directory=directory,
            recursive=recursive,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            file_extensions=file_extensions,
            max_depth=max_depth
        )

    def _handle_read_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a read_file request.

        Args:
            arguments: The request arguments.

        Returns:
            Dict[str, Any]: The response.
        """
        file_path = arguments.get("file_path")
        binary = arguments.get("binary", False)

        if not file_path:
            return {
                "error": "Missing required argument: file_path",
                "content": None,
                "binary": False,
                "file_info": None
            }

        return self._read_file_tool.execute(
            file_path=file_path,
            binary=binary
        )

    def _handle_search_files(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a search_files request.

        Args:
            arguments: The request arguments.

        Returns:
            Dict[str, Any]: The response.
        """
        directory = arguments.get("directory", os.getcwd())
        pattern = arguments.get("pattern")
        file_extensions = arguments.get("file_extensions")
        recursive = arguments.get("recursive", True)
        include_hidden = arguments.get("include_hidden", False)
        respect_gitignore = arguments.get("respect_gitignore", True)
        context_lines = arguments.get("context_lines", 2)
        max_results = arguments.get("max_results", 1000)

        if not pattern:
            return {
                "error": "Missing required argument: pattern",
                "results": []
            }

        return self._search_files_tool.execute(
            directory=directory,
            pattern=pattern,
            file_extensions=file_extensions,
            recursive=recursive,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            context_lines=context_lines,
            max_results=max_results
        )

    def _handle_extract_definitions(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an extract_definitions request.

        Args:
            arguments: The request arguments.

        Returns:
            Dict[str, Any]: The response.
        """
        file_path = arguments.get("file_path")
        directory = arguments.get("directory")
        recursive = arguments.get("recursive", False)
        include_hidden = arguments.get("include_hidden", False)
        respect_gitignore = arguments.get("respect_gitignore", True)
        file_extensions = arguments.get("file_extensions")

        if not file_path and not directory:
            return {
                "error": "Missing required argument: either file_path or directory must be provided",
                "definitions": []
            }

        return self._extract_definitions_tool.execute(
            file_path=file_path,
            directory=directory,
            recursive=recursive,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            file_extensions=file_extensions
        )

    def _handle_file_history(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a file_history request.

        Args:
            arguments: The request arguments.

        Returns:
            Dict[str, Any]: The response.
        """
        file_path = arguments.get("file_path")
        max_commits = arguments.get("max_commits", 10)
        include_content_diff = arguments.get("include_content_diff", False)

        if not file_path:
            return {
                "error": "Missing required argument: file_path",
                "history": None
            }

        return self._file_history_tool.execute(
            file_path=file_path,
            max_commits=max_commits,
            include_content_diff=include_content_diff
        )

    def _handle_find_related(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a find_related request.

        Args:
            arguments: The request arguments.

        Returns:
            Dict[str, Any]: The response.
        """
        file_path = arguments.get("file_path")
        search_directory = arguments.get("search_directory")
        max_results = arguments.get("max_results", 20)
        include_imports = arguments.get("include_imports", True)
        include_references = arguments.get("include_references", True)
        include_similar_names = arguments.get("include_similar_names", True)
        respect_gitignore = arguments.get("respect_gitignore", True)

        if not file_path:
            return {
                "error": "Missing required argument: file_path",
                "related_files": []
            }

        return self._find_related_tool.execute(
            file_path=file_path,
            search_directory=search_directory,
            max_results=max_results,
            include_imports=include_imports,
            include_references=include_references,
            include_similar_names=include_similar_names,
            respect_gitignore=respect_gitignore
        )

    def _handle_analyze_structure(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an analyze_structure request.

        Args:
            arguments: The request arguments.

        Returns:
            Dict[str, Any]: The response.
        """
        directory = arguments.get("directory", os.getcwd())
        include_hidden = arguments.get("include_hidden", False)
        respect_gitignore = arguments.get("respect_gitignore", True)
        max_depth = arguments.get("max_depth", -1)

        return self._analyze_structure_tool.execute(
            directory=directory,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            max_depth=max_depth
        )

    def _handle_calculate_metrics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a calculate_metrics request.

        Args:
            arguments: The request arguments.

        Returns:
            Dict[str, Any]: The response.
        """
        directory = arguments.get("directory", os.getcwd())
        include_hidden = arguments.get("include_hidden", False)
        respect_gitignore = arguments.get("respect_gitignore", True)
        file_extensions = arguments.get("file_extensions")

        return self._calculate_metrics_tool.execute(
            directory=directory,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            file_extensions=file_extensions
        )
