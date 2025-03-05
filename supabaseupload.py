import datetime
import requests
import logging
import pytz

# Supabase project details
SUPABASE_URL = "https://iljsvpxoiwnwxtjxypgi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlsanN2cHhvaXdud3h0anh5cGdpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczODk5NzYwMiwiZXhwIjoyMDU0NTczNjAyfQ.yHQOgRkEGo_NvJeT6ikONQQLiIhcuVVdsNcjZJE_9Rg"  # Use the service role key for secure upload
BUCKET_NAME = "Polycomm"          # Replace with your bucket name

def upload_file(file_path: str, file_name: str, callendedby):
    """
    Uploads a file to a Supabase bucket using the REST API.

    Args:
        file_path (str): Local path to the file to upload.
        file_name (str): Name of the file to save in the bucket.
    """
    try:
        # Endpoint for file upload
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{callendedby}/{file_name}"

        # File to upload
        with open(file_path, "rb") as file_data:
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "text/csv",  # Set MIME type if known
            }
            response = requests.post(url, headers=headers, data=file_data)

        if response.status_code == 200:
            print("File uploaded successfully:", response.json())
        else:
            print("Failed to upload file:", response.json())
    except Exception as e:
        print("An error occurred:", str(e))


def save_meeting_data(meeting_data, supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY):
    """
    Save meeting data to Supabase using direct REST API calls

    Args:
        meeting_data (dict): Meeting data from the request
        supabase_url (str): Supabase project URL (without trailing slash)
        supabase_key (str): Supabase project API key
    """
    try:
        # Setup headers for Supabase REST API
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }

        # Extract data from the request
        call_ended_by = meeting_data.get('callended', {})
        meeting_id = meeting_data.get('m_id')
        call_start_time_str = call_ended_by.get('callStartTime')
        call_end_time_str = call_ended_by.get('callEndTime')
        
        # Parse the start time and convert it to IST
        call_start_time_utc = datetime.datetime.fromisoformat(call_start_time_str)
        call_end_time_utc = datetime.datetime.fromisoformat(call_end_time_str)
        ist = pytz.timezone('Asia/Kolkata')
        call_start_time_ist = call_start_time_utc.astimezone(ist)
        call_end_time_ist = call_end_time_utc.astimezone(ist)

        # Get the current time in IST
        # call_end_time_utc = datetime.datetime.now(datetime.timezone.utc)
        # call_end_time_ist = call_end_time_utc.astimezone(ist)
        duration_seconds = (call_end_time_ist - call_start_time_ist).total_seconds()

        # Calculate duration in hours and minutes
        duration_hours = int(duration_seconds // 3600)
        duration_minutes = int((duration_seconds % 3600) // 60)

        # Prepare meeting record
        meeting_record = {
            'meeting_id': meeting_id,
            'ended_by_user_id': call_ended_by.get('id'),
            'ended_by_name': call_ended_by.get('name'),
            'ended_by_role': call_ended_by.get('role'),
            'ended_at': call_end_time_ist.isoformat(),
            'started_at': call_start_time_ist.isoformat(),
            'duration': {
                'seconds': duration_seconds,
                'hours': duration_hours,
                'minutes': duration_minutes
            },
            'user_metadata': {
                'image': call_ended_by.get('image'),
                'language': call_ended_by.get('language'),
                'teams': call_ended_by.get('teams'),
                'created_at': call_ended_by.get('created_at'),
                'updated_at': call_ended_by.get('updated_at'),
                'online_status': call_ended_by.get('online'),
            }
        }
        
        print(meeting_record)

        # Insert data into Supabase table
        table_url = f"{supabase_url}/rest/v1/meetings"
        response = requests.post(
            table_url,
            headers=headers,
            json=meeting_record
        )
        response.raise_for_status()

        # Upload file to storage bucket
        storage_url = f"{supabase_url}/storage/v1/object/{BUCKET_NAME}/meetings/{meeting_id}/meeting_data.csv"
        analytics_storage_url = f"{supabase_url}/storage/v1/object/{BUCKET_NAME}/meetings/{meeting_id}/analytics_data.csv"
        camera_analytics_storage_url = f"{supabase_url}/storage/v1/object/{BUCKET_NAME}/meetings/{meeting_id}/camera_analytics_data.csv"
        presence_analytics_storage_url = f"{supabase_url}/storage/v1/object/{BUCKET_NAME}/meetings/{meeting_id}/presence_analytics_data.csv"

        upload_headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "text/csv",  # Set MIME type if known
        }

        upload_results = {
            'meeting_data': False,
            'analytics_data': False,
            'camera_analytics': False,
            'presence_analytics': False
        }

        # Meeting data upload
        try:
            with open(f'__temp__/csv/{meeting_id}.csv', 'rb') as f:
                file_data = f.read()
                storage_response = requests.post(
                    storage_url,
                    headers=upload_headers,
                    data=file_data
                )
                storage_response.raise_for_status()
                upload_results['meeting_data'] = True
        except FileNotFoundError:
            logging.warning(f"Meeting data file not found for meeting {meeting_id}")
        except Exception as e:
            logging.error(f"Error uploading meeting data: {str(e)}")

        # Analytics data upload
        try:
            with open(f'__temp__/analytics/{meeting_id}.csv', 'rb') as f:
                analytics_file_data = f.read()
                analytics_storage_response = requests.post(
                    analytics_storage_url,
                    headers=upload_headers,
                    data=analytics_file_data
                )
                analytics_storage_response.raise_for_status()
                upload_results['analytics_data'] = True
        except FileNotFoundError:
            logging.warning(f"Analytics data file not found for meeting {meeting_id}")
        except Exception as e:
            logging.error(f"Error uploading analytics data: {str(e)}")

        # Camera analytics upload
        try:
            with open(f'__temp__/camera_analytics/{meeting_id}.csv', 'rb') as f:
                camera_analytics_file_data = f.read()
                camera_analytics_storage_response = requests.post(
                    camera_analytics_storage_url,
                    headers=upload_headers,
                    data=camera_analytics_file_data
                )
                camera_analytics_storage_response.raise_for_status()
                upload_results['camera_analytics'] = True
        except FileNotFoundError:
            logging.warning(f"Camera analytics file not found for meeting {meeting_id}")
        except Exception as e:
            logging.error(f"Error uploading camera analytics data: {str(e)}")

        # Presence analytics upload
        try:
            with open(f'__temp__/presence_analytics/{meeting_id}.csv', 'rb') as f:
                presence_analytics_file_data = f.read()
                presence_analytics_storage_response = requests.post(
                    presence_analytics_storage_url,
                    headers=upload_headers,
                    data=presence_analytics_file_data
                )
                presence_analytics_storage_response.raise_for_status()
                upload_results['presence_analytics'] = True
        except FileNotFoundError:
            logging.warning(f"Presence analytics file not found for meeting {meeting_id}")
        except Exception as e:
            logging.error(f"Error uploading presence analytics data: {str(e)}")

        # Check if at least one file was uploaded successfully
        if not any(upload_results.values()):
            raise Exception("No files were uploaded successfully")

        return {
            'status': 'partial_success' if not all(upload_results.values()) else 'success',
            'meeting_id': meeting_id,
            'upload_results': upload_results
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to save meeting data: {str(e)}", exc_info=True)
        raise Exception(f"Failed to save meeting data: {str(e)}")