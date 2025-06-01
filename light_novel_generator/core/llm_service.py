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


def enhance_dialogue(chapter_text: str, genre: str, characters_summary: str = "Two main female characters typical of a highschool yuri story.", overall_story_summary: str = "") -> str:
    """
    Reviews and enhances the dialogue in a piece of text using the Gemini API.

    Args:
        chapter_text (str): The text of the chapter (or scene) containing dialogue.
        genre (str): The genre of the light novel.
        characters_summary (str): Brief summary of the main characters involved in dialogues.
        overall_story_summary (str): Brief summary of the overall story for context.

    Returns:
        str: The chapter text with potentially enhanced dialogue.
    """
    prompt = (
        f"You are an editor specializing in {genre} light novels. Review the following chapter text. "
        f"Your task is to enhance the dialogue to make it more natural, engaging, and consistent with the characters and genre. "
        f"Do not rewrite the entire chapter, focus primarily on improving dialogue. Ensure the dialogue reflects a realistic highschool setting. "
        f"If the dialogue is already good, you can make minimal changes or affirm its quality. "
        f"Maintain the existing plot and scene structure.\n\n"
        f"Genre: {genre}\n"
        f"Character Context: {characters_summary}\n"
        f"Overall Story Context: {overall_story_summary if overall_story_summary else 'General highschool romance.'}\n\n"
        f"--- Chapter Text to Review ---\n"
        f"{chapter_text}\n"
        f"--- End of Chapter Text ---\n\n"
        f"Provide the full chapter text with your dialogue enhancements incorporated. Do not add any commentary before or after the revised chapter text."
    )

    try:
        # Assuming 'model' is already initialized (e.g., model = genai.GenerativeModel('gemini-pro'))
        response = model.generate_content(prompt)
        if response.parts:
            return response.text.strip()
        else:
            print(f"Warning: Dialogue enhancement for chapter produced no content. Returning original. Chapter start: {chapter_text[:100]}...")
            return chapter_text # Return original if no enhancement or error
    except Exception as e:
        print(f"An error occurred during dialogue enhancement: {e}. Returning original text.")
        return chapter_text # Return original text in case of error


def final_review_story(full_story_text: str, title: str, genre: str, characters_summary: str = "Two main female characters in a highschool yuri story.", overall_story_summary: str = "") -> tuple[str, str]:
    """
    Performs a final review of the entire generated narrative using the Gemini API.
    It can suggest improvements or provide a revised version.

    Args:
        full_story_text (str): The entire generated novel text, typically concatenated chapters.
        title (str): The title of the novel.
        genre (str): The genre of the novel.
        characters_summary (str): Brief summary of main characters.
        overall_story_summary (str): Brief summary of the overall story.

    Returns:
        tuple[str, str]: A tuple containing:
                         - review_status (str): "approved", "revised", "critique_provided".
                         - content (str): Either the revised story, critique notes, or the original story if approved as is.
    """
    prompt = (
        f"You are a senior editor for {genre} light novels. Perform a final review of the following complete draft for the novel titled '{title}'.\n"
        f"Focus on overall coherence, narrative consistency (plot, character arcs), pacing, thematic integrity, and reader engagement. "
        f"The story should be suitable for the {genre} genre and its intended audience.\n\n"
        f"Character Context: {characters_summary}\n"
        f"Overall Story Context: {overall_story_summary if overall_story_summary else 'General highschool romance.'}\n\n"
        f"--- Full Story Draft ---\n"
        f"{full_story_text}\n"
        f"--- End of Story Draft ---\n\n"
        f"Reviewer instructions:\n"
        f"1. If the story is excellent and requires no significant changes, respond with a short approval message starting with 'STATUS: APPROVED'. Example: 'STATUS: APPROVED. This story is well-written and coherent.'\n"
        f"2. If there are minor issues that can be fixed with light edits or suggestions you can provide as notes, respond with 'STATUS: CRITIQUE_PROVIDED' followed by your specific, actionable suggestions. Do not return the full story in this case, only your critique.\n"
        f"3. If the story has significant issues requiring substantial revisions to plot, character, or pacing, and you can provide an improved version, respond with 'STATUS: REVISED' followed by the *complete revised story text*. Ensure the revised story maintains the original chapter structure as much as possible if it was clear.\n"
        f"Begin your response *only* with 'STATUS: <status_code>' followed by the content as described."
    )

    try:
        response = model.generate_content(prompt) # Assuming 'model' is initialized
        response_text = response.text.strip()

        if response_text.startswith("STATUS: REVISED"):
            return "revised", response_text[len("STATUS: REVISED"):].strip()
        elif response_text.startswith("STATUS: APPROVED"):
            return "approved", response_text[len("STATUS: APPROVED"):].strip() # Return the approval message
        elif response_text.startswith("STATUS: CRITIQUE_PROVIDED"):
            return "critique_provided", response_text[len("STATUS: CRITIQUE_PROVIDED"):].strip() # Return critique
        else:
            # Fallback if status is missing or unexpected
            print(f"Warning: Final review returned unexpected format. Treating as critique. Response: {response_text[:200]}...")
            return "critique_provided", f"Reviewer output (unexpected format):\n{response_text}"

    except Exception as e:
        print(f"An error occurred during final story review: {e}")
        return "error", f"Failed to review story due to an error: {e}. Original story is preserved."

if __name__ == '__main__':
    print("Initializing test for llm_service.py...")

    # --- Environment Setup ---
    if not os.path.exists(".env") and not os.getenv("GEMINI_API_KEY"):
        print("Creating a dummy .env file for subtask execution.")
        with open(".env", "w") as f: f.write("GEMINI_API_KEY=dummy_key_for_subtask_no_api_call\n")
        load_dotenv(override=True)
    current_api_key = os.getenv("GEMINI_API_KEY")
    api_key_present_and_real = False
    if not current_api_key or current_api_key == "dummy_key_for_subtask_no_api_call":
        print("INFO: GEMINI_API_KEY not found or is dummy. Actual API calls will be skipped/placeholders used.")
    else:
        print("INFO: GEMINI_API_KEY found. Attempting API calls.")
        try:
            genai.configure(api_key=current_api_key)
            model = genai.GenerativeModel('gemini-pro')
            print("Gemini model re-initialized.")
            api_key_present_and_real = True
        except Exception as e: print(f"Error re-initializing Gemini model: {e}")

    # --- Test Data ---
    test_title = "Echoes of Tomorrow"
    test_genre = "highschool yuri"
    test_char_summary = "Kaori is quiet and introspective. Natsumi is energetic and outgoing."
    test_story_summary = f"A {test_genre} novel about Kaori and Natsumi discovering their feelings amidst club activities."

    # Simulate a short story for testing
    chapter1_text = "Chapter 1: First Meeting\nYui bumped into Kanna. 'Oh, sorry!' Kanna smiled, 'No problem! I'm Kanna.' Yui blushed."
    chapter2_text = "Chapter 2: Shared Lunch\nThey ate lunch on the rooftop. Kanna shared her bento. Yui found herself watching Kanna more than eating."
    dialogue_enhanced_story = f"{chapter1_text}\n\n{chapter2_text}" # Assume this is result after dialogue enhancement

    # --- Test Title Generation (minimal) ---
    print("\n--- Testing Title Generation ---")
    try:
        titles = generate_titles(test_genre, 1)
        if titles and not titles[0].startswith("Error") and api_key_present_and_real: print(f"Generated title: {titles[0]}")
        else: print(f"Title generation test (skipped/placeholder): {titles}")
    except Exception as e: print(f"Title gen error: {e}")

    # --- Test Outline Generation (minimal) ---
    print("\n--- Testing Outline Generation ---")
    try:
        outline = generate_outline(test_title, test_genre, 1)
        if outline and not outline.startswith("Error") and api_key_present_and_real: print(f"Generated outline (start): {outline[:100]}...")
        else: print(f"Outline gen test (skipped/placeholder): {outline}")
    except Exception as e: print(f"Outline gen error: {e}")

    # --- Test Chapter Generation (minimal) ---
    print("\n--- Testing Chapter Generation ---")
    try:
        chap_text = generate_chapter_text(test_title, test_genre, "Outline for a short chapter.", test_story_summary)
        if chap_text and not chap_text.startswith("Error") and api_key_present_and_real: print(f"Generated chapter (start): {chap_text[:100]}...")
        else: print(f"Chapter gen test (skipped/placeholder): {chap_text}")
    except Exception as e: print(f"Chapter gen error: {e}")

    # --- Test Dialogue Enhancement (minimal) ---
    print("\n--- Testing Dialogue Enhancement ---")
    try:
        enhanced_dialogue = enhance_dialogue(chapter1_text, test_genre, test_char_summary, test_story_summary)
        if enhanced_dialogue and enhanced_dialogue != chapter1_text and api_key_present_and_real: print(f"Enhanced dialogue (start): {enhanced_dialogue[:100]}...")
        elif enhanced_dialogue == chapter1_text and api_key_present_and_real: print("Dialogue enhancement returned original (quality OK or no change).")
        else: print(f"Dialogue enhance test (skipped/placeholder): {enhanced_dialogue}")
    except Exception as e: print(f"Dialogue enhance error: {e}")

    # --- Test Final Review ---
    print(f"\n--- Testing Final Story Review for story (total chars: {len(dialogue_enhanced_story)}) ---")
    try:
        review_status, review_content = final_review_story(dialogue_enhanced_story, test_title, test_genre, test_char_summary, test_story_summary)
        print(f"Review Status: {review_status}")
        if review_status == "error":
            print(f"Review Content (Error Message): {review_content}")
        elif not api_key_present_and_real and review_status != "error": # If using placeholder due to no API key
            print(f"Review Content (Placeholder/Skipped - first 150 chars): {review_content[:150]}...")
        else: # Actual API call was made or attempted
             print(f"Review Content (first 150 chars): {review_content[:150]}...")

        if review_status == "revised" and api_key_present_and_real:
            # Simple check: if revised, should be different from original
            if review_content.strip() != dialogue_enhanced_story.strip() and len(review_content) > 0:
                print("SUCCESS: Story was revised by the LLM.")
            else:
                print("NOTE: Story status is 'revised' but content is same as original or empty. Check LLM behavior.")
        elif review_status == "approved" and api_key_present_and_real:
            print("SUCCESS: Story was approved.")
        elif review_status == "critique_provided" and api_key_present_and_real:
             print("SUCCESS: Critique was provided.")

    except Exception as e:
        print(f"An error occurred during the final review test: {e}")

    print("\nllm_service.py tests concluded.")
