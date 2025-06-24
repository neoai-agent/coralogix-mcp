# Coralogix MCP Server

A command-line tool for monitoring and analyzing Coralogix logs using MCP (Model Control Protocol).

## Installation

Install directly from GitHub using pipx:

```bash
# Install
pipx install git+https://github.com/neoai-agent/coralogix-mcp.git

# Or run without installation
pipx run git+https://github.com/neoai-agent/coralogix-mcp.git
```

## Quick Start

Run the server with your credentials:

```bash
coralogix-mcp --coralogix-api-key "YOUR_CORALOGIX_API_KEY" \
              --application-name "YOUR_APPLICATION_NAME" \
              --openai-api-key "YOUR_OPENAI_API_KEY"
```

## Available Tools

The coralogix-mcp package provides the following MCP tools for interacting with Coralogix logs:

1. **get_2xx_logs** - Analyze 2XX success logs from Coralogix with API endpoint statistics
   - Returns API analysis showing top endpoints with request counts
   - Optional `service_name` parameter to filter by specific service

2. **get_4xx_logs** - Analyze 4XX client error logs from Coralogix
   - Returns API analysis with endpoint statistics
   - Includes recent error details from the last 2 minutes
   - Shows total error count
   - Optional `service_name` parameter to filter by specific service

3. **get_5xx_logs** - Analyze 5XX server error logs from Coralogix
   - Returns API analysis with endpoint statistics
   - Includes recent error details from the last 2 minutes
   - Shows total error count
   - Optional `service_name` parameter to filter by specific service

4. **get_coralogix_logs_by_string** - Search logs for a specific string and return context around matches
   - Required `search_string` parameter to search for
   - Optional `service_name` parameter to filter by specific service
   - Optional `context_lines` parameter (default: 100) to specify context around matches
   - Returns log entries with surrounding context for better debugging

All tools automatically handle:
- Service name matching and validation
- Time range filtering (default: last 15 minutes)
- Error handling and logging
- JSON response formatting

For more details, run:
```bash
coralogix-mcp --help
```

## Development

For development setup using a virtual environment:

```bash
# Clone the repository
git clone https://github.com/neoai-agent/coralogix-mcp.git
cd coralogix-mcp

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

## License

MIT License - See [LICENSE](LICENSE) file for details.
