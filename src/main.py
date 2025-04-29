#!/usr/bin/env python3
"""
Main entry point for the project reader MCP server.
"""
import argparse
import json
import logging
import os
import sys

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import ErrorCode, McpError

from .server import ProjectReaderServer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("project-reader")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Project Reader MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        # Create the MCP server
        server = Server(
            {
                "name": "project-reader-py",
                "version": "1.0.0",
            },
            {
                "capabilities": {
                    "resources": {},
                    "tools": {},
                },
            }
        )

        # Create the project reader server
        project_reader = ProjectReaderServer()

        # Set up tool handlers
        def list_tools_handler(_):
            return {
                "tools": [
                    {
                        "name": "list_files",
                        "description": "List files in a directory while respecting .gitignore patterns",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "directory": {
                                    "type": "string",
                                    "description": "The directory to list files from"
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "description": "Whether to list files recursively",
                                    "default": False
                                },
                                "include_hidden": {
                                    "type": "boolean",
                                    "description": "Whether to include hidden files",
                                    "default": False
                                },
                                "respect_gitignore": {
                                    "type": "boolean",
                                    "description": "Whether to respect .gitignore patterns",
                                    "default": True
                                },
                                "file_extensions": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "List of file extensions to include (e.g., [\"py\", \"txt\"])"
                                },
                                "max_depth": {
                                    "type": "integer",
                                    "description": "Maximum recursion depth (-1 for unlimited)",
                                    "default": -1
                                }
                            },
                            "required": ["directory"]
                        }
                    },
                    {
                        "name": "read_file",
                        "description": "Read the contents of a file",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path of the file to read"
                                },
                                "binary": {
                                    "type": "boolean",
                                    "description": "Whether to read the file as binary",
                                    "default": False
                                }
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "search_files",
                        "description": "Search for a pattern in files",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "directory": {
                                    "type": "string",
                                    "description": "The directory to search in"
                                },
                                "pattern": {
                                    "type": "string",
                                    "description": "The pattern to search for"
                                },
                                "file_extensions": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "List of file extensions to include"
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "description": "Whether to search recursively",
                                    "default": True
                                },
                                "include_hidden": {
                                    "type": "boolean",
                                    "description": "Whether to include hidden files",
                                    "default": False
                                },
                                "respect_gitignore": {
                                    "type": "boolean",
                                    "description": "Whether to respect .gitignore patterns",
                                    "default": True
                                },
                                "context_lines": {
                                    "type": "integer",
                                    "description": "Number of context lines to include",
                                    "default": 2
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return",
                                    "default": 1000
                                }
                            },
                            "required": ["pattern"]
                        }
                    },
                    {
                        "name": "extract_definitions",
                        "description": "Extract code definitions from files",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path of the file to extract definitions from"
                                },
                                "directory": {
                                    "type": "string",
                                    "description": "The directory to extract definitions from"
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "description": "Whether to extract definitions recursively",
                                    "default": False
                                },
                                "include_hidden": {
                                    "type": "boolean",
                                    "description": "Whether to include hidden files",
                                    "default": False
                                },
                                "respect_gitignore": {
                                    "type": "boolean",
                                    "description": "Whether to respect .gitignore patterns",
                                    "default": True
                                },
                                "file_extensions": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "List of file extensions to include"
                                }
                            }
                        }
                    },
                    {
                        "name": "file_history",
                        "description": "Get the Git history of a file",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path of the file to get history for"
                                },
                                "max_commits": {
                                    "type": "integer",
                                    "description": "Maximum number of commits to return",
                                    "default": 10
                                },
                                "include_content_diff": {
                                    "type": "boolean",
                                    "description": "Whether to include content diffs",
                                    "default": False
                                }
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "find_related",
                        "description": "Find files related to a given file",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path of the file to find related files for"
                                },
                                "search_directory": {
                                    "type": "string",
                                    "description": "The directory to search in"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return",
                                    "default": 20
                                },
                                "include_imports": {
                                    "type": "boolean",
                                    "description": "Whether to include imports",
                                    "default": True
                                },
                                "include_references": {
                                    "type": "boolean",
                                    "description": "Whether to include references",
                                    "default": True
                                },
                                "include_similar_names": {
                                    "type": "boolean",
                                    "description": "Whether to include files with similar names",
                                    "default": True
                                },
                                "respect_gitignore": {
                                    "type": "boolean",
                                    "description": "Whether to respect .gitignore patterns",
                                    "default": True
                                }
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "analyze_structure",
                        "description": "Analyze the structure of a project",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "directory": {
                                    "type": "string",
                                    "description": "The directory to analyze"
                                },
                                "include_hidden": {
                                    "type": "boolean",
                                    "description": "Whether to include hidden files",
                                    "default": False
                                },
                                "respect_gitignore": {
                                    "type": "boolean",
                                    "description": "Whether to respect .gitignore patterns",
                                    "default": True
                                },
                                "max_depth": {
                                    "type": "integer",
                                    "description": "Maximum recursion depth (-1 for unlimited)",
                                    "default": -1
                                }
                            }
                        }
                    },
                    {
                        "name": "calculate_metrics",
                        "description": "Calculate metrics for a project",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "directory": {
                                    "type": "string",
                                    "description": "The directory to calculate metrics for"
                                },
                                "include_hidden": {
                                    "type": "boolean",
                                    "description": "Whether to include hidden files",
                                    "default": False
                                },
                                "respect_gitignore": {
                                    "type": "boolean",
                                    "description": "Whether to respect .gitignore patterns",
                                    "default": True
                                },
                                "file_extensions": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "List of file extensions to include"
                                }
                            }
                        }
                    }
                ]
            }
        
        server.set_request_handler("list_tools", list_tools_handler)

        # Set up call tool handler
        def call_tool_handler(request):
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            if tool_name not in project_reader._tools:
                raise McpError(
                    ErrorCode.METHOD_NOT_FOUND,
                    f"Unknown tool: {tool_name}"
                )
            
            handler = project_reader._tools[tool_name]
            result = handler(arguments)
            
            # Format the result for MCP response
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        server.set_request_handler("call_tool", call_tool_handler)

        # Set up error handler
        server.on_error = lambda error: logger.error(f"MCP Error: {error}")

        # Connect to the transport
        transport = StdioServerTransport()
        server.connect(transport)
        
        logger.info("Project Reader MCP server running on stdio")
        
        # Keep the server running
        try:
            server.wait_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
