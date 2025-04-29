"""
Tool for calculating project metrics.
"""
import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

from ..services.code_parser import CodeParserService
from ..services.file_system import FileSystemService
from ..types.file_types import ProjectMetrics


class CalculateMetricsTool:
    """
    Tool for calculating project metrics.
    """

    def __init__(
        self,
        file_system_service: Optional[FileSystemService] = None,
        code_parser_service: Optional[CodeParserService] = None
    ):
        """
        Initialize the CalculateMetricsTool.

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
        file_extensions: Optional[List[str]] = None
    ) -> Dict:
        """
        Calculate project metrics.

        Args:
            directory: The directory to analyze.
            include_hidden: Whether to include hidden files.
            respect_gitignore: Whether to respect .gitignore patterns.
            file_extensions: List of file extensions to include (e.g., ["py", "js"]).

        Returns:
            Dict: A dictionary containing the project metrics.
        """
        # Normalize the directory path
        directory = os.path.abspath(directory)

        # Check if the directory exists
        if not os.path.isdir(directory):
            return {
                "error": f"Directory '{directory}' does not exist",
                "metrics": None
            }

        # Get the list of files to analyze
        files = self._file_system_service.list_files(
            directory,
            recursive=True,
            include_hidden=include_hidden,
            respect_gitignore=respect_gitignore,
            file_extensions=file_extensions
        )

        # Calculate metrics
        metrics = self._calculate_metrics(files)

        return {
            "error": None,
            "metrics": self._format_metrics(metrics)
        }

    def _calculate_metrics(self, files: List[str]) -> ProjectMetrics:
        """
        Calculate metrics for a list of files.

        Args:
            files: The list of files to analyze.

        Returns:
            ProjectMetrics: The calculated metrics.
        """
        total_files = len(files)
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        file_types = Counter()
        language_breakdown = Counter()
        complexity_metrics = {}

        # Process each file
        for file_path in files:
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lstrip('.').lower()
            
            # Update file types
            file_types[ext] += 1
            
            # Map extension to language
            language = self._get_language_from_extension(ext)
            if language:
                language_breakdown[language] += 1
            
            # Read file content
            content = self._file_system_service.read_file(file_path)
            if not content:
                continue
            
            # Count lines
            lines = content.splitlines()
            file_total_lines = len(lines)
            file_blank_lines = sum(1 for line in lines if not line.strip())
            file_comment_lines = self._count_comment_lines(content, ext)
            file_code_lines = file_total_lines - file_blank_lines - file_comment_lines
            
            # Update totals
            total_lines += file_total_lines
            code_lines += file_code_lines
            comment_lines += file_comment_lines
            blank_lines += file_blank_lines
            
            # Calculate complexity metrics
            if ext in ('py', 'js', 'ts', 'java', 'c', 'cpp'):
                complexity = self._calculate_complexity(content, ext)
                complexity_metrics[file_path] = complexity

        # Create metrics object
        metrics = ProjectMetrics(
            total_files=total_files,
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            file_types={ext: count for ext, count in file_types.items()},
            language_breakdown={lang: count for lang, count in language_breakdown.items()},
            complexity_metrics={
                "average_complexity": sum(complexity_metrics.values()) / len(complexity_metrics) if complexity_metrics else 0,
                "max_complexity": max(complexity_metrics.values()) if complexity_metrics else 0,
                "min_complexity": min(complexity_metrics.values()) if complexity_metrics else 0,
                "file_complexities": complexity_metrics
            }
        )

        return metrics

    def _count_comment_lines(self, content: str, file_ext: str) -> int:
        """
        Count the number of comment lines in a file.

        Args:
            content: The content of the file.
            file_ext: The file extension.

        Returns:
            int: The number of comment lines.
        """
        comment_count = 0
        lines = content.splitlines()
        
        # Python, Shell
        if file_ext in ('py', 'sh'):
            for line in lines:
                if line.strip().startswith('#'):
                    comment_count += 1
            
            # Count multiline docstrings
            docstring_pattern = r'""".*?"""'
            for match in re.finditer(docstring_pattern, content, re.DOTALL):
                comment_count += content[match.start():match.end()].count('\n') + 1
        
        # JavaScript, TypeScript, Java, C, C++
        elif file_ext in ('js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'h', 'hpp'):
            # Single-line comments
            for line in lines:
                if line.strip().startswith('//'):
                    comment_count += 1
            
            # Multi-line comments
            multiline_pattern = r'/\*.*?\*/'
            for match in re.finditer(multiline_pattern, content, re.DOTALL):
                comment_count += content[match.start():match.end()].count('\n') + 1
        
        # HTML, XML
        elif file_ext in ('html', 'xml'):
            multiline_pattern = r'<!--.*?-->'
            for match in re.finditer(multiline_pattern, content, re.DOTALL):
                comment_count += content[match.start():match.end()].count('\n') + 1
        
        return comment_count

    def _calculate_complexity(self, content: str, file_ext: str) -> float:
        """
        Calculate the cyclomatic complexity of a file.

        Args:
            content: The content of the file.
            file_ext: The file extension.

        Returns:
            float: The cyclomatic complexity.
        """
        # This is a simplified implementation
        # In a real implementation, we would use a proper parser
        
        # Count decision points (if, for, while, case, etc.)
        decision_points = 0
        
        if file_ext in ('py'):
            # Count if, elif, for, while, except
            decision_points += len(re.findall(r'\bif\b|\belif\b|\bfor\b|\bwhile\b|\bexcept\b', content))
        
        elif file_ext in ('js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp'):
            # Count if, for, while, case, catch
            decision_points += len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\bcase\b|\bcatch\b', content))
            
            # Count ternary operators
            decision_points += content.count('?')
        
        # Calculate complexity (1 + decision points)
        return 1 + decision_points

    def _get_language_from_extension(self, ext: str) -> Optional[str]:
        """
        Get the programming language from a file extension.

        Args:
            ext: The file extension.

        Returns:
            Optional[str]: The programming language, or None if unknown.
        """
        extension_to_language = {
            'py': 'Python',
            'js': 'JavaScript',
            'jsx': 'JavaScript',
            'ts': 'TypeScript',
            'tsx': 'TypeScript',
            'java': 'Java',
            'c': 'C',
            'cpp': 'C++',
            'h': 'C/C++ Header',
            'hpp': 'C++ Header',
            'go': 'Go',
            'rb': 'Ruby',
            'php': 'PHP',
            'rs': 'Rust',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala',
            'html': 'HTML',
            'css': 'CSS',
            'scss': 'SCSS',
            'sass': 'Sass',
            'less': 'Less',
            'json': 'JSON',
            'xml': 'XML',
            'yaml': 'YAML',
            'yml': 'YAML',
            'md': 'Markdown',
            'sh': 'Shell',
            'bat': 'Batch',
            'ps1': 'PowerShell',
            'sql': 'SQL'
        }
        
        return extension_to_language.get(ext)

    def _format_metrics(self, metrics: ProjectMetrics) -> Dict:
        """
        Format ProjectMetrics into a simpler dictionary.

        Args:
            metrics: The ProjectMetrics to format.

        Returns:
            Dict: A dictionary containing the formatted metrics.
        """
        return {
            "total_files": metrics.total_files,
            "total_lines": metrics.total_lines,
            "code_lines": metrics.code_lines,
            "comment_lines": metrics.comment_lines,
            "blank_lines": metrics.blank_lines,
            "file_types": [
                {"extension": ext, "count": count}
                for ext, count in metrics.file_types.items()
            ],
            "language_breakdown": [
                {"language": lang, "count": count}
                for lang, count in metrics.language_breakdown.items()
            ],
            "complexity_metrics": metrics.complexity_metrics
        }
