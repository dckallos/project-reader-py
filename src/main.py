#!/usr/bin/env python3
"""
Main entry point for the project reader MCP server.
"""
import argparse
import logging
import sys

from mcp.server.fastmcp.server import FastMCP

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
        # Instantiate the FastMCP server
        server = FastMCP(name="project-reader-py")

        # Create the project reader server
        project_reader = ProjectReaderServer()

        # Register each tool as a FastMCP tool
        for tool_name in project_reader._tools:
            def make_handler(tool):
                def handler(arguments):
                    # Compose a request dict as expected by ProjectReaderServer.handle_request
                    request = {"tool": tool, "arguments": arguments}
                    result = project_reader.handle_request(request)
                    # FastMCP expects just the result, not a dict with "error"/"result"
                    if result.get("error"):
                        raise Exception(result["error"])
                    return result["result"]
                return handler
            server.tool(tool_name)(make_handler(tool_name))

        logger.info("Project Reader MCP server running on stdio (FastMCP)")
        server.run(transport="stdio")

    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
