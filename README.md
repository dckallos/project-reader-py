# Project Reader MCP Server

A Python implementation of an MCP (Model Context Protocol) server that allows Cline to read project files while excluding any files captured in `.gitignore`.

Repository: [https://github.com/dckallos/project-reader-py](https://github.com/dckallos/project-reader-py)

## Features

- List files in a directory while respecting `.gitignore` patterns
- Read file contents
- Search for patterns across files
- Extract code definitions from files
- Get Git history for files
- Find files related to a given file
- Analyze project structure
- Calculate code metrics

## Installation

```bash
pip install -r requirements.txt
```

## MCP Integration

This project has been adapted to work as a Cline MCP server, allowing Cline to access project files while respecting `.gitignore` patterns. The MCP integration includes:

1. An `mcp.json` configuration file that defines the available tools
2. Updated server implementation that uses the MCP Python SDK
3. Configuration for the Cline MCP settings

### Setting up the MCP Server

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. The MCP server has been configured in the Cline MCP settings file at:
   `/Users/daniel/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

3. The server is configured to run with:
   - Command: `python3`
   - Arguments: `["/Users/daniel/dev/crowd/simple-trader/project-reader-py/src/main.py"]`

### Using the MCP Server with Cline

Once the MCP server is running, Cline will have access to the following tools:

- `list_files`: List files in a directory while respecting `.gitignore` patterns
- `read_file`: Read the contents of a file
- `search_files`: Search for patterns across files
- `extract_definitions`: Extract code definitions from files
- `file_history`: Get Git history for files
- `find_related`: Find files related to a given file
- `analyze_structure`: Analyze project structure
- `calculate_metrics`: Calculate code metrics

You can ask Cline to use these tools to help you navigate and understand your codebase.

## Development Usage

For development and testing, you can run the server directly:

```bash
python -m src.main
```

Enable debug logging:

```bash
python -m src.main --debug
```

## Development

### Project Structure

```
project-reader-py/
├── src/
│   ├── services/
│   │   ├── ignore_pattern.py
│   │   ├── file_system.py
│   │   ├── code_parser.py
│   │   ├── git_service.py
│   │   ├── cache_service.py
│   │   └── parsers/
│   │       ├── base.py
│   │       ├── registry.py
│   │       ├── python_parser.py
│   │       ├── javascript_parser.py
│   │       ├── typescript_parser.py
│   │       ├── java_parser.py
│   │       ├── c_parser.py
│   │       ├── go_parser.py
│   │       ├── ruby_parser.py
│   │       ├── php_parser.py
│   │       ├── rust_parser.py
│   │       ├── swift_parser.py
│   │       ├── kotlin_parser.py
│   │       └── scala_parser.py
│   ├── tools/
│   │   ├── list_files.py
│   │   ├── read_file.py
│   │   ├── search_files.py
│   │   ├── extract_definitions.py
│   │   ├── file_history.py
│   │   ├── find_related.py
│   │   ├── analyze_structure.py
│   │   └── calculate_metrics.py
│   ├── types/
│   │   └── file_types.py
│   ├── server.py
│   └── main.py
└── tests/
    ├── test_services/
    └── test_tools/
```

### Architecture

The project follows a modular architecture with clear separation of concerns:

1. **Core Data Types** (`src/types/file_types.py`):
   - Well-defined data structures like `FileInfo`, `DirectoryInfo`, `SearchResult`, `CodeDefinition`, etc.

2. **Core Services**:
   - **IgnorePatternService** (`src/services/ignore_pattern.py`): Handles `.gitignore` patterns using the `pathspec` library
   - **FileSystemService** (`src/services/file_system.py`): Provides file system operations with `.gitignore` support
   - **CacheService** (`src/services/cache_service.py`): Implements caching for performance optimization
   - **GitService** (`src/services/git_service.py`): Handles Git operations like retrieving file history
   - **CodeParserService** (`src/services/code_parser.py`): Delegates parsing to the appropriate language-specific parser

3. **Parser Architecture**:
   - **BaseParser** (`src/services/parsers/base.py`): Abstract base class defining the parser interface
   - **ParserRegistry** (`src/services/parsers/registry.py`): Registry for mapping file extensions to appropriate parsers
   - **Language-specific parsers**: Individual parsers for different languages

4. **Tools**:
   - Each tool in the `src/tools` directory provides a specific functionality
   - Tools use the services to perform their operations

5. **Server**:
   - **ProjectReaderServer** (`src/server.py`): Handles MCP requests and delegates to the appropriate tool
   - **Main** (`src/main.py`): Entry point for the server

### Running Tests

```bash
pytest
```

## Command Guide

This section provides a comprehensive guide to using the Project Reader MCP tools with Cline.

### list_files

Lists files in a directory while respecting `.gitignore` patterns.

**Parameters:**
- `directory` (required): The directory to list files from
- `recursive` (optional, default: false): Whether to list files recursively
- `include_hidden` (optional, default: false): Whether to include hidden files
- `respect_gitignore` (optional, default: true): Whether to respect .gitignore patterns
- `file_extensions` (optional): List of file extensions to include (e.g., ["py", "txt"])
- `max_depth` (optional, default: -1): Maximum recursion depth (-1 for unlimited)

**Example Cline Prompts:**
```
List all Python files in the src directory
List all JavaScript files in this project that are not in node_modules
Show me all markdown files in the docs directory
```

### read_file

Reads the contents of a file.

**Parameters:**
- `file_path` (required): The path of the file to read
- `binary` (optional, default: false): Whether to read the file as binary

**Example Cline Prompts:**
```
Show me the contents of package.json
Read the main configuration file
What's in the .gitignore file?
```

### search_files

Searches for a pattern in files.

**Parameters:**
- `directory` (optional, default: current directory): The directory to search in
- `pattern` (required): The pattern to search for
- `file_extensions` (optional): List of file extensions to include
- `recursive` (optional, default: true): Whether to search recursively
- `include_hidden` (optional, default: false): Whether to include hidden files
- `respect_gitignore` (optional, default: true): Whether to respect .gitignore patterns
- `context_lines` (optional, default: 2): Number of context lines to include
- `max_results` (optional, default: 1000): Maximum number of results to return

**Example Cline Prompts:**
```
Find all occurrences of "TODO" in the codebase
Search for "api.call" in JavaScript files
Look for deprecated function usage in the src directory
```

### extract_definitions

Extracts code definitions from files.

**Parameters:**
- `file_path` (optional): The path of the file to extract definitions from
- `directory` (optional): The directory to extract definitions from
- `recursive` (optional, default: false): Whether to extract definitions recursively
- `include_hidden` (optional, default: false): Whether to include hidden files
- `respect_gitignore` (optional, default: true): Whether to respect .gitignore patterns
- `file_extensions` (optional): List of file extensions to include

**Example Cline Prompts:**
```
Show me all function definitions in app.js
Extract all class definitions from the src directory
What are the exported functions in the utils module?
```

### file_history

Gets the Git history of a file.

**Parameters:**
- `file_path` (required): The path of the file to get history for
- `max_commits` (optional, default: 10): Maximum number of commits to return
- `include_content_diff` (optional, default: false): Whether to include content diffs

**Example Cline Prompts:**
```
Show me the commit history for package.json
What changes were made to the main configuration file in the last 10 commits?
Who last modified the authentication module?
```

### find_related

Finds files related to a given file.

**Parameters:**
- `file_path` (required): The path of the file to find related files for
- `search_directory` (optional): The directory to search in
- `max_results` (optional, default: 20): Maximum number of results to return
- `include_imports` (optional, default: true): Whether to include imports
- `include_references` (optional, default: true): Whether to include references
- `include_similar_names` (optional, default: true): Whether to include files with similar names
- `respect_gitignore` (optional, default: true): Whether to respect .gitignore patterns

**Example Cline Prompts:**
```
Find files related to auth.js
What files import the utils module?
Show me all components that use the UserContext
```

### analyze_structure

Analyzes the structure of a project.

**Parameters:**
- `directory` (optional, default: current directory): The directory to analyze
- `include_hidden` (optional, default: false): Whether to include hidden files
- `respect_gitignore` (optional, default: true): Whether to respect .gitignore patterns
- `max_depth` (optional, default: -1): Maximum recursion depth (-1 for unlimited)

**Example Cline Prompts:**
```
Analyze the structure of this project
Show me the main components of the application
What's the architecture of this codebase?
```

### calculate_metrics

Calculates metrics for a project.

**Parameters:**
- `directory` (optional, default: current directory): The directory to calculate metrics for
- `include_hidden` (optional, default: false): Whether to include hidden files
- `respect_gitignore` (optional, default: true): Whether to respect .gitignore patterns
- `file_extensions` (optional): List of file extensions to include

**Example Cline Prompts:**
```
Calculate code metrics for this project
Which files have the highest complexity?
Show me statistics about the codebase
```

## Advanced Usage Examples

### Project Exploration

```
Show me all JavaScript files in this project that are not in node_modules
Analyze the structure of my project and show me the main components
Calculate code metrics for this project and show me the most complex files
```

### Code Understanding

```
Find all functions that handle API requests in this project
Extract all class definitions from the src directory and show me their inheritance relationships
Search for all instances where we're using async/await in this codebase
```

### Code Navigation

```
Show me all files related to the authentication system in this project
Find all files that import or require the 'utils' module
Show me where the 'login' function is defined and all places where it's called
```

### Git Integration

```
Show me the commit history for the main configuration file
What files have changed the most in the last 10 commits?
Show me all changes to the authentication module in the last month
```

### Advanced Use Cases

```
Find all React components that use the useEffect hook and show me their dependencies
Analyze the project structure and identify files with too many dependencies
Find all places where we're using the deprecated API methods
```

## License

MIT
