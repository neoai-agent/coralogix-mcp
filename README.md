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

1. Run the server (for example, using the CLI):

   ```bash
   coralogix-mcp --coralogix-api-key "YOUR_CORALOGIX_API_KEY" --application-name "YOUR_APPLICATION_NAME" --openai-api-key "YOUR_OPENAI_API_KEY"
   ```

## Available Tools

The coralogix‑mcp package provides the following CLI commands (tools) for interacting with Coralogix logs:

1. **analyze‑logs** – Analyze (and summarize) log data (for example, show top 10 API endpoints with counts).  
   Example (using the CLI):
   ```bash
   coralogix-mcp analyze-logs --application-name "your-app-name"
   ```

2. **search‑logs** – Search (and filter) logs (for example, by a search string or service name).  
   Example (using the CLI):
   ```bash
   coralogix-mcp search-logs --search-string "error" --application-name "your-app-name"
   ```

3. **search‑recent‑error‑logs** – Search (and filter) recent error logs (for example, within a 2‑minute window) and return detailed error messages.  
   Example (using the CLI):
   ```bash
   coralogix-mcp search-recent-error-logs --application-name "your-app-name"
   ```

4. **get‑log‑context** – Extract (and display) log entries with context (for example, around a given search string).  
   Example (using the CLI):
   ```bash
   coralogix-mcp get-log-context --search-string "error" --application-name "your-app-name"
   ```

For more details, run (for example)  
  coralogix‑mcp --help  
or  
  coralogix‑mcp analyze‑logs --help  
(etc.).

## Development

For development setup (for example, using a virtual environment):

```bash
git clone https://github.com/yourusername/coralogix-mcp.git
cd coralogix-mcp
python -m venv venv
source venv/bin/activate  # (On Windows, use: venv\Scripts\activate)
pip install -e ".[dev]"
```

## License

MIT License – See [LICENSE](LICENSE) file for details.