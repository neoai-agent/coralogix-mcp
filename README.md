# Coralogix MCP Server

A command-line tool for monitoring and analyzing Coralogix logs using MCP (Model Control Protocol).

## Installation

Install directly from GitHub using pipx:

```bash
# Install
pipx install git+https://github.com/yourusername/coralogix-mcp.git

# Or run without installation
pipx run git+https://github.com/yourusername/coralogix-mcp.git
```

## Quick Start

Run the server with your credentials:

```bash
coralogix-mcp --coralogix-api-key "YOUR_CORALOGIX_API_KEY" \
              --application-name "YOUR_APPLICATION_NAME" \
              --openai-api-key "YOUR_OPENAI_API_KEY"
```

## Available Tools

The coralogix-mcp package provides the following CLI commands for interacting with Coralogix logs:

1. **analyze-logs** - Analyze and summarize log data (e.g., show top 10 API endpoints with counts)
   ```bash
   coralogix-mcp analyze-logs --application-name "your-app-name"
   ```

2. **search-logs** - Search and filter logs by search string or service name
   ```bash
   coralogix-mcp search-logs --search-string "error" --application-name "your-app-name"
   ```

3. **search-recent-error-logs** - Search and filter recent error logs within a 2-minute window
   ```bash
   coralogix-mcp search-recent-error-logs --application-name "your-app-name"
   ```

4. **get-log-context** - Extract and display log entries with context around a search string
   ```bash
   coralogix-mcp get-log-context --search-string "error" --application-name "your-app-name"
   ```

For more details, run:
```bash
coralogix-mcp --help
```
or
```bash
coralogix-mcp analyze-logs --help
```

## Development

For development setup using a virtual environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/coralogix-mcp.git
cd coralogix-mcp

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

## License

MIT License - See [LICENSE](LICENSE) file for details.