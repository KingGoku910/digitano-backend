# router.py - CONSOLIDATED AI AGENT ROUTER ENGINE
import json
import boto3
import google.generativeai as genai

# Initialize AWS Bedrock Client
bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")

# ==========================================
# 1. AGENT CONFIGURATION & SYSTEM PROMPTS
# ==========================================
AGENT_PROMPTS = {
    # AGENT 1: Product Owner
    "product_owner": """
    Role: Product Owner.
    Task: Take raw user prompt and define high-level scope, target audience, core features, and primary success metrics.
    Output: Must output JSON matching ProductOwnerSchema.
    """,

    # AGENT 2: Software Analyst
    "software_analyst": """
    Role: Software Analyst.
    Task: Review Product Owner output. Draft prioritized User Stories (As a... I want... So that...) and Edge Case Failure Modes.
    Output: Must output JSON matching AnalystSchema.
    """,

    # AGENT 3: UI Lead
    "ui_lead": """
    Role: UI/UX Architect.
    Task: Define component hierarchies, color tokens, layout grids, and ShadCN/Tailwind specifications based on user stories.
    Output: Must output JSON matching UISchema.
    """,

    # AGENT 4: Backend Lead
    "backend_lead": """
    Role: Backend Architect.
    Task: Design FastAPI endpoint specifications, HTTP methods, payload schemas, and single-table DynamoDB access patterns (PK/SK).
    Output: Must output JSON matching BackendSchema.
    """,

    # AGENT 5: Full Stack Lead
    "fullstack_lead": """
    Role: Full Stack Integrator.
    Task: Define state management patterns, client-side data fetching hooks (SWR/React Query), and API error handling contracts.
    Output: Must output JSON matching FullStackSchema.
    """,

    # AGENT 6: Infrastructure Architect
    "infra_architect": """
    Role: Cloud Infrastructure Engineer.
    Task: Specify serverless AWS deployment setup (App Runner, Amplify, DynamoDB, IAM Roles) for $0-tier execution.
    Output: Must output JSON matching InfraSchema.
    """,

    # AGENT 7: Scrum Master
    "scrum_master": """
    Role: Scrum Master & Prompt Engineer.
    Task: Consolidate outputs from all prior 6 agents. Audit for inconsistencies, format final PRD Markdown, and generate structured Vibe-Coder copy-paste prompts (Prompts 1.1, 1.2, 1.3).
    Output: Must output JSON matching FinalScrumOutputSchema.
    """
}

# ==========================================
# 2. DUAL-MODEL EXECUTION & FAILOVER
# ==========================================
async def call_agent(agent_name: str, system_prompt: str, context_data: str):
    full_prompt = f"{system_prompt}\n\nInput Context:\n{context_data}"
    
    # Primary LLM Call: AWS Bedrock (Claude 3.5 Sonnet)
    try:
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": full_prompt}]
        }
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps(payload)
        )
        result = json.loads(response["body"].read())["content"][0]["text"]
        return {"agent": agent_name, "status": "success", "provider": "Bedrock", "data": result}

    except Exception as e:
        print(f"AWS Bedrock throttled for {agent_name}. Failing over to Gemini Flash... Error: {e}")
        
        # Automated Fallback LLM Call: Google Gemini Flash
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            gemini_response = model.generate_content(full_prompt)
            return {"agent": agent_name, "status": "success", "provider": "Gemini-Fallback", "data": gemini_response.text}
        except Exception as gemini_err:
            return {"agent": agent_name, "status": "failed", "error": str(gemini_err)}
