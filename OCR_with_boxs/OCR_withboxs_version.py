import sys
import cv2
import easyocr
import re
import cv2
import matplotlib.pyplot as plt
from PIL import Image

# กำหนด encoding ของ stdout เป็น utf-8
sys.stdout.reconfigure(encoding='utf-8')

def read_image_and_check_keywords(image_path, keywords, bounding_box=None):
    # อ่านรูปภาพจากไฟล์
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Can't open the file: {image_path}")

    # ถ้ามีการกำหนด bounding_box ให้ครอบภาพตาม bounding_box
    if bounding_box is not None:
        x, y, w, h = bounding_box
        image = image[y:y+h, x:x+w]

    # อ่านข้อความจากภาพที่ครอบมาแล้วหรือจากภาพเต็ม
    reader = easyocr.Reader(['en', 'th'], verbose=False)
    results = reader.readtext(image)

    keyword_lines = {keyword: [] for keyword in keywords}
    current_keyword = None

    i = 0
    while i < len(results):
        bbox, text, confidence = results[i]
        stripped_text = text.strip()
        
        # เช็คสำหรับ hn ตามเงื่อนไขใหม่
        if stripped_text == 'hn' or stripped_text == 'hv':  # ตรวจสอบ 'hv' ด้วย
            # เปลี่ยน 'hv' เป็น 'hn'
            if stripped_text == 'hv':
                stripped_text = 'hn'

            # เก็บ 'hn' ไว้ในคีย์เวิร์ด 'hn'
            keyword_lines['hn'].append(stripped_text)

            # ตรวจสอบบรรทัดถัดไป
            if i + 1 < len(results):
                next_bbox, next_text, next_confidence = results[i + 1]
                next_stripped_text = next_text.strip()

                # ตรวจสอบว่าบรรทัดถัดไปเป็นตัวเลขในรูปแบบ "67-008286"
                if re.match(r'^\d{2}-\d{6}$', next_stripped_text):
                    keyword_lines['hn'].append(next_stripped_text)
                    i += 1  # ข้ามการประมวลผลบรรทัดถัดไป

        elif stripped_text.startswith('h') and len(stripped_text) > 2:
            # ตรวจสอบว่าตัวอักษรหลัง 'h' เป็น 'v' และเปลี่ยนเป็น 'n'
            if stripped_text[1] == 'v':
                modified_text = 'hn' + stripped_text[2:].strip()
                keyword_lines['hn'].append(modified_text)
            
            elif len(stripped_text) > 3 and stripped_text[2] == ' ':
                remaining_text = stripped_text[3:].strip()
                colon_index = remaining_text.find(':')
                if colon_index != -1:
                    potential_number = remaining_text[colon_index+1:].strip()
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
            # เพิ่มการตรวจสอบว่าถ้าเจอ 'vi' ให้เปลี่ยนเป็น 'vn'
            if stripped_text == 'vi':
                stripped_text = 'vn'  # เปลี่ยน 'vi' เป็น 'vn'
                keyword_lines['vn'].append(stripped_text)
            elif len(stripped_text) > 1 and stripped_text[1] == 'n':
                keyword_lines['vn'].append(stripped_text)
            elif len(stripped_text) == 2:
                modified_text = 'vn'
                keyword_lines['vn'].append(modified_text)
                
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
                        potential_number = remaining_text[colon_index+1:].strip()
                        if re.match(r'\d{3}/\d{6}', potential_number):
                            modified_text = 'vn' + stripped_text[2:].strip()
                            keyword_lines['vn'].append(modified_text)
                elif len(stripped_text) > 3 and stripped_text[2] == ':':
                    potential_number = stripped_text[3:].strip()
                    if re.match(r'\d{3}/\d{6}', potential_number):
                        modified_text = 'vn' + stripped_text[2:].strip()
                        keyword_lines['vn'].append(modified_text)
         
        # เช็คสำหรับ ht ตามเงื่อนไขใหม่
        elif stripped_text.startswith('ht'):
            colon_index = stripped_text.find(':')
            if colon_index != -1:
                keyword_lines['ht'].append(stripped_text)

        # เช็คสำหรับบรรทัดที่ขึ้นต้นด้วย 8 ตามด้วย p, t, w, mi
        elif stripped_text.startswith('8') and len(stripped_text) > 2:
            if stripped_text[1] in ['p', 't', 'w']:
                keyword = 'b' + stripped_text[1]  # เช่น 'bp', 'bt', 'bw'
                keyword_lines[keyword].append(stripped_text)
            elif stripped_text[1:3] == 'mi':
                keyword = 'bmi'
                keyword_lines[keyword].append(stripped_text)
        
        # แก้ไขข้อความผิดพลาดให้เป็นคำที่ถูกต้อง
        wrong_words_bun = ["buv", "8un"] 
        if stripped_text in wrong_words_bun:
            stripped_text = "bun"
        
        wrong_words_hbaic = ["hbalc", "hbaic", "h8alc", "h8aic"]
        if stripped_text in wrong_words_hbaic:
            stripped_text = "hbaic"
        
        # แก้ไขคำว่า "ชือ" เป็น "ชื่อ" และตรวจสอบบรรทัดถัดไป
        if stripped_text == "ชือ":
            stripped_text = "ชื่อ"
            keyword_lines['ชื่อ'].append(stripped_text)  # เก็บ "ชื่อ" ไว้ในคีย์เวิร์ด 'ชื่อ'
            
            # ตรวจสอบบรรทัดถัดไป
            if i + 1 < len(results):
                next_bbox, next_text, next_confidence = results[i + 1]
                next_stripped_text = next_text.strip()
                
                # ตรวจสอบว่าบรรทัดถัดไปมีคำว่า "นาย", "นางสาว" หรือคำที่ใกล้เคียง
                if re.search(r'\b(นาย|นางสาว|น.ส.)\b', next_stripped_text):
                    keyword_lines['ชื่อ'].append(next_stripped_text)  # เก็บบรรทัดถัดไปที่ตรงเงื่อนไข
                    i += 1  # ข้ามการประมวลผลบรรทัดถัดไป

        
        
            # ตรวจสอบว่า stripped_text ตรงกับคีย์เวิร์ดที่กำหนดหรือไม่
        if stripped_text in keywords:
            current_keyword = stripped_text
            # เก็บบรรทัดของคีย์เวิร์ดเองไว้เสมอ
            keyword_lines[current_keyword].append(f"{stripped_text}, Confidence: {confidence:.2f}")
        else:
            # ตรวจสอบเพิ่มเติมหากข้อความมีความเป็นไปได้ที่จะเป็นคีย์เวิร์ดใหม่
            if any(kw in stripped_text for kw in keywords):
                current_keyword = next(kw for kw in keywords if kw in stripped_text)
                # เก็บบรรทัดของคีย์เวิร์ดเองไว้เสมอ
                keyword_lines[current_keyword].append(f"{stripped_text}, Confidence: {confidence:.2f}")
            elif current_keyword:
                # ตรวจสอบว่าไม่ใช่ข้อความที่ไม่ควรถูกเก็บ เช่น ขึ้นต้นด้วยตัวเลขหรือเครื่องหมายพิเศษ
                if not re.match(r'^[.:]', stripped_text):
                    keyword_lines[current_keyword].append(stripped_text)
                else:
                    current_keyword = None

        i += 1  # เพิ่มค่า i เมื่อสิ้นสุดการประมวลผลของบรรทัดนั้น

    return keyword_lines, results

# ฟังก์ชันรวมผลลัพธ์จากหลายๆ ส่วนของภาพ
def combine_results(results_list):
    combined_keywords = {}
    for result in results_list:
        for key, lines in result.items():
            if key not in combined_keywords:
                combined_keywords[key] = []
            combined_keywords[key].extend(lines)
    return combined_keywords

def extract_keyword_values(keyword_lines):
    # คีย์เวิร์ดที่ต้องการเก็บค่า
    keyword_dict = {
        'cbc': ['wbc', 'rbc', 'hb', 'hct', 'mcv', 'mch', 'mchc', 'rdw', 'platelet', 
            'neutrophil', 'absolute neutrophil', 'lymphocyte', 'monocyte', 
            'eosinophil', 'baso', 'diff', 'report'],
    'bun': ['bun'],
    'cr': ['creatinine', 'mdrd study equation', 'mdrd equation thai', 'egfr epi'],
    'elec': ['sodium', 'potassium', 'chloride', 'tc02'],
    'lft': ['total protein', 'albumin', 'globulin', 'total bilirubin', 
            'direct bilirubin', 'alkaline phosphatase', 'sgot', 'sgpt'],
    'ua': ['color', 'transparency', 'specific gravity', 'ph', 'leukocyte', 
           'nitrite', 'urine protein', 'urine glucose', 'ketone', 
           'urobilinogen', 'bilirubin', 'erythrocyte', 'epithelium cells', 
           'urine wbc', 'urine rbc'],
    'tsh': ['tsh'],
    'ft4': ['ft4'],
    'ft3': ['ft3'],
    'pt': ['prothrombin time', 'inr'],
    'ptt': ['aptt time', 'aptt ratio'],
    'fbs': ['glucose fbs'],
    'lp': ['cholesterol', 'triglyceride', 'hdl', 'ldl-calculate'],
    'afp': ['afp'],
    'cea': ['cea'],
    'ca153': ['ca 153'],
    'ca125': ['ca 125'],
    'ca 19-9': ['ca 19-9'],
    'psa': ['psa'],
    'hn': ['hn'],
    'vn': ['vn'],
    'ชื่อ': ['ชื่อ'],
    'เพศ': ['เพศ'],
    'อายุ': ['อายุ'],
    'วันที่': ['วันที่'],
    'แพทย์': ['แพทย์'],
    'hbaic': ['hbaic'],
    'pi': ['pi'],
    'bp': ['bp'],
    'bt': ['bt'],
    'cc': ['cc'],
    'bw': ['bw'],
    'ht': ['ht'],
    'bmi': ['bmi']
    }
    
    keyword_data = {}

    for keyword, lines in keyword_lines.items():
        if keyword in keyword_dict:
            keyword_data[keyword] = {k: None for k in keyword_dict[keyword]}
        else:
            keyword_data[keyword] = {}
        
        current_measure = None
        
        for i, line in enumerate(lines):
            line = preprocess_line(line)  # เรียกใช้ฟังก์ชัน preprocess_line เพื่อทำการแทนที่ล่วงหน้า
            
            # การตรวจจับค่า HN โดยใช้ regex
            if keyword == 'hn':
                match = re.match(r'\d{2}-\d{6}', line)  # ตรวจจับรูปแบบ HN เช่น 67-006596
                if match:
                    keyword_data['hn']['hn'] = match.group()
                    continue  # ไปยังบรรทัดถัดไป
            # การตรวจจับค่า VN โดยดูบรรทัดถัดไป
            if keyword == 'vn':
                # ถ้าบรรทัดปัจจุบันมีคำว่า 'vn' ให้ไปดูค่าบรรทัดถัดไป
                if line.lower() == 'vn' and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()  # ดึงบรรทัดถัดไป
                    keyword_data['vn']['vn'] = next_line
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
            # การตรวจจับชื่อ
            if keyword == 'ชื่อ':
                # ตรวจสอบว่าบรรทัดปัจจุบันคือ "ชื่อ" หรือไม่
                if line == 'ชื่อ' and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()  # ดึงบรรทัดถัดไปที่เป็นชื่อ
                    keyword_data['ชื่อ']['ชื่อ'] = next_line
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
                
                # หากไม่มีคำว่า "ชื่อ" แต่เป็นชื่อเต็มในทันที
                elif re.match(r'^(นาย|นางสาว|นาง)\s+.+$', line):
                    keyword_data['ชื่อ']['ชื่อ'] = line.strip()
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
                
            # การตรวจจับเพศ
            if keyword == 'เพศ':
                # ตรวจสอบว่าบรรทัดนี้มีเพศ เช่น "ชาย" หรือ "หญิง"
                match = re.match(r'^(ชาย|หญิง)$', line.strip())
                if match:
                    keyword_data['เพศ']['เพศ'] = match.group(1)
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
                
            # การตรวจจับอายุ
            if keyword == 'อายุ':
                # ใช้ regex เพื่อตรวจจับข้อมูลอายุที่มีคำว่า 'ปี' ตามด้วยข้อมูลอื่น ๆ หรือไม่มี
                match = re.search(r'(\d+)\s*ปี', line)
                if match:
                    keyword_data['อายุ']['อายุ'] = match.group(1)  # เก็บเฉพาะตัวเลขของอายุ (ปี)
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
                
            # การตรวจจับวันที่
            if keyword == 'วันที่':
                # ใช้ regex เพื่อตรวจจับวันที่ในรูปแบบเช่น "15 ก.ค. 67"
                match = re.match(r'\d{1,2}\s+[ก-ฮ]+\.\s+\d{2}', line.strip())
                if match:
                    keyword_data['วันที่']['วันที่'] = match.group()
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
            
            # การตรวจจับข้อมูลแพทย์
            elif keyword == 'แพทย์':
                # ตรวจจับข้อมูลชื่อแพทย์ที่มีคำนำหน้า (เช่น ผศ.นพ, นส.)
                match = re.match(r'^(ผศ\.นพ|นพ|นส\.|นาย|นางสาว|นาง)\s+[ก-ฮ]+.*', line.strip())
                if match:
                    keyword_data['แพทย์']['แพทย์'] = line.strip()
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
                
            # การตรวจจับค่า CA 19-9
            if keyword == 'ca 19-9':
                # ตรวจสอบว่าบรรทัดแรกมีชื่อการทดสอบ
                if re.search(r'ca 19-9', line, re.IGNORECASE) and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()  # ดึงบรรทัดถัดไปที่เป็นค่าผลลัพธ์
                    keyword_data['ca 19-9']['ca 19-9'] = next_line
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
                
            # การตรวจจับค่า BP
            if keyword == 'bp':
                # ใช้ regex เพื่อตรวจจับค่าความดันโลหิตในรูปแบบ '119/76'
                match = re.search(r'(\d{2,3})/(\d{2,3})', line)
                if match:
                    bp_value = f"{match.group(1)}/{match.group(2)}"
                    keyword_data['bp']['bp'] = bp_value
                    continue  # ไปยังบรรทัดถัดไปหลังจากดึงค่าแล้ว
            
            if keyword in keyword_dict:
                keywords = keyword_dict[keyword]
                match = re.match(r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b', line, re.IGNORECASE)
                if match:
                    current_measure = match.group(1).lower()
                elif current_measure:
                    clean_value = clean_and_convert_value(line)
                    if re.match(r'^-?\d+(?:\.\d+)?$', clean_value):
                        keyword_data[keyword][current_measure] = clean_value
                        current_measure = None
                    else:
                        # ใช้ฟังก์ชัน get_next_decimal เพื่อหาค่าที่เป็นตัวเลขทศนิยมถัดไป
                        next_value = get_next_decimal(lines, i + 1)
                        if next_value:
                            keyword_data[keyword][current_measure] = next_value
                            current_measure = None
            else:
                if re.match(r'\b\w+\b', line, re.IGNORECASE):
                    current_measure = line.split()[0]
                elif current_measure:
                    keyword_data[keyword][current_measure] = line.strip()
                    current_measure = None
    
    return keyword_data

def clean_and_convert_value(value):
    """ฟังก์ชันเพื่อทำความสะอาดและแปลงค่าให้เป็นรูปแบบทศนิยมที่ถูกต้อง"""
    value = value.strip().lower()
    if ',' in value:
        value = value.replace(',', '.')
    if value.startswith('o.') or value.startswith('o,'):
        value = '0.' + value[2:]
    match = re.match(r'^-?\d+(\.\d+)?', value)
    if match:
        value = match.group(0)
    else:
        value = ''
    return value

def get_next_decimal(lines, start_index):
    """ฟังก์ชันเพื่อตรวจสอบบรรทัดถัดไปจนกว่าจะเจอค่าที่เป็นตัวเลขทศนิยม"""
    for line in lines[start_index:]:
        clean_value = clean_and_convert_value(line)
        if re.match(r'^-?\d+(?:\.\d+)?$', clean_value):
            return clean_value
    return None

def preprocess_line(line):
    """ฟังก์ชันเพื่อแทนที่ข้อความที่มีความใกล้เคียงกับคีย์เวิร์ดที่ต้องการ"""
    replacements = {
        'r8c': 'rbc',
        'rd!': 'rdw',
        'neulroph|': 'neutrophil',
        'alymphocyte': 'lymphocyte',
        'protrombin time': 'prothrombin time',
        '8as0': 'baso',
        '..7': '0.7',
        '1oo.00': '100.00',
        'a.': '0.',
        'ep|(ckd epi)': 'epi'
    }
    
    for key, value in replacements.items():
        line = line.replace(key, value)
    return line

def print_result(result):
    for category, values in result.items():
        print(f"{category.upper()}:")
        for key, value in values.items():
            print(f"  {key}: {value}")
        print()  # เพิ่มบรรทัดว่างระหว่างหมวดหมู่


if __name__ == "__main__":
    image_path = "opdcard/opd1 (17).jpg"  # ใช้พาธรูปที่คุณอัพโหลดมา
    
    # คีย์เวิร์ดสำหรับแต่ละส่วน
    keywords1 = ["cbc", "bun", "cr", "elec", "lft", "ua", "tsh", " ft4", "ft3", "pt", "ptt", "hbaic", "fbs", "lp", "afp", "cea", "ca153", "ca125", "ca 19-9", "psa"]
    keywords2 = ["opd","แพทย์","date","bp","pr","bw", "ht", "bt", "rr", "bmi", "o2sat"]
    keywords3 = ["hn", "vn", "ชื่อ", "เพศ", "อายุ"]

    # กำหนดพิกัดของกรอบที่ต้องการอ่าน
    bounding_box_1 = (1055, 302, 540,1400 )  # กรอบของ lab  #(1550, 200, 1200, 2800)  # กรอบสำหรับส่วนที่ 1 
    bounding_box_2 = (115,292,923,350) # กรอบของการอ่าน hn #(100, 400, 1500, 1400)  # กรอบสำหรับส่วนที่ 2
    bounding_box_3 = (100, 30, 1500, 100) # กรอบของการอ่าน opd (50, 50, 2400, 400)  # กรอบสำหรับส่วนที่ 3
    

    # อ่านและตรวจสอบข้อความในกรอบที่กำหนด
    keyword_lines_1, detected_texts_1 = read_image_and_check_keywords(image_path, keywords1, bounding_box_1)
    keyword_lines_2, detected_texts_2 = read_image_and_check_keywords(image_path, keywords2, bounding_box_2)
    keyword_lines_3, detected_texts_3 = read_image_and_check_keywords(image_path, keywords3, bounding_box_3)

    # รวมผลลัพธ์ทั้งหมด
    combined_keyword_lines = combine_results([keyword_lines_1, keyword_lines_2, keyword_lines_3])
    
    # ประมวลผลข้อมูลที่ดึงออกมา
    extracted_data = extract_keyword_values(combined_keyword_lines)
    
    print_result(extracted_data)

    # แสดงผลลัพธ์ที่รวมกันแล้ว
    # for keyword, lines in combined_keyword_lines.items():
    #     if lines:
    #         print(f"Lines under keyword '{keyword.upper()}':")
    #         for line in lines:
    #             print(f"- {line}")
    #         print()  # เพิ่มบรรทัดว่างหลังจากแสดงผลแต่ละคีย์เวิร์ด
    #     else:
    #         print(f"No text found under keyword '{keyword.upper()}'\n")

    # แสดงผลข้อความทั้งหมดที่ตรวจจับได้จากภาพ
    # print("All detected text: ")
    # for bbox, text, confidence in detected_texts_1 + detected_texts_2 + detected_texts_3:
    #     print(f"Text: {text}, Confidence: {confidence:.2f}")
        
  
