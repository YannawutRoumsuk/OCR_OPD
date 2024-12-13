import sys
import cv2
import easyocr
import re
from dotenv import load_dotenv
import os

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
        
        # แก้ไขข้อความผิดพลาดให้เป็นคำที่ถูกต้อง
        wrong_words_bun = ["buv", "8un"] 
        if stripped_text in wrong_words_bun:
            stripped_text = "bun"
        
        wrong_words_hbaic = ["hbalc", "hbaic", "h8alc", "h8aic"]
        if stripped_text in wrong_words_hbaic:
            stripped_text = "hbaic"
            
        wrong_words_อายุ = ["อาย","date"]
        if stripped_text in wrong_words_อายุ:
            stripped_text = "อายุ"
        
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

        # เช็คสำหรับ hn ตามเงื่อนไขใหม่
        if stripped_text.startswith('h') and len(stripped_text) > 2:
            if len(stripped_text) > 3 and stripped_text[2] == ' ':
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
            if len(stripped_text) > 1 and stripped_text[1] == 'n':
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
                        
        # เช็คสำหรับ pi, cc, ht ตามเงื่อนไขใหม่
        elif stripped_text.startswith(('pi', 'cc', 'ht')):
            colon_index = stripped_text.find(':')
            if colon_index != -1:
                keyword_lines[stripped_text[:2]].append(stripped_text)
                
        # เช็คสำหรับบรรทัดที่ขึ้นต้นด้วย 8 ตามด้วย p, t, w, mi
        elif stripped_text.startswith('8') and len(stripped_text) > 2:
            if stripped_text[1] in ['p', 't', 'w']:
                keyword = 'b' + stripped_text[1]  # เช่น 'bp', 'bt', 'bw'
                keyword_lines[keyword].append(stripped_text)
            elif stripped_text[1:3] == 'mi':
                keyword = 'bmi'
                keyword_lines[keyword].append(stripped_text)
            elif stripped_text[1:3] == 'un':
                keyword = 'bun'
                keyword_lines[keyword].append(stripped_text)

        elif stripped_text in keywords:
            current_keyword = stripped_text
        elif current_keyword:
            keyword_lines[current_keyword].append(stripped_text)
            if stripped_text in keywords:
                current_keyword = stripped_text

        i += 1

    return keyword_lines, results

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

def get_next_decimal(lines, start_index):
    """ฟังก์ชันเพื่อตรวจสอบบรรทัดถัดไปจนกว่าจะเจอค่าที่เป็นตัวเลขทศนิยม"""
    for line in lines[start_index:]:
        clean_value = clean_and_convert_value(line)
        if re.match(r'^-?\d+(?:\.\d+)?$', clean_value):
            return clean_value
    return None

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

def print_result(result):
    for category, values in result.items():
        print(f"{category.lower()}:")
        for key, value in values.items():
            key = key.lower().replace(" ", "_").replace("-", "_")
            if key == "diff":
                key = "diff_100"
            elif key == "report":
                key = "report_nrbc"
            elif key == "egfr_epi":
                key = "egfr_epi_ckd_dpi"
            elif key == "sgot":
                key = "sgot_ast"
            elif key == "sgpt":
                key = "sgpt_alt"
            elif key == "color":
                key = "color_ue"
            elif key == "ca_19_9":
                key = "ca19_9"
            print(f"  {key}: {value}")
        print()  # เพิ่มบรรทัดว่างระหว่างหมวดหมู่

if __name__ == "__main__":
        # โหลดค่าจาก .env
    load_dotenv()
    image_path = "opd3_edit.jpg"
    print(f"Image path: {image_path}")
    keywords = ["hn", "vn", "ชื่อ", "เพศ", "อายุ", "วันที่", "แพทย์", "cbc", "bun", "cr", "elec", "lft", "ua", "tsh", "ft4", "ft3", "pt", "ptt","hbaic", "fbs", "lp", "afp", "cea", "ca153", "ca125", "ca 19-9", "psa", "pi", "bp", "bt", "cc", "bw", "ht", "bmi"]

    # อ่านและตรวจสอบข้อความในภาพ
    keyword_lines, detected_texts = read_image_and_check_keywords(image_path, keywords)
    
    # ประมวลผลข้อมูลที่ดึงออกมา
    extracted_data = extract_keyword_values(keyword_lines)
    
    # พิมพ์ผลลัพธ์
    # แสดงผลข้อความภายใต้แต่ละคีย์เวิร์ด
    for keyword, lines in keyword_lines.items():
        if lines:
            print(f"Lines under keyword '{keyword.upper()}':")
            for line in lines:
                print(f"- {line}")
            print()  # เพิ่มบรรทัดว่างหลังจากแสดงผลแต่ละคีย์เวิร์ด
        else:
            print(f"No text found under keyword '{keyword.upper()}'\n")
            
    print("-----------------------------------------------------------")
    print_result(extracted_data)
    
    # # แสดงผลข้อความทั้งหมดที่ตรวจจับได้จากภาพ
    # print("-------------------------------------------------------------")
    # print("All detected text: ")
    # for bbox, text, confidence in detected_texts:
    #     print(f"Text: {text}, Confidence: {confidence:.2f}")

