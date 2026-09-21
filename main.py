import os
import json
import requests
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from jose import jwt, JWTError

from router import AGENT_PROMPTS, call_agent
from dynamo_service import save_project_prd

app = FastAPI(title="Digitano Builder API")

# Enable CORS for Next.js Bolt Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cognito JWT Setup
security = HTTPBearer()
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "")

# Cache Cognito Public Keys
JWKS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
jwks_data = None

def get_jwks():
    global jwks_data
    if not jwks_data and COGNITO_USER_POOL_ID:
        try:
            res = requests.get(JWKS_URL)
            if res.status_code == 200:
                jwks_data = res.json()
        except Exception as e:
            print(f"Failed to load JWKS keys from Cognito: {e}")
    return jwks_data or {"keys": []}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifies incoming Bearer JWT against AWS Cognito JWKS keys."""
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        jwks = get_jwks()
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Public key not found in JWKS")
            
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired JWT token: {str(e)}"
        )

@app.get("/")
def health_check():
    return {"status": "Digitano Backend Operating Normally"}

@app.get("/api/stream-progress/{project_id}")
async def stream_agent_execution(
    project_id: str,
    prompt: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub", "anonymous_user")
    
    async def event_generator():
        context = {"raw_prompt": prompt}
        for agent_name, system_prompt in AGENT_PROMPTS.items():
            yield {
                "event": "agent_update",
                "data": json.dumps({"agent": agent_name, "status": "Thinking..."})
            }
            
            res = await call_agent(agent_name, system_prompt, json.dumps(context))
            context[agent_name] = res["data"]
            
            yield {
                "event": "agent_update",
                "data": json.dumps({"agent": agent_name, "status": "Complete", "output": res["data"]})
            }
            
        # Persist final PRD associated with authenticated user ID
        save_project_prd(user_id, project_id, prompt, context)

    return EventSourceResponse(event_generator())
