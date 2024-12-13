# OCR Scripts for OPD Cards 

## Overview
This repository contains Python scripts for Optical Character Recognition (OCR) specifically designed for reading OPD cards and blood test results using EasyOCR as the primary tool.

## Scripts

### `ocr_without_boxs.py`
Basic OCR script for reading OPD card information

- General character recognition
- Reads basic information from OPD cards
- Medium accuracy
- Suitable for simple structured documents

### `ocr_with_boxs.py`
Advanced OCR script for reading blood test results

- Focuses on specific blood test value extraction
- Uses bounding boxes to enhance accuracy
- Extracts precise information from blood test results
- Reduces errors in numeric value recognition

## Key Differences

| Feature | `ocr_without_boxs.py` | `ocr_with_boxs.py` |
|---------|----------------------|-------------------|
| Document Type | OPD Card | OPD Card |
| Accuracy | Medium | High |
| Bounding Box | No | Yes |
| Data Extraction | General | Specific |

## Requirements
- Python 3.x
- EasyOCR
- OpenCV
- Numpy
- Pandas (for data management)

## Installation
```bash
pip install easyocr opencv-python numpy pandas
```

## Usage
```bash
python ocr_without_boxs.py [path_to_opd_card]
python ocr_with_boxs.py [path_to_blood_test_result]
```

## Special Features
- Supports static image files (JPEG, PNG)
- Processes Thai and English languages
- Saves results in CSV or Excel files

## Contributing
Welcome pull requests for improving accuracy and additional document support
