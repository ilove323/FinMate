"""AI chat SSE endpoint."""

import json

from openai import AuthenticationError, BadRequestError
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.agent.agent import chat_stream

router = APIRouter(prefix="/api/v1/ai-chat", tags=["ai-chat"])


@router.post("/stream")
async def stream_chat(body: dict, db: AsyncSession = Depends(get_db)):
    message = body.get("message", "")
    module_context = body.get("module_context")
    history = body.get("history", [])

    async def event_stream():
        try:
            async for chunk in chat_stream(message, module_context, history, db):
                yield f"data: {chunk}\n\n"
        except AuthenticationError:
            err = json.dumps({"type": "error", "content": "API Key 无效，请检查 .env 文件中的 VOLCENGINE_API_KEY。"}, ensure_ascii=False)
            yield f"data: {err}\n\n"
        except BadRequestError as e:
            err = json.dumps({"type": "error", "content": f"请求错误：{e}"}, ensure_ascii=False)
            yield f"data: {err}\n\n"
        except Exception as e:
            err = json.dumps({"type": "error", "content": f"AI 服务异常：{e}"}, ensure_ascii=False)
            yield f"data: {err}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
