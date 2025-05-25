# Proposed Backend Modular Design

This document outlines a proposed modular structure for the Python backend, aiming to improve organization, reduce coupling, enhance maintainability, and address pain points identified in Phase 1.

## 1. Proposed Modular Structure

The proposed structure moves towards a more layered and service-oriented architecture.

**Top-Level Directories/Modules:**

*   **`app/`**: The main application package.
    *   **`api/`**: Handles HTTP request routing and API endpoint definitions (Flask-related).
    *   **`services/`**: Contains business logic, orchestrating tasks by interacting with core modules and external services.
    *   **`core/`**: Provides fundamental, self-contained functionalities.
        *   **`parsing/`**: For document parsing and data extraction (from PDFs, etc.).
        *   **`db/`**: Manages database interactions, schema, and queries.
        *   **`llm/`**: Interfaces with Large Language Models.
        *   **`evaluation/`**: Logic for student assessment and report generation.
    *   **`utils/`**: Common utility functions and classes used across the application.
    *   **`config/`**: Application configuration management.
*   **`tests/`**: Root directory for all unit and integration tests.
*   **`instance/`**: (As potentially used by Flask or ChromaDB for instance-specific files, like vector stores or ephemeral data, distinct from application code).
*   **`scripts/`**: For utility scripts (e.g., one-off data migration, setup).
*   **`configs/`**: Directory for configuration files (like `config.yaml`), external to the main `app` package.

**Justification:**

This structure aims to:

*   **Improve Organization:** Group files by functionality rather than a flat structure. `api` handles web concerns, `services` handles business logic, `core` handles specific technical capabilities, `utils` provides shared tools, and `config` centralizes configuration.
*   **Reduce Coupling:**
    *   The `api` layer will primarily interact with the `services` layer, not directly with `core` components for complex operations.
    *   `services` will act as intermediaries, decoupling `api` from the specifics of data parsing, LLM interaction, or database queries.
    *   `core` modules will be designed to be relatively independent.
*   **Enhance Maintainability & Scalability:**
    *   Clearer separation of concerns makes it easier to understand, modify, and extend individual parts of the application without unintended side effects.
    *   Easier to add new API versions, services, or core functionalities.
*   **Improve Testability:** Smaller, more focused modules are easier to unit test. The separation of concerns allows for mocking dependencies (e.g., mocking a service in an API test, or mocking an LLM call in a service test).
*   **Address Pain Points:**
    *   Reduces the monolithic nature of `main.py` by distributing its responsibilities.
    *   Provides a clear home for configuration, discouraging hardcoded values.
    *   Facilitates better database connection management within the `core.db` module.

## 2. Module Details

### `app/` (Main Application Package)

*   **`__init__.py`**: Could initialize the Flask app object.

#### `app/api/`

*   **Responsibilities:** Defines all HTTP API endpoints. Handles request validation, serialization of responses, and calls to the `services` layer for business logic.
*   **Potential Public API (Flask routes):**
    *   `/post_db` (for submitting assessment materials)
    *   `/rag` (for RAG queries)
    *   `/json_file` (for fetching analysis status/results)
*   **Internal Components:**
    *   `routes.py` (or split into `assessment_routes.py`, `rag_routes.py`): Contains Flask Blueprint definitions and route handlers.
    *   `schemas.py` (optional, if using a library like Marshmallow or Pydantic for request/response validation and serialization).
    *   The existing `main.py` would be refactored, with its Flask app instance and route definitions moving here.

#### `app/services/`

*   **Responsibilities:** Implements the core business logic and use cases. Orchestrates operations by interacting with `core` modules (db, parsing, llm, evaluation) and potentially other external services.
*   **Potential Public API (Functions/Methods):**
    *   `assessment_service.process_submission(question_pdf, answer_key_pdf, student_sheet_pdf) -> dict`
    *   `rag_service.query_student_report(student_id, question_text) -> str`
    *   `analysis_service.get_analysis_results(analysis_id) -> dict`
*   **Internal Components:**
    *   `assessment_service.py`: Handles the logic currently in `main.py`'s `/post_db` related to orchestrating PDF processing, LLM analysis, and student evaluation.
    *   `rag_service.py`: Encapsulates the logic for using the RAG model.
    *   `file_management_service.py` (optional): Could handle temporary file storage and management if complex.

#### `app/core/`

This package contains the fundamental building blocks of the application.

##### `app/core/parsing/`

*   **Responsibilities:** Extracts structured data from various input formats, primarily PDFs.
*   **Potential Public API:**
    *   `pdf_parser.extract_questions_from_pdf(pdf_path) -> list[QuestionData]`
    *   `pdf_parser.extract_answers_from_key_pdf(pdf_path) -> AnswerKeyData`
    *   `pdf_parser.extract_student_responses_pdf(pdf_path) -> StudentResponseData`
*   **Internal Components:**
    *   `pdf_parser.py`: Refactoring of `io_operation.py` (class `PDFProcessor`). Could be further split if parsing logic becomes very complex for different document types.
    *   Uses libraries like `PyPDF2`, `PyMuPDF (fitz)`, `extractous`.

##### `app/core/db/`

*   **Responsibilities:** Manages all database interactions, including connection management, schema definition (and potentially migrations), and CRUD operations.
*   **Potential Public API:**
    *   `queries.get_question_by_id(qid, question_no) -> QuestionModel`
    *   `queries.get_llm_analysis(qid, question_no) -> LLMAnalysisModel`
    *   `queries.get_student_report(sid, qid) -> EvaluationReportModel`
    *   `commands.save_question_paper(qid, questions: list[QuestionData])`
    *   `commands.save_llm_analysis(qid, question_no, analysis_data: LLMAnalysisData)`
    *   `commands.save_student_evaluation(sid, qid, report_data: EvaluationReportData)`
    *   `schema.init_db(app_config)` or manage schema with a migration tool.
*   **Internal Components:**
    *   `connection.py`: Manages SQLite connection (e.g., could provide a connection pool or request-scoped connections for Flask).
    *   `schema.py`: Defines table structures (potentially using an ORM like SQLAlchemy, or just SQL DDL statements). Could handle initial table creation. The DDL parts of current `database.py` functions go here.
    *   `queries.py`: Contains functions for fetching data.
    *   `commands.py`: Contains functions for inserting/updating/deleting data. The DML parts of current `database.py` functions go here.
    *   `models.py` (optional): If using an ORM or Pydantic models to represent database entities.

##### `app/core/llm/`

*   **Responsibilities:** Handles all interactions with external Large Language Models (e.g., Gemini). Manages API calls, prompt engineering, and parsing LLM responses.
*   **Potential Public API:**
    *   `generation.generate_question_analysis(question_text, options, correct_option) -> LLMAnalysisData`
    *   `rag.query_documents(documents_json_path, query_text) -> str`
*   **Internal Components:**
    *   `client.py`: Generic LLM client setup, API key management (could absorb `APIKeyManager` from `explain_gem.py`).
    *   `generation.py`: Specific logic for generating explanations and analysis (refactoring of `explain_gem.py`'s `AIModelEvaluator`).
    *   `rag.py`: Logic for RAG, including vector store interaction (refactoring of `gemi_rag.py`'s `Ask_Gemini`).
    *   `prompts.py`: Centralized storage for prompt templates.

##### `app/core/evaluation/`

*   **Responsibilities:** Calculates student scores and generates evaluation reports.
*   **Potential Public API:**
    *   `evaluator.generate_student_report(student_answers: StudentResponseData, question_paper_data: QuestionPaperWithAnalysis) -> EvaluationReportData`
*   **Internal Components:**
    *   `evaluator.py`: Refactoring of `evaluate_student.py`. Takes student answers and LLM-enriched question data to produce a final report.
    *   `scoring.py`: (Optional) If scoring logic becomes complex, it could be a separate component.

#### `app/utils/`

*   **Responsibilities:** Provides common, reusable utility functions and classes that don't fit into a specific core domain but are used across the application.
*   **Potential Public API:**
    *   `file_helpers.save_temp_file(uploaded_file_object, desired_name) -> str`
    *   `logging_config.setup_logging(app_config)`
*   **Internal Components:**
    *   `file_helpers.py`: Utilities for file operations (e.g., managing temporary files).
    *   `logging_config.py`: Configuration for application-wide logging (refactoring of `logger_config.py`).
    *   Other miscellaneous utilities.

#### `app/config/`

*   **Responsibilities:** Manages application configuration, including loading from files and environment variables.
*   **Potential Public API:**
    *   `settings.GEMINI_API_KEY`
    *   `settings.DATABASE_URL`
    *   `settings.LOG_LEVEL`
    *   `settings.MAX_FILE_SIZE`
    *   `settings.GENERATED_FILES_DIR`
*   **Internal Components:**
    *   `loader.py`: Function to load `config.yaml` and environment variables (refactoring of `utils/get_keys.py`).
    *   `settings.py`: Defines Pydantic models for configuration or simply exposes loaded configuration values. It centralizes access to all config parameters.

### `configs/` (External Directory)

*   **Responsibilities:** Stores configuration files.
*   **Contents:**
    *   `config.yaml`: Main configuration file for API keys, database paths, LLM model names, file paths, etc.

### `tests/`

*   **Responsibilities:** Contains all automated tests.
*   **Internal Components:**
    *   `unit/`: Unit tests for individual modules/functions/classes.
        *   `unit/core/test_parsing.py`
        *   `unit/services/test_assessment_service.py`
    *   `integration/`: Integration tests for interactions between modules.
        *   `integration/api/test_assessment_routes.py`
    *   `fixtures/`: Test data and fixtures.

This modular design provides a solid foundation for a maintainable, scalable, and testable backend application. It maps existing functionalities to more organized locations and introduces a service layer to decouple API from core logic.Okay, I have created the `BACKEND_MODULAR_DESIGN.md` document.

It includes:
1.  **Proposed Modular Structure:**
    *   Top-level directories: `app/` (with sub-modules `api/`, `services/`, `core/` (further containing `parsing/`, `db/`, `llm/`, `evaluation/`), `utils/`, `config/`), `tests/`, `instance/`, `scripts/`, and `configs/`.
    *   Justification for this structure, focusing on improved organization, reduced coupling, enhanced maintainability, scalability, testability, and addressing previously identified pain points.

2.  **Module Details:**
    *   For each proposed module and sub-module (`app/api/`, `app/services/`, `app/core/parsing/`, `app/core/db/`, `app/core/llm/`, `app/core/evaluation/`, `app/utils/`, `app/config/`, as well as the external `configs/` and `tests/` directories):
        *   Defined its **Responsibilities**.
        *   Outlined its **Potential Public API** (key functions or classes it would export).
        *   Suggested **Internal Components** (sub-modules, classes, or groups of functions), including how existing files (`main.py`, `io_operation.py`, `database.py`, `evaluate_student.py`, `gemi_rag.py`, `explain_gem.py`, `utils/get_keys.py`, `logger_config.py`) would be refactored and integrated into this new structure.

The design aims to establish a clear separation of concerns, aligning with common backend application architecture practices.
