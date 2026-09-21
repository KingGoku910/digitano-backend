# main.py - SSE STREAMING ENDPOINT
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import asyncio

app = FastAPI()

@app.get("/api/stream-progress/{project_id}")
async def stream_agent_execution(project_id: str):
    async def event_generator():
        context = {}
        for agent_name, system_prompt in AGENT_PROMPTS.items():
            # Emit "Thinking" status to UI
            yield {
                "event": "agent_update",
                "data": json.dumps({"agent": agent_name, "status": "Thinking..."})
            }
            
            # Execute Agent Call
            res = await call_agent(agent_name, system_prompt, json.dumps(context))
            
            # Trim payload & update running context for next agent
            context[agent_name] = res["data"]
            
            # Emit "Complete" status + terminal log chunk to UI
            yield {
                "event": "agent_update",
                "data": json.dumps({"agent": agent_name, "status": "Complete", "output": res["data"]})
            }
            
    return EventSourceResponse(event_generator())
