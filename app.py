import os
import base64
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PIL import Image
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Define the directory to store images
BASE_DIR = "collected_faces"
os.makedirs(BASE_DIR, exist_ok=True)

def save_compressed_image(image_data, folder_name, image_count):
    """Compress and save the image in the correct folder"""
    try:
        folder_path = os.path.join(BASE_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        image_path = os.path.join(folder_path, f"{image_count}.jpg")

        # Convert base64 to an image
        image = Image.open(BytesIO(base64.b64decode(image_data.split(",")[1])))

        # Compress image
        quality = 95
        while quality >= 10:
            buffer = BytesIO()
            image.save(buffer, "JPEG", quality=quality)
            size_kb = len(buffer.getvalue()) / 1024  # Convert bytes to KB

            if size_kb <= 1000:  # Below 1MB
                with open(image_path, "wb") as f:
                    f.write(buffer.getvalue())
                return image_path

            quality -= 5  # Reduce quality step-by-step

        # If image is still too big, save with lowest quality
        print(f"Warning: Image {image_path} saved at lowest quality.")
        with open(image_path, "wb") as f:
            f.write(buffer.getvalue())

        return image_path

    except Exception as e:
        print("Error compressing image:", str(e))
        return None


@app.route("/upload", methods=["POST"])
def upload():
    """Handle image uploads"""
    try:
        data = request.json
        person_name = data.get("person_name", "").strip()
        roll_number = data.get("roll_number", "").strip()
        image_data = data.get("image", "").strip()

        # Validate inputs
        if not person_name or not roll_number:
            return jsonify({"error": "Missing name or roll number!"}), 400
        if not image_data or "," not in image_data:
            return jsonify({"error": "Invalid image data!"}), 400

        # Create folder in "name_rollno" format
        folder_name = f"{person_name}_{roll_number}"

        # Count existing images in the person's folder
        folder_path = os.path.join(BASE_DIR, folder_name)
        image_count = len(os.listdir(folder_path)) + 1 if os.path.exists(folder_path) else 1

        # Save the compressed image
        image_path = save_compressed_image(image_data, folder_name, image_count)
        if not image_path:
            return jsonify({"error": "Failed to save image!"}), 500

        return jsonify({"message": "Image saved successfully!", "image_path": image_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    """Serve the main HTML page"""
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
