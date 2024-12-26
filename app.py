import base64  # Add this import for Base64 encoding
import json  # Add this import for handling JSON data
from flask import Flask, request, render_template
from PIL import Image
import os
import google.generativeai as genai  # Ensure you have the google generativeai package installed
from werkzeug.utils import secure_filename
from io import BytesIO
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from the environment variables
api_key = os.getenv('API_KEY')  # This will fetch the API key from the .env file

if not api_key:
    raise ValueError("API key is not set in the environment variables")

# Configure the Google Generative AI API with the API key
genai.configure(api_key=api_key)

# Initialize Flask app
app = Flask(__name__)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        file = request.files.get('file')
        user_style = request.form.get('user_style')
        word_limit = request.form.get('word_limit', '3-10')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Process image in memory for privacy
            img = Image.open(file.stream)
            
            # Convert the image to Base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            base64_image = base64.b64encode(buffer.read()).decode('utf-8')

            # Generate personalized caption
            response_personalized = genai.GenerativeModel("gemini-1.5-flash").generate_content([f"Generate a {user_style} caption sentence for this image of {word_limit} words, structured as a JSON object, and exclude any explanations or additional text.", img])

            # Extract and clean caption text
            response_text = response_personalized.text
            cleaned_text = response_text.replace("```json\n", "").replace("\n```", "")

            # Parse JSON for caption
            try:
                caption_data = json.loads(cleaned_text)
                personalized_caption = caption_data.get("caption", "No caption available")
            except json.JSONDecodeError:
                personalized_caption = "Error parsing caption."

            return render_template(
                'index.html',
                personalised_caption=personalized_caption,
                user_style=user_style,
                base64_image=base64_image
            )

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
