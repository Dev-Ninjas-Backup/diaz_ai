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
    

async def request_data(url : str):
    try:
        async with httpx.AsyncClient() as client:
            req = await client.get(url)
        return req.json()
    except Exception as e:
        raise(e)

