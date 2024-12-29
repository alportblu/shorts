# YouTube Shorts Generator

## Overview
YouTube Shorts Generator is a web application that simplifies the creation of YouTube Shorts videos. Users can paste a YouTube video link, provide their OpenAI API key, and generate highlights and subtitles effortlessly.

## Features
- **YouTube Link Support**: Paste the URL of any YouTube video to begin processing.
- **Highlight Extraction**: Automatically identifies and extracts key moments from videos.
- **Subtitle Generation**: Generates accurate subtitles for your videos using OpenAI.
- **User Management**: Allows users to register, log in, and save their projects.
- **Download Options**: Provides options to download processed videos with highlights and subtitles.
- **Audio & Transcript Processing**: Extracts audio and generates transcripts for videos.

## Project Structure
```
.
├── app.py                 # Main application logic
├── requirements.txt       # Project dependencies
├── static/                # Static files (CSS, JavaScript)
├── templates/             # HTML templates for the frontend
├── utils/                 # Utility scripts for processing videos
├── models/                # Data models for users and saved videos
├── data/                  # Contains application data (e.g., users.json)
└── tmp/                   # Temporary files
```

## Prerequisites
- Python 3.10+
- pip (Python package manager)
- OpenAI API Key

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/alportblu/shorts.git
   cd youtube-shorts-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory with the following content:
     ```env
     OPENAI_API_KEY=your_openai_api_key_here
     ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://127.0.0.1:5000`.

## Usage
1. **Enter YouTube Link**: Paste the URL of a YouTube video into the input field.
2. **Provide API Key**: Enter your OpenAI API key to enable subtitle generation.
3. **Generate Shorts**: Click the "Generate Shorts" button to process the video.
4. **Download**: Download the processed video with highlights and subtitles.

## Dependencies
- Flask: Web framework
- OpenCV: Computer vision library
- ffmpeg: Multimedia framework for video/audio processing
- OpenAI API: For subtitle generation
- Various Python libraries (see `requirements.txt`)

## Contributing
We welcome contributions! Please fork the repository and submit a pull request with your improvements.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions or feedback, please contact us


## Images
![image](https://github.com/user-attachments/assets/8075f14b-b954-49df-bb63-7b650025718b)
![image](https://github.com/user-attachments/assets/c674fbe4-a928-4caa-8b3b-2a80bb27ed3d)
![image](https://github.com/user-attachments/assets/1ab1572e-e9a4-4d1b-a0c7-30a0a3a1bdfb)






