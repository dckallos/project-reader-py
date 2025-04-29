"""
Package for code parsers.
"""
from .registry import ParserRegistry
from .base import BaseParser

# Import all parsers to register them
from . import python_parser
from . import javascript_parser
from . import java_parser
from . import c_parser
from . import go_parser
from . import ruby_parser
from . import php_parser
from . import rust_parser

# Create and export the parser registry
parser_registry = ParserRegistry()

__all__ = ["parser_registry", "BaseParser"]
