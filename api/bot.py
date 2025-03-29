from datetime import datetime
import json
from http.client import HTTPException
from typing import Dict, Any
from http import HTTPStatus
from http.client import responses

def handler(request):
    """Handle incoming requests."""
    try:
        if request.method == 'GET':
            body = {
                "status": "ok",
                "message": "DualAI test endpoint is working",
                "timestamp": datetime.now().isoformat()
            }
            return Response(
                status=200,
                body=json.dumps(body),
                headers={
                    "Content-Type": "application/json"
                }
            )
        elif request.method == 'POST':
            body = {
                "status": "ok",
                "message": "Webhook endpoint ready"
            }
            return Response(
                status=200,
                body=json.dumps(body),
                headers={
                    "Content-Type": "application/json"
                }
            )
        else:
            body = {
                "error": "Method not allowed"
            }
            return Response(
                status=405,
                body=json.dumps(body),
                headers={
                    "Content-Type": "application/json"
                }
            )
    except Exception as e:
        body = {
            "error": str(e)
        }
        return Response(
            status=500,
            body=json.dumps(body),
            headers={
                "Content-Type": "application/json"
            }
        )

class Response:
    def __init__(self, status: int, body: str, headers: Dict[str, str] = None):
        self.status = status
        self.statusText = responses[status]
        self.body = body
        self.headers = headers or {} 