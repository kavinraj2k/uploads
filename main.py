from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import boto3
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging




# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MySQL connection
db = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DB')
)

# S3 configuration
s3_client = boto3.client('s3',
                         aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                         aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                         region_name=os.getenv('AWS_REGION'),verify=False)

BUCKET_NAME = os.getenv('BUCKET_NAME')

# Enable boto3 logging
boto3.set_stream_logger('boto3.resources', logging.DEBUG)
def upload_image_to_s3(file, folder_name):
    """Upload image to S3 and return the image URL."""
    try:
        filename = secure_filename(file.filename)
        # Logging details before uploading
        print(f"Uploading file: {filename} to S3 in folder: {folder_name}")

        # Attempt to upload the file to S3
        s3_client.upload_fileobj(file, BUCKET_NAME, f"{folder_name}/{filename}")

        # Logging after successful upload
        print(f"Successfully uploaded {filename} to {folder_name}")

        # Generate and return the image URL
        image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{folder_name}/{filename}"
        return image_url

    except s3_client.exceptions.ClientError as e:
        # Log AWS error response for more detail
        print(f"Error response from AWS: {e.response}")
        print(f"Error code: {e.response['Error']['Code']}")
        print(f"Error message: {e.response['Error']['Message']}")
        return None

    except Exception as e:
        # General exception handling
        print(f"Error uploading image: {str(e)}")
        return None

# API route to post a new lost/found item
@app.route('/api/items', methods=['POST'])
def post_item():
    try:
        data = request.form
        title = data.get('title')
        description = data.get('description')
        category = data.get('category')
        location = data.get('location')
        status = data.get('status')  # Either 'lost' or 'found'
        image_file = request.files.get('image')

        if not image_file:
            return jsonify({'error': 'Image file is required'}), 400

        # Upload image to S3
        image_url = upload_image_to_s3(image_file, folder_name=status)
        if not image_url:
            return jsonify({'error': 'Image upload failed'}), 500

        # Insert item data into MySQL
        cursor = db.cursor()
        query = """
            INSERT INTO items (title, description, category, location, status, image_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (title, description, category, location, status, image_url))
        db.commit()

        return jsonify({'message': 'Item posted successfully'}), 201

    except Exception as e:
        print(f"Error in POST /api/items: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/items', methods=['GET'])
def get_items():
    try:
        status = request.args.get('status')  # 'lost' or 'found'
        category = request.args.get('category')
        location = request.args.get('location')
        order = request.args.get('order', 'recent')  # Default to 'recent'

        query = "SELECT * FROM items WHERE 1=1"
        filters = []

        if status:
            query += " AND status = %s"
            filters.append(status)
        if category:
            query += " AND category = %s"
            filters.append(category)
        if location:
            query += " AND location LIKE %s"
            filters.append(f"%{location}%")

        if order == 'recent':
            query += " ORDER BY created_at DESC"

        cursor = db.cursor(dictionary=True)
        cursor.execute(query, tuple(filters))
        items = cursor.fetchall()

        return jsonify(items), 200

    except Exception as e:
        print(f"Error in GET /api/items: {e}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
