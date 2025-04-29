# Project Reader MCP Server

A Python implementation of an MCP (Model Context Protocol) server that allows Cline to read project files while excluding any files captured in `.gitignore`.

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

## License

MIT
