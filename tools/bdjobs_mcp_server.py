#!/usr/bin/env python3
"""
BDJobs Enterprise MCP Server (v2.0) for Hamim Ahmed (Sayed Johon)
Exposes BDJobs search, deep contact extraction, and 4-track persona match intelligence to AI Agents.
"""

import sys
import json
import re
import requests

API_BASE_URL = "http://100.86.193.4:19828"

def send_response(response: dict):
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def handle_tools_list():
    return {
        "tools": [
            {
                "name": "bdjobs_search",
                "description": "Search live jobs on BDJobs.com (Bangladesh) with real-time Persona Match scoring (Track A, B, C, D) and recency filtering.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Keywords, role, or skill (e.g. 'python', 'video editor', 'growth marketing')."
                        },
                        "category": {
                            "type": "string",
                            "description": "Category alias ('it', 'media', 'video', 'creative', 'marketing', 'management') or category code."
                        },
                        "location": {
                            "type": "string",
                            "description": "Location / District in Bangladesh (e.g. 'Dhaka', 'Chittagong', 'Remote')."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results to return (default 20, max 50)."
                        },
                        "jobage": {
                            "type": "integer",
                            "description": "Recency filter: 1 for last 24h, 2 for 48h, 7 for 7 days, 14 for 14 days."
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["latest", "match", "deadline"],
                            "description": "Sort order: 'latest' (newest first), 'match' (highest Persona match), 'deadline' (closing soonest)."
                        }
                    }
                }
            },
            {
                "name": "bdjobs_research_job",
                "description": "Extract full 360° research dossier for a BDJobs posting, including direct recruiter emails, phone numbers, application method, detailed requirements, and AI CV tailoring advice.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "The BDJobs Job ID (e.g. '1522795', '1523323') or full BDJobs URL."
                        }
                    },
                    "required": ["job_id"]
                }
            },
            {
                "name": "bdjobs_get_categories",
                "description": "List all BDJobs category aliases and their mappings to Sayed Johon's 4 Persona Tracks.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }

def handle_tool_call(name: str, arguments: dict):
    if name == "bdjobs_search":
        q = arguments.get("query", "")
        cat = arguments.get("category", "")
        loc = arguments.get("location", "")
        limit = arguments.get("limit", 20)
        jobage = arguments.get("jobage")
        sort = arguments.get("sort", "latest")
        
        params = {"q": q, "category": cat, "location": loc, "limit": limit, "sort": sort}
        if jobage:
            params["jobage"] = jobage

        res = requests.get(f"{API_BASE_URL}/search", params=params, timeout=15)
        return res.json()

    elif name in ["bdjobs_research_job", "bdjobs_get_job_detail"]:
        raw_id = str(arguments.get("job_id", ""))
        m = re.search(r"(?:details\/|id=)?(\d+)", raw_id)
        job_id = m.group(1) if m else raw_id
        res = requests.get(f"{API_BASE_URL}/detail/{job_id}", timeout=15)
        return res.json()

    elif name == "bdjobs_get_categories":
        res = requests.get(f"{API_BASE_URL}/categories", timeout=15)
        return res.json()

    else:
        raise ValueError(f"Unknown tool: {name}")

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "initialize":
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": "bdjobs-mcp",
                            "version": "2.0.0"
                        },
                        "capabilities": {
                            "tools": {}
                        }
                    }
                })
            elif method == "tools/list":
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": handle_tools_list()
                })
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result_data = handle_tool_call(tool_name, tool_args)
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_data, indent=2, ensure_ascii=False)
                            }
                        ]
                    }
                })
            elif method == "ping":
                send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})
            else:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                })
        except Exception as e:
            send_response({
                "jsonrpc": "2.0",
                "id": req.get("id") if 'req' in locals() and isinstance(req, dict) else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            })

if __name__ == "__main__":
    main()
