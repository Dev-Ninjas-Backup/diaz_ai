# from app.services.chat_storage_service import ChatStorageService
# from app.utils.logger import get_logger
# from openai import OpenAI
# from app.config import settings
# from datetime import datetime, timedelta, timezone
# from dateutil import parser

# logger = get_logger(__name__)
# storage = ChatStorageService()

# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# class LeadGenerator:

#     async def extract_lead_from_chats(self, user_id: str):
#         chats = await storage.get_user_chat_history(user_id)
#         if not chats:
#             return None
        
#         # Get current time in UTC
#         now = datetime.now(timezone.utc)
#         twenty_four_hours_ago = now - timedelta(hours=24)
        
#         recent_chats = []
#         for c in chats:
#             try:
#                 # Handle different timestamp formats
#                 if isinstance(c.timestamp, str):
#                     # If SQLite returned a string, parse it
#                     chat_time = parser.isoparse(c.timestamp)
#                 else:
#                     chat_time = c.timestamp
                
#                 # Make timezone-aware if naive
#                 if chat_time.tzinfo is None:
#                     chat_time = chat_time.replace(tzinfo=timezone.utc)
                
#                 if chat_time >= twenty_four_hours_ago:
#                     recent_chats.append(c)
                    
#             except Exception as e:
#                 logger.warning(f"Could not parse timestamp for chat: {e}")
#                 continue
        
#         if not recent_chats:
#             return None

#         # Build cleaned conversation text from last 24 hours only
#         whole_chat = "\n".join(
#             [f"{c.role.capitalize()}: {c.content}" for c in recent_chats]
#         )
        
#         logger.info(f"Processing {len(recent_chats)} messages from last 24 hours for user {user_id}")

#         prompt = f"""
# You are an AI lead extraction assistant.

# Your job is to read the conversation below and identify the ONE product, boat, or item 
# the user is MOST interested in buying.

# Conversation:
# {whole_chat}

# IMPORTANT RULES:
# - Return ONLY the product/boat name.
# - No explanations.
# - No quotes.
# - No JSON.
# """

#         try:
#             # Use chat.completions.create
#             response = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "You are a lead extraction assistant. Extract only the product name the user is most interested in."
#                     },
#                     {
#                         "role": "user",
#                         "content": prompt
#                     }
#                 ],
#                 temperature=0,  # For consistent extraction
#                 max_tokens=100  # Product names shouldn't be long
#             )

#             # Access the response correctly
#             product_name = response.choices[0].message.content.strip()

#             # Validate: reject garbage model responses
#             if not product_name or len(product_name) > 150:
#                 return None

#             return product_name

#         except Exception as e:
#             logger.error(f"OpenAI error for user {user_id}: {e}")
#             return None

#     async def generate_all_leads(self):
#         users = await storage.get_all_users()
#         leads = []

#         for user in users:
#             product = await self.extract_lead_from_chats(user.user_id)

#             if product:
#                 leads.append({
#                     "name": user.name,
#                     "email": user.email,
#                     "product": product
#                 })

#         return leads



from app.services.chat_storage_service import ChatStorageService
from app.services.lead_storage_services import LeadStorageService
from app.utils.logger import get_logger
from openai import OpenAI
from app.config import settings
from datetime import datetime, timedelta, timezone
from dateutil import parser

logger = get_logger(__name__)
storage = ChatStorageService()
lead_storage = LeadStorageService()

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class LeadGenerator:

    async def extract_lead_from_chats(self, user_id: str):
        chats = await storage.get_user_chat_history(user_id)
        if not chats:
            return None
        
        # Get current time in UTC
        now = datetime.now(timezone.utc)
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        recent_chats = []
        for c in chats:
            try:
                # Handle different timestamp formats
                if isinstance(c.timestamp, str):
                    # If SQLite returned a string, parse it
                    chat_time = parser.isoparse(c.timestamp)
                else:
                    chat_time = c.timestamp
                
                # Make timezone-aware if naive
                if chat_time.tzinfo is None:
                    chat_time = chat_time.replace(tzinfo=timezone.utc)
                
                if chat_time >= twenty_four_hours_ago:
                    recent_chats.append(c)
                    
            except Exception as e:
                logger.warning(f"Could not parse timestamp for chat: {e}")
                continue
        
        if not recent_chats:
            return None

        # Build cleaned conversation text from last 24 hours only
        whole_chat = "\n".join(
            [f"{c.role.capitalize()}: {c.content}" for c in recent_chats]
        )
        
        logger.info(f"Processing {len(recent_chats)} messages from last 24 hours for user {user_id}")

        prompt = f"""
You are an AI lead extraction assistant.

Your job is to read the conversation below and identify the ONE product, boat, or item 
the user is MOST interested in buying.

Conversation:
{whole_chat}

IMPORTANT RULES:
- Return ONLY the product/boat name.
- No explanations.
- No quotes.
- No JSON.
"""

        try:
            # Use chat.completions.create
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a lead extraction assistant. Extract only the product name the user is most interested in."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # For consistent extraction
                max_tokens=100  # Product names shouldn't be long
            )

            # Access the response correctly
            product_name = response.choices[0].message.content.strip()

            # Validate: reject garbage model responses
            if not product_name or len(product_name) > 150:
                return None

            return product_name

        except Exception as e:
            logger.error(f"OpenAI error for user {user_id}: {e}")
            return None

    async def generate_all_leads(self):
        """
        Generate leads from all users' chat history.
        Save them to the all-time table and refresh them in the 24-hour table.
        """
        # Initialize database if not exists
        await lead_storage.init_db()
        await lead_storage.delete_expired_daily_leads()

        users = await storage.get_all_users()
        leads = []

        for user in users:
            product = await self.extract_lead_from_chats(user.user_id)

            if product:
                try:
                    all_time_lead = await lead_storage.create_or_get_lead(
                        user_id=user.user_id,
                        name=user.name,
                        email=user.email,
                        product=product
                    )
                    daily_lead = await lead_storage.create_or_refresh_daily_lead(
                        user_id=user.user_id,
                        name=user.name,
                        email=user.email,
                        product=product,
                        status=all_time_lead["status"]
                    )
                    leads.append({
                        "all_time": all_time_lead,
                        "daily": daily_lead
                    })
                except Exception as e:
                    logger.error(f"Error saving lead for user {user.user_id}: {e}")
                    leads.append({
                        "user_id": user.user_id,
                        "name": user.name,
                        "email": user.email,
                        "product": product,
                        "status": "not contacted",
                        "error": str(e)
                    })

        return leads
