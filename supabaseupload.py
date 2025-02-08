import datetime
import requests
import logging

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

        # Prepare meeting record
        meeting_record = {
            'meeting_id': meeting_id,
            'ended_by_user_id': call_ended_by.get('id'),
            'ended_by_name': call_ended_by.get('name'),
            'ended_by_role': call_ended_by.get('role'),
            'ended_at': datetime.datetime.utcnow().isoformat(),
            'user_metadata': {
                'image': call_ended_by.get('image'),
                'language': call_ended_by.get('language'),
                'teams': call_ended_by.get('teams'),
                'created_at': call_ended_by.get('created_at'),
                'updated_at': call_ended_by.get('updated_at'),
                'online_status': call_ended_by.get('online'),
            }
        }

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

        with open(f'__temp__/csv/{meeting_id}.csv', 'rb') as f:
            file_data = f.read()

        upload_headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'text/csv',
            'Cache-Control': '3600'
        }

        storage_response = requests.post(
            storage_url,
            headers=upload_headers,
            data=file_data
        )
        logging.debug(f"Storage response status code: {storage_response.status_code}")
        logging.debug(f"Storage response text: {storage_response.text}")
        storage_response.raise_for_status()

        return {
            'status': 'success',
            'meeting_id': meeting_id,
            'storage_path': f'{BUCKET_NAME}/meetings/{meeting_id}/meeting_data.csv'
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to save meeting data: {str(e)}", exc_info=True)
        raise Exception(f"Failed to save meeting data: {str(e)}")