from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from uuid import uuid4

from app.services.chatbot.chat_function.chat import InitChat
from app.schemas.schema import ChatResponse, ChatRequest, HistoryModel
from app.utils.logger import get_logger

import re

# def parse_chat_response_flat(message: str):
#     """
#     Parses a GPT-style chat message into:
#     - initial: introduction text
#     - products: list of flat product cards
#     - interaction: final interaction message
#     """

#     message = message.strip()
#     sections = message.split("\n\n")

#     if len(sections) < 3:
#         # fallback if message doesn't follow expected format
#         return {"initial": message, "products": [], "interaction": ""}

#     # First section is the initial message
#     initial = sections[0].strip()

#     # Last section is the interaction message
#     interaction = sections[-1].strip()

#     # Everything in between is product cards
#     products_raw = sections[1:-1]

#     products = []
#     for block in products_raw:
#         block = block.strip()
#         product = {}

#         # Title + URL
#         title_match = re.search(r"\[(.*?)\]\((.*?)\)", block)
#         if title_match:
#             product["title"] = title_match.group(1).strip()
#             product["url"] = title_match.group(2).strip()
#         else:
#             product["title"] = block.split("\n")[0].strip()
#             product["url"] = None

#         # Image
#         img_match = re.search(r"!\[.*?\]\((.*?)\)", block)
#         product["image"] = img_match.group(1) if img_match else None

#         # Year
#         year_match = re.search(r"-\s*\*\*Year\*\*:\s*(\d{4})", block)
#         if not year_match:
#             year_match = re.search(r"\b(19|20)\d{2}\b", product["title"])
#         product["year"] = int(year_match.group(0)) if year_match else None

#         # Price
#         price_match = re.search(r"-\s*\*\*Price\*\*:\s*([\$\d,]+)", block)
#         if not price_match:
#             price_match = re.search(r"\$[\d,]+", block)
#         product["price"] = price_match.group(0) if price_match else None

#         # Location
#         loc_match = re.search(r"-\s*\*\*Location\*\*:\s*(.*)", block)
#         product["location"] = loc_match.group(1).strip() if loc_match else None

#         # Description
#         desc_match = re.search(r"-\s*\*\*Description\*\*:\s*(.*)", block, re.DOTALL)
#         product["description"] = desc_match.group(1).strip() if desc_match else None

#         products.append(product)

#     return {
#         "initial": initial,
#         "products": products,
#         "interaction": interaction
#     }


# def parse_chat_response(message: str):
#     # Normalize
#     message = message.strip()

#     # -------------------------------------------------------
#     # 1. Split by double newlines → this gives main 3 sections
#     # -------------------------------------------------------
#     sections = message.split("\n\n")

#     if len(sections) < 3:
#         # fallback if GPT returned something unusual
#         return {
#             "initial": message,
#             "products": [],
#             "interaction": ""
#         }

#     # FIRST PART → INITIAL message
#     initial = sections[0].strip()

#     # LAST PART → INTERACTION message
#     interaction = sections[-1].strip()

#     # EVERYTHING IN BETWEEN → PRODUCTS text
#     products_raw = sections[1:-1]

#     # -------------------------------------------------------
#     # 2. Parse product cards individually
#     # -------------------------------------------------------
#     product_cards = []
#     for block in products_raw:
#         block = block.strip()
#         product = {}

#         # Title + URL
#         title_match = re.search(r"\[(.*?)\]\((.*?)\)", block)
#         if title_match:
#             product["title"] = title_match.group(1)
#             product["url"] = title_match.group(2)
#         else:
#             # fallback title → first line
#             product["title"] = block.split("\n")[0].strip()
#             product["url"] = None

#         # Image (optional)
#         img_match = re.search(r"!\[.*?\]\((.*?)\)", block)
#         product["image"] = img_match.group(1) if img_match else None

#         # Bullet fields
#         fields = {}
#         for line in block.split("\n"):
#             bullet_match = re.match(r"\s*-\s*\*\*(.*?)\*\*:\s*(.*)", line)
#             if bullet_match:
#                 key = bullet_match.group(1).strip().lower()
#                 value = bullet_match.group(2).strip()
#                 fields[key] = value

#         product["fields"] = fields
#         product_cards.append(product)

#     return {
#         "initial": initial,
#         "products": product_cards,
#         "interaction": interaction
#     }




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
async def chat(request: ChatRequest, init_chat : InitChat = Depends(get_chat_instance)):
    try:
        logger.info(f"Received chat request: {request}")
        # session_id = request.session_id or uuid4()
        user_id = request.user_id
        # full_id = f"{user_id}_{session_id}"
        
   

        respond = await init_chat.chat(request.messages, user_id)

        return JSONResponse(status_code=200, content={
            "messages" : respond,
            "user_id" : user_id
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
