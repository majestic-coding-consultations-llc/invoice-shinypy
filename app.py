import sqlite3
from shiny import App, Inputs, Outputs, Session, render, ui
from fpdf import FPDF
import os
from datetime import datetime

# Directory to save PDF files
PDF_DIR = "static"

# Ensure the directory exists
os.makedirs(PDF_DIR, exist_ok=True)

# Create SQLite database and table
DB_FILE = "invoices.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                video_title TEXT,
                invoice_amount REAL,
                invoice_number TEXT,
                date TEXT
            )
        """)
        conn.commit()

# Function to create an itemized invoice PDF
def create_invoice_pdf(client_name, video_title, invoice_amount):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    invoice_number = datetime.now().strftime("%Y%m%d%H%M%S")
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf.cell(200, 10, txt="Invoice from Majestic Coding Consultations LLC", ln=True, align="C")

    pdf.cell(200, 10, txt=f"Invoice Number: {invoice_number}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {date}", ln=True)
    pdf.cell(200, 10, txt=f"Client Name: {client_name}", ln=True)

    pdf.ln(10)  # Add a line break

    # Add itemized list
    pdf.set_font("Arial", size=10)
    pdf.cell(100, 10, txt="Video Title", border=1)
    pdf.cell(50, 10, txt="Invoice Amount", border=1, ln=True)
    pdf.cell(100, 10, txt=video_title, border=1)
    pdf.cell(50, 10, txt=f"${invoice_amount}", border=1, ln=True)

    pdf.ln(10)  # Add a line break
    pdf.set_font("Arial", size=12)
    pdf.cell(100, 10, txt="Total", border=1)
    pdf.cell(50, 10, txt=f"${invoice_amount}", border=1, ln=True)

    pdf.ln(10)  # Add a line break
    pdf.cell(200, 10, txt="Invoice is to be paid to Majestic Coding Consultations LLC within 60 days.", ln=True)

    file_path = os.path.join(PDF_DIR, "invoice.pdf")
    pdf.output(file_path)
    return file_path, invoice_number, date

# Define the UI components and layout
app_ui = ui.page_fluid(
    ui.panel_title("Majestic Coding Shiny Invoicing Tool"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.input_dark_mode(mode="dark"),
            ui.input_text_area("client_name", "Client Name", ""),
            ui.input_text_area("video_title", "Video Title", ""),
            ui.input_numeric("invoice_amount", "Invoice Amount", 0),
        ),
        ui.panel_main(
            ui.tags.div(
                ui.tags.img(src="https://avatars.githubusercontent.com/u/33904170?v=4", style="width: 100px; height: 100px;"),
                ui.tags.h3("Fill out the fields on the left"),
                ui.download_button("download_pdf", "Generate and Download PDF"),
                style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;"
            )
        )
    )
)

def server(input: Inputs, output: Outputs, session: Session):
    @output
    @render.download(filename=lambda: f"invoice-{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
    async def download_pdf():
        client_name = input.client_name()
        video_title = input.video_title()
        invoice_amount = input.invoice_amount()
        file_path, invoice_number, date = create_invoice_pdf(client_name, video_title, invoice_amount)
        
        # Store the invoice data in the SQLite database
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (client_name, video_title, invoice_amount, invoice_number, date)
                VALUES (?, ?, ?, ?, ?)
            """, (client_name, video_title, invoice_amount, invoice_number, date))
            conn.commit()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(1024):
                yield chunk

# Initialize the database
init_db()

app = App(app_ui, server)

if __name__ == "__main__":
    app.run(port=8000)
