# router.py - AGENT CALL & FAILOVER ENGINE
import boto3
import google.generativeai as genai
import json

bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")

async def call_agent(agent_name: str, system_prompt: str, context_data: str):
    full_prompt = f"{system_prompt}\n\nInput Context:\n{context_data}"
    
    # 1. Try Primary LLM: AWS Bedrock
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
        
        # 2. Automated Failover: Google Gemini Flash
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            gemini_response = model.generate_content(full_prompt)
            return {"agent": agent_name, "status": "success", "provider": "Gemini-Fallback", "data": gemini_response.text}
        except Exception as gemini_err:
            return {"agent": agent_name, "status": "failed", "error": str(gemini_err)}

