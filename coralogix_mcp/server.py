from mcp.server.fastmcp import FastMCP
import logging
from coralogix_mcp.client import CoralogixClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('rds_mcp')


class CoralogixMCPServer:
    def __init__(self, model: str, openai_api_key: str, coralogix_api_key: str, application_name: str):
        self.mcp = FastMCP("coralogix")
        self.client = CoralogixClient(model=model, openai_api_key=openai_api_key, coralogix_api_key=coralogix_api_key, application_name=application_name)
        self._register_tools()
        self.openai_api_key = openai_api_key
        self.coralogix_api_key = coralogix_api_key
        self.application_name = application_name
        self.model = model
        
    def _register_tools(self):
        self.mcp.tool()(self.get_2xx_logs)
        self.mcp.tool()(self.get_4xx_logs)
        self.mcp.tool()(self.get_5xx_logs)
        self.mcp.tool()(self.get_coralogix_logs_by_string)
    
    def run_mcp_blocking(self):
        """
        Runs the FastMCP server. This method is blocking and should be called
        after any necessary asynchronous initialization (like self.client.initialize_coralogix_client)
        has been completed in a separate AnyIO event loop.
        """
        # self.client.initialize_coralogix_client() is assumed to have been awaited
        # before this synchronous method is called.
        
        # The FastMCP server's run method will internally call anyio.run()
        # and manage its own event loop for stdio transport.
        self.mcp.run(transport='stdio')

    async def get_2xx_logs(self, service_name = None):
        """Analyze 2XX error logs from Coralogix with both API endpoint statistics and detailed error messages"""
        try:
            query = await self.client.http_generate_query(service_name, query_type="2xx")
            logs = await self.client.search_coralogix_logs(query)
            
            if logs is None:
                return {"status": "error", "message": "Error fetching logs"}
            
            api_analysis = await self.client.analyze_logs(logs)
            
            return {
                "status": "success",
                "api_analysis": api_analysis
            }
        
        except Exception as e:
            logger.error(f"Error in get_2xx_logs: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_4xx_logs(self, service_name = None):
        """Analyze 4XX error logs from Coralogix with both API endpoint statistics and detailed error messages"""
        try:
            query = await self.client.http_generate_query(service_name, query_type="4xx")
            logs = await self.client.search_coralogix_logs(query)
            
            # Get error details from search_recent_error_logs (always)
            error_details = await self.client.search_recent_error_logs(service_name)
            
            if logs is None:
                return {
                    "status": "success",
                    "api_analysis": "Error fetching 4XX error logs",
                    "error_details": error_details,
                    "total_errors": len(error_details) if error_details else 0
                }
            elif not logs:
                return {
                    "status": "success",
                    "api_analysis": "No 4XX errors found in the specified time period",
                    "error_details": error_details,
                    "total_errors": len(error_details) if error_details else 0
                }
            
            api_analysis = await self.client.analyze_logs(logs)
            
            return {
                "status": "success",
                "api_analysis": api_analysis,
                "error_details": error_details,
                "total_errors": len(error_details) if error_details else 0
            }
            
        except Exception as e:
            logger.error(f"Error in get_4xx_logs: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_5xx_logs(self, service_name = None):
        """Analyze 5XX error logs from Coralogix with both API endpoint statistics and detailed error messages"""
        try:
            query = await self.client.http_generate_query(service_name, query_type="5xx")
            logs = await self.client.search_coralogix_logs(query)
            
            # Get error details from search_recent_error_logs (always)
            error_details = await self.client.search_recent_error_logs(service_name)
            
            if logs is None:
                return {
                    "status": "success",
                    "api_analysis": "Error fetching 5XX error logs",
                    "error_details": error_details,
                    "total_errors": len(error_details) if error_details else 0
                }
            elif not logs:
                return {
                    "status": "success",
                    "api_analysis": "No 5XX errors found in the specified time period",
                    "error_details": error_details,
                    "total_errors": len(error_details) if error_details else 0
                }
            
            api_analysis = await self.client.analyze_logs(logs)
            
            return {
                "status": "success",
                "api_analysis": api_analysis,
                "error_details": error_details,
                "total_errors": len(error_details) if error_details else 0
            }
            
        except Exception as e:
            logger.error(f"Error in get_5xx_logs: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_coralogix_logs_by_string(self, search_string: str, service_name: str = None, context_lines: int = 100):
        """Search logs for a specific string and return context around matches"""
        try:
            query = await self.client.search_generate_query(search_string, service_name)
            logs = await self.client.search_coralogix_logs(query)
            
            if logs is None:
                return {"status": "error", "message": "Error fetching logs"}
            elif not logs:
                return {"status": "success", "message": f"No logs found containing '{search_string}'", "results": []}
            
            context_results = await self.client.get_log_context(logs, search_string, context_lines)
            
            return {
                "status": "success",
                "search_string": search_string,
                "total_matches": len(context_results),
                "results": context_results
            }
            
        except Exception as e:
            logger.error(f"Error searching logs: {str(e)}")
            return {"status": "error", "message": str(e)}