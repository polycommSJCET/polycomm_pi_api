import json
import requests
import csv

def generate_minutes():
    file_input=''

    with open('sample_meeting.csv', mode='r') as file:
        csv_reader = csv.reader(file)
            
        for row in csv_reader:
            file_input += ", ".join(row) + "\n"



    response = requests.post(
        'http://localhost:11434/api/chat',
        json={
            "model": "llama3.2",
            "messages": [
                {
                    "role": "system",
                    "content": "Reply in format where each title/heading/sub-heading are enclosed in <angle brackets>."
                },
                {
                    "role": "user",
                    "content": "Generate meeting minutes based on the following conversation: "+file_input
                }
            ]
        },
        stream=True  # Enable streaming
    )

    # Collect the final message content
    message_content = []

    for line in response.iter_lines():
        if line:  # Ignore empty lines
            try:
                # Parse the line as JSON
                data = json.loads(line)
                # Append content if the "message" key exists
                if "message" in data and "content" in data["message"]:
                    message_content.append(data["message"]["content"])
            except json.JSONDecodeError:
                print("Failed to decode line:", line)

    # Combine all message parts into the final response
    final_message = "".join(message_content)
    print(final_message)

    return "success"
