import json
import httpx

def load_json(folder_loc : str, index):
    try:
        with open(f"{folder_loc}boat_data_{index}.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except Exception as e:
        raise(e)

def save_json(json_data,index, folder_loc : str):
    try:
        with open(f"{folder_loc}/boat_data_{index}.json", "w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=4)
    except Exception as e:
        raise(e)
    

# async def request_data(url : str):
#     try:
#         async with httpx.AsyncClient() as client:
#             req = await client.get(url)
#         return req.json()
#     except Exception as e:
#         raise(e)

import httpx
import asyncio

async def request_data(url, retries=5):
    timeout = httpx.Timeout(40.0)

    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:  # Added verify=False
                print(f"🔗 Attempting to connect to: {url}")
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True  # Follow redirects
                )
                response.raise_for_status()
                return response.json()

        except httpx.ConnectError as e:
            print(f"🔌 Connection failed on attempt {attempt+1}/{retries}: {e}")
            await asyncio.sleep(3 * (attempt + 1))  # Exponential backoff

        except httpx.ReadTimeout:
            print(f"⏳ Timeout on attempt {attempt+1}/{retries} → retrying...")
            await asyncio.sleep(2)

        except httpx.HTTPStatusError as e:
            print(f"📛 HTTP error {e.response.status_code} on attempt {attempt+1}/{retries}")
            await asyncio.sleep(2)

        except Exception as e:
            print(f"⚠️ Error on attempt {attempt+1}/{retries}: {type(e).__name__} - {e}")
            await asyncio.sleep(2)

    raise Exception(f"❌ Failed after {retries} retries for URL: {url}")