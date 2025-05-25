# Backend Environment Setup Guide

This guide provides instructions for setting up the backend environment for the application.

## 1. Cloning the Repository

To get started, clone the repository to your local machine using the following command:

```bash
git clone https://your-repository-url.git
cd <repository-directory>
```
Replace `https://your-repository-url.git` with the actual URL of the repository and `<repository-directory>` with the name of the directory created by the clone command.

## 2. Backend Dependencies

The backend application relies on several Python libraries. These are categorized into standard libraries (usually part of Python installations) and external packages that require installation via `pip`.

**Standard Python Libraries:**

*   `sqlite3` (for database operations)
*   `json` (for handling JSON data)
*   `os` (for operating system interactions, like file paths)
*   `tempfile` (for creating temporary files)
*   `sys` (for system-specific parameters and functions)
*   `pathlib` (for object-oriented filesystem paths)
*   `re` (for regular expression operations)
*   `logging` (for application logging)
*   `typing` (for type hinting: List, Dict, Union, Any)
*   `time` (for time-related functions)

**External Packages (requires pip installation):**

*   `Flask` (web framework)
*   `Flask-CORS` (Flask extension for Cross-Origin Resource Sharing)
*   `Pillow` (PIL fork, for image processing, used by `fitz`)
*   `PyMuPDF` (fitz, for PDF processing)
*   `PyPDF2` (for PDF manipulation)
*   `extractous` (for text and data extraction from documents)
*   `langchain` (framework for developing applications powered by language models)
*   `langchain_community` (community-contributed components for Langchain)
*   `langchain_google_genai` (Google Generative AI integrations for Langchain)
*   `langchain_core` (core components for Langchain)
*   `google-generativeai` (Google's Generative AI SDK)
*   `PyYAML` (for loading configuration files like `config.yaml`)
*   `chromadb` (vector database for RAG functionality)

## 3. Installation Instructions

It is highly recommended to use a Python virtual environment to manage project dependencies and avoid conflicts with system-wide packages.

**Create and Activate a Virtual Environment:**

```bash
# For Linux/macOS
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

**Install Dependencies using pip:**

Once the virtual environment is activated, install the required packages using the following command:

```bash
pip install Flask Flask-CORS Pillow PyMuPDF PyPDF2 extractous langchain langchain_community langchain_google_genai langchain_core google-generativeai PyYAML chromadb
```

## 4. Running the Flask Application

To run the backend Flask application, navigate to the project's root directory (if you are not already there) and execute the following command:

```bash
python backend_src/main.py
```

The application will start, and by default, it will be accessible at `http://127.0.0.1:5000/`. This is specified in the `main.py` file (`app.run(debug=True, port=5000, use_reloader=False)`).

## 5. Database Setup (SQLite)

The application uses SQLite for its database needs. SQLite is a file-based database system, meaning the databases are stored as single files on your local system.

*   **Automatic Directory Creation:** The `main.py` file includes logic to create a `Database` directory if it doesn't already exist (`os.makedirs("Database", exist_ok=True)`). This directory will store the SQLite database files.
*   **Database Management:** The primary database files (e.g., `Questions.db`, `<student_id>.db`) are created and managed by the application's code, primarily within `backend_src/database.py`. When you run the application and perform operations like uploading question papers or student answers, the necessary tables and data will be populated automatically.
*   **Writable Directory:** Ensure that the `Database` directory within `backend_src` is writable by the application, as it needs to create and modify files within it.
*   **ChromaDB:** Additionally, the application uses ChromaDB for its Retrieval Augmented Generation (RAG) capabilities. You might notice a `backend_src/instance/vector_db` directory containing files related to ChromaDB, which is used by `gemi_rag.py`. This is also managed by the application.

No manual SQLite setup is typically required beyond ensuring the application has the necessary permissions to create and write to files in the `backend_src/Database/` and `backend_src/instance/vector_db/` directories.

## 6. API Key Configuration

The application requires API keys for services like Google Gemini for its generative AI features.

**Create `configs/config.yaml`:**

1.  Create a directory named `configs` in the root of the project repository (i.e., at the same level as `backend_src`).
2.  Inside the `configs` directory, create a file named `config.yaml`.

**Add API Keys to `config.yaml`:**

Open `configs/config.yaml` and add your API keys in the following format:

```yaml
GEMINI_API_KEY: 'your_gemini_api_key_here'
# Add any other API keys if identified as necessary.
# For example, if a specific Groq API key is used, add it here:
# GROQ_API_KEY: 'your_groq_api_key_here'
```

**Important:**

*   Replace `'your_gemini_api_key_here'` with your actual Google Gemini API key.
*   If other services requiring API keys are used (e.g., Groq, though not explicitly listed as a direct dependency in the provided file analysis for key loading, it's good practice to manage all keys here), add them similarly.
*   The `backend_src/main.py` file calls `load_config('../configs/config.yaml')`. This function, defined in `backend_src/utils/get_keys.py`, loads the keys from this YAML file and sets them as environment variables for the application to use.

Ensure this file is correctly populated before running the application to enable all features that rely on these external AI services.
