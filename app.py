# file: app.py
from flask import Flask, request, jsonify
from PIL import Image
import io
import cv2
import easyocr
import sys
import os

# นำเข้าฟังก์ชันจากไฟล์ ocr_data_processing.py
from ocr_data_processing import read_image_and_check_keywords,extract_keyword_values

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_image():
    # ตรวจสอบว่ามีไฟล์รูปภาพถูกอัพโหลด
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    # ตรวจสอบว่าไฟล์มีข้อมูลและเป็นไฟล์รูปภาพ
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # อ่านไฟล์รูปภาพจากที่ผู้ใช้อัพโหลด
        image = Image.open(io.BytesIO(file.read()))
        
        # แปลงรูปภาพเป็นฟอร์แมตที่ cv2 สามารถอ่านได้
        image_path = 'temp_image.jpg'
        image.save(image_path,'JPEG')

        # สร้างรายการ keywords ที่ต้องการค้นหา
        keywords = ["hn", "vn", "ชื่อ", "เพศ", "อายุ", "วันที่", "แพทย์", "cbc", "bun", "cr", "elec", "lft", "ua", "tsh", "ft4", "ft3",
                    "pt", "ptt","hbaic", "fbs", "lp", "afp", "cea", "ca153", "ca125", "ca 19-9", "psa", "pi", "bp", "bt", "cc", "bw", "ht", "bmi"]  # เปลี่ยนเป็นคำที่คุณต้องการค้นหา

        # ใช้ฟังก์ชันที่นำเข้ามาเพื่อทำ OCR และค้นหาคำสำคัญ
        keyword_lines, detected_texts = read_image_and_check_keywords(image_path, keywords)
    
    # ประมวลผลข้อมูลที่ดึงออกมา
        ocr_results = extract_keyword_values(keyword_lines)

        # ลบไฟล์รูปภาพชั่วคราว
        os.remove(image_path)

        return jsonify(ocr_results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
