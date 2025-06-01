import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API key
# It's good practice to ensure the API key is set
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in a .env file.")
genai.configure(api_key=api_key)

# Initialize the generative model
# For text generation, 'gemini-pro' is a common choice.
# Safety settings can be adjusted if needed, but defaults are often fine to start.
model = genai.GenerativeModel('gemini-pro')

def generate_titles(genre: str, num_titles: int = 5) -> list[str]:
    """
    Generates a list of light novel titles for a given genre using the Gemini API.

    Args:
        genre (str): The genre of the light novel (e.g., "highschool yuri").
        num_titles (int): The number of titles to generate.

    Returns:
        list[str]: A list of generated titles.
    """
    prompt = f"Generate {num_titles} potential light novel titles for the genre: '{genre}'. The titles should be catchy and appropriate for the genre. Return only the list of titles, each on a new line, without numbering or any other surrounding text."

    try:
        response = model.generate_content(prompt)
        # Assuming the response text contains titles separated by newlines
        titles = [title.strip() for title in response.text.strip().split('\n') if title.strip()]
        return titles[:num_titles] # Ensure we return the exact number of titles requested
    except Exception as e:
        print(f"An error occurred during title generation: {e}")
        # In a real application, you might want to return a default list or raise the exception
        return [f"Error generating title: {i}" for i in range(1, num_titles + 1)]


def generate_outline(title: str, genre: str, num_chapters: int = 5) -> str:
    """
    Generates a story outline based on a title and genre using the Gemini API.

    Args:
        title (str): The title of the light novel.
        genre (str): The genre of the light novel.
        num_chapters (int): Approximate number of chapters for the outline.

    Returns:
        str: A string containing the generated story outline.
    """
    prompt = f"Generate a detailed story outline for a light novel titled '{title}' in the genre '{genre}'. "              f"The outline should cover approximately {num_chapters} chapters. "              f"For each chapter, provide a brief summary of key events, character development points, and setting details. "              f"The output should be a structured outline. For example:\n\n"              f"Chapter 1: Introduction\n- Summary of events...\n- Character focus...\n\n"              f"Chapter 2: Rising Action\n- Summary of events...\n- Character focus...\n\n"              f"Ensure the output is just the outline text."

    try:
        response = model.generate_content(prompt)
        # It's good practice to access the text part and handle potential errors or empty responses
        if response.parts:
            return response.text.strip()
        else:
            # Handle cases where the response might be blocked or empty
            return f"Error: No content generated for outline. Response was empty or blocked. Prompt: {prompt}"
    except Exception as e:
        print(f"An error occurred during outline generation: {e}")
        return f"Error generating outline for title: {title}. Details: {str(e)}"


def generate_chapter_text(title: str, genre: str, chapter_outline: str, overall_story_summary: str = "", previous_chapters_summary: str = "") -> str:
    """
    Generates the full text for a single chapter based on its outline,
    the overall story, and summaries of previous chapters.

    Args:
        title (str): The main title of the light novel.
        genre (str): The genre of the light novel.
        chapter_outline (str): The specific outline or summary for this chapter.
        overall_story_summary (str): A brief summary of the entire story arc (optional but recommended).
        previous_chapters_summary (str): A summary of events from previous chapters (optional but recommended for continuity).

    Returns:
        str: The generated text for the chapter.
    """
    prompt = (
        f"You are writing a chapter for a light novel titled '{title}' in the '{genre}' genre.\n"
        f"Overall story context: {overall_story_summary if overall_story_summary else 'Not provided. Focus on the chapter outline.'}\n"
        f"Summary of previous chapters: {previous_chapters_summary if previous_chapters_summary else 'This is an early chapter or context is not provided.'}\n\n"
        f"Current Chapter Outline:\n{chapter_outline}\n\n"
        f"Please write the full text for this chapter. Include dialogue, descriptions, and character interactions as appropriate. "
        f"Ensure the chapter flows well and aligns with the provided outline and context. "
        f"The output should be only the chapter text itself, without any extra titles like 'Chapter X Text:'."
    )

    try:
        response = model.generate_content(prompt)
        if response.parts:
            return response.text.strip()
        else:
            # Handle cases where the response might be blocked or empty
            error_message = f"Error: No content generated for chapter. Response was empty or blocked. Chapter Outline: {chapter_outline}"
            print(error_message) # Also print for server-side logs if any
            return error_message
    except Exception as e:
        error_message = f"Error generating chapter text for outline: '{chapter_outline}'. Details: {str(e)}"
        print(error_message) # Also print for server-side logs
        return error_message

if __name__ == '__main__':
    print("Initializing test for llm_service.py...")

    if not os.path.exists(".env") and not os.getenv("GEMINI_API_KEY"):
        print("Creating a dummy .env file for subtask execution (no API key).")
        with open(".env", "w") as f:
            f.write("GEMINI_API_KEY=dummy_key_for_subtask_no_api_call\n")
        load_dotenv(override=True)

    current_api_key = os.getenv("GEMINI_API_KEY")
    api_key_present_and_real = False
    if not current_api_key:
        print("CRITICAL: GEMINI_API_KEY is not set. Please create a .env file in 'light_novel_generator' directory.")
    elif current_api_key == "dummy_key_for_subtask_no_api_call":
        print("INFO: Using a dummy API key. Actual API calls will be skipped or will use a placeholder.")
    else:
        print("INFO: GEMINI_API_KEY found. Attempting API calls.")
        try:
            genai.configure(api_key=current_api_key)
            model = genai.GenerativeModel('gemini-pro')
            print("Gemini model re-initialized with loaded API key.")
            api_key_present_and_real = True
        except Exception as e:
            print(f"Error re-initializing Gemini model with API key: {e}")

    # --- Test Title Generation ---
    print("\n--- Testing Title Generation ---")
    selected_title_for_tests = "Default Test Title"
    try:
        generated_titles = generate_titles("highschool yuri", 1) # Generate 1 for brevity
        if generated_titles and not any("Error generating title" in t for t in generated_titles) and api_key_present_and_real:
            selected_title_for_tests = generated_titles[0]
            print(f"Successfully generated title: {selected_title_for_tests}")
        elif generated_titles:
            print(f"Test run (title): Function returned or used placeholder: {generated_titles[0]}")
            if not generated_titles[0].startswith("Error"):
                 selected_title_for_tests = generated_titles[0] # Use placeholder if not an error
        else:
            print("Test run (title): No titles returned.")
    except Exception as e:
        print(f"Error during title generation test: {e}")

    # --- Test Outline Generation ---
    print(f"\n--- Testing Outline Generation for title: '{selected_title_for_tests}' ---")
    generated_outline_for_chapter_test = "Chapter 1: A Fateful Encounter\n- Main characters Yui and Misaki bump into each other in the school library, dropping their books. They share a brief, awkward but memorable moment."
    try:
        outline_full = generate_outline(selected_title_for_tests, "highschool yuri", 2) # 2 chapters for test
        if outline_full and not outline_full.startswith("Error") and api_key_present_and_real:
            print(f"Successfully generated outline:\n{outline_full}")
            # Extract first chapter description for next test if possible
            first_chapter_desc = outline_full.split('\n\n')[0] if '\n\n' in outline_full else outline_full
            if "Chapter 1" in first_chapter_desc:
                 generated_outline_for_chapter_test = first_chapter_desc
        elif outline_full:
            print(f"Test run (outline): Function returned or used placeholder:\n{outline_full}")
            # Try to use placeholder if not an error for chapter test
            if not outline_full.startswith("Error"):
                first_chapter_desc = outline_full.split('\n\n')[0] if '\n\n' in outline_full else outline_full
                if "Chapter 1" in first_chapter_desc:
                    generated_outline_for_chapter_test = first_chapter_desc
        else:
            print("Test run (outline): No outline returned.")
    except Exception as e:
        print(f"Error during outline generation test: {e}")

    # --- Test Chapter Generation ---
    print(f"\n--- Testing Chapter Generation for outline: '{generated_outline_for_chapter_test}' ---")
    try:
        chapter_text = generate_chapter_text(
            selected_title_for_tests,
            "highschool yuri",
            generated_outline_for_chapter_test,
            overall_story_summary=f"A story about {selected_title_for_tests} focusing on the developing relationship between two high school girls.",
            previous_chapters_summary="" # No previous chapters for this first test
        )
        if chapter_text and not chapter_text.startswith("Error") and api_key_present_and_real:
            print("Successfully generated chapter text (first 200 chars):")
            print(chapter_text[:200] + "...")
        elif chapter_text:
             print(f"Test run (chapter): Function returned or used placeholder. Output (first 200 chars):\n{chapter_text[:200]}...")
        else:
            print("Test run (chapter): No chapter text returned.")
    except Exception as e:
        print(f"Error during chapter generation test: {e}")

    print("\nllm_service.py tests concluded.")
