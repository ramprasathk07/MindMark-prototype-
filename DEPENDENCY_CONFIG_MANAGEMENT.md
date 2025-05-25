# Dependency and Configuration Management Guide

This document outlines the practices for managing external dependencies and application configuration for the Python backend.

## 1. Configuration Management

Effective configuration management is crucial for security, flexibility, and maintainability.

### 1.1. Centralized Configuration File

*   **Primary Configuration File:** As detailed in `ENVIRONMENT_SETUP.md`, primary application configuration, especially sensitive data like API keys and environment-specific parameters, **is and must be centralized** in the `configs/config.yaml` file. This file is located in the `configs/` directory at the root of the project.

*   **Current Structure (from `ENVIRONMENT_SETUP.md`):**
    ```yaml
    GEMINI_API_KEY: 'your_gemini_api_key_here'
    # Potentially GROQ_API_KEY: 'your_groq_api_key_here'
    ```

### 1.2. Loading Configuration

*   **Mechanism:** The configuration from `configs/config.yaml` is loaded into environment variables at runtime.
*   **Implementation:** This is handled by the `load_config(file_path)` function in `backend_src/utils/get_keys.py`.
*   **Usage:** The `main.py` file calls `load_config('../configs/config.yaml')` at startup to make these configurations available to the application (e.g., for `explain_gem.py` and `gemi_rag.py` to access `GEMINI_API_KEY`).

### 1.3. Expanding Centralized Configuration (Recommendation)

To maintain a single source of truth for all configurable aspects of the application, it is highly recommended that any other application-level settings currently hardcoded should be moved to `configs/config.yaml`.

*   **Examples of Settings to Centralize:**
    *   Default LLM model names (e.g., `"gemini-2.0-flash-exp"` currently hardcoded in `main.py`, `explain_gem.py`, and `gemi_rag.py`).
    *   File paths for generated files or temporary storage, if they need to be configurable (e.g., `generated_files/`, `Database/`, `backend_src/instance/vector_db`).
    *   Default LLM parameters (e.g., temperature, top_p) if they need to be tuned without code changes.

*   **Example of Extended `configs/config.yaml` Structure:**
    ```yaml
    # API Keys (as before)
    GEMINI_API_KEY: 'your_gemini_api_key_here'
    # GROQ_API_KEY: 'your_groq_api_key_here' # If used

    # LLM Settings
    DEFAULT_GENERATIVE_MODEL: "gemini-1.5-flash-latest" # Updated from "gemini-2.0-flash-exp"
    DEFAULT_EMBEDDING_MODEL: "models/embedding-001"
    DEFAULT_LLM_TEMPERATURE: 0.7
    DEFAULT_LLM_TOP_P: 0.9

    # File Paths and Directories
    # These paths should be relative to the project root or absolute,
    # and the application logic should handle them accordingly.
    # The proposed modular design (BACKEND_MODULAR_DESIGN.md) suggests making
    # these configurable via an app.config.settings object.
    GENERATED_FILES_DIR: "generated_files"
    DATABASE_DIR: "instance/databases" # Example: moving DBs to instance directory
    VECTOR_DB_DIR: "instance/vector_stores"
    TEMP_FILES_DIR: "/tmp/my_app_temp" # Or a project-relative temp path

    # Logging
    LOG_LEVEL: "INFO"
    ```
    The application's `app.config.loader` (as proposed in `BACKEND_MODULAR_DESIGN.md`) would then be responsible for loading these values and making them accessible in a type-safe manner (e.g., via an `AppSettings` Pydantic model).

## 2. Dependency Management (Python)

Consistent and explicit dependency management is key to ensuring reproducible builds and stable deployments.

### 2.1. `requirements.txt` File

*   **Purpose:** A `requirements.txt` file must be used to list all Python dependencies required by the project, along with their specific versions.
*   **Benefits:**
    *   **Reproducible Environments:** Guarantees that the same versions of dependencies are used across all development, testing, and production environments, minimizing "works on my machine" issues.
    *   **Clarity:** Provides a clear and explicit list of all third-party packages the project relies on.
    *   **Ease of Installation:** Simplifies the setup process for new developers or deployment environments with a single command.

### 2.2. Virtual Environments

*   **Importance:** As emphasized in `ENVIRONMENT_SETUP.md`, Python virtual environments (e.g., created using `venv`) must always be used for project development.
*   **Synergy with `requirements.txt`:** Virtual environments isolate project dependencies from the system-wide Python installation and from other projects. The `requirements.txt` file then defines the specific packages to be installed *within* that isolated environment.

### 2.3. Generating `requirements.txt`

*   **Command:** After ensuring all necessary packages are installed and the application is working correctly within the activated virtual environment, generate or update the `requirements.txt` file using:
    ```bash
    pip freeze > requirements.txt
    ```
*   **Best Practice:** Only include packages that are direct dependencies. Development tools (like Black, isort, Flake8) can be managed separately or included in a `requirements-dev.txt` if preferred. For this project, we will include them in `requirements.txt` for simplicity unless it becomes unwieldy.

### 2.4. Installing from `requirements.txt`

*   **Command:** To install all dependencies listed in `requirements.txt` into the currently active virtual environment, use:
    ```bash
    pip install -r requirements.txt
    ```
    This is the standard command for setting up the project's Python dependencies.

### 2.5. Updating Dependencies

*   **Process:**
    1.  Identify the package to update.
    2.  Install the new version within the virtual environment (e.g., `pip install <package_name>==<new_version>` or `pip install --upgrade <package_name>`).
    3.  Test the application thoroughly to ensure the update doesn't introduce regressions or compatibility issues.
    4.  Once satisfied, regenerate the `requirements.txt` file using `pip freeze > requirements.txt` to reflect the new version.
    5.  Commit the updated `requirements.txt` file.

### 2.6. Initial `requirements.txt` Content

Based on the dependencies identified in `ENVIRONMENT_SETUP.md` and common development tools discussed in `CODING_STANDARDS.md`, the initial `requirements.txt` should include:

```
# Core Application Framework
Flask==3.0.0 # Example version, use actual version from testing
Flask-CORS==4.0.0 # Example version

# PDF and File Processing
Pillow==10.2.0 # Example version (PIL fork)
PyMuPDF==1.23.21 # Example version (fitz)
PyPDF2==3.0.1 # Example version
extractous==0.2.6 # Example version (or latest compatible)

# Language Model and AI Services
langchain==0.1.9 # Example version
langchain-community==0.0.24 # Example version
langchain-google-genai==0.0.9 # Example version
langchain-core==0.1.26 # Example version
google-generativeai==0.4.1 # Example version
chromadb==0.4.22 # Example version (for Chroma vector store)

# Configuration
PyYAML==6.0.1 # Example version

# Code Quality & Formatting (Development Dependencies)
black==24.2.0 # Example version
isort==5.13.2 # Example version
flake8==7.0.0 # Example version
```

**Note:** The versions listed above are examples. The actual versions should be determined by installing the latest compatible versions in a virtual environment during setup, testing thoroughly, and then running `pip freeze > requirements.txt`. It's crucial to pin versions to avoid unexpected updates breaking the application.
