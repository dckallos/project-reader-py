"""
Type definitions for file operations.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Union
from datetime import datetime


class FileType(Enum):
    """Enum representing different file types."""
    UNKNOWN = "unknown"
    TEXT = "text"
    BINARY = "binary"
    DIRECTORY = "directory"
    SYMLINK = "symlink"


@dataclass
class FileInfo:
    """Information about a file."""
    path: str
    name: str
    type: FileType
    size: int
    modified_time: datetime
    is_hidden: bool = False
    extension: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class DirectoryInfo:
    """Information about a directory."""
    path: str
    name: str
    files: List[FileInfo] = field(default_factory=list)
    directories: List['DirectoryInfo'] = field(default_factory=list)
    is_hidden: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Result of a search operation."""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)


@dataclass
class CodeDefinition:
    """Information about a code definition (function, class, etc.)."""
    name: str
    type: str  # "function", "class", "method", "variable", etc.
    file_path: str
    line_number: int
    end_line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent: Optional[str] = None  # For methods, the class they belong to
    children: List[str] = field(default_factory=list)  # For classes, their methods
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class CommitInfo:
    """Information about a Git commit."""
    commit_hash: str
    author_name: str
    author_email: str
    commit_date: datetime
    message: str
    changed_files: List[str] = field(default_factory=list)


@dataclass
class FileHistory:
    """History of a file."""
    file_path: str
    commits: List[CommitInfo] = field(default_factory=list)


@dataclass
class ProjectMetrics:
    """Metrics about a project."""
    total_files: int
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    file_types: Dict[str, int] = field(default_factory=dict)
    language_breakdown: Dict[str, int] = field(default_factory=dict)
    complexity_metrics: Dict[str, float] = field(default_factory=dict)
