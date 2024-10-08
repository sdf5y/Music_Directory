# %%
import numpy as np
import pandas as pd
import os
import re
from mutagen import File
from mutagen.mp3 import HeaderNotFoundError
from mutagen.wave import InvalidChunk
from mutagen.flac import FLACNoHeaderError  

# %%
dir_path = 'D:\\Music'

acceptable_file_types = ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.aiff', '.m4a')

# %%
file_data = []

for root, dirs, files in os.walk(dir_path):
    for file in files: 
        if file.endswith(acceptable_file_types):
            file_data.append(root + "\\" + file)

# %%
file_data = []

for root, dirs, files in os.walk(dir_path):
    for file in files:
        if file.endswith(acceptable_file_types):
            file_path = os.path.join(root, file)

            try:
                audio = File(file_path)

                if audio:
                    title = audio.get("TIT2", file)  
                    album = audio.get("TALB", "Unknown Album")  
                    artist = audio.get("TPE1", "Unknown Artist") 

                    file_info = {
                        "title": str(title),  
                        "album": str(album),
                        "artist": str(artist),
                        "root": root,
                        "file_name": file  
                    }

                    file_data.append(file_info)

            except HeaderNotFoundError:
                continue

            except InvalidChunk:
                continue

            except FLACNoHeaderError:
                continue

# %%
for file_info in file_data:
    print(file_info)

# %%
def clean_sort_key(text):
    if text is None:
        return ""
    return re.sub(r'\s', '', text).lower()

def sort_by(file_data, key="title"):
    if key == "title":
        file_data.sort(key=lambda x: clean_sort_key(x.get("title", "")) if isinstance(x, dict) else "")
    elif key == "album":
        file_data.sort(key=lambda x: clean_sort_key(x.get("album", "")) if isinstance(x, dict) else "")
    elif key == "artist":
        file_data.sort(key=lambda x: clean_sort_key(x.get("artist", "")) if isinstance(x, dict) else "")

# %%
print(len(file_data))
sort_by(file_data, key="title")

# %%
def clean_string(text):
    if text is None:
        return ""
    return re.sub(r'\W+', ' ', str(text)).strip().lower()

def search_by_keyword(file_data, keyword, key="title"):
    results = []
    cleaned_keywords = [clean_string(word) for word in keyword]
    
    for file_info in file_data:
        if isinstance(file_info, dict):
            cleaned_value = clean_string(file_info.get(key, ""))
            if any(keyword in cleaned_value for keyword in cleaned_keywords):
                results.append(file_info)
    return results

# %%
search_results = search_by_keyword(file_data, keyword = [ "cumberland gap"], key="title")

print(f"Total Search Results: {len(search_results)}")

for result in search_results:
    title = result.get("title", "Unknown Title")  
    artist = result.get("artist", "Unknown Artist") 
    root = result.get('root', 'Unknown folder')
    print(f"{title:<60} BY: {artist}  FOLDER: {root:>60}")


