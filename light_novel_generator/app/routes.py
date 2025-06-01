from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import sys
import os

# Ensure the parent directory is in sys.path to find the 'core' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from core.llm_service import generate_titles, generate_outline
except ImportError:
    # This might happen if the path isn't set up correctly during Flask's runtime
    # For development, ensure light_novel_generator is in PYTHONPATH or run from there
    print("ERROR in routes.py: Could not import from core.llm_service. Ensure PYTHONPATH is set or app is run from project root.")
    # Fallback for generate_titles if import fails, to allow app to run for UI testing
    def generate_titles(genre, num_titles=5):
        print(f"Warning: Using fallback generate_titles. Import failed. Genre: {genre}, Num: {num_titles}")
        return [f"Fallback Title {i}: The Lost {genre} Scroll" for i in range(1, num_titles + 1)]
    def generate_outline(title, genre, num_chapters=3):
        print(f"Warning: Using fallback generate_outline. Title: {title}, Genre: {genre}")
        return f"Placeholder outline for '{title}'.\nChapter 1: Meeting\nChapter 2: Adventure\nChapter 3: Conclusion"

bp = Blueprint('main', __name__)
GENRE = "highschool yuri" # Project-specific genre

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/start', methods=['POST'])
def start_generation():
    session.clear()
    session['status'] = 'titles_requested'
    # Instead of redirecting to generate_title_options directly,
    # let generate_title_options be a GET route that checks session status
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

# Placeholder for chapter generation page
@bp.route('/generate_chapters')
def generate_chapters_page():
    if session.get('status') != 'outline_confirmed' or 'generated_outline' not in session:
        flash("Please confirm the outline first.", "warning")
        return redirect(url_for('main.generate_outline_page'))

    selected_title = session.get('selected_title', 'Unknown Title')
    outline = session.get('generated_outline', 'No outline found.')
    # This will be implemented in a subsequent step
    return f"Chapter generation page placeholder for title: '{selected_title}'. Outline will be used: <pre>{outline[:200]}...</pre>"
    # return render_template('story_display.html', title=selected_title, story_parts=...)
