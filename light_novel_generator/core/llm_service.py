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
model = genai.GenerativeModel('gemini-2.0-flash-lite') # Updated model

import re # Added for re.findall in test block
import time # Add this line

# Define the global delay constant under the imports
LLM_CALL_DELAY_SECONDS = 2.5

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

    print(f"Introducing delay of {LLM_CALL_DELAY_SECONDS}s before LLM call for title generation...") # Optional: for logging/debugging
    time.sleep(LLM_CALL_DELAY_SECONDS)
    try:
        response = model.generate_content(prompt)
        # Assuming the response text contains titles separated by newlines
        titles = [title.strip() for title in response.text.strip().split('\n') if title.strip()]
        return titles[:num_titles] # Ensure we return the exact number of titles requested
    except Exception as e:
        print(f"An error occurred during title generation: {e}")
        # In a real application, you might want to return a default list or raise the exception
        return [f"Error generating title: {i}" for i in range(1, num_titles + 1)]


def generate_outline(title: str, genre: str, story_length: str = "medium") -> str:
    """
    Generates a story outline based on a title, genre, and desired story length using the Gemini API.

    Args:
        title (str): The title of the light novel.
        genre (str): The genre of the light novel.
        story_length (str): Desired length ('short', 'medium', 'long'). Affects chapter count.

    Returns:
        str: A string containing the generated story outline.
    """
    length_to_chapters_map = {
        "short": 3,
        "medium": 5,
        "long": 8  # Example: long could be 7-10, using 8 as a target
    }
    num_chapters_target = length_to_chapters_map.get(story_length.lower(), 5) # Default to 5 if invalid

    prompt = f"Generate a detailed story outline for a light novel titled '{title}' in the genre '{genre}'. "              f"The story should be '{story_length}' in length, covering approximately {num_chapters_target} chapters. "              f"For each chapter, provide a title line starting exactly with 'Chapter X: [Your Chapter Title]' (e.g., 'Chapter 1: The Accidental Meeting'). "              f"Immediately following the title line for each chapter, provide a multi-line summary of its key events, character development points, and setting details, with each point preferably on a new line starting with a hyphen '- '. "              f"Example of a single chapter's format:\n"              f"Chapter 1: The Spark\n"              f"- Main characters bump into each other in a crowded hallway.\n"              f"- Brief, awkward but memorable interaction.\n"              f"- One character drops a distinctive item, the other picks it up.\n\n"              f"Ensure the output consists *only* of the chapter titles and their summaries, formatted as requested, one chapter after another. Do not include any introductory or concluding text outside of the outline itself."

    print(f"Introducing delay of {LLM_CALL_DELAY_SECONDS}s before LLM call for outline generation (length: {story_length})...") # Optional
    time.sleep(LLM_CALL_DELAY_SECONDS)
    try:
        response = model.generate_content(prompt) # Assuming 'model' is initialized
        if response.parts:
            return response.text.strip()
        else:
            return f"Error: No content generated for outline. Response was empty or blocked. Prompt asked for {num_chapters_target} chapters for a '{story_length}' story."
    except Exception as e:
        print(f"An error occurred during outline generation (length: {story_length}): {e}")
        return f"Error generating outline for title: {title} (length: {story_length}). Details: {str(e)}"


def generate_chapter_text(title: str, genre: str, chapter_outline: str, detail_level: str = "medium", narrative_pacing: str = "medium", overall_story_summary: str = "", previous_chapters_summary: str = "") -> str:
    """
    Generates the full text for a single chapter based on its outline,
    the overall story, desired detail level, narrative pacing, and summaries of previous chapters.

    Args:
        title (str): The main title of the light novel.
        genre (str): The genre of the light novel.
        chapter_outline (str): The specific outline or summary for this chapter.
        detail_level (str): Desired level of detail ('low', 'medium', 'high').
        overall_story_summary (str): A brief summary of the entire story arc (optional but recommended).
        previous_chapters_summary (str): A summary of events from previous chapters (optional but recommended for continuity).

    Returns:
        str: The generated text for the chapter.
    """
    detail_instructions = {
        "low": "Focus on advancing the plot with concise descriptions. Keep imagery and exposition minimal unless critical.",
        "medium": "Provide balanced descriptions, giving enough detail to set the scene and convey character emotions without excessive length. Standard narrative detail.",
        "high": "Weave in rich, vivid descriptions using sensory details (sight, sound, smell, touch, taste) where appropriate. Explore character thoughts and emotions more deeply. Create a strong atmosphere."
    }
    detail_prompt_segment = detail_instructions.get(detail_level.lower(), detail_instructions["medium"])

    pacing_instructions = {
        "slow": "Adopt a slower narrative pace for this chapter. Allow scenes to breathe, delve into character thoughts and emotions more deeply, and build atmosphere. Plot progression can be gradual.",
        "medium": "Maintain a standard narrative pace, balancing scene development, character interaction, and plot progression appropriately.",
        "fast": "Adopt a faster narrative pace. Focus on moving the plot forward quickly. Scenes may be shorter and more direct, with a higher density of events or quicker resolution of conflicts within this chapter."
    }
    pacing_prompt_segment = pacing_instructions.get(narrative_pacing.lower(), pacing_instructions["medium"])

    prompt = (
        f"You are writing a chapter for a light novel titled '{title}' in the '{genre}' genre.\n"
        f"Overall story context: {overall_story_summary if overall_story_summary else 'Not provided. Focus on the chapter outline.'}\n"
        f"Summary of previous chapters: {previous_chapters_summary if previous_chapters_summary else 'This is an early chapter or context is not provided.'}\n\n"
        f"Current Chapter Outline:\n{chapter_outline}\n\n"
        f"Instructions for this chapter's composition:\n"
        f"- Level of Detail: {detail_prompt_segment}\n"
        f"- Narrative Pacing: {pacing_prompt_segment}\n\n"
        f"Please write the full text for this chapter. Include dialogue, descriptions, and character interactions as appropriate. "
        f"Ensure the chapter flows well and aligns with the provided outline, context, and requested detail and pacing. "
        f"The output should be only the chapter text itself, without any extra titles like 'Chapter X Text:'."
    )

    print(f"Introducing delay of {LLM_CALL_DELAY_SECONDS}s before LLM call for chapter text (detail: {detail_level}, pacing: {narrative_pacing})...") # Optional
    time.sleep(LLM_CALL_DELAY_SECONDS)
    try:
        response = model.generate_content(prompt) # Assuming 'model' is initialized
        if response.parts:
            return response.text.strip()
        else:
            error_message = f"Error: No content generated for chapter (detail: {detail_level}, pacing: {narrative_pacing}). Response was empty or blocked. Chapter Outline: {chapter_outline[:100]}..."
            print(error_message)
            return error_message
    except Exception as e:
        error_message = f"Error generating chapter text (detail: {detail_level}, pacing: {narrative_pacing}) for outline: '{chapter_outline[:100]}...'. Details: {str(e)}"
        print(error_message)
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
        f"You are an expert dialogue editor for {genre} light novels. Your task is to review and enhance ONLY the dialogue in the following chapter text. "
        f"Make the dialogue more natural, engaging, and consistent with the characters (context provided below) and the {genre} genre. "
        f"Dialogue should reflect a realistic highschool setting and the established character voices. "
        f"Focus PURELY on dialogue improvement. Do NOT alter plot points, scene structure, or descriptive text unless a minor tweak to narration immediately around dialogue is essential for the dialogue change to make sense. "
        f"If the existing dialogue is already high quality and fitting, make minimal or no changes. "
        f"Preserve all non-dialogue parts of the chapter as they are.\n\n"
        f"Genre: {genre}\n"
        f"Character Context: {characters_summary}\n"
        f"Overall Story Context: {overall_story_summary if overall_story_summary else 'General highschool romance.'}\n\n"
        f"--- Chapter Text to Review ---\n"
        f"{chapter_text}\n"
        f"--- End of Chapter Text ---\n\n"
        f"Return the ENTIRE chapter text, with your dialogue enhancements seamlessly integrated. Do not add any commentary, analysis, or summary before or after the revised chapter text. Output only the complete, edited chapter."
    )

    print(f"Introducing delay of {LLM_CALL_DELAY_SECONDS}s before LLM call for dialogue enhancement...") # Optional
    time.sleep(LLM_CALL_DELAY_SECONDS)
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
        f"You are a senior editor for {genre} light novels. Perform a final, holistic review of the complete draft for the novel titled '{title}'.\n"
        f"Focus on overall coherence, narrative consistency (plot, character arcs), pacing, thematic integrity, and reader engagement. "
        f"The story must be suitable for the {genre} genre and its intended audience.\n\n"
        f"Character Context: {characters_summary}\n"
        f"Overall Story Context: {overall_story_summary if overall_story_summary else 'General highschool romance.'}\n\n"
        f"--- Full Story Draft ---\n"
        f"{full_story_text}\n"
        f"--- End of Story Draft ---\n\n"
        f"**IMPORTANT INSTRUCTIONS FOR YOUR RESPONSE FORMAT:** Your entire response MUST begin *EXACTLY* with one of the following status codes, followed by the corresponding content, and nothing else before the status code.\n\n"
        f"1.  If the story is excellent and requires no significant changes: Respond with 'STATUS: APPROVED' on the first line, followed by a brief (1-2 sentence) approval message on the next line. Example:\n"
        f"    STATUS: APPROVED\n"
        f"    This story is well-written, coherent, and engaging. Ready for publication.\n\n"
        f"2.  If there are minor issues (e.g., typos, awkward phrasing, small continuity errors) that can be fixed with light edits or suggestions you can list: Respond with 'STATUS: CRITIQUE_PROVIDED' on the first line. On subsequent lines, provide ONLY your specific, actionable critique notes. Do NOT return the full story text in this case.\n\n"
        f"3.  If the story has significant issues (e.g., major plot holes, inconsistent character behavior, severe pacing problems) and you can provide an improved version: Respond with 'STATUS: REVISED' on the first line. On subsequent lines, provide *ONLY THE COMPLETE REVISED STORY TEXT*. The revised story should start directly with its first chapter's title or text. Attempt to maintain the original chapter divisions and formatting if they were clear. Do not add any commentary before or after the revised story text itself.\n\n"
        f"Choose only ONE of these three response formats. Ensure your response starts precisely with 'STATUS: <status_code>'."
    )

    print(f"Introducing delay of {LLM_CALL_DELAY_SECONDS}s before LLM call for final story review...") # Optional
    time.sleep(LLM_CALL_DELAY_SECONDS)
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
    # Add this new print statement here:
    if 'LLM_CALL_DELAY_SECONDS' in globals() and LLM_CALL_DELAY_SECONDS > 0:
        print(f"NOTE: LLM calls in this test suite include a {LLM_CALL_DELAY_SECONDS}s delay each for rate limit management.")
        print("Test execution will be slower accordingly.")
    else:
        print("NOTE: No LLM call delays are active in this test suite.")


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
            model = genai.GenerativeModel('gemini-2.0-flash-lite') # Updated model
            print("Gemini model re-initialized with gemini-2.0-flash-lite.") # Updated print message
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
    for length_test in ["short", "medium", "long"]:
        print(f"--- Testing for story_length: '{length_test}' ---")
        try:
            # Use a slightly more specific title for testing this part
            outline = generate_outline(f"{test_title} - {length_test.capitalize()} Version", test_genre, story_length=length_test)
            if outline and not outline.startswith("Error") and api_key_present_and_real:
                print(f"Generated outline for '{length_test}' (first 150 chars):\n{outline[:150]}...")
                # Basic check if number of "Chapter X" mentions aligns somewhat with expectation
                # This is a very rough check.
                chapter_mentions = len(re.findall(r"Chapter \d+", outline, re.IGNORECASE))
                print(f"Found {chapter_mentions} 'Chapter X' mentions.")
            elif outline: # Placeholder or error response
                print(f"Outline gen test for '{length_test}' (skipped/placeholder or error): {outline[:150]}...")
            else:
                print(f"Outline gen test for '{length_test}': No outline returned.")
        except Exception as e:
            print(f"Outline gen error for '{length_test}': {e}")
    # Ensure 're' module is imported at the top of llm_service.py if not already: import re

    # --- Test Chapter Generation (minimal) ---
    print("\n--- Testing Chapter Generation ---")
    sample_chapter_outline_for_pacing_test = "A critical confrontation occurs between Yui and Mika regarding Kanna, leading to a tense cliffhanger."
    # Test pacing with medium detail level
    detail_level_for_pacing_test = "medium"
    for pace_test in ["slow", "medium", "fast"]:
        print(f"--- Testing for narrative_pacing: '{pace_test}' (detail: {detail_level_for_pacing_test}) ---")
        try:
            chap_text = generate_chapter_text(
                f"{test_title} - {pace_test.capitalize()} Pace",
                test_genre,
                sample_chapter_outline_for_pacing_test,
                detail_level=detail_level_for_pacing_test,
                narrative_pacing=pace_test, # Add new parameter
                overall_story_summary=test_story_summary
            )
            if chap_text and not chap_text.startswith("Error") and api_key_present_and_real:
                print(f"Generated chapter for '{pace_test}' pacing (first 150 chars):\n{chap_text[:150]}...")
                print(f"Generated text length: {len(chap_text)}") # Length might vary with pacing
            elif chap_text: # Placeholder or error response
                print(f"Chapter gen test for '{pace_test}' pacing (skipped/placeholder or error): {chap_text[:150]}...")
            else:
                print(f"Chapter gen test for '{pace_test}' pacing: No chapter text returned.")
        except Exception as e:
            print(f"Chapter gen error for '{pace_test}' pacing: {e}")

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
