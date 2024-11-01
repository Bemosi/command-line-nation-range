import requests
import time
import concurrent.futures

def get_nation_towns(nation_name):
    url = "https://api.earthmc.net/v3/aurora/nations"
    
    payload = {
        "query": [nation_name],
        "template": {
            "status": True,
            "towns": True
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            nations_data = response.json() 
            
            towns_list = []
            
            for nation in nations_data:
                if 'towns' in nation:
                    towns_data = nation['towns'] 
                    towns_list.extend([town['name'] for town in towns_data])
            
            if towns_list:
                return towns_list
            else:
                return []
        else:
            return []
    
    except requests.RequestException as e:
        return []

def get_town_homeblock(town_name):
    url = "https://api.earthmc.net/v3/aurora/towns"
    
    payload = {
        "query": [town_name],
        "template": {
            "coordinates": True,
            "status": True 
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            global towns_data
            towns_data = response.json() 
            if not towns_data: 
                return None
            
            for town in towns_data:
                if 'coordinates' in town and 'homeBlock' in town['coordinates']:
                    homeblock = town['coordinates']['homeBlock']  
                    townblocks = town['coordinates']['townBlocks']
                    return {'town': town_name, 'homeblock': homeblock, 'townblocks': townblocks, 'status': town['status']} 
                else:
                    return None
        else:
            return None
    
    except requests.RequestException:
        return None

def chunk_list(lst, chunk_size):
    """Yield successive chunks from lst."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def fetch_all_homeblocks(nation_name):
    towns = get_nation_towns(nation_name)

    if isinstance(towns, list) and towns:
        homeblocks = []
        start_time = time.time()  
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(get_town_homeblock, towns)  
            
            for result in results:
                if result:
                    homeblocks.append(result)
        
        end_time = time.time()  
        print(f"Total time taken for fetching homeblock data: {end_time - start_time:.2f} seconds")
        return homeblocks
    else:
        return []
