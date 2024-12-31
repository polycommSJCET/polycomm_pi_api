import requests

# Supabase project details
SUPABASE_URL = "https://nvpibtldabwvptyvhair.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52cGlidGxkYWJ3dnB0eXZoYWlyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU1NDc3NDEsImV4cCI6MjA1MTEyMzc0MX0.nOq545_ugdBDIygunQ5Fbz4O2s3iKdoRCTL12rTtvlU"  # Use the service role key for secure upload
BUCKET_NAME = "Polycomm"          # Replace with your bucket name

def upload_file(file_path: str, file_name: str):
    """
    Uploads a file to a Supabase bucket using the REST API.

    Args:
        file_path (str): Local path to the file to upload.
        file_name (str): Name of the file to save in the bucket.
    """
    try:
        # Endpoint for file upload
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_name}"

        # File to upload
        with open(file_path, "rb") as file_data:
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/pdf",  # Set MIME type if known
            }
            response = requests.post(url, headers=headers, data=file_data)

        if response.status_code == 200:
            print("File uploaded successfully:", response.json())
        else:
            print("Failed to upload file:", response.json())
    except Exception as e:
        print("An error occurred:", str(e))

# Example usage

