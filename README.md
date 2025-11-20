 Gene List Analyzer (Chat with Gene List)

Questo è un assistente di bioinformatica basato su Streamlit che sfrutta il modello Gemini 2.5 Flash per analizzare liste di simboli genici e restituire informazioni strutturate in formato tabellare, pronte per l'esportazione in CSV. Include una validazione esterna tramite API NCBI per garantire l'accuratezza dei simboli genici.

Funzionalità Principali

Analisi LLM Strutturata: Utilizza il modello gemini-2.5-flash-preview-09-2025 per estrarre dati specifici (es. nome completo, funzione, malattie associate) dalle liste di geni, forzando l'output esclusivamente in formato JSON per una facile elaborazione.

Validazione Ibrida: Converte la risposta JSON in un pandas DataFrame e aggiunge un passaggio di validazione esterna contro le NCBI E-utilities per confermare l'esistenza e il nome completo di ciascun gene.

Prompting Dinamico e Flessibile: Gli utenti possono personalizzare la query all'IA, decidendo esattamente quali colonne di dati vogliono estrarre (es. Ensembl ID, Cromosoma, Funzione).

Robustezza e Stabilità: Sia le chiamate a Gemini che quelle a NCBI implementano una logica di Exponential Backoff per gestire automaticamente i limiti di frequenza (rate limit) e garantire la stabilità dell'applicazione.

Containerizzazione per la Riproducibilità: Utilizza Docker e Docker Compose per un ambiente di esecuzione isolato, consistente e riproducibile.

🛠️ Prerequisiti

Per eseguire l'applicazione in locale, sono necessari i seguenti strumenti:

Docker Desktop (include Docker Engine e Docker Compose).

Una Chiave API Google Gemini.

Configurazione API

L'applicazione richiede l'autenticazione tramite la chiave API di Gemini.

Crea un file chiamato .env nella directory principale del tuo progetto.

Aggiungi la tua chiave API al file .env nel seguente formato:

GEMINI_API_KEY="LA_TUA_CHIAVE_API_GEMINI"


Nota: Il file .env è referenziato in docker-compose.yml e garantisce che la tua chiave API sia gestita in modo sicuro e separato dal codice sorgente.

Installazione e Avvio

Segui questi passaggi per avviare l'applicazione in locale utilizzando Docker Compose.

Clona il Repository (o naviga alla directory del progetto):

cd /percorso/al/tuo/progetto


Avvia l'Applicazione:
Il comando up --build costruirà l'immagine Docker (basata sul Dockerfile), creerà il container e lo avvierà. Il processo include l'installazione delle dipendenze elencate in requirements.txt.

docker compose up --build


Accedi all'Interfaccia:
Una volta che i log indicano che Streamlit è in esecuzione, apri il tuo browser e naviga su:

http://localhost:8501


Dettaglio Tecnico: La porta predefinita di Streamlit è 8501.

Istruzioni per l'Uso

L'interfaccia Streamlit guida l'utente attraverso tre semplici fasi:

Inserisci i Geni (Sezione 1): Incolla una lista di simboli genici. Il sistema accetta geni separati da virgole, spazi o nuove linee.

Definisci la Query (Sezione 2): Modifica l'istruzione predefinita per specificare esattamente quali campi tabellari vuoi che l'IA restituisca (es. "Fornisci Ensembl ID e Associazione Malattie").

Analizza: Clicca sul pulsante 🚀 Analyze Genes with Gemini.

I risultati saranno mostrati in una tabella interattiva:

Le righe con problemi di validazione NCBI saranno evidenziate in rosso.

Puoi scaricare la tabella completa in formato CSV per ulteriori analisi.

Struttura del Progetto

.
├── .env                  # Variabili d'ambiente (per la chiave API)
├── README.md             # Questo file (Documentazione principale)
├── README_en.md          # Documentazione in inglese
├── requirements.txt      # Dipendenze Python
├── Dockerfile            # Istruzioni per l'immagine Docker
├── docker-compose.yml    # Definizione del servizio Docker
└── gene_chat_app.py      # L'applicazione Streamlit (logica LLM e NCBI)
