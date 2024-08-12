import requests
from apod_api import get_apod_info, get_apod_image_url, API_KEY, BASE_URL
from datetime import date
import sys

def main():
    """Main function to handle command line execution and display APOD info."""
    apod_date = get_apod_date()
    apod_info = get_apod_info(apod_date)
    if apod_info:
        print(apod_info)
        image_url = get_apod_image_url(apod_info)
        print('APOD Image URL:', image_url)
    else:
        print('Failed to retrieve APOD info')

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

def get_apod_info(apod_date):
    """Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.
    Args:
        apod_date (date): APOD date (Can also be a string formatted as YYYY-MM-DD)
    Returns:
        dict: Dictionary of APOD info, if successful. None if unsuccessful
    """
    params = {
        'api_key': API_KEY,
        'date': apod_date,
        'thumbs': True
    }
    
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def get_apod_image_url(apod_info_dict):
    """Gets the URL of the APOD image from the dictionary of APOD information.
    If the APOD is an image, gets the URL of the high definition image.
    If the APOD is a video, gets the URL of the video thumbnail.
    Args:
        apod_info_dict (dict): Dictionary of APOD info from API
    Returns:
        str: APOD image URL
    """
    if apod_info_dict['media_type'] == 'image':
        return apod_info_dict['hdurl'] if 'hdurl' in apod_info_dict else apod_info_dict['url']
    elif apod_info_dict['media_type'] == 'video':
        return apod_info_dict['thumbnail_url']
    else:
        return None

if __name__ == '__main__':
    main()
