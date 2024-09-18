from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from analyse_dicom_image import analyse_dicom_image

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"message": "File uploaded successfully", "filepath": filepath})

@app.route('/analyze', methods=['POST'])
def analyze_image():
    try:
        data = request.json
        print("Received data:", data) 
        
        image_path = data.get('filepath')

        if not image_path:
            print("Error: Missing image path")
            return jsonify({"error": "Missing parameters"}), 400

        if not os.path.exists(image_path):
            print(f"Error: File {image_path} not found")
            return jsonify({"error": "File not found"}), 404

        print(f"Starting analysis for image: {image_path}")

        total_cell_count, infected_cell_count, patient_status, initial_image_path, processed_image_path = analyse_dicom_image(
            image_path, 
        )

        print(f"Analysis complete. Total cells: {total_cell_count}, Infected cells: {infected_cell_count}")

        # Return the analysis result
        return jsonify({
            "total_cell_count": total_cell_count,
            "infected_cell_count": infected_cell_count,
            "patient_status": patient_status,
            "initial_image_path": initial_image_path,
            "processed_image_path": processed_image_path
        })

    except Exception as e:
        # Log the full error
        print(f"Error during analysis: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route('/display_image/<filename>')
def display_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
