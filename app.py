import base64  # For Base64 encoding
import json  # For handling JSON data
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
api_key = os.getenv('API_KEY')  # Fetch the API key from the .env file

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

# Compress image to WebP format
def compress_image_to_webp(image):
    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=80)  # Compress without resizing
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        file = request.files.get('file')
        user_style = request.form.get('user_style')
        word_limit = request.form.get('word_limit', '3-10')

        if file and allowed_file(file.filename):
            try:
                # Process image in memory for privacy
                img = Image.open(file.stream)
                
                # Compress the image to WebP format
                compressed_image = compress_image_to_webp(img)
                
                # Convert the compressed image to Base64
                base64_image = base64.b64encode(compressed_image.read()).decode('utf-8')

                # Generate personalized caption
                prompt = (
                    f"Generate a {user_style} caption sentence for this image of exact {word_limit} words, "
                    f"structured as a JSON object, and exclude any explanations or additional text."
                )
                response_personalized = genai.GenerativeModel("gemini-1.5-flash").generate_content([prompt, img])

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
            except Exception as e:
                return render_template(
                    'index.html',
                    error=f"An error occurred: {str(e)}"
                )

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
