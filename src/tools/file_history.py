"""
Tool for retrieving Git history for files.
"""
import os
from typing import Dict, List, Optional

from ..services.git_service import GitService
from ..types.file_types import CommitInfo, FileHistory


class FileHistoryTool:
    """
    Tool for retrieving Git history for files.
    """

    def __init__(self, git_service: Optional[GitService] = None):
        """
        Initialize the FileHistoryTool.

        Args:
            git_service: The GitService to use. If None, a new instance will be created.
        """
        self._git_service = git_service or GitService()

    def execute(
        self,
        file_path: str,
        max_commits: int = 10,
        include_content_diff: bool = False
    ) -> Dict:
        """
        Retrieve Git history for a file.

        Args:
            file_path: The path to the file.
            max_commits: Maximum number of commits to retrieve.
            include_content_diff: Whether to include content diffs in the results.

        Returns:
            Dict: A dictionary containing the file history.
        """
        # Normalize the file path
        file_path = os.path.abspath(file_path)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return {
                "error": f"File '{file_path}' does not exist",
                "history": None
            }

        # Get the file history
        history = self._git_service.get_file_history(file_path, max_commits, include_content_diff)
        if not history:
            return {
                "error": f"Failed to get history for '{file_path}'",
                "history": None
            }

        return {
            "error": None,
            "history": self._format_file_history(history)
        }

    def _format_file_history(self, history: FileHistory) -> Dict:
        """
        Format FileHistory into a simpler dictionary.

        Args:
            history: The FileHistory to format.

        Returns:
            Dict: A dictionary containing the formatted file history.
        """
        return {
            "file_path": history.file_path,
            "commits": [self._format_commit_info(commit) for commit in history.commits]
        }

    def _format_commit_info(self, commit: CommitInfo) -> Dict:
        """
        Format CommitInfo into a simpler dictionary.

        Args:
            commit: The CommitInfo to format.

        Returns:
            Dict: A dictionary containing the formatted commit info.
        """
        return {
            "commit_hash": commit.commit_hash,
            "author_name": commit.author_name,
            "author_email": commit.author_email,
            "commit_date": commit.commit_date.isoformat(),
            "message": commit.message,
            "changed_files": commit.changed_files
        }
