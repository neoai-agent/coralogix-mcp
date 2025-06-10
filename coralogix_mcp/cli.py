"""CLI for RDS MCP server."""
import os
import anyio
import argparse
import logging
from dotenv import load_dotenv
from coralogix_mcp.server import CoralogixMCPServer

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger('coralogix_mcp')

async def perform_async_initialization(server_obj: CoralogixMCPServer) -> None:
    """Initialize AWS clients asynchronously."""
    try:
        # AWS clients are now initialized by AWSClientManager in the constructor
        # No need for explicit initialization
        pass
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")
        return 1

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Coralogix MCP Server")
    parser.add_argument("--host", default="localhost", type=str, help="Custom host for the server")
    parser.add_argument("--port", default=8000, type=int, help="Custom port for the server")
    parser.add_argument("--model", default="openai/gpt-4o-mini", type=str, help="OpenAI model to use")
    parser.add_argument("--openai-api-key", type=str, required=True, help="OpenAI API key")
    parser.add_argument("--coralogix-api-key", type=str, required=True, help="Coralogix API key")
    parser.add_argument("--application-name", type=str, required=True, help="Application name")

    args = parser.parse_args()

    if not args.openai_api_key or not args.coralogix_api_key or not args.application_name:
        logger.error("OpenAI API key, Coralogix API key, and application name are required")
        return 1

    try:
        # Create server instance
        server = CoralogixMCPServer(
            model=args.model,
            openai_api_key=args.openai_api_key,
            coralogix_api_key=args.coralogix_api_key,
            application_name=args.application_name
        )

        anyio.run(perform_async_initialization, server)
        logger.info("Starting Coralogix MCP Server")
        server.run_mcp_blocking()
        return 0

    except Exception as e:
        logger.error(f"Error running server: {e}")
        return 1

if __name__ == "__main__":
    main()