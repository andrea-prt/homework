import streamlit as st
import openai
import PyPDF2
import io
import tempfile
import os
import subprocess
import base64

# Set your OpenAI API Key here
openai.api_key = "sk-svcacct-BjW8iBg-"  # Replace with your actual API key

st.title("Chatbot Interface")

system_message = """
Sei un assistente virtuale per professori del liceo scientifico. Sei molto brava a creare verifiche per gli studenti.
Le tue risposte devono essere sempre in italiano e contenere solo ed esclusivamente la prova, inoltre devono essere formattate in latex.
"""

# Initialize session state variables if not present
if 'latex_response' not in st.session_state:
    st.session_state.latex_response = None

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

pdf_text = ""

if uploaded_file:
    # Extract text from the uploaded PDF
    with io.BytesIO(uploaded_file.read()) as file_stream:
        reader = PyPDF2.PdfReader(file_stream)
        pdf_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    st.success("PDF text extracted successfully!")

# User input
user_instruction = st.text_area("Enter your instructions", placeholder="Write your prompt here...")

if st.button("Generate Response"):
    if user_instruction:
        # Combine user prompt with extracted PDF text
        full_prompt = f"{user_instruction}\n\nContext from PDF:\n{pdf_text}" if pdf_text else user_instruction

        # Get AI response
        try:
            with st.spinner("Generating response..."):
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7
                )

                st.session_state.latex_response = response.choices[0].message.content

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
    else:
        st.warning("Please enter a prompt instruction.")

# Display LaTeX response if available
if st.session_state.latex_response:
    st.text_area("Generated LaTeX:", value=st.session_state.latex_response, height=300)

# Function to convert LaTeX to PDF
def latex_to_pdf(latex_content):
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define file paths
        tex_path = os.path.join(temp_dir, "document.tex")
        
        # Prepare complete LaTeX document if needed
        if "\\documentclass" not in latex_content:
            complete_latex = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[italian]{{babel}}
\\usepackage{{amsmath, amssymb, amsfonts}}
\\usepackage{{graphicx}}
\\usepackage{{geometry}}
\\geometry{{a4paper, margin=1in}}

\\begin{{document}}
{latex_content}
\\end{{document}}
"""
        else:
            complete_latex = latex_content
            
        # Write LaTeX content to file
        with open(tex_path, "w", encoding="utf-8") as tex_file:
            tex_file.write(complete_latex)
        
        try:
            # Run pdflatex command
            process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, tex_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check if PDF was created
            pdf_path = os.path.join(temp_dir, "document.pdf")
            if os.path.exists(pdf_path):
                # Read the PDF file
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
                return pdf_data, None
            else:
                # Return error message
                return None, f"PDF not generated. LaTeX error: {process.stderr}"
        
        except Exception as e:
            return None, f"Error: {str(e)}"

# Generate PDF button
if st.session_state.latex_response and st.button("Generate PDF"):
    with st.spinner("Generating PDF..."):
        pdf_data, error = latex_to_pdf(st.session_state.latex_response)
        
        if pdf_data:
            st.success("PDF generated successfully!")
            
            # Create download button
            st.download_button(
                label="Download PDF",
                data=pdf_data,
                file_name="generated_test.pdf",
                mime="application/pdf"
            )
        else:
            st.error(f"Failed to generate PDF: {error}")
