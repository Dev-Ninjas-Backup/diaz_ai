import pandas as pd
import openai
import json
import os
import ast
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found. Please add it to your .env file")


class CSVQueryAgent:
    def __init__(self, csv_path: str):
        """Initialize the CSV Query Agent with a CSV file."""
        self.csv_path = csv_path
        try:
            self.df = self.load_and_clean_csv()
        except Exception as e:
            raise Exception(f"Failed to load CSV file '{csv_path}': {str(e)}")
        
    def load_and_clean_csv(self) -> pd.DataFrame:
        """Load and clean the CSV file."""
        df = pd.read_csv(self.csv_path)
        
        # Columns that should always remain as strings (not converted to numeric)
        string_columns = ['Source', 'DocumentID', 'BeamMeasure', 'TotalEnginePowerQuantity', 
                          'BoatLocation', 'Model', 'Engines', 'MakeString', 'LengthOverall', 
                          'NominalLength', 'GeneralBoatDescription', 'AdditionalDetailDescription', 
                          'Images', 'Link']
        
        # Auto-clean numeric columns (only for columns that are clearly numeric)
        numeric_columns = ['Price', 'ModelYear']  # Only convert explicitly numeric columns
        
        for col in df.columns:
            # Skip string columns and already numeric columns
            if col in string_columns:
                continue
            if col in numeric_columns:
                # Convert explicitly numeric columns
                if df[col].dtype == 'object':
                    try:
                        # Clean and convert to numeric
                        cleaned = df[col].astype(str).str.replace('[^0-9.]', '', regex=True)
                        numeric_col = pd.to_numeric(cleaned, errors='coerce')
                        df[col] = numeric_col
                    except:
                        pass
        
        # Ensure Model and other string columns remain as strings
        # Convert to string, preserving all values (both numeric-looking and text strings)
        for col in string_columns:
            if col in df.columns:
                # Convert entire column to string type to preserve all values as strings
                df[col] = df[col].astype(str)
                # Replace pandas NaN string representation with None
                df.loc[df[col] == 'nan', col] = None
        
        return df
    
    def get_dataframe_context(self, df: Optional[pd.DataFrame] = None) -> str:
        """Generate context about the dataframe for the LLM with ALL columns."""
        if df is None:
            df = self.df
        
        context = f"""
Dataset Information:
- Total Rows: {len(df)}
- ALL Columns (use ALL of these for search): {', '.join(df.columns.tolist())}

IMPORTANT: You must search ONLY within this CSV data. Use ALL columns as input for filtering and searching.

Column Details (ALL columns available for search):
"""
        for col in df.columns:
            dtype = df[col].dtype
            null_count = df[col].isna().sum()
            
            context += f"\n{col} ({dtype}):"
            context += f"\n  - Non-null values: {len(df) - null_count}"
            
            if pd.api.types.is_numeric_dtype(df[col]):
                context += f"\n  - Range: {df[col].min()} to {df[col].max()}"
                context += f"\n  - Mean: {df[col].mean():.2f}"
            else:
                unique_count = df[col].nunique()
                context += f"\n  - Unique values: {unique_count}"
                if unique_count <= 20:
                    sample_values = df[col].dropna().unique()[:20]
                    context += f"\n  - Sample values: {', '.join(map(str, sample_values))}"
        
        # Include sample data with ALL columns (limit size)
        # sample_df = df.head(2)  # Only 2 rows to reduce context size
        # # Truncate long text columns in sample
        # for col in sample_df.columns:
        #     if sample_df[col].dtype == 'object':
        #         sample_df[col] = sample_df[col].astype(str).str[:200]  # Limit to 200 chars per cell
        sample_df = df.head(2).copy()  # <-- copy() prevents SettingWithCopyWarning

        # Truncate long text columns without modifying original df
        for col in sample_df.columns:
            if sample_df[col].dtype == 'object':
                sample_df.loc[:, col] = sample_df[col].astype(str).str[:200]  # Limit to 200 chars per cell
                
        context += f"\n\nSample Data (first 2 rows with ALL columns):\n{sample_df.to_string()}"
        return context
    
    def generate_code(self, user_query: str, df: Optional[pd.DataFrame] = None) -> str:
        """Use OpenAI to generate pandas code based on user query.
        
        If df is provided, uses that dataframe for context instead of self.df.
        """
        system_prompt = """You are a Python pandas expert. Generate ONLY executable Python code using pandas to answer the user's question.

CRITICAL RULES:
1. The dataframe is already loaded as 'df'
2. You MUST search ONLY within the CSV data provided - NEVER use external data or knowledge
3. Use ALL available columns from the CSV for filtering and searching (Source, DocumentID, BeamMeasure, TotalEnginePowerQuantity, Price, BoatLocation, Model, Engines, ModelYear, MakeString, LengthOverall, NominalLength, GeneralBoatDescription, AdditionalDetailDescription, Images, Link)
4. ALWAYS assign your result to a variable named 'result'
5. ALWAYS output ALL columns from the result DataFrame - do not filter columns
6. Return ONLY the code, no explanations or markdown
7. Use pandas operations efficiently
8. Handle potential errors gracefully
9. Keep code concise and readable

MANDATORY OUTPUT FORMAT:
- ALWAYS end your code with: result = <your_filtered_dataframe>
- DO NOT filter columns - keep ALL columns in the result
- The variable 'result' MUST be a DataFrame containing ALL columns from the filtered results
- Do NOT use print() in your code - just assign to 'result'

Example queries and responses:
Query: "Show me boats under 500000"
Code: result = df[df['Price'] < 500000]

Query: "Find boats with ModelYear 2024"
Code: result = df[df['ModelYear'] == 2024]

Query: "Show me top 5 most expensive boats"
Code: result = df.nlargest(5, 'Price')

Query: "Search for boats with 'Freeman' in any column"
Code: mask = df.astype(str).apply(lambda x: x.str.contains('Freeman', case=False, na=False)).any(axis=1); result = df[mask]

Query: "Find boats in Miami"
Code: result = df[df['BoatLocation'].astype(str).str.contains('Miami', case=False, na=False)]
"""
        
        user_prompt = f"""Dataset Context (ALL columns available - search ONLY in this CSV data):
{self.get_dataframe_context(df)}

User Query: {user_query}

IMPORTANT: 
- Search STRICTLY within the CSV data provided above
- Use ALL columns as input for filtering/searching
- Output ALL columns in the result (do not filter columns)
- Assign result to variable 'result' without printing

Generate Python pandas code to answer this query. Return ONLY the code."""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
        except openai.APIError as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
        
        code = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        code = code.replace('```python', '').replace('```', '').strip()
        return code
    
    def parse_string_to_object(self, value: Any) -> Any:
        """Parse string representations of Python objects (lists, dicts) to actual objects."""
        if pd.isna(value) or value is None:
            return None
        
        # If it's already a dict or list, return as is
        if isinstance(value, (dict, list)):
            return value
        
        # Convert to string if not already
        str_value = str(value).strip()
        
        # Skip empty strings
        if not str_value or str_value == 'nan':
            return None
        
        # Check if it looks like a Python object representation
        # Must start with { or [ (possibly with quotes)
        str_value_clean = str_value
        if (str_value.startswith("'") and str_value.endswith("'")) or \
           (str_value.startswith('"') and str_value.endswith('"')):
            str_value_clean = str_value[1:-1].strip()
        
        # Check if it's a dict or list representation
        is_dict_like = str_value_clean.startswith('{') and str_value_clean.endswith('}')
        is_list_like = str_value_clean.startswith('[') and str_value_clean.endswith(']')
        
        if not (is_dict_like or is_list_like):
            # Not a Python object representation, return as string
            return value
        
        # Try to parse string representations of Python objects
        try:
            # Use ast.literal_eval for safe parsing of Python literals
            parsed = ast.literal_eval(str_value_clean)
            return parsed
        except (ValueError, SyntaxError, TypeError) as e:
            # If parsing fails, return the original string value
            return value
    
    def format_output_to_dict(self, result: pd.DataFrame) -> list:
        """Convert DataFrame to list of dictionaries."""
        # Convert to dictionary with records orientation
        records = result.to_dict(orient='records')
        
        # Clean up records: replace NaN/NaT with None and parse string objects
        def clean_value(value):
            if pd.isna(value):
                return None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                return str(value)
            elif isinstance(value, (int, float)) and pd.isna(value):
                return None
            
            # Try to parse string representations of Python objects (lists, dicts)
            parsed_value = self.parse_string_to_object(value)
            return parsed_value
        
        cleaned_records = []
        for record in records:
            cleaned_record = {k: clean_value(v) for k, v in record.items()}
            cleaned_records.append(cleaned_record)
        
        return cleaned_records
    
    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filter parameters to dataframe. Filters are prioritized and applied first."""
        filtered_df = df.copy()
        
        # Boat Type - map to GeneralBoatDescription
        if filters.get('boat_type'):
            boat_type = str(filters['boat_type']).strip()
            if boat_type:
                filtered_df = filtered_df[
                    filtered_df['GeneralBoatDescription'].astype(str).str.contains(boat_type, case=False, na=False)
                ]
        
        # Make - map to MakeString
        if filters.get('make'):
            make = str(filters['make']).strip()
            if make:
                filtered_df = filtered_df[
                    filtered_df['MakeString'].astype(str).str.contains(make, case=False, na=False)
                ]
        
        # Build Year (ModelYear) - range filter
        if filters.get('build_year_min') is not None:
            try:
                min_year = int(filters['build_year_min'])
                filtered_df = filtered_df[pd.to_numeric(filtered_df['ModelYear'], errors='coerce') >= min_year]
            except (ValueError, TypeError):
                pass
        
        if filters.get('build_year_max') is not None:
            try:
                max_year = int(filters['build_year_max'])
                filtered_df = filtered_df[pd.to_numeric(filtered_df['ModelYear'], errors='coerce') <= max_year]
            except (ValueError, TypeError):
                pass
        
        # Model - search in both boat Model column and Engines column (for engine makes/models)
        if filters.get('model'):
            model = str(filters['model']).strip()
            if model:
                # Search in boat Model column
                boat_model_mask = filtered_df['Model'].astype(str).str.contains(model, case=False, na=False)
                # Also search in Engines column (for engine makes/models like "Yamaha")
                engine_mask = filtered_df['Engines'].astype(str).str.contains(model, case=False, na=False)
                # Combine both searches (OR logic - match if found in either column)
                combined_mask = boat_model_mask | engine_mask
                filtered_df = filtered_df[combined_mask]
        
        # Price Range
        if filters.get('price_min') is not None:
            try:
                min_price = float(filters['price_min'])
                filtered_df = filtered_df[pd.to_numeric(filtered_df['Price'], errors='coerce') >= min_price]
            except (ValueError, TypeError):
                pass
        
        if filters.get('price_max') is not None:
            try:
                max_price = float(filters['price_max'])
                filtered_df = filtered_df[pd.to_numeric(filtered_df['Price'], errors='coerce') <= max_price]
            except (ValueError, TypeError):
                pass
        
        # Length Range - check both LengthOverall and NominalLength (use either column)
        length_min = filters.get('length_min')
        length_max = filters.get('length_max')
        if length_min is not None or length_max is not None:
            try:
                length_mask = pd.Series([True] * len(filtered_df), index=filtered_df.index)
                
                if length_min is not None:
                    min_len = float(length_min)
                    # Check if EITHER LengthOverall OR NominalLength is >= min_len
                    min_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                    if 'LengthOverall' in filtered_df.columns:
                        min_mask = min_mask | (pd.to_numeric(filtered_df['LengthOverall'], errors='coerce') >= min_len)
                    if 'NominalLength' in filtered_df.columns:
                        min_mask = min_mask | (pd.to_numeric(filtered_df['NominalLength'], errors='coerce') >= min_len)
                    length_mask = length_mask & min_mask
                
                if length_max is not None:
                    max_len = float(length_max)
                    # Check if EITHER LengthOverall OR NominalLength is <= max_len
                    max_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                    if 'LengthOverall' in filtered_df.columns:
                        max_mask = max_mask | (pd.to_numeric(filtered_df['LengthOverall'], errors='coerce') <= max_len)
                    if 'NominalLength' in filtered_df.columns:
                        max_mask = max_mask | (pd.to_numeric(filtered_df['NominalLength'], errors='coerce') <= max_len)
                    length_mask = length_mask & max_mask
                
                filtered_df = filtered_df[length_mask]
            except (ValueError, TypeError):
                pass
        
        # Beam Size (BeamMeasure)
        if filters.get('beam_min') is not None:
            try:
                min_beam = float(filters['beam_min'])
                filtered_df = filtered_df[pd.to_numeric(filtered_df['BeamMeasure'], errors='coerce') >= min_beam]
            except (ValueError, TypeError):
                pass
        
        if filters.get('beam_max') is not None:
            try:
                max_beam = float(filters['beam_max'])
                filtered_df = filtered_df[pd.to_numeric(filtered_df['BeamMeasure'], errors='coerce') <= max_beam]
            except (ValueError, TypeError):
                pass
        
        # Number of Engine (Engines)
        if filters.get('number_of_engine'):
            engine_count = str(filters['number_of_engine']).strip()
            if engine_count:
                filtered_df = filtered_df[
                    filtered_df['Engines'].astype(str).str.contains(engine_count, case=False, na=False)
                ]
        
        # Number of Cabin - check if column exists
        if filters.get('number_of_cabin') and 'Cabin' in filtered_df.columns:
            cabin_count = str(filters['number_of_cabin']).strip()
            if cabin_count:
                filtered_df = filtered_df[
                    filtered_df['Cabin'].astype(str).str.contains(cabin_count, case=False, na=False)
                ]
        
        # Number of Heads - check if column exists
        if filters.get('number_of_heads') and 'Heads' in filtered_df.columns:
            heads_count = str(filters['number_of_heads']).strip()
            if heads_count:
                filtered_df = filtered_df[
                    filtered_df['Heads'].astype(str).str.contains(heads_count, case=False, na=False)
                ]
        
        # Additional Unit - map to AdditionalDetailDescription
        if filters.get('additional_unit'):
            additional_unit = str(filters['additional_unit']).strip()
            if additional_unit:
                filtered_df = filtered_df[
                    filtered_df['AdditionalDetailDescription'].astype(str).str.contains(additional_unit, case=False, na=False)
                ]
        
        return filtered_df
    
    def execute_query(self, user_query: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a natural language query on the CSV and return structured response.
        
        Both query and filters are optional:
        - If only filters provided: returns filtered results without AI query
        - If only query provided: runs AI query on full dataset
        - If both provided: applies filters first, then runs AI query on filtered results
        - Filters are applied FIRST (prioritized) before the AI query runs.
        """
        try:
            # PRIORITY 1: Apply filters first if provided
            df = self.df.copy()
            if filters:
                df = self.apply_filters(df, filters)
            
            # If filters resulted in empty dataframe, return early
            if len(df) == 0:
                return {
                    "success": True,
                    "data": [],
                    "error": None,
                    "count": 0
                }
            
            # If no query provided, just return the filtered results
            if not user_query or not user_query.strip():
                try:
                    # Convert filtered dataframe to list of dictionaries
                    data = self.format_output_to_dict(df)
                    return {
                        "success": True,
                        "data": data,
                        "error": None,
                        "count": len(data)
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"JSON conversion failed: {str(e)}",
                        "data": None,
                        "count": 0
                    }
            
            # PRIORITY 2: Generate code using OpenAI (on filtered dataframe)
            try:
                code = self.generate_code(user_query, df=df)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to generate code: {str(e)}",
                    "data": None,
                    "count": 0
                }
            
            if not code or not code.strip():
                return {
                    "success": False,
                    "error": "Generated code is empty",
                    "data": None,
                    "count": 0
                }
            
            # Execute the generated code on the FILTERED dataframe
            local_vars = {'df': df, 'pd': pd}
            
            try:
                # Execute code in isolated namespace
                exec(code, local_vars)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Code execution failed: {str(e)}",
                    "data": None,
                    "count": 0
                }
            
            # Try to capture 'result' variable if it exists and format it
            if 'result' in local_vars:
                result = local_vars['result']
                if isinstance(result, pd.DataFrame) and len(result) > 0:
                    try:
                        # Convert to list of dictionaries
                        data = self.format_output_to_dict(result)
                        return {
                            "success": True,
                            "data": data,
                            "error": None,
                            "count": len(data)
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"JSON conversion failed: {str(e)}",
                            "data": None,
                            "count": 0
                        }
                elif isinstance(result, pd.DataFrame) and len(result) == 0:
                    return {
                        "success": True,
                        "data": [],
                        "error": None,
                        "count": 0
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Result is not a DataFrame. Type: {type(result)}",
                        "data": None,
                        "count": 0
                    }
            else:
                return {
                    "success": False,
                    "error": "No result variable found in generated code",
                    "data": None,
                    "count": 0
                }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return {
                "success": False,
                "error": f"{str(e)}: {error_details}",
                "data": None,
                "count": 0
            }

