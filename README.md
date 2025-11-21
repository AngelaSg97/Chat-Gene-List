Plaintext

# Gene List Analyzer (Chat with Gene List)

This is a bioinformatics assistant based on Streamlit that leverages the **Gemini 2.5 Flash** model to analyze lists of gene symbols and return structured information in a tabular format, ready for CSV export. It includes external validation against NCBI APIs to ensure gene symbol accuracy.

## Key Features

  * **Structured LLM Analysis:** Uses the `gemini-2.5-flash-preview-09-2025` model to extract specific data (e.g., full name, function, diseases) from gene lists, ensuring the output is exclusively in JSON format for easy processing.
  * **Hybrid Validation:** Converts the JSON response into a pandas DataFrame and adds an external validation step against NCBI E-utilities to confirm the existence and full name of each gene.
  * **Dynamic and Flexible Prompting:** Users can customize the AI query, deciding which data columns they want to extract (e.g., Ensembl ID, Chromosome, Function).
  * **Robustness and Stability:** Both Gemini and NCBI calls implement an **Exponential Backoff** logic to automatically handle rate limits and ensure application stability.
  * **Containerization for Reproducibility:** Uses Docker and Docker Compose for an isolated, consistent, and reproducible execution environment.

## Prerequisites

To run the application locally, you need the following:

  * **Docker Desktop** (includes Docker Engine and Docker Compose).
  * A Google **Gemini API Key**.

## API Configuration

The application requires authentication via the Gemini API key.

1.  Create a file named `.env` in the root directory of your project.
2.  Add your API key to the `.env` file in the following format:


GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
Note: The .env file is referenced in docker-compose.yml and ensures your API key is managed securely and separate from the source code.

Installation and Startup
Add your email address to the "NCBI_EMAIL" variable in the "gene_chat_app.py" file and follow these steps to start the application locally using Docker Compose.

Clone the Repository (or navigate to the project directory):
```bash
cd /path/to/your/project
```
Start the Application: The up --build command will build the Docker image (based on the Dockerfile), create the container, and start it. The process includes installing the dependencies listed in requirements.txt.


```bash
docker compose up --build
```
Access the Interface: Once the logs indicate that Streamlit is running, open your browser and navigate to:
```text
http://localhost:8501
```
Technical Detail: Streamlit's default port is 8501.

Usage Instructions
The Streamlit interface guides the user through three simple phases:

Enter Genes (Section 1): Paste a list of gene symbols. The system accepts genes separated by commas, spaces, or new lines.

Define the Query (Section 2): Modify the default instruction to specify exactly which tabular fields you want the AI to return (e.g., "Provide Ensembl ID and Disease Association").

Analyze: Click the Analyze Genes with Gemini button.

The results will be shown in an interactive table:

Rows with NCBI validation issues will be highlighted in red.

You can download the complete table in CSV format for further analysis.


