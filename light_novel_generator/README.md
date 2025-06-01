# AI Light Novel Generator

## Overview

The AI Light Novel Generator is a web-based application designed to automatically create complete light novels in the "highschool yuri" genre. It leverages the Gemini Large Language Model (LLM) through a chained, multi-step process to generate everything from titles and outlines to full chapter text, including dialogue enhancement and a final review. The application aims for full automation of the narrative creation process, with user interaction primarily for selection, customization, and approval.

## Features

-   **Automated Title Generation:** Suggests multiple titles for a highschool yuri light novel.
-   **Outline Creation:** Generates a story outline based on the selected title.
-   **Chapter Generation:** Expands the outline into full chapters with scenes and dialogue.
-   **Dialogue Enhancement:** LLM reviews and refines dialogue within chapters.
-   **Final Story Review:** LLM performs a final pass on the complete narrative for coherence and quality, potentially revising it or providing critique.
-   **Functional Customization Options:** User selections for story length, level of detail, and narrative pacing now actively influence the LLM's generation process.
-   **Basic Loading Indicators:** UI provides visual feedback during longer LLM operations.
-   **Web-Based Interface:** Local web application for user interaction.
-   **Session Management:** Maintains user progress through the generation steps.
-   **PDF Output:** Converts the final approved novel into a downloadable PDF.
-   **Command-Line POC:** A script for testing core LLM generation logic.

## Project Structure

```
light_novel_generator/
├── app/                    # Flask application package
│   ├── static/             # Static files (CSS, JS - currently minimal)
│   ├── templates/          # HTML templates
│   ├── __init__.py         # Application factory
│   └── routes.py           # Web application routes and main UI logic
├── core/                   # Core LLM interaction and business logic
│   ├── llm_service.py      # Functions for interacting with Gemini API
│   └── output_formatter.py # PDF generation logic
├── scripts/                # Utility and testing scripts
│   └── run_poc.py          # Command-line proof-of-concept script
├── temp_pdfs_output/       # Temporary directory for generated PDFs (should be in .gitignore)
├── .env                    # Environment variables (API keys, secret key) - User must create
├── requirements.txt        # Python dependencies
├── run.py                  # Script to start the Flask web application
└── README.md               # This file
```

## Setup Instructions

1.  **Python Version:** Ensure you have Python 3.8 or newer installed.

2.  **Clone the Repository:**
    ```bash
    # git clone <repository_url> # Replace with actual URL when available
    # cd light_novel_generator
    ```
    (For now, you are working within the generated project structure.)

3.  **Create a Virtual Environment:**
    It's highly recommended to use a virtual environment.
    ```bash
    python -m venv venv
    ```
    Activate it:
    -   Windows: `.\venv\Scripts\activate`
    -   macOS/Linux: `source venv/bin/activate`

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Up Environment Variables:**
    Create a file named `.env` in the `light_novel_generator` root directory. Add the following content, replacing placeholders with your actual keys:
    ```env
    GEMINI_API_KEY=your_actual_gemini_api_key_here
    FLASK_SECRET_KEY=a_strong_random_secret_key_for_flask_sessions
    ```
    -   `GEMINI_API_KEY`: Your API key for the Gemini LLM.
    -   `FLASK_SECRET_KEY`: A secret key used by Flask for session management. Generate a strong random string for this.

## Running the Application

1.  **Start the Flask Development Server:**
    Make sure your virtual environment is activated and you are in the `light_novel_generator` root directory.
    ```bash
    python run.py
    ```

2.  **Access the Web Interface:**
    Open your web browser and go to: `http://127.0.0.1:5000` (or the address shown in your terminal).

## Using the Command-Line POC

The Proof-of-Concept script allows testing the core LLM generation chain without the web interface.

1.  Ensure your `.env` file is set up correctly with `GEMINI_API_KEY`.
2.  Navigate to the `light_novel_generator/scripts` directory or run from the root:
    ```bash
    python scripts/run_poc.py
    ```
    The script will guide you through title selection and then generate an outline and chapter content to the console.

## Key Files & Logic Overview

-   **`core/llm_service.py`**: This is the heart of the AI generation. It contains:
    -   `generate_titles()`: Creates potential novel titles.
    -   `generate_outline()`: Builds a story outline. Now influenced by the user's 'Story Length' selection (short, medium, long) which adjusts the target number of chapters.
    -   `generate_chapter_text()`: Writes full chapter content. Now actively uses 'Level of Detail' (low, medium, high) and 'Narrative Pacing' (slow, medium, fast) selections to guide the LLM's writing style for each chapter.
    -   `enhance_dialogue()`: Reviews and refines dialogue. Prompts refined for better focus.
    -   `final_review_story()`: Performs a holistic review. Prompts refined for more reliable status codes and content.
-   **`core/output_formatter.py`**: Handles the conversion of the generated story into a PDF document using the `fpdf2` library.
-   **`app/routes.py`**: Defines all web page routes and manages the user's journey through the novel generation process. It calls functions from `llm_service.py` and `output_formatter.py` based on user interactions and session state.
-   **`run.py`**: The entry point to start the Flask web application.
-   **`scripts/run_poc.py`**: Useful for developers to quickly test the LLM chain and prompt effectiveness.

## Current LLM Functions & Flow

The application uses a chained LLM approach:
1.  **Title Generation**: User provides no input other than starting; system generates titles in the "highschool yuri" genre.
2.  **Outline Creation**: Based on user-selected title.
3.  **Chapter Writing**: Each chapter from the outline is expanded.
4.  **Dialogue Enhancement**: Each chapter's dialogue is reviewed and refined by the LLM.
5.  **Final Review**: The entire concatenated story (after dialogue enhancement) is reviewed by the LLM, which can approve, critique, or revise it.
6.  **PDF Conversion**: The final version of the story is converted to PDF.

Customization options for story length, detail, and pacing are now actively integrated into the LLM prompting logic. Prompts for outline generation, dialogue enhancement, and final review have also been refined to improve output quality and consistency.
