"""
COMP 593 - Final Project
Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.
Usage:
  python apod_desktop.py [apod_date]
Parameters:
  apod_date = APOD date (format: YYYY-MM-DD)
"""
from datetime import date
import sys
import os
import re
import hashlib
import sqlite3
import requests
import ctypes
import apod_api
import logging

# Full paths of the image cache folder and database
script_dir = os.path.dirname(os.path.abspath(__file__))
image_cache_dir = os.path.join(script_dir, 'images')
image_cache_db = os.path.join(image_cache_dir, 'image_cache.db')

def main():
    """Main function to handle command line execution and setting APOD as desktop background."""
    apod_date = get_apod_date()
    init_apod_cache()
    apod_id = add_apod_to_cache(apod_date)
    apod_info = get_apod_info(apod_id)

    if apod_id != 0 and apod_info:
        set_desktop_background_image(apod_info['file_path'])
    else:
        print("Error: Unable to set APOD as desktop background.")

def get_apod_date():
    """Gets the APOD date from command line or defaults to today's date.
    Returns:
        date: APOD date
    """
    if len(sys.argv) > 1:
        try:
            return date.fromisoformat(sys.argv[1])
        except ValueError:
            print("Error: Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
    return date.today()

def init_apod_cache():
    """Initializes the image cache directory and database."""
    # Check if the directory exists, if not create it
    if not os.path.exists(image_cache_dir):
        os.makedirs(image_cache_dir)
    
    # Check if the database file exists
    if not os.path.exists(image_cache_db):
        print(f"Database not found. Creating new database at: {image_cache_db}")
        try:
            # Create the database and tables
            conn = sqlite3.connect(image_cache_db)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS apod (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
            print("Database and table created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating database: {e}")
    else:
        print(f"Database already exists at: {image_cache_db}")

def add_apod_to_cache(apod_date):
    """Adds the APOD image from a specified date to the cache.
    Args:
        apod_date (date): Date of the APOD image
    Returns:
        int: Record ID of the APOD in the image cache DB
    """
    if isinstance(apod_date, str):
        try:
            apod_date = date.fromisoformat(apod_date)
        except ValueError:
            raise ValueError("Invalid date format")

    apod_info = apod_api.get_apod_info(apod_date.isoformat())
    if not apod_info:
        return 0

    image_url = apod_api.get_apod_image_url(apod_info)
    if not image_url:
        return 0

    image_data = download_image(image_url)
    if not image_data:
        return 0

    image_sha256 = hashlib.sha256(image_data).hexdigest()
    apod_id = get_apod_id_from_db(image_sha256)
    if apod_id != 0:
        return apod_id

    file_path = determine_apod_file_path(apod_info['title'], image_url)
    if not save_image_file(image_data, file_path):
        return 0

    return add_apod_to_db(apod_info['title'], apod_info['explanation'], file_path, image_sha256)

def add_apod_to_db(title, explanation, file_path, sha256):
    """Adds specified APOD information to the image cache DB.

    Args:
        title (str): Title of the APOD image
        explanation (str): Explanation of the APOD image
        file_path (str): Full path of the APOD image file
        sha256 (str): SHA-256 hash value of APOD image
    Returns:
        int: The ID of the newly inserted APOD record
    """
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO apod (title, explanation, file_path, sha256)
        VALUES (?, ?, ?, ?)
    ''', (title, explanation, file_path, sha256))
    conn.commit()
    apod_id = cursor.lastrowid
    conn.close()
    print(f"Added APOD to DB with ID: {apod_id}")
    return apod_id

def get_apod_id_from_db(image_sha256):
    """Gets the record ID of the APOD in the cache with a specified SHA-256 hash.
    Args:
        image_sha256 (str): SHA-256 hash value of APOD image
    Returns:
        int: Record ID of the APOD in the image cache DB
    """
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM apod WHERE sha256 = ?', (image_sha256,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def determine_apod_file_path(image_title, image_url):
    """Determines the path at which a newly downloaded APOD image must be saved.

    Args:
        image_title (str): APOD title
        image_url (str): APOD image URL
    Returns:
        str: Full path at which the APOD image file must be saved
    """
    image_path = image_cache_dir
    file_extension = get_file_extension(image_url)
    file_name = re.sub(r'[\\/*?:"<>|]', '', image_title)  # Clean filename
    file_path = os.path.join(image_path, f"{file_name}{file_extension}")
    return file_path

def get_file_extension(image_url):
    """Extracts the file extension from the image URL.
    Args:
        image_url (str): URL of the image
    Returns:
        str: File extension including the dot, e.g., '.jpg'
    """
    _, ext = os.path.splitext(image_url)
    if not ext:
        ext = '.jpg'  # Default extension if none found
    return ext

def download_image(image_url):
    """Downloads an image from a specified URL.
    Args:
        image_url (str): URL of image
    Returns:
        bytes: Binary image data, if successful. None, if unsuccessful.
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"An error occurred while downloading the image: {e}")
        return None

def save_image_file(image_data, file_path):
    """Saves image data as a file on disk.
    Args:
        image_data (bytes): Binary image data
        file_path (str): Full path where the image will be saved
    Returns:
        bool: True if the file was saved successfully, False otherwise
    """
    try:
        with open(file_path, 'wb') as file:
            file.write(image_data)
        return True
    except IOError as e:
        print(f"An error occurred while saving the image: {e}")
        return False
def resize_image(image_path, new_width, new_height):
    """Resizes the image to the specified dimensions."""
    image = image.open(image_path)
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    return ImageTk.PhotoImage(resized_image)

def set_desktop_background_image(image_path):
    """Sets the desktop background image to a specific image.
    Args:
        image_path (str): Path of image file
    Returns:
        bool: True, if successful. False, if unsuccessful        
    """
    try:
        if os.name == 'nt':  # For Windows
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
            return True
        else:
            print("Setting desktop background is not supported on this OS")
            return False
    except Exception as e:
        print(f"An error occurred while setting the desktop background: {e}")
        return False

def get_apod_info(image_id):
    """Gets the title, explanation, and full path of the APOD with a specified ID.

    Args:
        image_id (int): ID of APOD in the DB
    Returns:
        dict: Dictionary of APOD information
    """
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    cursor.execute('SELECT title, explanation, file_path FROM apod WHERE id = ?', (image_id,))
    result = cursor.fetchone()
    conn.close()
    return {
        'title': result[0],
        'explanation': result[1],
        'file_path': result[2]
    } if result else None

def get_apod_info_by_title(title):
    """Gets the APOD information from the DB using the specified title.
    Args:
        title (str): Title of the APOD image
    Returns:
        dict: Dictionary of APOD information if found, otherwise None
    """
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()
    cursor.execute('SELECT title, explanation, file_path FROM apod WHERE title = ?', (title,))
    result = cursor.fetchone()
    conn.close()
    return {
        'title': result[0],
        'explanation': result[1],
        'file_path': result[2]
    } if result else None

logging.basicConfig(level=logging.DEBUG)

def get_all_apod_titles():
    conn = sqlite3.connect(image_cache_db)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM apod")
        titles = [row[0] for row in cursor.fetchall()]
        logging.debug(f"Retrieved titles: {titles}")
    except Exception as e:
        logging.error(f"Error executing SQL query: {e}")
    finally:
        conn.close()
    return titles

def load_data():
    conn = sqlite3.connect(image_cache_db)
    cursor = conn.cursor()

    # Select all relevant data from the cache
    cursor.execute("SELECT * FROM apod")  # Adjust the table name and columns as needed
    cached_data = cursor.fetchall()

    conn.close()
    return cached_data

if __name__ == '__main__':
    main()
