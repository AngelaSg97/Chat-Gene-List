import streamlit as st
import pandas as pd
import json
import re
import os
import requests
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types

# --- Configuration and Constants ---
# Use the API key provided via environment variables, or an empty string for the Canvas
API_KEY = os.environ.get("GEMINI_API_KEY", "")
# Using the model specified in the original file
MODEL_NAME = "gemini-2.5-flash-preview-09-2025" 
# IMPORTANT: Provide a non-default email to NCBI E-utilities. 
# Using a dummy email like this will prevent request errors if the user doesn't set one.
NCBI_EMAIL = "gene.analyzer.tool@google.com" 
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# --- NCBI Validation Function ---
@st.cache_data(show_spinner="Validating data against NCBI...")
def validate_results_with_ncbi(data_array):
    """
    Iterates through the structured data from Gemini, queries NCBI Entrez for 
    the gene symbol, and adds validation fields (NCBI Status, NCBI Full Name).
    """
    validated_data = []

    for item in data_array:
        # Attempts to extract the gene symbol using common keys, handling LLM-generated cases
        # Check for both 'Gene Symbol' (as requested in the prompt) and 'geneSymbol' (or other variants)
        gene_symbol = item.get('Gene Symbol') or item.get('geneSymbol') 
        
        # Check if the LLM explicitly marked the gene as "Not Found"
        status_from_llm = item.get('status')
        
        # LOGICAL STEP 4: Validation Tracking NCBI (Backend Log)
        print(f"\n[NCBI VALIDATION] Analisi del gene: {gene_symbol}")
        
        # 1. Skip Condition: Only skip if the gene symbol is definitively missing or marked 'Not Found' by the LLM
        if not gene_symbol:
            item['NCBI Status'] = 'Skipped (Symbol Missing)'
            item['NCBI Full Name'] = 'N/A'
            validated_data.append(item)
            print(f"[NCBI VALIDATION] -> RISULTATO: Saltato (Simbolo Mancante).")
            continue

        if status_from_llm == 'Not Found':
            item['NCBI Status'] = 'Skipped (LLM Not Found)'
            item['NCBI Full Name'] = 'N/A'
            validated_data.append(item)
            print(f"[NCBI VALIDATION] -> RISULTATO: Saltato (LLM ha marcato 'Not Found').")
            continue

        # If we reach here, we have a symbol and the LLM didn't explicitly fail. Proceed to NCBI.

        # 2. ESearch: Find the Gene ID (UID) for the human gene
        esearch_url = f"{NCBI_BASE_URL}esearch.fcgi?db=gene&term={gene_symbol}[gene]+AND+human[organism]&retmode=json&tool=GeneAnalyzer&email={NCBI_EMAIL}"
        try:
            print(f"[NCBI VALIDATION] Chiamata ESearch per ID gene: {esearch_url}")
            esearch_response = requests.get(esearch_url, timeout=10)
            esearch_response.raise_for_status()
            esearch_data = esearch_response.json()
            
            gene_ids = esearch_data.get('esearchresult', {}).get('idlist', [])
            
            if not gene_ids:
                item['NCBI Status'] = 'Gene Not Found in NCBI'
                item['NCBI Full Name'] = 'N/A'
                validated_data.append(item)
                print(f"[NCBI VALIDATION] -> RISULTATO: ID non trovato in NCBI per {gene_symbol}.")
                continue
                
            gene_id = gene_ids[0]
            print(f"[NCBI VALIDATION] -> ID Trovato: {gene_id}")

            # 3. ESummary: Get the gene summary data (for the full name)
            esummary_url = f"{NCBI_BASE_URL}esummary.fcgi?db=gene&id={gene_id}&retmode=xml&tool=GeneAnalyzer&email={NCBI_EMAIL}"
            print(f"[NCBI VALIDATION] Chiamata ESummary per Nome Completo: {esummary_url}")
            esummary_response = requests.get(esummary_url, timeout=10)
            esummary_response.raise_for_status()
            
            # Parsing the XML response
            root = ET.fromstring(esummary_response.content)
            
            # Extract the full name (usually in the 'Description' tag in Entrez Gene summary)
            full_name = 'Not Available'
            for doc_sum in root.findall('./DocumentSummarySet/DocumentSummary'):
                description_element = doc_sum.find('Description')
                if description_element is not None:
                    full_name = description_element.text
                    break
            
            item['NCBI Status'] = f'Found (ID: {gene_id})'
            item['NCBI Full Name'] = full_name
            print(f"[NCBI VALIDATION] -> NOME COMPLETO: {full_name}")
            
        except requests.exceptions.RequestException as req_err:
            item['NCBI Status'] = f'API Error: {req_err}'
            item['NCBI Full Name'] = 'N/A'
            print(f"[NCBI VALIDATION] -> ERRORE API NCBI: {req_err}")
        except Exception as e:
            item['NCBI Status'] = f'Processing Error: {e}'
            item['NCBI Full Name'] = 'N/A'
            print(f"[NCBI VALIDATION] -> ERRORE DI ELABORAZIONE: {e}")
            
        validated_data.append(item)
        
    return validated_data

# --- Function to interact with the Gemini API ---
def query_gemini_structured(gene_list, custom_prompt):
    """
    Sends the gene list and the user's prompt (or the default one) to the 
    Gemini API, requesting a structured JSON output.
    
    Returns: data_array (list of dicts), full_prompt (str), raw_text (str)
    """
    if not API_KEY:
        st.error("Error: Gemini API Key not found. To run the app locally, please set the GEMINI_API_KEY environment variable.")
        return None, None, None # Return None for all three outputs

    # Initialize raw_text for error handling
    raw_text = ""

    try:
        client = genai.Client(api_key=API_KEY)
        
        # 1. Define the System Instruction (The fixed rules for the LLM)
        # This instruction enforces the bioinformatician persona and the JSON output format.
        system_instruction = f"""
        You are an expert bioinformatics assistant. Your mission is to analyze a list of gene symbols and respond to the user's request.
        **Your output MUST be EXCLUSIVELY a JSON object**, which can be parsed directly.
        The JSON must contain an array called 'data'. Each object in the 'data' array must represent a gene and the requested information.
        Do not include descriptive text, Markdown, or explanations outside the JSON block.
        If a gene is not found, its object in the array must indicate the status 'Not Found'.
        """

        # 2. Define the User Query (Genes + User's Custom Prompt)
        # We combine the gene list and the user's custom prompt into a single query.
        gene_list_str = ', '.join(gene_list)
        user_query = f"""
        **Gene List to Analyze:** {gene_list_str}
        
        **Detailed User Instruction:** {custom_prompt}
        
        Generate the output as JSON, adhering to system requirements.
        """
        
        # LOGICAL STEP 1: System Instruction (Backend Log)
        print("\n" + "="*50)
        print(f"PASSO LOGICO 1: Istruzione di Sistema Inviata a Gemini")
        print("="*50)
        print(system_instruction.strip())
        
        # LOGICAL STEP 2: Complete User Query (Backend Log)
        print("\n" + "="*50)
        print(f"LOGICAL STEP 2: Complete User Query Sent to Gemini")
        print("="*50)
        print(user_query.strip())
        print("="*50 + "\n")


        st.info("Sending structured request to Gemini. Please wait...")

        # API Call
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            )
        )
        
        # 3. Store the full, raw response text
        raw_text = response.text.strip()
        
        # LOGICAL STEP 3: Raw LLM Output Received (Backend Log)
        print("\n" + "="*50)
        print("LOGICAL STEP 3: Raw LLM Output Received (Parsing ...)")
        print("="*50)
        print(raw_text)
        print("="*50 + "\n")
        
        # 4. Parse the response to extract JSON
        
        # Use regex to find a JSON block (often enclosed in backticks)
        json_match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
        else:
            # Assume the entire response is the JSON string if no code block is found
            json_str = raw_text

        # 5. Convert the JSON string into a Python object
        data_object = json.loads(json_str)
        
        # Return the data array, the full prompt, and the raw text
        return data_object.get('data', []), user_query, raw_text 

    except Exception as e:
        # Include raw_text in the error message for debugging
        st.error(f"Error interacting with the Gemini API or parsing JSON: {e}")
        st.code(f"Raw Output Received:\n{raw_text}", language="json")
        return None, user_query, raw_text

# --- Streamlit UI Setup ---

st.set_page_config(page_title="Gene List Analyzer Chat", layout="centered")

# Header
st.title("Chat with your Gene List")
st.markdown("Use AI to quickly obtain **structured information** about a list of gene symbols.")

# --- Input Area for Gene List ---
st.header("1. Enter Genes")
gene_list_input = st.text_area(
    "Gene List (separated by comma, space, or new line)", 
    value="TP53, BRCA1, MYC", 
    height=150,
    placeholder="E.g.: TP53\nBRCA1\nEGFR\nPDCD1"
)

# --- Input Area for Prompt Customization (Hybrid Approach) ---
st.header("2. Define the Query (AI Instruction)")

# Define the default, fixed prompt
DEFAULT_PROMPT = """
For the provided genes, supply the following structured information:
1. Gene Symbol
2. Full Gene Name
3. Main Molecular Function (max 30 words)
4. Primary Associated Human Disease
"""

# Text area for user to modify the prompt, with clear guidelines
custom_prompt = st.text_area(
    "Modify the AI Assistant Instruction (Optional)", 
    value=DEFAULT_PROMPT,
    height=200,
)

popover = st.popover("💡 Tips for creating custom prompts")
with popover:
    st.markdown("### **Requesting Structured Data**") 
    st.markdown("To ensure the AI returns clean, tabular results, please follow these rules:")

    st.markdown("""
    - **PRECISE COLUMNS:** Be extremely specific and request information as **separate fields or columns**. 
      *Example: "Provide Symbol, Full Name, Chromosome, and Disease Association."*
    - **STANDARD TERMINOLOGY:** Use **common or standard names** for data fields (e.g., "HGNC ID", "Chromosome", "Full Name") to help the AI structure the output accurately.
    - **NO FREE-FORM TEXT:** **DO NOT** ask for sentences, paragraphs, summaries, or conversational text. The goal is to generate exclusively tabular data.
    - **CLARITY = QUALITY:** The clearer your request is about the column names, the better the quality of the downloadable table will be.
    """)

st.markdown("---")


# --- Analysis Button ---
if st.button("Analyze Genes with Gemini", type="primary"):
    
    # 1. Pre-process the gene list input
    # Normalize input: split by common delimiters and filter out empty strings
    genes = re.split(r'[,\s\n]+', gene_list_input)
    genes = [g.strip().upper() for g in genes if g.strip()]
    
    if not genes:
        st.error("Please enter a valid list of gene symbols before proceeding.")
        st.stop()
        
    st.session_state['genes'] = genes
    st.session_state['prompt'] = custom_prompt
    
    # 2. Call the API (expects 3 return values)
    # This call now logs the System Instruction, User Query, and Raw LLM Output to the backend
    data_array, full_prompt, raw_llm_text = query_gemini_structured(genes, custom_prompt)
    
    st.header("3. Analysis Results (Validated)")
    
    # PASSO LOGICO 5: Conversione e Visualizzazione (Frontend)
    if data_array is not None and full_prompt is not None:
        if data_array:
            # --- Validation Step ---
            # This function now logs the NCBI steps for each gene to the backend
            validated_data_array = validate_results_with_ncbi(data_array)
            
            # Convert validated data into a pandas DataFrame
            df = pd.DataFrame(validated_data_array)
            
            # --- Styling Logic ---
            def color_status(val):
                val_str = str(val)
                # Highlight LLM Not Found
                if 'Skipped (LLM Not Found)' in val_str:
                    return 'background-color: #fce7f3; color: #9d174d' # Pink for LLM errors
                # Highlight NCBI Errors
                if 'API Error' in val_str or 'Processing Error' in val_str or 'Gene Not Found in NCBI' in val_str:
                    return 'background-color: #fee2e2; color: #ef4444' # Red for NCBI errors
                return ''
            
            # Use df.style.map for cell-wise styling (preferred in recent pandas/streamlit versions)
            styled_df = df.style.map(color_status)

            # Use width='stretch' to make the dataframe responsive
            st.dataframe(styled_df, width='stretch')
            
            # Offer download option
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results (CSV)",
                data=csv,
                file_name='gene_analysis_gemini_validated.csv',
                mime='text/csv',
            )
            
        else:
            st.warning("The AI responded, but the data array ('data' key) is empty. Check the Sent Prompt.")
            
        # Expander to show the exact prompt sent to the LLM
        with st.expander("View Full Prompt Sent to Gemini"):
            st.code(full_prompt, language='markdown')