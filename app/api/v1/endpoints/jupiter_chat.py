from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from uuid import uuid4

from app.services.chatbot.chat_function.chat import InitChat
from app.schemas.schema import JupiterChatRequest, ChatRequest
from app.utils.logger import get_logger

import re
from app.services.chat_storage_service import ChatStorageService

storage = ChatStorageService()


logger = get_logger(__name__)
router = APIRouter()

chat_instance = None

async def get_chat_instance():
    global chat_instance
    if chat_instance is None:
        chat_instance = InitChat()
        await chat_instance.initialize_chat()
    return chat_instance


@router.post("/chat")
async def chat(request: JupiterChatRequest, init_chat : InitChat = Depends(get_chat_instance)):
    try:
        logger.info(f"Received chat request: {request}")
        # session_id = request.session_id or uuid4()
        user_id = request.user_id
        # full_id = f"{user_id}_{session_id}"
        collection_name = "jupiter_marine_sales"


        # Save or update user info to aqlchemy database# Save / update user
        await storage.save_user(user_id, request.name, request.email)

        # Save user message
        await storage.save_chat_message(user_id, "user", request.messages)

        respond = await init_chat.chat(request.messages, user_id, collection_name)

        # Save assistant message to aqlchemy database
        await storage.save_chat_message(user_id, "assistant", respond)

        return JSONResponse(status_code=200, content={
            "messages" : respond,
            "user_id" : user_id,
            "name": request.name,
            "email": request.email
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))



    
@router.get("/chat_history")
async def chat_history(user_id: str, init_chat: InitChat = Depends(get_chat_instance)):
    try:
        logger.info(f"Received chat history request for user_id: {user_id}")

        respond = await init_chat.get_chat_history(user_id)

        return JSONResponse(status_code=200, content=respond)

    except Exception as e:
        logger.error(f"Error in chat history endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat_history_sql")
async def chat_history_sql(user_id: str):
    history = await storage.get_user_chat_history(user_id)

    return [
        {"role": h.role, "content": h.content, "timestamp": h.timestamp.isoformat()}
        for h in history
    ]
