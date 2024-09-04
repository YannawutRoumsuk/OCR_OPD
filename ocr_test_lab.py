import re

def clean_and_convert_value(value):
    """ฟังก์ชันเพื่อทำความสะอาดและแปลงค่าให้เป็นรูปแบบทศนิยมที่ถูกต้อง"""
    value = value.strip().lower()
    if ',' in value:
        value = value.replace(',', '.')
    if value.startswith('o.') or value.startswith('o,'):
        value = '0.' + value[2:]
    # ใช้ regex เพื่อตัดส่วนที่ไม่ใช่ตัวเลขทศนิยมออก
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
        '8as0': 'baso',  # ใช้เพื่อแทนที่ 8as0 ด้วย baso
        '..7': '0.7',     # แทนที่ค่า ..7 ด้วย 0.7
        '1oo.00': '100.00', # แทนที่ค่าที่พิมพ์ผิด
        'a.': '0.',        # แทนที่ "a." ด้วย "0."
        'ep|(ckd epi)': 'epi'  # แก้ไข "ep|(ckd epi)" เป็น "epi"
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
    cbc_keywords = ['wbc', 'rbc', 'hb', 'hct', 'mcv', 'mch', 'mchc', 'rdw', 'platelet', 
                    'neutrophil', 'absolute neutrophil', 'lymphocyte', 'monocyte', 
                    'eosinophil', 'baso', 'diff', 'report']
    bun_keywords = ['bun']
    cr_keywords = ['creatinine', 'mdrd study equation', 'mdrd equation thai', 'egfr epi']
    elec_keywords = ['sodium', 'potassium', 'chloride', 'tc02']
    lft_keywords = ['total protein', 'albumin', 'globulin', 'total bilirubin', 
                    'direct bilirubin', 'alkaline phosphatase', 'sgot', 'sgpt']
    ua_keywords = ['color', 'transparency', 'specific gravity', 'ph', 'leukocyte', 
                   'nitrite', 'urine protein', 'urine glucose', 'ketone', 
                   'urobilinogen', 'bilirubin', 'erythrocyte', 'epithelium cells', 
                   'urine wbc', 'urine rbc']
    tsh_keywords = ['tsh']
    ft4_keywords = ['ft4']
    ft3_keywords = ['ft3']
    pt_keywords = ['prothrombin time', 'inr']
    ptt_keywords = ['aptt time', 'aptt ratio']
    fbs_keywords = ['glucosefbs']
    lp_keywords = ['cholesterol', 'triglyceride', 'hdl', 'ldl-calculate']
    afp_keywords = ['afp']
    cea_keywords = ['cea']
    ca153_keywords = ['ca 153']
    ca125_keywords = ['ca 125']
    ca199_keywords = ['ca 19-9']
    psa_keywords = ['psa']
    
    keyword_data = {}

    for keyword, lines in keyword_lines.items():
        if keyword == 'cbc':
            keyword_data[keyword] = {k: None for k in cbc_keywords}
        elif keyword == 'bun':
            keyword_data[keyword] = {k: None for k in bun_keywords}
        elif keyword == 'cr':
            keyword_data[keyword] = {k: None for k in cr_keywords}
        elif keyword == 'elec':
            keyword_data[keyword] = {k: None for k in elec_keywords}
        elif keyword == 'lft':
            keyword_data[keyword] = {k: None for k in lft_keywords}
        elif keyword == 'ua':
            keyword_data[keyword] = {k: None for k in ua_keywords}
        elif keyword == 'tsh':
            keyword_data[keyword] = {k: None for k in tsh_keywords}
        elif keyword == 'ft4':
            keyword_data[keyword] = {k: None for k in ft4_keywords}
        elif keyword == 'ft3':
            keyword_data[keyword] = {k: None for k in ft3_keywords}
        elif keyword == 'pt':
            keyword_data[keyword] = {k: None for k in pt_keywords}
        elif keyword == 'ptt':
            keyword_data[keyword] = {k: None for k in ptt_keywords}
        elif keyword == 'fbs':
            keyword_data[keyword] = {k: None for k in fbs_keywords}
        elif keyword == 'lp':
            keyword_data[keyword] = {k: None for k in lp_keywords}
        elif keyword == 'afp':
            keyword_data[keyword] = {k: None for k in afp_keywords}
        elif keyword == 'cea':
            keyword_data[keyword] = {k: None for k in cea_keywords}
        elif keyword == 'ca153':
            keyword_data[keyword] = {k: None for k in ca153_keywords}
        elif keyword == 'ca125':
            keyword_data[keyword] = {k: None for k in ca125_keywords}
        elif keyword == 'ca19-9':
            keyword_data[keyword] = {k: None for k in ca199_keywords}
        elif keyword == 'psa':
            keyword_data[keyword] = {k: None for k in psa_keywords}
        else:
            keyword_data[keyword] = {}
        
        current_measure = None
        
        for i, line in enumerate(lines):
            line = preprocess_line(line)  # เรียกใช้ฟังก์ชัน preprocess_line เพื่อทำการแทนที่ล่วงหน้า
            
            if keyword in ['cbc', 'bun', 'cr', 'elec', 'lft', 'ua', 'tsh', 'ft4', 'ft3', 'pt', 'ptt', 'fbs', 'lp', 'afp', 'cea', 'ca153', 'ca125', 'ca199', 'psa']:
                keywords = eval(f"{keyword}_keywords")
                match = re.match(r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b', line, re.IGNORECASE)
                if match:
                    current_measure = match.group(1).lower()
                elif current_measure:
                    clean_value = clean_and_convert_value(line)
                    if re.match(r'^-?\d+(?:\.\d+)?$', clean_value):
                        keyword_data[keyword][current_measure] = clean_value
                        current_measure = None
                    else:
                        # Use the get_next_decimal function to find the next valid number
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



# ตัวอย่างข้อมูลเพื่อทดสอบฟังก์ชัน
sample_keyword_lines_opd = {
    "cbc": [
        "cc",
        "case",
        "wbc [#.40-10.30x10 3cel/ul]",
        "9.83",
        "r8c [4,00-5.50x10 6cell ul]",
        "(4.70`",
        "แพทย์นัดนอน ร.พ.เพื่อผ่าตัด craiotomy + tumor removal under ga",
        "hb [12.0-14.99/๔|]",
        "13.6",
        "pi",
        "case cerebellum mass left",
        "hct [37.0-45,7%]",
        "39.7",
        "ไม่มีไข้ไอเจ็บคอน้ำมูก., งดยา plavix ตังแต่ 19/7/67 03 ก.ค. 67",
        "09.26 น.",
        "mcv [80.4-95,9{1]",
        "84.5",
        "(5/7/67), อาการทัวไป ปกติ",
        "mch |25,0-31.2pg]",
        "28.9",
        "mchc [30,2-34.2g/d1]",
        "34.3 - h",
        "zmmhpr",
        "9a/min rr",
        "2o/min",
        "bw",
        "51 kg.",
        "ht: 145 cm",
        "bmi",
        "24.26",
        "rd![11,7-15.0%]",
        "11.8",
        "bp",
        "120/7",
        "platelet [\"79.0-435.0x10 3cell/ul",
        "(294.0)",
        "37 : 36.4 c",
        "hc",
        "o2sat",
        "neulroph| [40,0-73.1%]",
        "66.4",
        "absolute neutrophil 51.80-6.8010",
        "6.53",
        "ic)",
        "alymphocyte [20.347.9%]",
        "27.6",
        "pe",
        "monocyte [3.4-9,7%]",
        "a.4",
        "eosinophil [0.4-7,5%]",
        "0.9",
        "wnl",
        "8as0 [0.2-1.^%]",
        "..7",
        "diff 100%",
        "1oo.00",
        "heent",
        "report nrbc%",
        "o.0"
    ],
    "bun": [
        "dx",
        "bun [8.0-23.0mg/dl]",
        "13.1"
    ],
    "cr": [
        "creatinine [0.51-0.95mg/dl]",
        "0.72",
        "mdrd study equation",
        "92.97",
        "mdrd equation thai",
        "79,09",
        "egfr ep|(ckd epi)",
        "90.67"
    ],
    "elec": [
        "sodium [136-145mmo/l]",
        "135 - l",
        "potassium [3.4-4.5mmol/l]",
        "4.4",
        "chloride [98-107mmol/l]",
        "95 - l",
        "tc02 [22-29mmo|/l]",
        "27",
        "นัดครั้งต่อไปวันที่",
        "คำแนะนำหลังการตรวจรักษา",
        "การใช้ยา",
        "การมาตรวจตามนัด",
        "การดูแลก่อน/หลังผ่าตัด",
        "อาการผิดปกติที่ควรรีบมาพบแพทย์",
        "การดูแลแผล",
        "ไจตา",
        "นพ",
        "พีรศิลปโตวชิราภรณ์",
        "ลงชอ",
        ".พยาบาล",
        "ว54759",
        "สูบบุหรี่.",
        "นส.",
        "พว.กังสฑาล"
    ],
    "pt": [
        "heart",
        "protrombin time [10.90-13.30$e6",
        "11.00",
        "inr",
        "0.89",
        "lung"
    ],
    "ptt": [
        "aptt time [21,30-31,10$ecs.]",
        "21.00 - l_",
        "abdomen",
        "pow+",
        "นส",
        "อัฏษฎาพร อันเกษม(",
        "extremities",
        "hbalc",
        "hba1c by hplc [4,5-5.7%]",
        "10.8",
        "orther",
        "นาย นพดล ช้างน้อย( ทน"
    ]
}

def print_result(result):
    for category, values in result.items():
        print(f"{category.upper()}:")
        for key, value in values.items():
            print(f"  {key}: {value}")
        print()  # เพิ่มบรรทัดว่างระหว่างหมวดหมู่
# Extract the keyword values
extracted_data = extract_keyword_values(sample_keyword_lines_opd)
print_result(extracted_data)




