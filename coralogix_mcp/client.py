import os
import sys
import time
from dotenv import load_dotenv
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP
import json
from coralogix_mcp.common.logger import setup_logger
from litellm import acompletion
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

CORALOGIX_API_URL = "https://ng-api-http.coralogixsg.com/api/v1/dataprime/query"
# Load environment variables from .env file
load_dotenv()

# Set up logger using the central configuration
logger = setup_logger('coralogix_mcp')

class CoralogixClient:
    def __init__(self, model: str, openai_api_key: str, coralogix_api_key: str, application_name: str, time_range_minutes: int = 15):
        """Initialize the CoralogixClient"""
        self.model = model
        self.openai_api_key = openai_api_key
        self.coralogix_api_key = coralogix_api_key
        self.application_name = application_name
        self.time_range_minutes = time_range_minutes
    
        self._service_name_cache = {
            "data": None,
            "timestamp": None,
            "cache_ttl": 300  # 5 minutes in seconds
        }
        self._service_name_matching_cache = {}
        self.end_time = datetime.now(timezone.utc)
        self.start_time = self.end_time - timedelta(minutes=time_range_minutes)
        
        # Set up headers for Coralogix API
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {coralogix_api_key}"
        }
        self.metadata = {
            "syntax": "QUERY_SYNTAX_DATAPRIME",
            "tier": "TIER_ARCHIVE",
            "startTime": self.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "endTime": self.end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "defaultSource": "logs"
        }

        self.service_names_available = []

    async def initialize_coralogix_client(self):
        """Initialize Coralogix client Data"""
        self.service_names_available =  await self.fetch_service_names()
        logger.info(f"Initialized Coralogix client with {len(self.service_names_available)} service names")

    async def fetch_service_names(self):
        """Fetch service names from Coralogix"""
        current_time = datetime.now(timezone.utc)
        query = f"source logs | filter $l.applicationname == '{self.application_name}' | filter $l.subsystemname != null | groupby $l.subsystemname"

        # Check if we have valid cache data
        if (self._service_name_cache["data"] is not None and 
            self._service_name_cache["timestamp"] is not None and 
            (current_time - self._service_name_cache["timestamp"]).total_seconds() < self._service_name_cache["cache_ttl"]):
            logger.info("Returning cached service names")
            return self._service_name_cache["data"]

        try:
            payload = {
                "query": query,
                "metadata": self.metadata
            }
            response = requests.post(
                f"{CORALOGIX_API_URL}",
                json=payload,
                headers=self.headers
            )

            if response.ok:
                try:
                    # Get the second JSON object containing results
                    json_lines = [line.strip() for line in response.text.split('\n') if line.strip()]
                    if len(json_lines) >= 2:
                        results_json = json.loads(json_lines[1])
                        log_results = results_json.get("result", {}).get("results", [])
                        
                        if not log_results:
                            logger.info("No logs found for the given time period")
                            return []
                            
                        # Properly parse the userData JSON string and extract subsystemname
                        service_names = []
                        for log in log_results:
                            try:
                                user_data = json.loads(log.get("userData", "{}"))
                                subsystem_name = user_data.get("subsystemname")
                                if subsystem_name:
                                    service_names.append(subsystem_name)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse userData JSON: {log.get('userData')}")
                                continue
                        
                        logger.info(f"Found {len(service_names)} service names")
                        
                        # Update cache
                        self._service_name_cache["data"] = service_names
                        self._service_name_cache["timestamp"] = current_time
                        
                        return service_names
                    else:
                        logger.info("No service names found")
                        return []
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing response: {e}")
                    return []
            else:
                logger.error(f"Failed to fetch service names: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching service names: {str(e)}")
            return []

    async def find_matching_coralogix_service_name(self, service_name: str) -> str:
        """Find Coralogix service name"""
        if not service_name:
            logger.error("No service name provided")
            return None

        # Check if we have a cached result for this service name
        if service_name in self._service_name_matching_cache:
            logger.info(f"Returning cached match for service name: {service_name}")
            return self._service_name_matching_cache[service_name]
        
        # Get all available service names
        service_names_available = await self.fetch_service_names()
        if not service_names_available:
            logger.error("No service names available")
            return None
        
        # Check if the service name is in the list of available service names
        if service_name in service_names_available:
            logger.info(f"Found exact match for service name: {service_name}")
            self._service_name_matching_cache[service_name] = service_name
            return service_name
        
        # Try LLM matching first
        system_prompt = f"""
        You are a helpful assistant that can find the best match for a given service name "{service_name}" from the list of available service names.
        The list of Coralogix service names available are: {service_names_available}.
        
        Format the response as a JSON object with:
        {{
            "service_name": "best matching Coralogix service name"
        }}
        """
        
        try:
            response = await self.call_llm(system_prompt)
            if response:
                try:
                    response_json = json.loads(response)
                    best_match = response_json.get("service_name")
                    if best_match and best_match in service_names_available:
                        logger.info(f"LLM found match for service name: {service_name} -> {best_match}")
                        self._service_name_matching_cache[service_name] = best_match
                        return best_match
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM response as JSON")
        except Exception as e:
            logger.error(f"Error in LLM matching: {str(e)}")
        
        # Fallback to basic matching if LLM fails or returns invalid result
        logger.info("Falling back to basic matching")
        best_match = self.find_best_match_basic(service_name, service_names_available)
        if best_match:
            logger.info(f"Basic matching found match for service name: {service_name} -> {best_match}")
            self._service_name_matching_cache[service_name] = best_match
        else:
            logger.warning(f"No match found for service name: {service_name}")
        
        return best_match
    
    def find_best_match_basic(self, target: str, candidates: list) -> str:
        """Basic fallback matching function when LLM is not available"""
        if not target or not candidates:
            return None
        
        # Convert to lowercase for case-insensitive matching
        target = target.lower()
        
        # Exact match check
        for candidate in candidates:
            if candidate.lower() == target:
                return candidate
        
        # Partial match check (contains)
        partial_matches = [
            c for c in candidates
            if target in c.lower() or c.lower() in target
        ]
        
        if partial_matches:
            # Sort by length to prefer shorter, more precise matches
            partial_matches.sort(key=len)
            return partial_matches[0]
        
        return None
    
    async def http_generate_query(self, service_name: str, query_type: str = None) -> str:
        """Generate a query for Coralogix DataPrime for HTTP requests
        Args:
            service_name: The service name to generate a query for
            query_type: The type of query to generate. Can be "4xx", "5xx", "2xx", or "critical"
        Returns:
            A string containing the query for Coralogix DataPrime
        """

        service_name = await self.find_matching_coralogix_service_name(service_name)
        if not service_name:
            raise ValueError(f"No matching service name found for {service_name}")
    
        
        query = (
            f"source logs | filter $l.applicationname == '{self.application_name}' "
            f"| filter $l.subsystemname == '{service_name}' "
        )

        if query_type == "4xx":
            query += " | filter ($d.status_code >= '400' && $d.status_code <= '499') | filter $d.http_method != null"
        elif query_type == "5xx":
            query += " | filter ($d.status_code >= '500' && $d.status_code <= '599') | filter $d.http_method != null"
        elif query_type == "2xx":
            query += " | filter ($d.status_code >= '200' && $d.status_code <= '399') | filter $d.http_method != null"
        else:
            query += " | filter $m.severity == CRITICAL"

        # New extraction and grouping logic
        query += (
            "| extract $d.path into $d using regexp(e=/(?<new_path>^.+)\\?.+/) "
            "| groupby $d.new_path, $d.http_method, $d.status_code aggregate count() as log_count"
        )
        return query

    async def search_generate_query(self, search_string: str, service_name: str = None) -> str:
        """Generate a query for Coralogix DataPrime"""
        
        service_name = await self.find_matching_coralogix_service_name(service_name)
        if not service_name:
            raise ValueError(f"No matching service name found for {service_name}")
        
        query = (
            f"source logs | filter $l.applicationname == '{self.application_name}'"
        )
        
        if service_name:
            query += f" | filter $l.subsystemname == '{service_name}'"
        
        # Handle multiple search strings
        search_strings = [s.strip() for s in search_string.split('and')]
        search_conditions = []
        
        for s in search_strings:
            safe_search_string = s.replace("'", "\\'")
            if s.isdigit() and len(s) == 3:
                # Match status code in both log line and JSON format
                search_conditions.append(
                    f"($d.logRecord.body.log.contains(' {s} ') || "
                    f"$d.logRecord.body.log.contains('\"status\":\"{s}\"') || "
                    f"$d.logRecord.body.log.contains('\"status\": {s}'))"
                )
            else:
                search_conditions.append(f"$d.logRecord.body.log.contains('{safe_search_string}')")
        
        # Combine all search conditions with AND operator
        if search_conditions:
            query += " | filter (" + " && ".join(search_conditions) + ")"
        
        query += " | limit 100"

        return query

    async def search_coralogix_logs(self, query: str) -> Optional[Dict]:
        """Search Coralogix logs for error details"""
        try:
            # Format timestamps in microseconds and Z suffix to properly format the date range
            end_time_str = self.end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            start_time_str = self.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
            payload = {
                "query": query,
                "metadata": self.metadata
            }
            
            # Enhanced logging
            logger.info("=== Coralogix API Request Details ===")
            logger.info(f"URL: {CORALOGIX_API_URL}")
            logger.info(f"Time Range: {start_time_str} to {end_time_str}")
            logger.info(f"Query: {query}")
            
            response = requests.post(
                CORALOGIX_API_URL,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.ok:
                try:
                    # Get the second JSON object containing results
                    json_lines = [line.strip() for line in response.text.split('\n') if line.strip()]
                    if len(json_lines) >= 2:
                        results_json = json.loads(json_lines[1])
                        log_results = results_json.get("result", {}).get("results", [])
                        
                        # If no logs found, return empty list instead of None
                        if not log_results:
                            logger.info("No logs found for the given time period")
                            return []
                        
                        user_data_list = []
                        for log in log_results:
                            # Try to parse logRecord.body.log as JSON if present
                            log_record = log.get("logRecord", {})
                            if isinstance(log_record, dict):
                                body = log_record.get("body", {})
                                if isinstance(body, dict):
                                    log_text = body.get("log", None)
                                    if log_text:
                                        try:
                                            user_data = json.loads(log_text)
                                            user_data_list.append(user_data)
                                            continue
                                        except Exception:
                                            pass
                            # Fallback to userData
                            user_data = json.loads(log.get("userData", "{}"))
                            user_data_list.append(user_data)
                        logger.info(f"Found {len(user_data_list)} log entries")
                        return user_data_list
                    # No results in response, return empty list
                    logger.info("No logs found in response")
                    return []
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing response: {e}")
                    return None
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error searching logs: {str(e)}")
            return None

    async def analyze_logs(self, user_data_list: list) -> dict:
        """Analyze logs and show top 10 API endpoints with counts"""
        if not user_data_list or not isinstance(user_data_list, list):
            return {"summary": "No logs found for analysis"}
        
        api_counts = {}
        total_requests = 0
        
        # Process logs
        for log in user_data_list:
            path = log.get("new_path", "")
            # Skip unknown or null paths
            if not path or path == "unknown":
                continue
                
            count = int(log.get("log_count", 0))
            method = log.get("http_method", "")
            status = log.get("status_code", "")
            
            # Create unique key for path+method+status
            key = f"{path}|{method}|{status}"
            api_counts[key] = {
                "http_method": method,
                "log_count": count,
                "new_path": path,
                "status_code": status
            }
            total_requests += count
        
        # Get top 10 by count
        top_apis = sorted(
            api_counts.values(),
            key=lambda x: x["log_count"],
            reverse=True
        )[:10]
        
        return {
            "total_requests": total_requests,
            "top_apis": top_apis
        }

    async def get_log_context(self, user_data_list: list, search_string: str, context_lines: int = 10) -> list:
        """Extract logs with context around the search string"""
        context_results = []
        
        for log in user_data_list:
            try:
                if isinstance(log, str):
                    logger.warning(f"expected dict but got str: {log[:100]}...")
                    continue
                
                log_record = log.get("logRecord", {})
                if isinstance(log_record, str):
                    continue
                
                body = log_record.get("body", {})
                if isinstance(body, str):
                    log_text = body
                else:
                    log_text = body.get("log", "")

                if not log_text:
                    continue
                
                lines = log_text.split('\n')
                
                matches = []
                for i, line in enumerate(lines):
                    if search_string.lower() in line.lower():
                        matches.append(i)
                
                if not matches:
                    continue
                    
                for match_line in matches:
                    start = max(0, match_line - context_lines)
                    end = min(len(lines), match_line + context_lines + 1)
                    context = []
                    for i in range(start, end):
                        if i == match_line:
                            context.append(f">>> {lines[i]}")
                        else:
                            context.append(f"    {lines[i]}")
                    
                    timestamp = log.get("timestamp", "")
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                        except:
                            pass
                    
                    context_results.append({
                        "timestamp": timestamp,
                        "service": log.get("subsystemname", ""),
                        "context": "\n".join(context)
                    })
            except Exception as e:
                logger.error(f"Error processing log for context: {str(e)}")
                continue
        
        return context_results


    async def format_error_analysis(self, user_data_list: list, error_type: str) -> str:
        """Format error analysis results"""
        analysis = await self.analyze_logs(user_data_list)

        return analysis

    async def search_recent_error_logs(self, service_name: str = None) -> Optional[Dict]:
        """Search error logs within a 2-minute time window from the current time and return detailed error messages"""
        service_name = await self.find_matching_coralogix_service_name(service_name)
        if not service_name:
            raise ValueError(f"No matching service name found for {service_name}")
        try:
            # Generate query for both 4xx and 5xx errors
            query = f"source logs | filter $l.applicationname == '{self.application_name}'"
            if service_name:
                query += f" | filter $l.subsystemname == '{service_name}'"
            # Add severity filter for both CRITICAL and ERROR
            query += " | filter ($m.severity == CRITICAL || $m.severity == ERROR)"
            # Add filters for error-related terms
            query += (
                " | filter ("
                "$d.logRecord.body.log.contains('error') || "
                "$d.logRecord.body.log.contains('exception') || "
                "$d.logRecord.body.log.contains('failed') || "
                "$d.logRecord.body.log.contains('failure') || "
                "$d.logRecord.body.log.contains('stacktrace') || "
                "$d.logRecord.body.log.contains('traceback') || "
                "($d.status_code >= '400' && $d.status_code <= '599')"
                ")"
            )
            # Search logs with 2-minute time window
            results = await self.search_coralogix_logs(query)
            if not results:
                return []
                
            # Extract and format log messages
            formatted_logs = []
            for log in results:
                try:
                    if isinstance(log, str):
                        continue
                        
                    log_record = log.get("logRecord", {})
                    if isinstance(log_record, str):
                        continue
                        
                    body = log_record.get("body", {})
                    if isinstance(body, str):
                        log_text = body
                    else:
                        log_text = body.get("log", "")
                        
                    if not log_text:
                        continue
                        
                    # Only include logs that contain error-related terms or have ERROR/CRITICAL severity
                    if not any(term in log_text.lower() for term in ['error', 'exception', 'failed', 'failure', 'stacktrace', 'stack trace', 'traceback', 'trace back']):
                        continue
                        
                    timestamp = log.get("timestamp", "")
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                        except:
                            pass
                            
                    formatted_logs.append({
                        "timestamp": timestamp,
                        "service": log.get("subsystemname", ""),
                        "severity": log.get("severity", ""),
                        "log_message": log_text
                    })
                except Exception as e:
                    logger.error(f"Error processing log entry: {str(e)}")
                    continue
                    
            return formatted_logs
            
        except Exception as e:
            logger.error(f"Error searching recent error logs: {str(e)}")
            return None
    
    async def call_llm(self, prompt: str) -> str:
        """
        Call LLM using LiteLLM to find matching names.
        
        Args:
            prompt (str): The prompt to send to the LLM
            
        Returns:
            str: JSON string containing the LLM's response with coralogix service_name
        """
        try:
            response = await acompletion(
                model=self.model,
                api_key=self.openai_api_key,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that finds the best matching Coralogix service name. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            # Extract the response content
            response_content = response.choices[0].message.content
            
            # Validate that the response is valid JSON
            try:
                json.loads(response_content)
                return response_content
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Error llm calling: {str(e)}")
            return None