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
        await server_obj.client.initialize_coralogix_client()
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")
        return 1

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Coralogix MCP Server")
    parser.add_argument("--host", default="localhost", type=str, help="Custom host for the server")
    parser.add_argument("--port", default=8000, type=int, help="Custom port for the server")
    parser.add_argument("--model", default="openai/gpt-4o-mini", type=str, help="OpenAI model to use")
    parser.add_argument("--openai-api-key", type=str, help="OpenAI API key")
    parser.add_argument("--coralogix-api-key", type=str, help="Coralogix API key")
    parser.add_argument("--application-name", type=str, help="Application name")

    args = parser.parse_args()

    # Get OpenAI API key from args or environment
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or use --openai-api-key")
        return 1

    # Get model from args or environment
    model = args.model or os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

    # Get Coralogix API key from args or environment
    coralogix_api_key = args.coralogix_api_key or os.getenv("CORALOGIX_API_KEY")
    if not coralogix_api_key:
        logger.error("Coralogix API key not provided. Set CORALOGIX_API_KEY environment variable or use --coralogix-api-key")
        return 1

    # Get application name from args or environment
    application_name = args.application_name or os.getenv("APPLICATION_NAME")
    if not application_name:
        logger.error("Application name not provided. Set APPLICATION_NAME environment variable or use --application-name")
        return 1

    try:
        # Create server instance
        server = CoralogixMCPServer(
            model=model,
            openai_api_key=openai_api_key,
            coralogix_api_key=coralogix_api_key,
            application_name=application_name
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