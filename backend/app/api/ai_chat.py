"""AI chat SSE endpoint."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.agent.agent import chat_stream

router = APIRouter(prefix="/api/v1/ai-chat", tags=["ai-chat"])


@router.post("/stream")
async def stream_chat(body: dict, db: AsyncSession = Depends(get_db)):
    message = body.get("message", "")
    module_context = body.get("module_context")  # e.g. "reconciliation"
    history = body.get("history", [])

    async def event_stream():
        async for chunk in chat_stream(message, module_context, history, db):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
