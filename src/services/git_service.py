"""
Service for Git operations.
"""
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import git

from ..types.file_types import CommitInfo, FileHistory


class GitService:
    """
    Service for Git operations.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the GitService.

        Args:
            repo_path: The path to the Git repository. If None, the current directory is used.
        """
        self._repo_path = repo_path or os.getcwd()
        self._repo = None
        self._initialize_repo()

    def _initialize_repo(self) -> None:
        """Initialize the Git repository."""
        try:
            self._repo = git.Repo(self._repo_path)
        except git.InvalidGitRepositoryError:
            print(f"Warning: {self._repo_path} is not a valid Git repository.")
            self._repo = None
        except Exception as e:
            print(f"Error initializing Git repository: {e}")
            self._repo = None

    def is_git_repo(self) -> bool:
        """
        Check if the current directory is a Git repository.

        Returns:
            bool: True if the current directory is a Git repository, False otherwise.
        """
        return self._repo is not None

    def get_repo_root(self) -> Optional[str]:
        """
        Get the root directory of the Git repository.

        Returns:
            Optional[str]: The root directory of the Git repository, or None if not a Git repository.
        """
        if not self._repo:
            return None
        return self._repo.git.rev_parse("--show-toplevel")

    def get_file_history(self, file_path: str, max_commits: int = 10) -> Optional[FileHistory]:
        """
        Get the history of a file.

        Args:
            file_path: The path to the file.
            max_commits: The maximum number of commits to retrieve.

        Returns:
            Optional[FileHistory]: The history of the file, or None if not a Git repository or the file doesn't exist.
        """
        if not self._repo or not os.path.isfile(file_path):
            return None

        try:
            # Get the relative path to the file from the repository root
            repo_root = self.get_repo_root()
            if not repo_root:
                return None

            rel_path = os.path.relpath(os.path.abspath(file_path), repo_root)

            # Get the commit history for the file
            commits = []
            for commit in self._repo.iter_commits(paths=rel_path, max_count=max_commits):
                commit_info = CommitInfo(
                    commit_hash=commit.hexsha,
                    author_name=commit.author.name,
                    author_email=commit.author.email,
                    commit_date=datetime.fromtimestamp(commit.committed_date),
                    message=commit.message.strip(),
                    changed_files=list(commit.stats.files.keys())
                )
                commits.append(commit_info)

            return FileHistory(file_path=file_path, commits=commits)
        except Exception as e:
            print(f"Error getting file history for {file_path}: {e}")
            return None

    def get_file_blame(self, file_path: str) -> Optional[Dict[int, Dict[str, str]]]:
        """
        Get blame information for a file.

        Args:
            file_path: The path to the file.

        Returns:
            Optional[Dict[int, Dict[str, str]]]: A dictionary mapping line numbers to blame information,
                                               or None if not a Git repository or the file doesn't exist.
        """
        if not self._repo or not os.path.isfile(file_path):
            return None

        try:
            # Get the relative path to the file from the repository root
            repo_root = self.get_repo_root()
            if not repo_root:
                return None

            rel_path = os.path.relpath(os.path.abspath(file_path), repo_root)

            # Get the blame information for the file
            blame = self._repo.git.blame(rel_path, '--line-porcelain').split('\n')
            
            result = {}
            current_commit = None
            current_line_num = None
            
            for line in blame:
                if line.startswith('\t'):
                    # This is the content of the line
                    if current_commit and current_line_num:
                        result[current_line_num]['content'] = line[1:]
                elif line.startswith('author '):
                    if current_commit and current_line_num:
                        result[current_line_num]['author'] = line[7:]
                elif line.startswith('author-mail '):
                    if current_commit and current_line_num:
                        result[current_line_num]['author_mail'] = line[12:]
                elif line.startswith('author-time '):
                    if current_commit and current_line_num:
                        timestamp = int(line[12:])
                        result[current_line_num]['author_time'] = datetime.fromtimestamp(timestamp).isoformat()
                elif line.startswith('summary '):
                    if current_commit and current_line_num:
                        result[current_line_num]['summary'] = line[8:]
                else:
                    # This might be a new commit line
                    match = re.match(r'^([0-9a-f]{40}) (\d+) (\d+)( \d+)?$', line)
                    if match:
                        current_commit = match.group(1)
                        current_line_num = int(match.group(3))
                        result[current_line_num] = {'commit': current_commit}

            return result
        except Exception as e:
            print(f"Error getting file blame for {file_path}: {e}")
            return None

    def get_file_diff(self, file_path: str, commit_hash: Optional[str] = None) -> Optional[str]:
        """
        Get the diff for a file.

        Args:
            file_path: The path to the file.
            commit_hash: The commit hash to compare against. If None, compare against the previous commit.

        Returns:
            Optional[str]: The diff for the file, or None if not a Git repository or the file doesn't exist.
        """
        if not self._repo or not os.path.isfile(file_path):
            return None

        try:
            # Get the relative path to the file from the repository root
            repo_root = self.get_repo_root()
            if not repo_root:
                return None

            rel_path = os.path.relpath(os.path.abspath(file_path), repo_root)

            # Get the diff for the file
            if commit_hash:
                return self._repo.git.diff(commit_hash, rel_path)
            else:
                return self._repo.git.diff('HEAD^', 'HEAD', '--', rel_path)
        except Exception as e:
            print(f"Error getting file diff for {file_path}: {e}")
            return None

    def get_file_contributors(self, file_path: str) -> Optional[List[Dict[str, str]]]:
        """
        Get the contributors to a file.

        Args:
            file_path: The path to the file.

        Returns:
            Optional[List[Dict[str, str]]]: A list of contributors to the file,
                                          or None if not a Git repository or the file doesn't exist.
        """
        if not self._repo or not os.path.isfile(file_path):
            return None

        try:
            # Get the relative path to the file from the repository root
            repo_root = self.get_repo_root()
            if not repo_root:
                return None

            rel_path = os.path.relpath(os.path.abspath(file_path), repo_root)

            # Get the contributors to the file
            shortlog = self._repo.git.shortlog('-sne', '--', rel_path)
            contributors = []
            
            for line in shortlog.split('\n'):
                if not line.strip():
                    continue
                
                match = re.match(r'^\s*(\d+)\s+(.+?)\s+<(.+?)>$', line)
                if match:
                    commits = int(match.group(1))
                    name = match.group(2)
                    email = match.group(3)
                    contributors.append({
                        'name': name,
                        'email': email,
                        'commits': commits
                    })
            
            return contributors
        except Exception as e:
            print(f"Error getting file contributors for {file_path}: {e}")
            return None

    def get_file_creation_date(self, file_path: str) -> Optional[datetime]:
        """
        Get the creation date of a file.

        Args:
            file_path: The path to the file.

        Returns:
            Optional[datetime]: The creation date of the file,
                              or None if not a Git repository or the file doesn't exist.
        """
        if not self._repo or not os.path.isfile(file_path):
            return None

        try:
            # Get the relative path to the file from the repository root
            repo_root = self.get_repo_root()
            if not repo_root:
                return None

            rel_path = os.path.relpath(os.path.abspath(file_path), repo_root)

            # Get the creation date of the file
            log = self._repo.git.log('--follow', '--format=%at', '--', rel_path).split('\n')
            if log and log[-1].strip():
                timestamp = int(log[-1].strip())
                return datetime.fromtimestamp(timestamp)
            return None
        except Exception as e:
            print(f"Error getting file creation date for {file_path}: {e}")
            return None
