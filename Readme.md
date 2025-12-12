Run the Dockeriaze Image that has been Pushed to DockerHub using the below command  
```bash
docker run -d -p 5000:5000 ozairkhan1/pescoencoder:v2
```
The App can be access using The following URL
```bash
https://pesco-base64-encoderdecoder.onrender.com
```
# Image Converter Pro

## Overview
A professional web application for converting between base64-encoded text files and ZIP archives containing extracted images. Features a modern, visually appealing interface with two-way conversion capabilities.

## Features
- **TXT to ZIP**: Upload encoded .txt files → Download ZIP archive with all extracted images
- **ZIP to TXT**: Upload ZIP archive → Download re-encoded .txt file
- Modern gradient UI with drag-and-drop file upload
- Automatic file naming convention preserved

## Usage
Access the web app at the provided URL. The interface has two cards:

1. **Text to ZIP** (left card): Drop or select a .txt file containing base64-encoded images
2. **ZIP to Text** (right card): Drop or select a previously exported .zip file to re-encode

## Naming Convention
Images follow the pattern: `{YEAR_MONTH}{SUBDIV_CODE}{SEQUENCE}{METER}{DIRECTION}.jpg`
Example: `202512122126523010011E.jpg`

## Technical Details

### Files
- `app.py` - Flask backend with conversion routes
- `templates/index.html` - Modern responsive frontend UI
- `uploads/` - Temporary file storage
- `extract_images.py` - Legacy CLI script (not used by web app)

### Routes
- `GET /` - Main page
- `POST /convert-txt-to-zip` - Convert .txt to .zip with images
- `POST /convert-zip-to-txt` - Convert .zip back to encoded .txt

### ZIP Structure
Exported ZIP files contain:
- `images/` folder with all extracted .jpg files
- `header.txt` - Original file header
- `metadata.json` - Record metadata for re-encoding

## Recent Changes
- 2025-12-06: Major redesign with professional UI and dual conversion workflow
- Removed image gallery display in favor of direct ZIP download
- Added reverse conversion (ZIP to TXT) functionality
