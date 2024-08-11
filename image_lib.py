import os
from datetime import date
import sys
import re
import requests
import ctypes
from apod_api import get_apod_info, get_apod_image_url

def main():
    """Main function to handle command line execution and setting APOD as desktop background."""
    apod_date = get_apod_date()
    apod_info = get_apod_info(apod_date)
    if apod_info:
        image_url = get_apod_image_url(apod_info)
        if image_url:
            image_data = download_image(image_url)
            if image_data:
                image_title = apod_info['title']
                image_path = save_image_file(image_data, image_title, image_url)
                if image_path:
                    print(f"Image saved to {image_path}")
                    if set_desktop_background_image(image_path):
                        print("Desktop background set successfully")
                    else:
                        print("Failed to set desktop background")
                else:
                    print("Failed to save image")
            else:
                print("Failed to download image")
        else:
            print("Failed to get image URL")
    else:
        print("Failed to retrieve APOD info")

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

def save_image_file(image_data, image_title, image_url):
    """Saves image data as a file on disk with the title as filename.

    Args:
        image_data (bytes): Binary image data
        image_title (str): Title of the image, used as filename
        image_url (str): URL of the image, used to determine the file extension

    Returns:
        str: Full path of the saved image file if successful, None if unsuccessful
    """
    image_path = './images/'
    file_extension = get_file_extension(image_url)
    file_name = re.sub(r'[\\/*?:"<>|]', '', image_title)  # Clean filename
    file_path = os.path.join(image_path, f"{file_name}{file_extension}")
    
    try:
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        with open(file_path, 'wb') as file:
            file.write(image_data)
        return file_path
    except IOError as e:
        print(f"An error occurred while saving the image: {e}")
        return None

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

if __name__ == '__main__':
    main()
