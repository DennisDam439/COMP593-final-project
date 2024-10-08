from datetime import date
import sys
import requests

API_KEY = 'QzFwm92OcOTymgJhWVpzYSLOM37TmiJ6letWC9LE'  # Replace with your NASA API key if available
BASE_URL = 'https://api.nasa.gov/planetary/apod'

def main():
    # Example usage
    apod_date = get_apod_date()
    apod_info = get_apod_info(apod_date)
    if apod_info:
        print(apod_info)
        image_url = get_apod_image_url(apod_info)
        print('APOD Image URL:', image_url)
    else:
        print('Failed to retrieve APOD info')

def get_apod_info(apod_date=None, start_date=None, end_date=None, count=None):
    """Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date or date range or random images.

    Args:
        apod_date (str): APOD date (formatted as YYYY-MM-DD)
        start_date (str): Start date for a range (formatted as YYYY-MM-DD)
        end_date (str): End date for a range (formatted as YYYY-MM-DD)
        count (int): Number of random images to retrieve

    Returns:
        dict or list: Dictionary of APOD info or list of dictionaries if multiple APODs are requested. None if unsuccessful.
    """
    params = {
        'api_key': API_KEY,
        'thumbs': True
    }
    
    if apod_date:
        params['date'] = apod_date
    if start_date and end_date:
        params['start_date'] = start_date
        params['end_date'] = end_date
    if count:
        params['count'] = count
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred!! try again later: {e}")
        return None

def get_apod_date():
    """Gets the APOD date from command line or defaults to today's date.

    Returns:
        date: APOD date
    """
    first_apod_date = date(1995, 6, 16)  
    today_date = date.today()

    if len(sys.argv) > 1:
        try:
            apod_date = date.fromisoformat(sys.argv[1])
            if apod_date < first_apod_date:
                print(f"Error: Date cannot be before {first_apod_date}.")
                sys.exit(1)
            elif apod_date > today_date:
                print(f"Error: Cannot be future date")
                sys.exit(1)
            return apod_date
        except ValueError:
            print("Error: Date format should be Please use YYYY-MM-DD.")
            sys.exit(1)
    return today_date
def get_apod_image_url(apod_info_dict):
    """Gets the URL of the APOD image from the dictionary of APOD information.

    If the APOD is an image, gets the URL of the high definition image.
    If the APOD is a video, gets the URL of the video thumbnail.

    Args:
        apod_info_dict (dict): Dictionary of APOD info from API

    Returns:
        str: APOD image URL
    """
    if isinstance(apod_info_dict, list):
        return [get_apod_image_url(apod) for apod in apod_info_dict]
    
    if apod_info_dict['media_type'] == 'image':
        return apod_info_dict.get('hdurl', apod_info_dict.get('url'))
    elif apod_info_dict['media_type'] == 'video':
        return apod_info_dict.get('thumbnail_url')
    else:
        return None

if __name__ == '__main__':
    main()
