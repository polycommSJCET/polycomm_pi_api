import json
import requests
import csv
from fpdf import FPDF

class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Meeting Minutes", border=False, ln=True, align="C")
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_pdf(content,m_id):
        # Initialize PDF
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        
        # Split content into lines
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith("<") and line.endswith(">"):  # Identify headings (e.g., <Meeting Minutes>)
                pdf.set_font("Arial", "B", 14)
                pdf.ln(10)
                pdf.cell(0, 10, line.strip("<>"), ln=True)
            elif line.startswith("-") or line.startswith("*"):  # Bulleted lists
                pdf.set_font("Arial", "I", 12)
                pdf.cell(10)  # Add indentation
                pdf.multi_cell(0, 10, line)
            elif line.isdigit() or line.startswith("1.") or line.startswith("2."):  # Numbered lists
                pdf.set_font("Arial", "I", 12)
                pdf.cell(10)  # Add indentation
                pdf.multi_cell(0, 10, line)
            elif line == "":  # Empty lines
                pdf.ln(5)
            else:  # Regular paragraphs
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, line)
        
        # Save the PDF
        output_file = m_id+".pdf"
        pdf.output(output_file)
        return output_file

def generate_minutes(m_id):
    file_input=''

    with open(m_id+'.csv', mode='r') as file:
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


    # Generate PDF
    output_file = generate_pdf(final_message,m_id)
    print(f"PDF generated and saved as {output_file}")


    return final_message


