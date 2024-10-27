# file: app.py
from flask import Flask, request, jsonify
from PIL import Image
import io
import os
from ocr_data_processing import read_image_and_check_keywords, extract_keyword_values

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
        image_temp_path = 'temp_image.jpg'
        image.save(image_temp_path, 'JPEG')

        # สร้างรายการ keywords ที่ต้องการค้นหา
        keywords = ["hn", "vn", "ชื่อ", "เพศ", "อายุ", "วันที่", "แพทย์", "cbc", "bun", "cr", "elec", "lft", "ua", "tsh", "ft4", "ft3",
                    "pt", "ptt", "hbaic", "fbs", "lp", "afp", "cea", "ca153", "ca125", "ca 19-9", "psa", "pi", "bp", "bt", "cc", "bw", "ht", "bmi"]

        # ใช้ฟังก์ชันที่นำเข้ามาเพื่อทำ OCR และค้นหาคำสำคัญ
        keyword_lines, detected_texts = read_image_and_check_keywords(image_temp_path, keywords)
    
        # ประมวลผลข้อมูลที่ดึงออกมา
        ocr_results = extract_keyword_values(keyword_lines)
        
        # ปรับผลลัพธ์ให้อยู่ในรูปแบบที่เหมือนกับการใช้ฟังก์ชัน print_result
        formatted_results = format_result(ocr_results)

        # ลบไฟล์รูปภาพชั่วคราว
        os.remove(image_temp_path)

        return jsonify(formatted_results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def format_result(result):
    formatted_data = {}
    for category, values in result.items():
        formatted_category = category.lower()
        formatted_data[formatted_category] = {}
        for key, value in values.items():
            formatted_key = key.lower().replace(" ", "_").replace("-", "_")
            # แก้ไขชื่อคีย์เฉพาะบางคีย์ที่ต้องการ
            if formatted_key == "diff":
                formatted_key = "diff_100"
            elif formatted_key == "report":
                formatted_key = "report_nrbc"
            elif formatted_key == "egfr_epi":
                formatted_key = "egfr_epi_ckd_dpi"
            elif formatted_key == "sgot":
                formatted_key = "sgot_ast"
            elif formatted_key == "sgpt":
                formatted_key = "sgpt_alt"
            elif formatted_key == "color":
                formatted_key = "color_ue"
            elif formatted_key == "ca_19_9":
                formatted_key = "ca19_9"
            
            formatted_data[formatted_category][formatted_key] = value

    return formatted_data

if __name__ == '__main__':
    # รันแอปพลิเคชัน
    app.run(debug=True)
