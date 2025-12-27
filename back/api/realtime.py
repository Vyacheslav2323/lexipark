import os
import httpx
from fastapi import APIRouter, HTTPException, Response

router = APIRouter(tags=["realtime"])

@router.get("/realtime-token")
async def realtime_token():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.openai.com/v1/realtime/sessions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-realtime-preview-latest",
            },
        )

    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    data = r.json()
    token = (data.get("client_secret") or {}).get("value")
    if not token:
        raise HTTPException(status_code=500, detail=f"Missing client_secret.value: {data}")

    return Response(content=token, media_type="text/plain")
