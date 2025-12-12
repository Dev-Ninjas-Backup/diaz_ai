from app.db.database import async_session
from app.models.user import User
from app.models.chat_messages import ChatMessage
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ChatStorageService:

    async def save_user(self, user_id: str, name: str, email: str):
        try:
            async with async_session() as session:
                result = await session.execute(select(User).where(User.user_id == user_id))
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    # Update name/email if changed
                    existing_user.name = name
                    existing_user.email = email
                else:
                    new_user = User(user_id=user_id, name=name, email=email)
                    session.add(new_user)

                await session.commit()
                logger.info(f"Saved/updated user: {user_id}")
        except Exception as e:
            logger.error(f"Error saving user {user_id}: {e}")
            raise

    async def save_chat_message(self, user_id: str, role: str, content: str):
        try:
            async with async_session() as session:
                msg = ChatMessage(
                    user_id=user_id,
                    role=role,
                    content=content,
                    timestamp=datetime.now(timezone.utc)  # Explicit UTC timestamp
                )
                session.add(msg)
                await session.commit()
                logger.debug(f"Saved chat message for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving chat message for {user_id}: {e}")
            raise

    async def get_user_chat_history(self, user_id: str):
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(ChatMessage)
                    .where(ChatMessage.user_id == user_id)
                    .order_by(ChatMessage.timestamp)
                )
                # Convert to list of dicts to avoid detached instance issues
                messages = result.scalars().all()
                
                # Create detached copies with all data loaded
                return [
                    type('ChatMessage', (), {
                        'user_id': msg.user_id,
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp
                    })() for msg in messages
                ]
        except Exception as e:
            logger.error(f"Error fetching chat history for {user_id}: {e}")
            return []
    
    async def get_all_users(self):
        try:
            async with async_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                
                # Create detached copies
                return [
                    type('User', (), {
                        'user_id': user.user_id,
                        'name': user.name,
                        'email': user.email
                    })() for user in users
                ]
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []