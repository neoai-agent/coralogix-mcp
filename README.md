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
pipx install coralogix-mcp

# Or install using pip
pip install coralogix-mcp
```

## Configuration

Create a `.env` file in your working directory with the following variables:

```env
CORALOGIX_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
MODEL=gpt-3.5-turbo  # or your preferred model
APPLICATION_NAME=your_application_name
```

## Usage

### Basic Usage

```bash
# Search for recent errors in a service
coralogix-mcp search-errors --service my-service

# Get HTTP request analysis
coralogix-mcp analyze-http --service my-service --type 4xx

# Search logs with custom query
coralogix-mcp search --query "error in payment service"

# Get log context around a specific string
coralogix-mcp context --service my-service --search "payment failed"
```

### Command Reference

```bash
# Search for recent errors
coralogix-mcp search-errors [--service SERVICE] [--environment {prod,staging}]

# Analyze HTTP requests
coralogix-mcp analyze-http --service SERVICE --type {2xx,4xx,5xx,critical}

# Search logs
coralogix-mcp search --query QUERY [--service SERVICE]

# Get log context
coralogix-mcp context --service SERVICE --search SEARCH_STRING [--lines LINES]

# List available services
coralogix-mcp list-services
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