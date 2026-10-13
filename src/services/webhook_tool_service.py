import json
import logging
import urllib.parse
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class WebhookToolService:
    @staticmethod
    def execute_tool(tool_def: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically execute an HTTP tool/webhook defined for a project.
        Replaces URL path placeholders like {order_id} with arguments.
        """
        url = tool_def.get("endpoint_url", "")
        method = tool_def.get("method", "GET").upper()
        headers = tool_def.get("headers", {}) or {}

        # 1. Substitute URL path placeholders
        for k, v in args.items():
            placeholder = f"{{{k}}}"
            if placeholder in url:
                url = url.replace(placeholder, urllib.parse.quote(str(v)))

        try:
            with httpx.Client(timeout=10.0) as client:
                if method == "GET":
                    # Send non-URL params as query params
                    query_params = {k: v for k, v in args.items() if f"{{{k}}}" not in tool_def.get("endpoint_url", "")}
                    res = client.get(url, params=query_params, headers=headers)
                elif method == "POST":
                    res = client.post(url, json=args, headers=headers)
                elif method == "PUT":
                    res = client.put(url, json=args, headers=headers)
                elif method == "DELETE":
                    res = client.delete(url, headers=headers)
                else:
                    return {"status": "error", "message": f"Unsupported HTTP method: {method}"}

                try:
                    data = res.json()
                except Exception:
                    data = {"response_text": res.text}

                return {
                    "status_code": res.status_code,
                    "data": data,
                }
        except httpx.TimeoutException:
            logger.error("Timeout connecting to tool webhook URL: %s", url)
            return {"status": "error", "message": "The external service timed out. Please try again."}
        except Exception as e:
            logger.exception("Error executing tool webhook %s: %s", tool_def.get("name"), e)
            return {"status": "error", "message": str(e)}
