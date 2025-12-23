import os
from typing import Optional, Dict, Any, List
import pandas as pd
from openai import OpenAI
from sqlalchemy import create_engine, text
from app.db.boats_db import boats_session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

if not client.api_key:
    raise ValueError("OPENAI_API_KEY not found. Please add it to your .env file")


class SQLiteQueryAgent:
    """SQLite-based query agent for AI natural language search on boats table."""
    
    def __init__(self, db_path: str, table_name: str ):
        self.db_path = db_path
        self.table_name = table_name
        self.engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
        self._validate_table()
        
    def _validate_table(self):
        """Validate that the boats table exists."""
        with self.engine.connect() as conn:
            result = conn.execute(text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.table_name}'"
            ))
            if not result.fetchone():
                raise ValueError(f"Table '{self.table_name}' not found in database")
    
    def execute_query(self, table_name: str, user_query: str, limit: int = 10) -> Dict[str, Any]:
        """Execute natural language query using SQL generation."""
        if not user_query.strip():
            return {"success": False, "error": "Query is empty", "data": None, "count": 0}

        try:
            # Generate SQL query using OpenAI
            sql_query = self._generate_sql(table_name, user_query, limit)
            
            # Execute SQL query safely
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                columns = result.keys()
                rows = result.fetchall()
                
                # Convert to list of dicts
                data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "success": True,
                "data": data,
                "error": None,
                "count": len(data),
                "sql_query": sql_query  # For debugging
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Query execution failed: {str(e)}",
                "data": None,
                "count": 0
            }

    def _generate_sql(self, table_name: str, user_query: str, limit: int) -> str:
        """Generate SQL query using OpenAI (safer than code execution)."""
        
        system_prompt = f"""You are a SQL expert. Generate SQLite queries for a boat database.

Table: {self.table_name}
Columns:
- document_id (TEXT, PRIMARY KEY) - Unique identifier
- source (TEXT) - Data source
- make (TEXT) - Boat manufacturer
- model (TEXT) - Boat model
- model_year (INTEGER) - Year of manufacture
- price (FLOAT) - Boat price
- nominal_length (FLOAT) - Nominal length in feet
- length_overall (FLOAT) - Overall length in feet
- beam (FLOAT) - Beam width in feet
- number_of_engines (INTEGER) - Number of engines
- total_engine_power (FLOAT) - Total engine power
- location (TEXT) - Full location description
- city (TEXT) - City location
- general_description (TEXT) - General boat description
- additional_description (TEXT) - Additional details
- engines (TEXT) - Engine information
- images (TEXT) - Image URLs
- link (TEXT) - Listing link

RULES:
1. Return ONLY valid SQLite query, no explanations, no markdown
2. Always SELECT * to keep all columns
3. Use proper numeric comparisons (no CAST needed for FLOAT/INTEGER columns)
4. Use LOWER() for case-insensitive text searches with LIKE
5. Handle NULL values with IS NOT NULL when needed
6. Add ORDER BY for rankings (e.g., ORDER BY price DESC for expensive boats)
7. Never include LIMIT in your query (it will be added automatically)
8. For text searches in descriptions, use: LOWER(general_description) LIKE '%keyword%'

Example queries:
- "boats under 500000" → SELECT * FROM {self.table_name} WHERE price < 500000
- "boats in Miami" → SELECT * FROM {self.table_name} WHERE LOWER(city) LIKE '%miami%' OR LOWER(location) LIKE '%miami%'
- "2024 Freeman boats" → SELECT * FROM {self.table_name} WHERE model_year = 2024 AND LOWER(make) LIKE '%freeman%'
- "boats longer than 40 feet" → SELECT * FROM {self.table_name} WHERE length_overall > 40
- "most expensive boats" → SELECT * FROM {self.table_name} ORDER BY price DESC
- "boats with 2 engines" → SELECT * FROM {self.table_name} WHERE number_of_engines = 2
"""

        user_prompt = f"User Query: {user_query}\n\nGenerate the SQL query:"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up the response (remove markdown, extra spaces)
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        sql_query = ' '.join(sql_query.split())  # Remove extra whitespace
        
        # Add LIMIT if not present
        if 'LIMIT' not in sql_query.upper():
            sql_query += f" LIMIT {limit}"
        
        return sql_query
    
    def __del__(self):
        """Dispose of the engine on cleanup."""
        if hasattr(self, 'engine'):
            self.engine.dispose()