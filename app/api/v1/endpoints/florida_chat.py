from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from uuid import uuid4

from app.services.chatbot.chat_function.chat import InitChat
from app.schemas.schema import ChatResponse, ChatRequest, HistoryModel
from app.utils.logger import get_logger

import re


logger = get_logger(__name__)
router = APIRouter()

chat_instance = None

async def get_chat_instance():
    global chat_instance
    if chat_instance is None:
        chat_instance = InitChat()
        await chat_instance.initialize_chat()
    return chat_instance


@router.post("/florida_chat")
async def chat(request: ChatRequest, init_chat : InitChat = Depends(get_chat_instance)):
    try:
        logger.info(f"Received chat request: {request}")
        # session_id = request.session_id or uuid4()
        user_id = request.user_id
        # full_id = f"{user_id}_{session_id}"
        collection_name = "florida_yacht_sales"
   

        respond = await init_chat.chat(request.messages, user_id, collection_name)

        return JSONResponse(status_code=200, content={
            "messages" : respond,
            "user_id" : user_id
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    
@router.get("/florida_chat_history")
async def chat_history(user_id: str, init_chat: InitChat = Depends(get_chat_instance)):
    try:
        logger.info(f"Received chat history request for user_id: {user_id}")

        respond = await init_chat.get_chat_history(user_id)

        return JSONResponse(status_code=200, content=respond)

    except Exception as e:
        logger.error(f"Error in chat history endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/chat_history")
# async def chat_history(request : HistoryModel, init_chat : InitChat = Depends(get_chat_instance)):
#     try:
#         logger.info(f"Received chat history request: {request}")
#         # full_id = f"{request.user_id}_{request.session_id}"
#         user_id= request.user_id

#         respond = await init_chat.get_chat_history(user_id)

#         return JSONResponse(status_code=200, content=respond)
#     except Exception as e:
#         logger.error(f"Error in chat history endpoint: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/delete_chat_history")
# async def delete_history(request : HistoryModel, init_chat : InitChat = Depends(get_chat_instance)):
#     try:
#         logger.info(f"Received Chat history delete request: {request}")
#         full_id = f"{request.user_id}_{request.session_id}"

#         respond = await init_chat.delete_chat_history(full_id)

#         if respond:
#             return JSONResponse(status_code=200, content={"message" : "Chat history deleted successfully", "status" : respond})

#         return JSONResponse(status_code=400, content={"message" : "No Chat History Found", "status" : respond})

#     except Exception as e:
#         logger.error(f"Error in chat history delete endpoint: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
