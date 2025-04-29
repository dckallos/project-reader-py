"""
Service for file system operations with .gitignore support.
"""
import os
import mimetypes
import stat
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from ..types.file_types import DirectoryInfo, FileInfo, FileType
from .ignore_pattern import IgnorePatternService


class FileSystemService:
    """
    Service for file system operations with .gitignore support.
    """

    def __init__(self, ignore_service: Optional[IgnorePatternService] = None):
        """
        Initialize the FileSystemService.

        Args:
            ignore_service: The IgnorePatternService to use for checking ignored files.
                           If None, a new instance will be created.
        """
        self._ignore_service = ignore_service or IgnorePatternService()
        # Initialize mimetypes
        mimetypes.init()

    def is_ignored(self, path: str, base_dir: Optional[str] = None) -> bool:
        """
        Check if a file is ignored based on .gitignore patterns.

        Args:
            path: The path to check.
            base_dir: The base directory to use for relative paths.

        Returns:
            bool: True if the file is ignored, False otherwise.
        """
        return self._ignore_service.is_ignored(path, base_dir)

    def get_file_type(self, path: str) -> FileType:
        """
        Get the type of a file.

        Args:
            path: The path to check.

        Returns:
            FileType: The type of the file.
        """
        if not os.path.exists(path):
            return FileType.UNKNOWN

        if os.path.isdir(path):
            return FileType.DIRECTORY
        elif os.path.islink(path):
            return FileType.SYMLINK
        else:
            # Check if the file is binary or text
            try:
                with open(path, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\0' in chunk:  # If null bytes are found, it's likely binary
                        return FileType.BINARY
                    return FileType.TEXT
            except Exception:
                return FileType.UNKNOWN

    def get_file_info(self, path: str) -> Optional[FileInfo]:
        """
        Get information about a file.

        Args:
            path: The path to the file.

        Returns:
            Optional[FileInfo]: Information about the file, or None if the file doesn't exist.
        """
        if not os.path.exists(path) or os.path.isdir(path):
            return None

        try:
            stat_result = os.stat(path)
            name = os.path.basename(path)
            file_type = self.get_file_type(path)
            size = stat_result.st_size
            modified_time = datetime.fromtimestamp(stat_result.st_mtime)
            is_hidden = name.startswith('.') or bool(stat_result.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) if hasattr(stat_result, 'st_file_attributes') else name.startswith('.')
            extension = os.path.splitext(name)[1].lstrip('.') if '.' in name else None
            mime_type, _ = mimetypes.guess_type(path)

            return FileInfo(
                path=path,
                name=name,
                type=file_type,
                size=size,
                modified_time=modified_time,
                is_hidden=is_hidden,
                extension=extension,
                mime_type=mime_type
            )
        except Exception as e:
            print(f"Error getting file info for {path}: {e}")
            return None

    def list_files(
        self,
        directory: str,
        recursive: bool = False,
        include_hidden: bool = False,
        respect_gitignore: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        List files in a directory.

        Args:
            directory: The directory to list files from.
            recursive: Whether to list files recursively.
            include_hidden: Whether to include hidden files.
            respect_gitignore: Whether to respect .gitignore patterns.
            file_extensions: List of file extensions to include (e.g., ["py", "txt"]).

        Returns:
            List[str]: A list of file paths.
        """
        if not os.path.isdir(directory):
            return []

        # Load .gitignore files if needed
        if respect_gitignore:
            self._ignore_service.load_all_ignore_files(directory)

        result = []

        if recursive:
            for root, dirs, files in os.walk(directory):
                # Filter out ignored directories
                if respect_gitignore:
                    dirs[:] = [d for d in dirs if not self.is_ignored(os.path.join(root, d), directory)]

                # Filter out hidden directories if needed
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    file_path = os.path.join(root, file)

                    # Skip ignored files
                    if respect_gitignore and self.is_ignored(file_path, directory):
                        continue

                    # Skip hidden files if needed
                    if not include_hidden and file.startswith('.'):
                        continue

                    # Filter by extension if needed
                    if file_extensions:
                        ext = os.path.splitext(file)[1].lstrip('.')
                        if ext not in file_extensions:
                            continue

                    result.append(file_path)
        else:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)

                # Skip directories
                if os.path.isdir(item_path):
                    continue

                # Skip ignored files
                if respect_gitignore and self.is_ignored(item_path, directory):
                    continue

                # Skip hidden files if needed
                if not include_hidden and item.startswith('.'):
                    continue

                # Filter by extension if needed
                if file_extensions:
                    ext = os.path.splitext(item)[1].lstrip('.')
                    if ext not in file_extensions:
                        continue

                result.append(item_path)

        return result

    def get_directory_info(
        self,
        directory: str,
        recursive: bool = False,
        include_hidden: bool = False,
        respect_gitignore: bool = True,
        max_depth: int = -1
    ) -> Optional[DirectoryInfo]:
        """
        Get information about a directory and its contents.

        Args:
            directory: The directory to get information about.
            recursive: Whether to get information recursively.
            include_hidden: Whether to include hidden files and directories.
            respect_gitignore: Whether to respect .gitignore patterns.
            max_depth: Maximum recursion depth (-1 for unlimited).

        Returns:
            Optional[DirectoryInfo]: Information about the directory, or None if the directory doesn't exist.
        """
        if not os.path.isdir(directory):
            return None

        # Load .gitignore files if needed
        if respect_gitignore:
            self._ignore_service.load_all_ignore_files(directory)

        name = os.path.basename(directory)
        is_hidden = name.startswith('.')

        result = DirectoryInfo(
            path=directory,
            name=name,
            is_hidden=is_hidden
        )

        # If we've reached the maximum depth, don't go further
        if max_depth == 0:
            return result

        # Adjust max_depth for the next level
        next_depth = max_depth - 1 if max_depth > 0 else -1

        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)

                # Skip ignored items
                if respect_gitignore and self.is_ignored(item_path, directory):
                    continue

                # Skip hidden items if needed
                if not include_hidden and item.startswith('.'):
                    continue

                if os.path.isdir(item_path):
                    if recursive:
                        subdir_info = self.get_directory_info(
                            item_path,
                            recursive=True,
                            include_hidden=include_hidden,
                            respect_gitignore=respect_gitignore,
                            max_depth=next_depth
                        )
                        if subdir_info:
                            result.directories.append(subdir_info)
                else:
                    file_info = self.get_file_info(item_path)
                    if file_info:
                        result.files.append(file_info)
        except Exception as e:
            print(f"Error getting directory info for {directory}: {e}")

        return result

    def read_file(self, path: str) -> Optional[str]:
        """
        Read the contents of a file.

        Args:
            path: The path to the file.

        Returns:
            Optional[str]: The contents of the file, or None if the file doesn't exist or is binary.
        """
        if not os.path.isfile(path):
            return None

        file_type = self.get_file_type(path)
        if file_type == FileType.BINARY:
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with a different encoding
                with open(path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading file {path}: {e}")
                return None
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return None

    def read_binary_file(self, path: str) -> Optional[bytes]:
        """
        Read the contents of a binary file.

        Args:
            path: The path to the file.

        Returns:
            Optional[bytes]: The contents of the file, or None if the file doesn't exist.
        """
        if not os.path.isfile(path):
            return None

        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading binary file {path}: {e}")
            return None
