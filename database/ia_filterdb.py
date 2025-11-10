# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging
from struct import pack
import re
import base64
from html import unescape
from datetime import datetime
from pyrogram.file_id import FileId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from info import FILE_DB_URI, SEC_FILE_DB_URI, DATABASE_NAME, COLLECTION_NAME, MULTIPLE_DATABASE, USE_CAPTION_FILTER, MAX_B_TN
from utils import get_settings, save_group_settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ------------------ Database Connections ------------------
client = MongoClient(FILE_DB_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]

sec_client = MongoClient(SEC_FILE_DB_URI)
sec_db = sec_client[DATABASE_NAME]
sec_col = sec_db[COLLECTION_NAME]


# ------------------ Save File Function ------------------
async def save_file(media):
    """Save file in database.
    Take caption as file name if available, else use original file name.
    """

    file_id, file_ref = unpack_new_file_id(media.file_id)

    # Original file name cleanup
    original_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    unwanted_chars = ['[', ']', '(', ')']
    for char in unwanted_chars:
        original_name = original_name.replace(char, '')
    original_name = ' '.join(filter(lambda x: not x.startswith('@'), original_name.split())).strip()

    # ------------------ Caption-based Name Extraction ------------------
    if media.caption and media.caption.html:
        caption_text = unescape(media.caption.html)
        caption_text = re.sub(r'<.*?>', '', caption_text)  # Remove HTML tags
        caption_text = caption_text.strip()

        # Try to extract movie/file-style name (with extension)
        match = re.search(r'([A-Za-z0-9].*\.(mkv|mp4|avi|mov|m4v|srt|zip|rar))', caption_text)
        if match:
            file_name = match.group(1).strip()
        else:
            file_name = caption_text.strip()
    else:
        file_name = original_name

    # ------------------ Cleanup Final File Name ------------------
    file_name = re.sub(r'@\S+', '', file_name)  # remove @tags
    file_name = re.sub(r'[<>:"/\\|?*]', '', file_name)  # illegal FS chars
    file_name = re.sub(r'\s+', ' ', file_name).strip()

    # ------------------ Caption Fallback ------------------
    if media.caption and media.caption.html:
        caption_text_final = media.caption.html
    else:
        caption_text_final = f"<code>{file_name}</code>"

    # ------------------ Build File Record ------------------
    file_doc = {
        'file_id': file_id,
        'file_name': file_name,
        'file_size': media.file_size,
        'caption': caption_text_final
    }

    found_by_name = {'file_name': file_name}
    found_by_id = {'file_id': file_id}

    # ------------------ Duplicate Check ------------------
    if col.find_one(found_by_name) or col.find_one(found_by_id):
        print(f"{file_name} is already saved.")
        return False, 0

    if MULTIPLE_DATABASE:
        if sec_col.find_one(found_by_id) or sec_col.find_one(found_by_name):
            print(f"{file_name} is already saved.")
            return False, 0

        result = db.command('dbstats')
        data_size = result['dataSize']

        try:
            if data_size > 503316480:  # ~480MB limit
                sec_col.insert_one(file_doc)
                print(f"{file_name} successfully saved to secondary DB.")
            else:
                col.insert_one(file_doc)
                print(f"{file_name} successfully saved.")
            return True, 1
        except DuplicateKeyError:
            print(f"{file_name} is already saved.")
            return False, 0
    else:
        try:
            col.insert_one(file_doc)
            print(f"{file_name} successfully saved.")
            return True, 1
        except DuplicateKeyError:
            print(f"{file_name} is already saved.")
            return False, 0


# ------------------ Search Functions ------------------
async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset, total_results)"""
    if chat_id is not None:
        settings = await get_settings(int(chat_id))
        try:
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)
        except KeyError:
            await save_group_settings(int(chat_id), 'max_btn', False)
            settings = await get_settings(int(chat_id))
            if settings['max_btn']:
                max_results = 10
            else:
                max_results = int(MAX_B_TN)

    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if MULTIPLE_DATABASE:
        cursor1 = col.find(filter).sort('$natural', -1)
        cursor2 = sec_col.find(filter).sort('$natural', -1)
        files_ = list(cursor1) + list(cursor2)
    else:
        cursor = col.find(filter).sort('$natural', -1)
        files_ = list(cursor)

    total_results = len(files_)
    files = files_[offset:offset + max_results]
    next_offset = offset + max_results if offset + max_results < total_results else ""

    return files, next_offset, total_results


async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, total_results)"""
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if MULTIPLE_DATABASE:
        files1 = list(col.find(filter))
        files2 = list(sec_col.find(filter))
        files = files1 + files2
        total_results = len(files)
    else:
        files = list(col.find(filter))
        total_results = len(files)

    return files, total_results


# ------------------ File Details ------------------
async def get_file_details(query):
    """Get file details; fallback to file_name if caption missing."""
    filter = {'file_id': query}
    filedetails = col.find_one(filter) or sec_col.find_one(filter)
    if not filedetails:
        return None

    caption = filedetails.get('caption')
    file_name = filedetails.get('file_name')
    filedetails['display_name'] = caption if caption and caption.strip() else file_name
    return filedetails


# ------------------ ID Encode/Decode Helpers ------------------
def encode_file_id(s: bytes) -> str:
    r, n = b"", 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    """Return (file_id, file_ref)"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack("<iiqq", int(decoded.file_type), decoded.dc_id, decoded.media_id, decoded.access_hash)
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref

# ------------------ Admin Movie Search ------------------
async def get_movies_by_name(query, limit=10):
    """Search for movies by name (compatibility function)"""
    return await Media().search_movie_files(query, limit)

# ------------------ Admin Movie Search ------------------
class Media:
    def __init__(self):
        self.collection = col
        self.sec_collection = sec_col

    def search_movie_files(self, query, limit=10):
        """Search for movie files by name or caption - SYNC version for PyMongo"""
        try:
            # Create a case-insensitive regex pattern for searching
            pattern = {"$regex": query, "$options": "i"}
            
            # Search in both file_name and caption fields
            filter_query = {
                "$or": [
                    {"file_name": pattern},
                    {"caption": pattern}
                ]
            }
            
            # Find documents matching the query from both collections
            results = []
            
            # Search in primary collection
            primary_results = list(self.collection.find(filter_query).limit(limit))
            results.extend(primary_results)
            
            # If we need more results and have multiple databases, search secondary
            if MULTIPLE_DATABASE and len(results) < limit:
                remaining = limit - len(results)
                secondary_results = list(self.sec_collection.find(filter_query).limit(remaining))
                results.extend(secondary_results)
            
            return results[:limit]  # Ensure we don't exceed limit
            
        except Exception as e:
            logger.error(f"Error searching movie files: {e}")
            return []

# Compatibility function
def get_movies_by_name(query, limit=10):
    """Search for movies by name - SYNC version"""
    media = Media()
    return media.search_movie_files(query, limit)
