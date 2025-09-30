import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Excuse Email Draft Tool",
    description="Generate professional excuse emails using Databricks Model Serving",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ExcuseRequest(BaseModel):
    category: str = Field(..., description="Category of excuse")
    tone: str = Field(..., description="Tone of the email")
    seriousness: int = Field(..., ge=1, le=5, description="Seriousness level 1-5")
    recipient_name: str = Field(..., description="Name of the recipient")
    sender_name: str = Field(..., description="Name of the sender")
    eta_when: str = Field(..., description="ETA or when information")

class ExcuseResponse(BaseModel):
    subject: str
    body: str
    success: bool
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# Environment configuration
DATABRICKS_API_TOKEN = os.getenv("DATABRICKS_API_TOKEN")
DATABRICKS_ENDPOINT_URL = os.getenv(
    "DATABRICKS_ENDPOINT_URL", 
    "https://dbc-32cf6ae7-cf82.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations"
)
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# LLM Integration
async def generate_excuse_with_llm(request_data: ExcuseRequest) -> ExcuseResponse:
    """Generate excuse email using Databricks Model Serving"""
    
    if not DATABRICKS_API_TOKEN:
        raise HTTPException(
            status_code=500, 
            detail="DATABRICKS_API_TOKEN not configured"
        )
    
    # Create the prompt
    prompt = f"""Generate a professional excuse email based on the following parameters:

Category: {request_data.category}
Tone: {request_data.tone}
Seriousness Level: {request_data.seriousness}/5 (1=very silly, 5=serious)
Recipient: {request_data.recipient_name}
Sender: {request_data.sender_name}
ETA/When: {request_data.eta_when}

Please generate a JSON response with the following format:
{{
    "subject": "Appropriate email subject line",
    "body": "Dear [Recipient],\\n\\n[Apology/Excuse]\\n\\n[Reason/Explanation]\\n\\n[Next Steps/Resolution]\\n\\nBest regards,\\n[Sender]"
}}

Guidelines:
- Match the tone (sincere, playful, corporate, or assertive)
- Adjust formality based on seriousness level
- Include the ETA/when information naturally
- Keep it professional but appropriate for the tone
- Use proper email formatting with line breaks
- For "assertive" tone: Write in a style that blames the recipient for the situation, use language like "due to your lack of advance notice", "given your unclear instructions", "this could have been avoided if you had", "the miscommunication on your end", "as we previously discussed but you failed to", "per our earlier conversation which you seem to have forgotten", "your poor planning has caused", "the confusion you created", "your failure to communicate properly", make it clear the sender is not at fault and the recipient is responsible
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {DATABRICKS_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            logger.info(f"Making request to Databricks endpoint: {DATABRICKS_ENDPOINT_URL}")
            response = await client.post(
                DATABRICKS_ENDPOINT_URL,
                headers=headers,
                json=payload
            )
            
            logger.info(f"Databricks response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Databricks API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM service error: {response.status_code}"
                )
            
            result = response.json()
            logger.info(f"Databricks response: {result}")
            
            # Parse the response - handle different response formats
            content = ""
            if "choices" in result and len(result["choices"]) > 0:
                message_content = result["choices"][0].get("message", {}).get("content", "")
                # Handle both string and list formats
                if isinstance(message_content, list):
                    # Find the text content in the list
                    for item in message_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            content = item.get("text", "")
                            break
                    if not content:
                        # Fallback: convert list to string
                        content = str(message_content)
                else:
                    content = message_content
            elif "predictions" in result and len(result["predictions"]) > 0:
                content = result["predictions"][0]
            elif "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0].get("content", "")
            else:
                content = str(result)
            
            logger.info(f"Extracted content: {content}")
            
            # Try to parse JSON from the content
            try:
                # Extract JSON from the response if it's wrapped in markdown
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                # Try to find JSON object in the content
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    parsed_content = json.loads(json_content)
                    subject = parsed_content.get("subject", "Excuse Email")
                    body = parsed_content.get("body", "Email content could not be generated.")
                else:
                    raise json.JSONDecodeError("No JSON object found", content, 0)
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not parse JSON response: {e}")
                # Fallback: create a simple email instead of returning raw JSON
                subject = f"{request_data.category} - {request_data.eta_when}"
                body = f"Dear {request_data.recipient_name},\n\nI wanted to let you know that I will be {request_data.category.lower()}.\n\n{request_data.eta_when}\n\nBest regards,\n{request_data.sender_name}"
            
            return ExcuseResponse(
                subject=subject,
                body=body,
                success=True,
                error=None
            )
            
    except httpx.TimeoutException:
        logger.error("Timeout calling Databricks API")
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail="Network error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# API Endpoints
@app.post("/api/generate-excuse", response_model=ExcuseResponse)
async def generate_excuse(request: ExcuseRequest):
    """Generate an excuse email based on the provided parameters"""
    try:
        return await generate_excuse_with_llm(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating excuse: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate excuse")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import datetime
    return HealthResponse(
        status="healthy",
        timestamp=datetime.datetime.utcnow().isoformat(),
        version="1.0.0"
    )

@app.get("/healthz")
async def healthz():
    """Kubernetes-style health check"""
    return {"status": "ok"}

@app.get("/ready")
async def ready():
    """Readiness check"""
    return {"status": "ready"}

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    return "# HELP excuse_generator_requests_total Total number of requests\n# TYPE excuse_generator_requests_total counter\nexcuse_generator_requests_total 0\n"

@app.get("/debug")
async def debug():
    """Debug endpoint for environment information"""
    return {
        "environment": {
            "DATABRICKS_ENDPOINT_URL": DATABRICKS_ENDPOINT_URL,
            "DATABRICKS_API_TOKEN": "***" if DATABRICKS_API_TOKEN else "Not set",
            "PORT": PORT,
            "HOST": HOST,
        },
        "paths": {
            "current_dir": os.getcwd(),
            "app_dir": Path(__file__).parent,
            "public_dir": Path(__file__).parent.parent / "public",
        }
    }

# Static file serving with multiple path resolution
def get_static_file_path():
    """Get the path to the static HTML file with multiple fallback locations"""
    possible_paths = [
        Path(__file__).parent.parent / "public" / "index.html",
        Path("public") / "index.html",
        Path("index.html"),
        Path(__file__).parent / "public" / "index.html",
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Serving static files from: {path}")
            return path
    
    logger.error("Could not find index.html in any expected location")
    return None

@app.get("/", response_class=HTMLResponse)
async def serve_app():
    """Serve the React application"""
    static_path = get_static_file_path()
    if static_path and static_path.exists():
        return FileResponse(static_path)
    else:
        # Fallback HTML if file not found
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Excuse Email Draft Tool</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <h1>Excuse Email Draft Tool</h1>
            <p class="error">Error: Could not find the application files.</p>
            <p>Please ensure the public/index.html file exists.</p>
        </body>
        </html>
        """)

# Mount static files (fallback)
try:
    public_path = Path(__file__).parent.parent / "public"
    if public_path.exists():
        app.mount("/static", StaticFiles(directory=str(public_path)), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

