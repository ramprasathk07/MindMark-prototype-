# Python Backend Coding Standards and Style Guide

This document outlines the coding standards and style guidelines to be followed for the Python backend development. Adhering to these standards will help ensure code consistency, readability, and maintainability.

## 1. Code Formatting: Black

We use **Black** for automated code formatting. Black is an opinionated code formatter that ensures PEP 8 compliance and produces consistent code style across the entire project.

*   **Benefits:**
    *   **Consistency:** Eliminates debates over formatting; code looks the same regardless of who wrote it.
    *   **PEP 8 Compliance:** Automatically formats code to follow most PEP 8 guidelines.
    *   **Reduced Diffs:** Minimizes formatting changes in pull requests, allowing reviewers to focus on substantive changes.
    *   **Improved Readability:** Consistent formatting makes code easier to read and understand.

*   **Installation:**
    ```bash
    pip install black
    ```

*   **Usage:**
    To format all Python files in the current directory and its subdirectories:
    ```bash
    black .
    ```
    It's recommended to run Black before committing changes. This can also be integrated into pre-commit hooks.

## 2. Import Sorting: isort

We use **isort** for automatically sorting and organizing import statements.

*   **Benefits:**
    *   **Readability:** Neatly organized imports make it easier to see what modules are being used.
    *   **Consistency:** Ensures a standard order for imports across the project.
    *   **Conflict Avoidance:** Helps prevent merge conflicts related to import statement ordering.

*   **Installation:**
    ```bash
    pip install isort
    ```

*   **Usage:**
    To sort imports in all Python files in the current directory and its subdirectories:
    ```bash
    isort .
    ```
    Like Black, isort can be integrated into pre-commit hooks. It is generally recommended to run `isort` before `black`.

## 3. Linting: Flake8 (Recommended)

While Black handles formatting, a linter helps catch common errors, potential bugs, and style issues that Black doesn't address. We recommend using **Flake8**.

*   **Benefits:**
    *   **Error Detection:** Catches syntax errors, undefined names, and other common programming mistakes.
    *   **Style Enforcement:** Enforces additional style guidelines (e.g., complexity checks via mccabe plugin).
    *   **Improved Code Quality:** Helps maintain a higher standard of code quality and reduce bugs.

*   **Installation:**
    ```bash
    pip install flake8
    ```

*   **Usage:**
    To lint all Python files in the current directory and its subdirectories:
    ```bash
    flake8 .
    ```
    Flake8 can be configured with a `.flake8` file in the project root to customize checks (e.g., line length, specific errors to ignore if necessary).

    *Alternative: Pylint is another powerful linter, though it can be more verbose and require more configuration.*

## 4. Naming Conventions

Clear and consistent naming is crucial for readability and understanding.

*   **Variables, Functions, and Modules/Files:**
    *   Use `snake_case` (lowercase with words separated by underscores).
    *   Examples: `student_id`, `calculate_total_score()`, `data_parser.py`.

*   **Class Names:**
    *   Use `PascalCase` (or `CapWords` - capitalize the first letter of each word).
    *   Examples: `PdfProcessor`, `DatabaseManager`, `StudentEvaluationService`.

*   **Constants:**
    *   Use `UPPER_SNAKE_CASE` (uppercase with words separated by underscores).
    *   Declare constants at the module level.
    *   Examples: `MAX_RETRIES = 3`, `DEFAULT_TIMEOUT = 60`.

*   **General Advice:**
    *   **Be Descriptive:** Names should clearly indicate the purpose or content of the variable, function, class, etc. Avoid overly short or cryptic names.
    *   **Avoid Single-Letter Names (mostly):** Except for simple loop counters (`i`, `j`, `k`) or well-established mathematical conventions if applicable.
    *   **Boolean Variables/Functions:** Often prefixed with `is_`, `has_`, `should_` (e.g., `is_valid`, `has_permission`).

## 5. Commit Message Style: Conventional Commits

We will follow the **Conventional Commits** specification for writing commit messages. This standard provides a simple and structured way to write commit messages.

*   **Format:**
    ```
    <type>[optional scope]: <description>

    [optional body]

    [optional footer(s)]
    ```

*   **Common Types:**
    *   `feat`: A new feature for the user.
    *   `fix`: A bug fix for the user.
    *   `docs`: Documentation-only changes.
    *   `style`: Code style changes (formatting, missing semi-colons, etc.) that do not affect the meaning of the code.
    *   `refactor`: Code changes that neither fix a bug nor add a feature.
    *   `perf`: Code changes that improve performance.
    *   `test`: Adding missing tests or correcting existing tests.
    *   `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation.
    *   `ci`: Changes to CI configuration files and scripts.

*   **Examples:**
    *   `feat: implement user registration endpoint`
    *   `fix: correct PDF parsing error for multi-page documents`
    *   `docs: update API documentation for /submit_assessment`
    *   `refactor(auth): simplify token generation logic`
    *   `chore: add Black and isort to pre-commit hooks`

*   **Benefits:**
    *   **Clearer Git History:** Easy to understand the nature of changes at a glance.
    *   **Automated Changelog Generation:** Tools can generate changelogs automatically.
    *   **Simpler Collaboration:** Provides a common language for commit messages.
    *   More information: [https://www.conventionalcommits.org/](https://www.conventionalcommits.org/)

## 6. Branching Model: GitHub Flow (Simplified)

We will use a simple branching model like **GitHub Flow**.

*   **`main` Branch:**
    *   The `main` branch (or `master`) is the definitive branch. It should always be stable and deployable.
    *   Direct commits to `main` are prohibited.

*   **Feature Branches:**
    *   All new work (features, bug fixes, refactoring) must be done on a separate branch, created from `main`.
    *   Branch names should be descriptive (e.g., `feat/user-authentication`, `fix/pdf-encoding-issue`).

*   **Pull Requests (PRs):**
    *   Once work on a feature branch is complete, open a Pull Request (PR) to merge it into `main`.
    *   PRs are mandatory for code review. At least one other team member should review and approve the PR.
    *   Automated checks (CI builds, linters, tests) should pass before a PR can be merged.

*   **Merging:**
    *   After approval and successful CI checks, the feature branch is merged into `main` (typically using a squash merge or a regular merge, depending on team preference for history cleanliness).
    *   Delete the feature branch after merging.

*   **Benefits:**
    *   **Collaboration:** Facilitates parallel development and team collaboration.
    *   **Code Review:** Ensures code quality and knowledge sharing.
    *   **Continuous Integration (CI):** PRs are ideal integration points for automated builds and tests.
    *   **Stable `main`:** Keeps the main branch reliable for deployments or further development.

## 7. General Best Practices

*   **Docstrings:**
    *   Write clear and concise docstrings for all public modules, classes, functions, and methods.
    *   Follow a consistent style (e.g., Google Python Style Docstrings or reStructuredText).
    *   Explain what the component does, its arguments, and what it returns.
    ```python
    class PdfFileProcessor:
        """
        Processes PDF files to extract text and metadata.

        Attributes:
            file_path (str): The path to the PDF file.
        """

        def extract_text(self, page_number: int = None) -> str:
            """Extracts text from the PDF.

            Args:
                page_number: Optional; the specific page number to extract text from.
                             If None, extracts text from all pages.

            Returns:
                The extracted text as a single string.

            Raises:
                FileNotFoundError: If the PDF file does not exist.
                InvalidPageNumberError: If the specified page_number is out of range.
            """
            # ... implementation ...
            pass
    ```

*   **Keep Functions Short and Focused:**
    *   Functions should ideally do one thing well (Single Responsibility Principle).
    *   Aim for functions that are easy to understand and test, generally not exceeding 30-40 lines of code (excluding comments/docstrings).

*   **Avoid Deep Nesting:**
    *   Deeply nested `if/else` blocks or loops can make code hard to read and follow.
    *   Try to reduce nesting by using early exits (guard clauses), helper functions, or polymorphism.

*   **Comments:**
    *   Write comments to explain *why* something is done a certain way if it's not obvious, or to clarify complex logic. Avoid comments that just restate what the code clearly does.

*   **Configuration:**
    *   Avoid hardcoding values like file paths, API keys, or model names. Use a centralized configuration mechanism (e.g., `config.yaml` loaded into `app.config.settings`).

*   **Error Handling:**
    *   Handle exceptions explicitly and gracefully. Avoid broad `except:` clauses.
    *   Log errors with sufficient context.

*   **Testing:**
    *   Write unit tests for new functionality and bug fixes. Aim for good test coverage. (Details on testing strategy can be a separate document).

By following these standards, we can build a more robust, maintainable, and understandable backend system.
