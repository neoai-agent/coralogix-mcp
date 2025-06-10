# Coralogix MCP

A Monitoring and Control Panel (MCP) for Coralogix log analysis and service monitoring. This tool provides a command-line interface for querying and analyzing logs from Coralogix, with features for service name matching, error analysis, and log context extraction.

## Features

- Service name matching with LLM-powered fuzzy matching
- HTTP request analysis (2xx, 4xx, 5xx status codes)
- Critical error log analysis
- Log context extraction with customizable context lines
- Caching for improved performance
- Environment-aware logging (prod/staging)

## Installation

```bash
# Install using pipx (recommended)
# Install
pipx install git+https://github.com/yourusername/coralogix-mcp.git

# Or run without installation
pipx run git+https://github.com/yourusername/coralogix-mcp.git
```

## Configuration

Create a `.env` file in your working directory with the following variables:

```env
CORALOGIX_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
MODEL=gpt-3.5-turbo  # or your preferred model
APPLICATION_NAME=your_application_name
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/healthifyme/coralogix-mcp.git
cd coralogix-mcp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## Tools

The coralogix-mcp package provides a command-line interface (CLI) for interacting with Coralogix logs. You can use the following commands (for example, via pipx):

- **analyze-logs** – Analyze (and summarize) log data (for example, show top 10 API endpoints with counts).  
- **search-logs** – Search (and filter) logs (for example, by a search string or service name).  
- **search-recent-error-logs** – Search (and filter) recent error logs (for example, within a 2‑minute window) and return detailed error messages.  
- **get-log-context** – Extract (and display) log entries with context (for example, around a given search string).

For more details, run (for example)  
  coralogix-mcp --help  
or  
  coralogix-mcp analyze-logs --help  
(etc.). 

The server provides the following tools for coralogix log analysis:
get_2xx_logs
get_4xx_logs
get_5xx_logs
get_coralogix_logs_by_string

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team at dev@healthifyme.com.