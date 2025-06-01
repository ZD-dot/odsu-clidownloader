from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import sys
import os

# Ensure the parent directory is in sys.path to find the 'core' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Flask and other standard imports
from flask import send_file, current_app # current_app might be useful for path constructions
import re # For parsing chapter outlines
# os is already imported by sys path logic, but good to have if direct os calls are made here beyond path manipulation

# Core application imports with fallbacks
try:
    from core.llm_service import generate_titles, generate_outline, generate_chapter_text, enhance_dialogue, final_review_story
    from core.output_formatter import create_pdf_from_story
except ImportError as e:
    print(f"ERROR in routes.py: Could not import one or more functions from core modules: {e}. Ensure PYTHONPATH is set or app is run from project root.")
    # Fallback definitions for UI testing if core modules are missing
    def generate_titles(genre, num_titles=5, **kwargs):
        print(f"Warning: Using fallback generate_titles. Genre: {genre}")
        return [f"Fallback Title {i}: The Lost {genre} Scroll" for i in range(1, num_titles + 1)]
    def generate_outline(title, genre, num_chapters=3, **kwargs):
        print(f"Warning: Using fallback generate_outline. Title: {title}")
        return f"Placeholder outline for '{title}'.\nChapter 1: Meeting\nChapter 2: Adventure\nChapter 3: Conclusion"
    def generate_chapter_text(title, genre, chapter_outline, overall_story_summary="", previous_chapters_summary="", **kwargs):
        print(f"Warning: Using fallback generate_chapter_text for outline: {chapter_outline[:50]}...")
        return f"Fallback chapter text for '{title}' based on outline: {chapter_outline}"
    def enhance_dialogue(chapter_text, genre, characters_summary="", overall_story_summary="", **kwargs):
        print(f"Warning: Using fallback enhance_dialogue for chapter: {chapter_text[:50]}...")
        return chapter_text
    def final_review_story(full_story_text, title, genre, characters_summary="", overall_story_summary="", **kwargs):
        print(f"Warning: Using fallback final_review_story for title: {title}")
        return "approved", "Fallback: Story approved as is by fallback function."
    def create_pdf_from_story(story_title, story_chapters, output_dir="temp_pdfs_output", **kwargs):
        print(f"Warning: Using fallback create_pdf_from_story for {story_title}. PDF not actually generated.")
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        dummy_filename = "".join([c if c.isalnum() else "_" for c in story_title]) + "_fallback.pdf"
        dummy_path = os.path.join(output_dir, dummy_filename)
        with open(dummy_path, "w") as f: f.write(f"This is a dummy PDF for the story titled '{story_title}'.")
        return dummy_path

# Definition of parse_outline_into_chapters (can be moved to utils later)
# This is similar to the one in run_poc.py
def parse_outline_into_chapters(outline_text: str) -> list[dict[str, str]]:
    chapters = []
    # Regex to find lines starting with "Chapter " followed by a number and then text
    # Captures "Chapter X: Title" or "Chapter X - Title" and subsequent description
    raw_chapter_blocks = re.split(r"\n(?=Chapter\s*\d+\s*[:\-])", outline_text.strip())
    current_chapter_title = ""
    current_chapter_description = ""

    for block in raw_chapter_blocks:
        block = block.strip()
        if not block: continue
        title_match = re.match(r"(Chapter\s*\d+\s*[:\-].*?)\n", block, re.IGNORECASE)
        if title_match:
            if current_chapter_title and current_chapter_description:
                chapters.append({"title": current_chapter_title.strip(), "description": current_chapter_description.strip()})
            current_chapter_title = title_match.group(1).strip()
            current_chapter_description = block[len(current_chapter_title):].strip()
        elif current_chapter_title:
            current_chapter_description += "\n" + block
        else: # First block without "Chapter X"
            current_chapter_title = "Chapter 1: Introduction (auto-parsed)"
            current_chapter_description = block

    if current_chapter_title and current_chapter_description: # Add the last chapter
        chapters.append({"title": current_chapter_title.strip(), "description": current_chapter_description.strip()})
    if not chapters and outline_text: # Fallback for unparsable outline
        chapters.append({"title": "Chapter 1 (Full Outline)", "description": outline_text})
    return chapters

bp = Blueprint('main', __name__)
GENRE = "highschool yuri" # Project-specific genre

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/start', methods=['POST'])
def start_generation():
    session.clear() # Clear previous session data first

    # Store customization options from the form
    session['story_length'] = request.form.get('story_length', 'medium')
    session['detail_level'] = request.form.get('detail_level', 'medium')
    session['narrative_pacing'] = request.form.get('narrative_pacing', 'medium')

    session['status'] = 'titles_requested'

    # Optional: Flash a message confirming options received
    flash(f"Customization options received: Length - {session['story_length']}, Detail - {session['detail_level']}, Pacing - {session['narrative_pacing']}.", "info")

    return redirect(url_for('main.generate_title_options'))

@bp.route('/generate_titles', methods=['GET'])
def generate_title_options():
    if session.get('status') not in ['titles_requested', 'titles_generated']:
        flash("Please start the generation process first.", "warning")
        return redirect(url_for('main.index'))

    # Generate new titles or use existing ones if already generated and user refreshed
    # For simplicity on refresh, we can just regenerate.
    # A more complex app might store previous suggestions in session.
    try:
        titles = generate_titles(GENRE, num_titles=5)
        session['generated_titles'] = titles
        session['status'] = 'titles_generated'
    except Exception as e:
        flash(f"Error generating titles: {e}. Using placeholders.", "danger")
        titles = [f"Placeholder Title {i} (Error Occurred)" for i in range(1, 6)]
        session['generated_titles'] = titles # Store placeholders
        session['status'] = 'titles_error'


    return render_template('title_selection.html', titles=titles)

@bp.route('/select_title', methods=['POST'])
def select_title():
    if session.get('status') not in ['titles_generated', 'titles_error']: # Allow selection even if placeholders were shown due to error
        flash("Please generate titles first.", "warning")
        return redirect(url_for('main.generate_title_options'))

    selected_title = request.form.get('title')
    generated_titles = session.get('generated_titles', [])

    if selected_title and selected_title in generated_titles:
        session['selected_title'] = selected_title
        session['status'] = 'title_selected'
        flash(f"Title selected: '{selected_title}'", "success")
        # Next step will be outline generation
        return redirect(url_for('main.generate_outline_page')) # Placeholder for next step
    else:
        flash("Invalid title selection. Please try again.", "danger")
        return redirect(url_for('main.generate_title_options'))

@bp.route('/generate_outline', methods=['GET']) # Ensure this is GET or handles GET
def generate_outline_page():
    if session.get('status') != 'title_selected' or 'selected_title' not in session:
        flash("Please select a title first.", "warning")
        return redirect(url_for('main.generate_title_options')) # Redirect to title selection if no title

    selected_title = session['selected_title']

    # Avoid re-generating if outline already exists in session (e.g., user refreshed page)
    # However, for simplicity in this step, we can regenerate.
    # A better approach might be:
    # if 'generated_outline' in session and session.get('current_title_for_outline') == selected_title:
    #    outline = session['generated_outline']
    # else:
    #    ... generate ...
    #    session['current_title_for_outline'] = selected_title


    try:
        # Assuming GENRE is defined globally in routes.py or fetched from session
        outline = generate_outline(selected_title, GENRE, num_chapters=5) # Specify num_chapters
        session['generated_outline'] = outline
        session['status'] = 'outline_generated'
    except Exception as e:
        flash(f"Error generating outline: {e}. Using a placeholder.", "danger")
        outline = f"Placeholder outline for '{selected_title}' due to error.\nChapter 1: ...\nChapter 2: ...\nChapter 3: ..."
        session['generated_outline'] = outline # Store placeholder
        session['status'] = 'outline_error'

    return render_template('outline_display.html', title=selected_title, outline=outline)

@bp.route('/confirm_outline', methods=['POST'])
def confirm_outline():
    if session.get('status') not in ['outline_generated', 'outline_error'] or 'generated_outline' not in session:
        flash("Please generate an outline first.", "warning")
        # Redirect to title selection or outline generation page based on where they might be
        return redirect(url_for('main.generate_title_options' if 'selected_title' not in session else 'main.generate_outline_page'))

    # User confirms the outline, proceed to chapter generation
    session['status'] = 'outline_confirmed'
    flash("Outline confirmed. Proceeding to chapter generation.", "success")
    return redirect(url_for('main.generate_chapters_page')) # Placeholder for next step

@bp.route('/generate_chapters', methods=['GET']) # Ensure this is GET
def generate_chapters_page():
    if session.get('status') != 'outline_confirmed' or 'generated_outline' not in session:
        flash("Please confirm the outline first.", "warning")
        return redirect(url_for('main.generate_outline_page'))

    selected_title = session.get('selected_title', 'Untitled Novel')
    outline_text = session.get('generated_outline', '')

    # For simplicity, we regenerate chapters each time this page is visited.
    # A more advanced version might store generated chapters in session to avoid re-generation on refresh.

    story_chapters = []
    parsed_chapters = parse_outline_into_chapters(outline_text)

    if not parsed_chapters:
        flash("Could not parse the outline into chapters. Please review the outline.", "danger")
        return redirect(url_for('main.generate_outline_page'))

    previous_chapters_summary_text = ""
    overall_story_context = f"This is a {GENRE} light novel titled '{selected_title}'. The story should unfold according to the provided chapter outlines, maintaining narrative consistency."

    for i, chap_info in enumerate(parsed_chapters):
        try:
            print(f"Generating text for chapter: {chap_info['title']}") # Server log
            chapter_text_content = generate_chapter_text(
                title=selected_title,
                genre=GENRE,
                chapter_outline=chap_info['description'],
                overall_story_summary=overall_story_context,
                previous_chapters_summary=previous_chapters_summary_text
            )

            if chapter_text_content.startswith("Error: No content generated") or chapter_text_content.startswith("Error generating chapter text"):
                flash(f"Could not generate content for {chap_info['title']}. Placeholder used.", "warning")
                chapter_text_content = f"[Placeholder for {chap_info['title']} due to generation error. Outline was: {chap_info['description']}]"
            else: # If chapter text generation was successful, try to enhance dialogue
                try:
                    print(f"Enhancing dialogue for chapter: {chap_info['title']}") # Server log
                    # Basic character summary - can be improved with more context from outline/user input later
                    char_summary_for_dialogue = session.get('character_summary_stub', "Two main female characters in a highschool yuri story.")
                    story_summary_for_dialogue = session.get('overall_story_summary_stub', f"A {GENRE} novel titled '{selected_title}'.")

                    enhanced_chapter_text = enhance_dialogue(
                        chapter_text_content,
                        GENRE,
                        characters_summary=char_summary_for_dialogue,
                        overall_story_summary=story_summary_for_dialogue
                    )
                    if enhanced_chapter_text != chapter_text_content and not enhanced_chapter_text.startswith("Error"):
                        flash(f"Dialogue enhanced for {chap_info['title']}.", "info") # Optional: info flash
                        chapter_text_content = enhanced_chapter_text
                    elif enhanced_chapter_text.startswith("Error"): # Should not happen if enhance_dialogue returns original on error
                         flash(f"Dialogue enhancement failed for {chap_info['title']}. Using previous version.", "warning")
                    # If no change, it implies dialogue was already good or LLM chose not to modify significantly.
                except Exception as e_dialogue:
                    flash(f"Error during dialogue enhancement for {chap_info['title']}: {e_dialogue}. Using unenhanced version.", "warning")
                    # chapter_text_content remains the unenhanced version

            story_chapters.append({"title": chap_info['title'], "text": chapter_text_content})

            # Update summary for next chapter (simple version, could be LLM summarized)
            previous_chapters_summary_text += f"Summary of {chap_info['title']}:\n{chap_info['description']}\n---\n"

        except Exception as e:
            flash(f"An error occurred generating {chap_info['title']}: {e}", "danger")
            story_chapters.append({"title": chap_info['title'], "text": f"[Error generating this chapter: {e}. Outline: {chap_info['description']}]"})
            # Continue to next chapter if possible

    session['full_story_chapters'] = story_chapters # Store the list of chapter dicts
    session['status'] = 'chapters_generated_ready_for_review'

    return render_template('story_display.html', title=selected_title, story_chapters=story_chapters)

@bp.route('/initiate_final_review', methods=['POST'])
def initiate_final_review():
    if session.get('status') != 'chapters_generated_ready_for_review' or 'full_story_chapters' not in session:
        flash("Please generate the story chapters first.", "warning")
        return redirect(url_for('main.generate_chapters_page'))

    session['status'] = 'final_review_pending'
    # flash("Initiating final story review...", "info") # Optional flash
    return redirect(url_for('main.perform_final_review'))

@bp.route('/perform_final_review', methods=['GET'])
def perform_final_review():
    if session.get('status') != 'final_review_pending' or 'full_story_chapters' not in session:
        flash("Cannot perform final review at this stage.", "warning")
        # Determine best redirect based on what's missing
        if 'full_story_chapters' not in session:
            return redirect(url_for('main.generate_chapters_page'))
        return redirect(url_for('main.index')) # Fallback redirect

    selected_title = session.get('selected_title', 'Untitled Novel')
    story_chapters = session.get('full_story_chapters', []) # List of dicts

    # Concatenate chapter texts to form the full story for review
    full_story_text_for_review = "\n\n---\n\n".join([f"## {chap['title']}\n\n{chap['text']}" for chap in story_chapters])

    # Get other context from session if available (using stubs for now)
    char_summary = session.get('character_summary_stub', f"Main characters in a {GENRE} story.")
    story_summary = session.get('overall_story_summary_stub', f"A {GENRE} novel titled '{selected_title}'.")

    try:
        review_status, review_content = final_review_story(
            full_story_text_for_review,
            selected_title,
            GENRE, # Assuming GENRE is globally defined or from session
            characters_summary=char_summary,
            overall_story_summary=story_summary
        )

        session['final_review_status'] = review_status
        session['final_review_content'] = review_content
        session['status'] = 'final_review_displayed'

        if review_status == "revised":
            # If revised, we need to parse the new story back into chapters for consistency in data structure
            # This is a simplified parsing, assuming revised story maintains "## Chapter Title" format
            new_chapters_text = review_content.split("\n\n---\n\n")
            updated_story_chapters = []
            for i, text_block in enumerate(new_chapters_text):
                title_match = re.match(r"## (.*?)\n\n(.*)", text_block, re.DOTALL)
                if title_match:
                    updated_story_chapters.append({"title": title_match.group(1), "text": title_match.group(2)})
                else: # Fallback if parsing fails
                    updated_story_chapters.append({"title": f"Chapter {i+1} (Revised)", "text": text_block})
            session['full_story_chapters'] = updated_story_chapters # Replace original chapters with revised ones
            flash("The story has been revised by the AI editor.", "info")
        elif review_status == "approved":
            flash(f"Final Review: Approved! {review_content}", "success")
        elif review_status == "critique_provided":
            flash("Final Review: Critique Provided. Please see notes below.", "info")
        elif review_status == "error":
             flash(f"Final Review Error: {review_content}", "danger")


    except Exception as e:
        flash(f"An error occurred during the final review process: {e}", "danger")
        session['final_review_status'] = "error"
        session['final_review_content'] = f"Error during review: {e}"
        session['status'] = 'final_review_displayed' # Still go to display to show error

    return render_template('final_review_display.html',
                           title=selected_title,
                           review_status=session.get('final_review_status'),
                           review_content=session.get('final_review_content'),
                           original_chapters=story_chapters if session.get('final_review_status') != "revised" else None,
                           revised_chapters=session.get('full_story_chapters') if session.get('final_review_status') == "revised" else None
                           )

@bp.route('/finalize_story', methods=['POST']) # This is the existing route that confirms going to PDF
def finalize_story():
    # Check if review was displayed or if it was an error but user wants to proceed
    if session.get('status') != 'final_review_displayed' or 'final_review_status' not in session:
        flash("Please complete the final review step first.", "warning")
        # Redirect to where they left off or to start if session is very broken
        if 'full_story_chapters' not in session:
             return redirect(url_for('main.generate_chapters_page'))
        return redirect(url_for('main.perform_final_review')) # Send them back to review page

    final_review_status = session.get('final_review_status')
    if final_review_status == "error":
        # If review errored, user might still want to proceed with the pre-review story
        flash("Proceeding to PDF with the story version before the review error.", "warning")
    elif final_review_status == "revised":
        flash("Proceeding to PDF with the AI editor's revised story.", "info")
    elif final_review_status == "approved":
        flash("Proceeding to PDF with the approved story.", "success")
    elif final_review_status == "critique_provided":
         flash("Proceeding to PDF with the original story (critique was for information).", "info")


    session['status'] = 'story_approved_for_pdf'
    # No flash here, prior messages should suffice
    return redirect(url_for('main.download_pdf_page'))

@bp.route('/download_pdf')
def download_pdf_page():
    if session.get('status') != 'story_approved_for_pdf':
        flash("Please approve the story first.", "warning")
        return redirect(url_for('main.generate_chapters_page'))

    selected_title = session.get('selected_title', 'My Generated Novel')
    story_chapters = session.get('full_story_chapters', [])

    if not story_chapters:
        flash("No story content found to convert to PDF.", "danger")
        return redirect(url_for('main.generate_chapters_page'))

    # Define a temporary directory for PDFs within the app's instance path or a dedicated temp folder
    # Using current_app.root_path to get project root, then create a 'temp_pdfs' folder there.
    # Ensure this temp_pdfs path is gitignored if it's within the repo structure.
    # For simplicity here, let's assume a 'temp_pdfs' folder in the project root.
    # A better approach for production might use app.instance_path.

    temp_pdf_dir = os.path.join(current_app.root_path, '..', 'temp_pdfs_output') # One level up from 'app' directory to be in 'light_novel_generator/temp_pdfs_output'
    # Ensure the directory for the current_app.root_path is correct. current_app.root_path is often the app package directory.
    # If run.py is in light_novel_generator, and app is in light_novel_generator/app,
    # current_app.root_path will be light_novel_generator/app.
    # So, os.path.join(current_app.root_path, '..', 'temp_pdfs_output') should correctly point to light_novel_generator/temp_pdfs_output

    if not os.path.exists(temp_pdf_dir):
        try:
            os.makedirs(temp_pdf_dir)
        except OSError as e:
            flash(f"Error creating temporary PDF directory: {e}", "danger")
            return redirect(url_for('main.generate_chapters_page'))

    pdf_filepath = None
    try:
        pdf_filepath = create_pdf_from_story(selected_title, story_chapters, output_dir=temp_pdf_dir)

        if not pdf_filepath or not os.path.exists(pdf_filepath):
            flash("Failed to generate PDF file.", "danger")
            return redirect(url_for('main.generate_chapters_page'))

        # Send the file for download and then attempt to clean it up.
        # Using after_this_request to ensure cleanup happens after response is sent.

        # Make sure the filename for attachment is just the basename.
        attachment_filename = os.path.basename(pdf_filepath)

        # Return send_file. Cleanup will be handled by a request teardown or similar if needed,
        # or simply let temp files be managed by OS or periodic cleanup scripts for simplicity in this project.
        # For this project, let's send and not immediately delete in this subtask.
        # Deletion can be a later refinement or manual process for temp_pdfs_output.

        return send_file(pdf_filepath, as_attachment=True, download_name=attachment_filename)

    except Exception as e:
        flash(f"An error occurred during PDF processing: {e}", "danger")
        # Clean up if file was partially created and an error occurred
        if pdf_filepath and os.path.exists(pdf_filepath):
            try:
                os.remove(pdf_filepath)
            except Exception as remove_e:
                print(f"Error cleaning up PDF file {pdf_filepath}: {remove_e}")
        return redirect(url_for('main.generate_chapters_page'))
    # finally:
        # This finally block might execute too soon if send_file is streaming.
        # Consider a more robust cleanup strategy if this becomes an issue.
        # if pdf_filepath and os.path.exists(pdf_filepath) and 'response' not in locals(): # if error before send_file
        #     try:
        #         os.remove(pdf_filepath)
        #         print(f"Cleaned up PDF: {pdf_filepath}")
        #     except OSError as e:
        #         print(f"Error removing PDF file {pdf_filepath} in finally: {e}")
