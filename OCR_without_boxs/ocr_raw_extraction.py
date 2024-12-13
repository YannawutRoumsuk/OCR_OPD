import sys
import cv2
import easyocr
import re

# กำหนด encoding ของ stdout เป็น utf-8
sys.stdout.reconfigure(encoding='utf-8')

def read_image_and_check_keywords(image_path, keywords):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Can't open the file: {image_path}")

    reader = easyocr.Reader(['en', 'th'], verbose=False)
    results = reader.readtext(image)

    keyword_lines = {keyword: [] for keyword in keywords}
    current_keyword = None

    i = 0
    while i < len(results):
        bbox, text, confidence = results[i]
        stripped_text = text.strip()

        # เช็คสำหรับ hn ตามเงื่อนไขใหม่
        if stripped_text.startswith('h') and len(stripped_text) > 2:
            if len(stripped_text) > 3 and stripped_text[2] == ' ':
                remaining_text = stripped_text[3:].strip()
                colon_index = remaining_text.find(':')
                if colon_index != -1:
                    potential_number = remaining_text[colon_index + 1:].strip()
                    if re.match(r'\d{2}-\d{6}', potential_number):
                        modified_text = 'hn' + stripped_text[2:].strip()
                        keyword_lines['hn'].append(modified_text)
            elif len(stripped_text) > 3 and stripped_text[2] == ':':
                potential_number = stripped_text[3:].strip()
                if re.match(r'\d{2}-\d{6}', potential_number):
                    modified_text = 'hn' + stripped_text[2:].strip()
                    keyword_lines['hn'].append(modified_text)

        # เช็คสำหรับ vn ตามเงื่อนไขใหม่
        elif stripped_text.startswith('v'):
            if len(stripped_text) > 1 and stripped_text[1] == 'n':
                keyword_lines['vn'].append(stripped_text)
            elif len(stripped_text) == 2:
                keyword_lines['vn'].append('vn')

                if i + 1 < len(results):
                    next_bbox, next_text, next_confidence = results[i + 1]
                    next_stripped_text = next_text.strip()
                    if re.match(r'^\d{3}', next_stripped_text):
                        keyword_lines['vn'].append(next_stripped_text)
                        i += 1

            elif len(stripped_text) > 2:
                if len(stripped_text) > 3 and stripped_text[2] == ' ':
                    remaining_text = stripped_text[3:].strip()
                    colon_index = remaining_text.find(':')
                    if colon_index != -1:
                        potential_number = remaining_text[colon_index + 1:].strip()
                        if re.match(r'\d{3}/\d{6}', potential_number):
                            modified_text = 'vn' + stripped_text[2:].strip()
                            keyword_lines['vn'].append(modified_text)
                elif len(stripped_text) > 3 and stripped_text[2] == ':':
                    potential_number = stripped_text[3:].strip()
                    if re.match(r'\d{3}/\d{6}', potential_number):
                        modified_text = 'vn' + stripped_text[2:].strip()
                        keyword_lines['vn'].append(modified_text)

        # เช็คสำหรับ pi ตามเงื่อนไขใหม่
        elif stripped_text.startswith('pi'):
            colon_index = stripped_text.find(':')
            if colon_index != -1:
                keyword_lines['pi'].append(stripped_text)

        # เช็คสำหรับ cc ตามเงื่อนไขใหม่
        elif stripped_text.startswith('cc'):
            colon_index = stripped_text.find(':')
            if colon_index != -1:
                keyword_lines['cc'].append(stripped_text)

        # เช็คสำหรับ ht ตามเงื่อนไขใหม่
        elif stripped_text.startswith('ht'):
            colon_index = stripped_text.find(':')
            if colon_index != -1:
                keyword_lines['ht'].append(stripped_text)

        # เงื่อนไขใหม่: ถ้ามีช่องว่างขึ้นต้นในบรรทัดนั้น แล้วตามด้วย cr
        elif stripped_text.startswith(' cr'):
            keyword_lines['cr'].append(stripped_text)

        # แก้ไขข้อความผิดพลาดให้เป็นคำที่ถูกต้อง
        if stripped_text in ["buv", "8un"]:
            stripped_text = "bun"
        elif stripped_text in ["hbalc", "hbaic", "h8alc", "h8aic"]:
            stripped_text = "hbaic"

        # แก้ไขคำว่า "ชือ" เป็น "ชื่อ" และตรวจสอบบรรทัดถัดไป
        if stripped_text == "ชือ":
            stripped_text = "ชื่อ"
            keyword_lines['ชื่อ'].append(stripped_text)

        # เช็คสำหรับบรรทัดที่ขึ้นต้นด้วย 8 ตามด้วย p, t, w, mi
        elif stripped_text.startswith('8') and len(stripped_text) > 2:
            if stripped_text[1] in ['p', 't', 'w']:
                keyword = 'b' + stripped_text[1]  # เช่น 'bp', 'bt', 'bw'
                keyword_lines[keyword].append(stripped_text)
            elif stripped_text[1:3] == 'mi':
                keyword_lines['bmi'].append(stripped_text)
            elif stripped_text[1:3] == 'un':
                keyword_lines['bun'].append(stripped_text)

        elif stripped_text in keywords:
            current_keyword = stripped_text
        elif current_keyword:
            keyword_lines[current_keyword].append(stripped_text)
            if stripped_text in keywords:
                current_keyword = stripped_text

        i += 1  # เพิ่มค่า i เมื่อสิ้นสุดการประมวลผลของบรรทัดนั้น
        
    return keyword_lines, results


if __name__ == "__main__":
    image_path = "opd2_edit.jpg"
    keywords = ["hn", "vn", "ชื่อ", "เพศ", "อายุ", "วันที่", "แพทย์", "cbc", "bun", "cr", "elec", "lft", "ua", "tsh", "ft4", "ft3", "pt", "ptt", "fbs", "lp", "afp", "cea", "ca153", "ca125", "ca 19-9", "psa", "pi", "bp", "bt", "cc", "bw", "ht", "bmi"]

    keyword_lines, detected_texts = read_image_and_check_keywords(image_path, keywords)
    
    # แสดงผลข้อความภายใต้แต่ละคีย์เวิร์ด
    for keyword, lines in keyword_lines.items():
        if lines:
            print(f"Lines under keyword '{keyword.upper()}':")
            for line in lines:
                print(f"- {line}")
            print()  # เพิ่มบรรทัดว่างหลังจากแสดงผลแต่ละคีย์เวิร์ด
        else:
            print(f"No text found under keyword '{keyword.upper()}'\n")


    # แสดงผลข้อความทั้งหมดที่ตรวจจับได้จากภาพexit
    print("All detected text: ")
    for bbox, text, confidence in detected_texts:
        print(f"Text: {text}, Confidence: {confidence:.2f}") 
