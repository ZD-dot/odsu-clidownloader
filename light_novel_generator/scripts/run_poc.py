import sys
import os
import re # For parsing chapter outlines

# Add the parent directory (light_novel_generator) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.llm_service import generate_titles, generate_outline, generate_chapter_text
except ImportError:
    print("Error: Could not import from core.llm_service.")
    print("Ensure you are running this script from the 'light_novel_generator/scripts' directory,")
    print("or that the 'light_novel_generator' directory is in your PYTHONPATH.")
    exit(1)

def parse_outline_into_chapters(outline_text: str) -> list[dict[str, str]]:
    """
    Parses a full story outline into a list of chapter outlines.
    Assumes chapters are delineated by lines like "Chapter X:" or "Chapter X -"
    Returns a list of dictionaries, where each dict has 'title' and 'description'.
    """
    chapters = []
    # Regex to find lines starting with "Chapter " followed by a number and then text
    # It captures the chapter title (e.g., "Chapter 1: The Beginning") and the subsequent description
    # It looks for "Chapter X: Title" or "Chapter X - Title"
    # Then it captures everything until the next "Chapter X" or end of string
    pattern = re.compile(r"(Chapter\s*\d+\s*[:\-].*?)(?=\nChapter\s*\d+\s*[:\-]|$)", re.DOTALL | re.IGNORECASE)

    # First, split by the pattern to get individual chapter blocks
    raw_chapter_blocks = re.split(r"\n(?=Chapter\s*\d+\s*[:\-])", outline_text.strip())

    current_chapter_title = ""
    current_chapter_description = ""

    for block in raw_chapter_blocks:
        block = block.strip()
        if not block:
            continue

        # Try to extract a title line like "Chapter X: Title Name"
        title_match = re.match(r"(Chapter\s*\d+\s*[:\-].*?)\n", block, re.IGNORECASE)
        if title_match:
            if current_chapter_title and current_chapter_description: # Save previous chapter
                 chapters.append({"title": current_chapter_title.strip(), "description": current_chapter_description.strip()})
            current_chapter_title = title_match.group(1).strip()
            current_chapter_description = block[len(current_chapter_title):].strip() # Rest is description
        elif current_chapter_title: # If no new title match, append to current description
            current_chapter_description += "\n" + block
        else: # If no current chapter title, this block might be an intro or unformatted
            # For simplicity, assign it to a generic chapter or handle as needed
            if not chapters and not current_chapter_title: # If it's the very first block without a clear "Chapter X"
                current_chapter_title = "Chapter 1: Introduction (auto-parsed)" # Default title
                current_chapter_description = block
            # else, this block might be part of a previous chapter without proper new chapter heading, so ignore or append

    # Add the last processed chapter
    if current_chapter_title and current_chapter_description:
        chapters.append({"title": current_chapter_title.strip(), "description": current_chapter_description.strip()})

    # If parsing failed to find any chapters but there's content, treat the whole outline as one chapter
    if not chapters and outline_text:
        chapters.append({"title": "Chapter 1 (auto-parsed)", "description": outline_text})

    return chapters


def run_command_line_poc():
    """
    Runs a command-line proof-of-concept for generating light novel titles, outlines, and chapters.
    """
    print("Welcome to the Light Novel Generator POC!")
    print("----------------------------------------")

    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    api_key_configured = True
    if not os.path.exists(env_path) or not os.getenv("GEMINI_API_KEY"):
        print("\nIMPORTANT: The GEMINI_API_KEY is not configured.")
        print(f"Please create a '.env' file in the '{os.path.dirname(env_path)}' directory")
        print("with the following content: GEMINI_API_KEY=your_actual_gemini_api_key")
        print("The application will use placeholder data if the key is missing.")
        api_key_configured = False
        # Attempt to load anyway, llm_service will handle the error if key is truly missing
        from dotenv import load_dotenv
        load_dotenv() # Load .env if it exists, even if key might be missing for llm_service to check

    genre = "highschool yuri"
    print(f"Genre focus: {genre}\n")

    # --- Title Generation ---
    print("Generating titles...")
    selected_title = ""
    try:
        titles = generate_titles(genre, num_titles=3) # Reduced to 3 for brevity
        if not titles or any("Error generating title" in t for t in titles) or not api_key_configured:
            print("Could not generate titles effectively. Using placeholders.")
            if titles and any("Error generating title" in t for t in titles): print(f"Details: {titles}")
            titles = [
                "Placeholder Title 1: Sakura's Secret Sketchbook",
                "Placeholder Title 2: The Day We Met Under the Rain",
                "Placeholder Title 3: Melodies of a Shared Rooftop"
            ]

        print("\nAvailable Titles:")
        for i, t_option in enumerate(titles):
            print(f"{i + 1}. {t_option}")

        selected_index = -1
        while selected_index < 0 or selected_index >= len(titles):
            try:
                choice = input(f"Select a title by number (1-{len(titles)}): ")
                selected_index = int(choice) - 1
            except ValueError:
                print("Invalid input. Please enter a number.")
            if selected_index < 0 or selected_index >= len(titles):
                print("Invalid selection. Please try again.")

        selected_title = titles[selected_index]
        print(f"You selected: '{selected_title}'\n")

    except ValueError as ve:
        print(f"Configuration Error during Title Generation: {ve}")
        print("Cannot proceed without resolving API key issue if it's the cause.")
        return
    except Exception as e:
        print(f"An error occurred during title generation: {e}")
        selected_title = "Fallback Title due to Error" # Use a fallback
        print(f"Using fallback title: {selected_title}")


    # --- Outline Generation ---
    print(f"Generating outline for '{selected_title}'...")
    generated_outline_text = ""
    try:
        generated_outline_text = generate_outline(selected_title, genre, num_chapters=3) # 3 chapters for POC
        if not generated_outline_text or generated_outline_text.startswith("Error") or not api_key_configured:
            print("Could not generate an outline effectively. Using a placeholder.")
            if generated_outline_text and generated_outline_text.startswith("Error"): print(f"Details: {generated_outline_text}")
            generated_outline_text = (
                f"Placeholder Outline for: {selected_title}\n\n"
                f"Chapter 1: First Encounter\n- Summary: Main characters Hana and Yumi meet during the school's cultural festival preparations. Yumi is impressed by Hana's quiet dedication to her art project.\n- Characters: Hana (shy, artistic), Yumi (outgoing, supportive).\n\n"
                f"Chapter 2: Shared Moments\n- Summary: Hana and Yumi start spending lunch breaks together. They discover shared interests and a growing comfort with each other. A minor misunderstanding occurs but is quickly resolved, bringing them closer.\n- Setting: School rooftop, classroom.\n\n"
                f"Chapter 3: A Budding Connection\n- Summary: As the festival approaches, Yumi helps Hana finish her project late one evening. They share a vulnerable moment, hinting at deeper feelings. The chapter ends with them watching the sunset from the art room window.\n- Character Dev: Hana opens up more, Yumi realizes her feelings might be more than friendship."
            )
        print("\nGenerated Outline:")
        print("--------------------")
        print(generated_outline_text)
        print("--------------------\n")
    except Exception as e:
        print(f"An error occurred during outline generation: {e}")
        # Use the placeholder if an error occurred and text is empty
        if not generated_outline_text:
             generated_outline_text = (
                f"Placeholder Outline for: {selected_title}\n\n"
                f"Chapter 1: First Encounter\n- Summary: Main characters Hana and Yumi meet during the school's cultural festival preparations. Yumi is impressed by Hana's quiet dedication to her art project.\n- Characters: Hana (shy, artistic), Yumi (outgoing, supportive).\n\n"
                f"Chapter 2: Shared Moments\n- Summary: Hana and Yumi start spending lunch breaks together. They discover shared interests and a growing comfort with each other. A minor misunderstanding occurs but is quickly resolved, bringing them closer.\n- Setting: School rooftop, classroom.\n\n"
                f"Chapter 3: A Budding Connection\n- Summary: As the festival approaches, Yumi helps Hana finish her project late one evening. They share a vulnerable moment, hinting at deeper feelings. The chapter ends with them watching the sunset from the art room window.\n- Character Dev: Hana opens up more, Yumi realizes her feelings might be more than friendship."
            )


    # --- Chapter Generation ---
    print("Parsing outline into chapters...")
    chapter_outlines = parse_outline_into_chapters(generated_outline_text)

    if not chapter_outlines:
        print("Could not parse chapter outlines from the generated text. Using a default single chapter structure based on the full outline.")
        chapter_outlines = [{"title": "Chapter 1 (Full Outline)", "description": generated_outline_text}]

    print(f"Found {len(chapter_outlines)} chapter(s) in the outline.\n")

    full_story_text = []
    previous_chapters_summary = ""
    overall_story_summary = f"This is a highschool yuri light novel titled '{selected_title}'. The story revolves around the developing relationship between the main characters amidst their school life." # Simple overall summary

    for i, chap_info in enumerate(chapter_outlines):
        print(f"--- Generating Chapter {i + 1}: {chap_info['title']} ---")
        print(f"Using outline section:\n{chap_info['description'][:150]}..." if len(chap_info['description']) > 150 else chap_info['description'])

        try:
            chapter_text = generate_chapter_text(
                title=selected_title,
                genre=genre,
                chapter_outline=chap_info['description'],
                overall_story_summary=overall_story_summary,
                previous_chapters_summary=previous_chapters_summary
            )
            if not chapter_text or chapter_text.startswith("Error: No content generated") or chapter_text.startswith("Error generating chapter text") or not api_key_configured:
                print(f"Could not generate text for Chapter {i+1} effectively. Using placeholder.")
                if chapter_text and (chapter_text.startswith("Error:") or chapter_text.startswith("Error generating")): print(f"Details: {chapter_text}")
                chapter_text = f"Placeholder text for Chapter {i+1}: {chap_info['title']}\n\n{chap_info['description']}\n\n[Imagine detailed scenes and dialogues here based on the summary above.]"

            print(f"\n--- Text for Chapter {i + 1}: {chap_info['title']} ---")
            print(chapter_text)
            print("--- End of Chapter ---")

            full_story_text.append(f"## {chap_info['title']}\n\n{chapter_text}") # Using markdown-like title for chapter

            # Update previous_chapters_summary (simple version for POC)
            # For a more sophisticated approach, an LLM could summarize the generated chapter_text.
            # Here, we just append the outline of the chapter that was just generated.
            previous_chapters_summary += f"Summary of {chap_info['title']}:\n{chap_info['description']}\n\n"

        except Exception as e:
            print(f"An error occurred during chapter generation for {chap_info['title']}: {e}")
            full_story_text.append(f"## {chap_info['title']}\n\n[Error generating content for this chapter. Original outline was: {chap_info['description']}]")
            previous_chapters_summary += f"Error occurred while generating {chap_info['title']}.\n"
        print("\n")

    print("\n--- Full Generated Story Draft ---")
    for story_part in full_story_text:
        print(story_part)
        print("\n------------------------------------\n")

    print("\nPOC Finished.")

if __name__ == "__main__":
    # Ensure .env is loaded if script is run directly
    # This is especially important if the script is in a subfolder and .env is in parent
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    from dotenv import load_dotenv
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        # If .env is in the current script's directory (less likely for this structure)
        load_dotenv()

    run_command_line_poc()
