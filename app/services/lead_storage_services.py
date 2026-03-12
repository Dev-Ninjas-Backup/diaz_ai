import aiosqlite
from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone
from app.utils.logger import get_logger

logger = get_logger(__name__)

class LeadStorageService:
    def __init__(self, db_path: str = "leads.db"):
        self.db_path = db_path
    
    async def init_db(self):
        """Initialize the leads database table"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    product TEXT NOT NULL,
                    status TEXT DEFAULT 'not contacted',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, product)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    product TEXT NOT NULL,
                    status TEXT DEFAULT 'not contacted',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    UNIQUE(user_id, product)
                )
            """)
            await db.commit()
            logger.info("Leads database initialized")
    
    async def create_or_get_lead(
        self, 
        user_id: str, 
        name: str, 
        email: str, 
        product: str
    ) -> Dict:
        """
        Create a new lead or return existing one.
        If user_id + product exists, return existing lead.
        If product is different for same user, create new lead.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Check if lead exists for this user and product
            cursor = await db.execute(
                "SELECT * FROM leads WHERE user_id = ? AND product = ?",
                (user_id, product)
            )
            existing = await cursor.fetchone()
            
            if existing:
                logger.info(f"Lead already exists for user {user_id} and product {product}")
                return dict(existing)
            
            # Create new lead
            now = datetime.now(timezone.utc).isoformat()
            await db.execute(
                """
                INSERT INTO leads (user_id, name, email, product, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'not contacted', ?, ?)
                """,
                (user_id, name, email, product, now, now)
            )
            await db.commit()
            
            # Get the newly created lead
            cursor = await db.execute(
                "SELECT * FROM leads WHERE user_id = ? AND product = ?",
                (user_id, product)
            )
            new_lead = await cursor.fetchone()
            logger.info(f"New lead created for user {user_id} and product {product}")
            return dict(new_lead)
    
    async def get_all_leads(self) -> List[Dict]:
        """Get all leads from database"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM leads ORDER BY created_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def create_or_refresh_daily_lead(
        self,
        user_id: str,
        name: str,
        email: str,
        product: str,
        status: str = "not contacted"
    ) -> Dict:
        """
        Persist a lead in the 24-hour bucket.
        If the same user/product is seen again, extend the expiry window.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                "SELECT * FROM daily_leads WHERE user_id = ? AND product = ?",
                (user_id, product)
            )
            existing = await cursor.fetchone()

            now_dt = datetime.now(timezone.utc)
            now = now_dt.isoformat()
            expires_at = (now_dt + timedelta(hours=24)).isoformat()

            if existing:
                await db.execute(
                    """
                    UPDATE daily_leads
                    SET name = ?, email = ?, status = ?, updated_at = ?, expires_at = ?
                    WHERE user_id = ? AND product = ?
                    """,
                    (name, email, status, now, expires_at, user_id, product)
                )
                await db.commit()

                cursor = await db.execute(
                    "SELECT * FROM daily_leads WHERE user_id = ? AND product = ?",
                    (user_id, product)
                )
                refreshed = await cursor.fetchone()
                logger.info(f"Daily lead refreshed for user {user_id} and product {product}")
                return dict(refreshed)

            await db.execute(
                """
                INSERT INTO daily_leads (
                    user_id, name, email, product, status, created_at, updated_at, expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, email, product, status, now, now, expires_at)
            )
            await db.commit()

            cursor = await db.execute(
                "SELECT * FROM daily_leads WHERE user_id = ? AND product = ?",
                (user_id, product)
            )
            new_lead = await cursor.fetchone()
            logger.info(f"Daily lead created for user {user_id} and product {product}")
            return dict(new_lead)

    async def get_active_daily_leads(self) -> List[Dict]:
        """Return leads that are still inside the 24-hour daily window."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            now = datetime.now(timezone.utc).isoformat()
            cursor = await db.execute(
                """
                SELECT * FROM daily_leads
                WHERE expires_at > ?
                ORDER BY created_at DESC
                """,
                (now,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def delete_expired_daily_leads(self) -> int:
        """Remove daily leads that have passed their expiry timestamp."""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now(timezone.utc).isoformat()
            cursor = await db.execute(
                "DELETE FROM daily_leads WHERE expires_at <= ?",
                (now,)
            )
            await db.commit()
            return cursor.rowcount
    
    async def get_lead_by_id(self, lead_id: int) -> Optional[Dict]:
        """Get a specific lead by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM leads WHERE id = ?",
                (lead_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_lead_status(self, lead_id: int, status: str) -> Optional[Dict]:
        """Update the status of a lead"""
        if status not in ["not contacted", "contacted"]:
            raise ValueError("Status must be 'not contacted' or 'contacted'")
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Check if lead exists
            cursor = await db.execute(
                "SELECT * FROM leads WHERE id = ?",
                (lead_id,)
            )
            existing = await cursor.fetchone()
            
            if not existing:
                return None
            
            # Update status
            now = datetime.now(timezone.utc).isoformat()
            await db.execute(
                "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, lead_id)
            )
            await db.commit()
            
            # Get updated lead
            cursor = await db.execute(
                "SELECT * FROM leads WHERE id = ?",
                (lead_id,)
            )
            updated = await cursor.fetchone()
            logger.info(f"Lead {lead_id} status updated to {status}")
            return dict(updated)

    async def update_daily_lead_status(self, lead_id: int, status: str) -> Optional[Dict]:
        """Update the status of a daily lead."""
        if status not in ["not contacted", "contacted"]:
            raise ValueError("Status must be 'not contacted' or 'contacted'")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM daily_leads WHERE id = ?",
                (lead_id,)
            )
            existing = await cursor.fetchone()

            if not existing:
                return None

            now = datetime.now(timezone.utc).isoformat()
            await db.execute(
                "UPDATE daily_leads SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, lead_id)
            )
            await db.commit()

            cursor = await db.execute(
                "SELECT * FROM daily_leads WHERE id = ?",
                (lead_id,)
            )
            updated = await cursor.fetchone()
            logger.info(f"Daily lead {lead_id} status updated to {status}")
            return dict(updated)
    
    async def get_leads_by_user(self, user_id: str) -> List[Dict]:
        """Get all leads for a specific user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM leads WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
