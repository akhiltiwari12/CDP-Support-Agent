# CDP Support Agent Chatbot

## Overview
The **CDP Support Agent Chatbot** is a Flask-based chatbot designed to assist users with "how-to" questions related to four major **Customer Data Platforms (CDPs):**
- **Segment**
- **mParticle**
- **Lytics**
- **Zeotap**

The chatbot extracts relevant information from the official documentation of these platforms to provide accurate and actionable responses. It also supports cross-CDP comparisons and advanced queries related to CDP functionalities.

---

## Features
### 1. Answer "How-to" Questions
- Understands and processes user queries regarding **how to perform specific tasks** in Segment, mParticle, Lytics, and Zeotap.
- Examples:
  - *"How do I set up a new source in Segment?"*
  - *"How can I create a user profile in mParticle?"*
  - *"How do I build an audience segment in Lytics?"*
  - *"How can I integrate my data with Zeotap?"*

### 2. Extract Information from Documentation
- Retrieves relevant content from official documentation:
  - [Segment Docs](https://segment.com/docs/?ref=nav)
  - [mParticle Docs](https://docs.mparticle.com/)
  - [Lytics Docs](https://docs.lytics.com/)
  - [Zeotap Docs](https://docs.zeotap.com/home/en-us/)
- Uses **text indexing** for efficient searching.

### 3. Handle Variations in Questions
- Processes different phrasing styles and lengths without breaking.
- Filters out **irrelevant** questions (e.g., *"Which movie is releasing this week?"*).


---

## Project Structure
```
cdp-support-agent/
├── data/
│   ├── raw/                      # Raw scraped documentation
│   ├── processed/                # Processed text chunks
│   └── index/                    # Search index files
├── scripts/
│   ├── scraper.py                # Scraper for documentation
│   ├── processor.py              # Processes scraped data
│   └── indexer.py                # Builds search index
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css
│   │   └── js/
│   │       └── chat.js
│   ├── templates/
│   │   └── index.html            # Chatbot UI
│   ├── query_engine.py           # Query processing logic
│   ├── response_generator.py     # Formats chatbot responses
│   └── app.py                    # Flask app
├── requirements.txt              # Dependencies
└── README.md                     # Project documentation
```

---

## Installation
### 1. Clone the Repository
```sh
git clone https://github.com/yourusername/cdp-support-agent.git
cd cdp-support-agent
```

### 2. Set Up a Virtual Environment *(Optional but Recommended)*
```sh
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Run the Application
```sh
python -m app.app
```
- The chatbot will be available at **http://127.0.0.1:5000/**

---

## Usage
1. **Open the Chat Interface** (`index.html`)
2. **Ask "how-to" questions** related to CDPs.
3. **Receive accurate responses** extracted from official documentation.
4. **Ask for comparisons** between CDPs if needed.



---

## Future Enhancements
- **Integrate LLM (e.g., GPT-4) for better NLP understanding**.
- **Enhance UI with real-time chat updates**.
- **Improve indexing & retrieval for faster response times**.


