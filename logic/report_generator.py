from fpdf import FPDF
import datetime

class PDFReport(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Title
        self.cell(0, 10, 'IP Evaluation Report', 0, 1, 'C')
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def chapter_title(self, label):
        # Arial 12
        self.set_font('Arial', 'B', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, label, 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def chapter_body(self, body):
        # Read text file
        self.set_font('Arial', '', 11)
        # Output justified text
        self.multi_cell(0, 5, body)
        # Line break
        self.ln()

def create_pdf(patent_data, evaluation_text, user_context, filename="ip_report.pdf"):
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Metadata Section
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Patent: {patent_data.get('title', 'Unknown')}", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"Publication Number: {patent_data.get('publication_number', 'N/A')}", 0, 1)
    pdf.cell(0, 5, f"Date Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.ln(5)
    
    # User Context
    pdf.chapter_title("User Context")
    pdf.chapter_body(user_context)
    
    # Evaluation Content
    # We can try to parse the markdown a bit or just dump it textually but cleaner.
    # For V1 let's just dump the text but filter out the markdown headers for the PDF headers
    
    # Simple markdown parsing for the PDF structure
    lines = evaluation_text.split('\n')
    
    current_body = ""
    
    for line in lines:
        if line.strip().startswith('### '):
            # If we have accumulated body, print it
            if current_body:
                pdf.chapter_body(current_body.strip())
                current_body = ""
            
            # Print new chapter title
            title = line.strip().replace('### ', '')
            pdf.chapter_title(title)
        else:
            # Accumulate text, removing bold markers for cleaner plain text
            clean_line = line.replace('**', '').replace('* ', '- ') # Convert bullets
            current_body += clean_line + "\n"
            
    # Print remaining body
    if current_body:
        pdf.chapter_body(current_body.strip())

    return pdf.output(dest='S') # Return as byte string for Streamlit download
