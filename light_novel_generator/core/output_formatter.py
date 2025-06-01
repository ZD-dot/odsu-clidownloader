from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1: # Only on the first page
            # Arial bold 15
            self.set_font('Arial', 'B', 15)
            # Calculate width of title and position
            title_w = self.get_string_width(self.title) + 6
            self.set_x((self.w - title_w) / 2)
            # Colors of frame, background and text
            # self.set_draw_color(0, 80, 180) # Frame
            # self.set_fill_color(230, 230, 0) # Background
            # self.set_text_color(220, 50, 50) # Text
            # Thickness of frame (1 mm)
            # self.set_line_width(1)
            # Title
            self.cell(title_w, 10, self.title, border=0, ln=1, align='C', fill=0) # No border/fill
            # Line break
            self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Text color in gray
        self.set_text_color(128)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, title_text):
        # Arial 12
        self.set_font('Arial', 'B', 12)
        # Background color
        # self.set_fill_color(200, 220, 255)
        # Title
        self.ln(10) # Space before chapter title
        self.cell(0, 6, title_text, 0, 1, 'L', 0) # No fill
        # Line break
        self.ln(4)

    def chapter_body(self, body_text):
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        self.multi_cell(0, 5, body_text)
        # Line break
        self.ln()

    def add_story_chapter(self, chapter_title_str, chapter_text_str):
        self.add_page()
        self.chapter_title(chapter_title_str)
        self.chapter_body(chapter_text_str)

def create_pdf_from_story(story_title: str, story_chapters: list[dict[str,str]], output_dir: str = "temp_pdf_output") -> str:
    """
    Creates a PDF document from a list of story chapters.

    Args:
        story_title (str): The title of the novel.
        story_chapters (list[dict[str,str]]): A list of dictionaries,
                                            where each dict has 'title' (chapter title)
                                            and 'text' (chapter content).
        output_dir (str): The directory to save the PDF in.

    Returns:
        str: The path to the generated PDF file, or None if error.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf = PDF()
    pdf.set_title(story_title)
    pdf.set_author("AI Light Novel Generator") # You can change this

    # Add chapters
    for chapter in story_chapters:
        chapter_title_text = chapter.get('title', 'Untitled Chapter')
        chapter_content_text = chapter.get('text', 'No content for this chapter.')
        pdf.add_story_chapter(chapter_title_text, chapter_content_text)

    # Sanitize title for filename
    safe_filename = "".join([c if c.isalnum() else "_" for c in story_title])
    if not safe_filename: safe_filename = "generated_novel"
    safe_filename = safe_filename[:50] # Limit length

    pdf_filename = f"{safe_filename}.pdf"
    pdf_filepath = os.path.join(output_dir, pdf_filename)

    try:
        pdf.output(pdf_filepath, 'F')
        return pdf_filepath
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

if __name__ == '__main__':
    # Example Usage:
    print("Testing PDF generation...")
    example_chapters = [
        {"title": "Chapter 1: The Beginning", "text": "It was a dark and stormy night... " * 50},
        {"title": "Chapter 2: The Discovery", "text": "Suddenly, a wild plot appeared! " * 60},
        {"title": "Chapter 3: The Climax and End", "text": ("This is the story of a hero who did many things. " * 30) + "\nAnd then they lived happily ever after, or did they? " * 20 }
    ]
    example_title = "My Awesome AI Novel"

    # Create a dummy temp_pdf_output directory if it doesn't exist for the test
    if not os.path.exists("temp_pdf_output"):
        os.makedirs("temp_pdf_output")

    pdf_file = create_pdf_from_story(example_title, example_chapters)
    if pdf_file:
        print(f"Successfully generated PDF: {os.path.abspath(pdf_file)}")
    else:
        print("Failed to generate PDF.")
