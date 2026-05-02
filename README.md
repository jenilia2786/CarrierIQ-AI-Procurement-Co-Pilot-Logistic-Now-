# CarrierIQ — AI-Powered Procurement Co-Pilot for Logistics

## 📖 About the Project - Problem it Solves
CarrierIQ is an intelligent, AI-driven platform designed to revolutionize the logistics procurement process. 

**The Problem:** Traditional logistics procurement relies heavily on spreadsheets, manual bid comparisons, and gut-feel decisions. This process is slow, prone to errors, and lacks the visibility needed to identify risks or overbilling.
**The Solution:** CarrierIQ replaces manual chaos with data-driven, explainable AI recommendations. It automates carrier selection, evaluates risks, and generates complex RFQ documents and Award Letters in seconds. The platform helps procurement teams make decisions up to 85% faster while achieving average cost reductions of 25%.

## 🚀 Features
*   **🧠 LangChain AI Agent:** Evaluates and scores carriers intelligently based on price, reliability, transit time, and risk factors, delivering actionable and ranked recommendations with full explainability.
*   **🛡️ Risk & Intelligence:** Performs live risk analysis, identifies fraud signals, flags performance warnings, and spots potential seasonal drops—all while automatically suggesting backup options.
*   **💬 Natural Language Chat:** Ask complex procurement questions in plain English (e.g., "Best carrier for Mumbai to Delhi under ₹20k") and get instant, context-aware answers derived from your historical data.
*   **📄 Smart Documents Generation:** With just a single click, the AI dynamically generates comprehensive RFQs and Award Letters including SLA clauses, payment terms, and penalties, ready to be exported as PDFs.
*   **🧬 Carrier DNA Profiles:** In-depth analytics showcasing carrier mood indices, fraud fingerprints, and lane-specific performance track records.
*   **🌱 Green Freight Tracking:** Estimates and tracks Scope 3 CO2 emissions, allowing teams to optimize supply chain sustainability.
*   **🧾 Invoice Reconciliation:** AI performs automated 3-way matching of invoices, intelligently spotting overbilling and hidden accessorials against contracted rates.

## 🛠️ Technologies, Frameworks, and Algorithms Used

### Core Technologies & Frameworks
*   **Python 3.11 (Backend Language):** Chosen for its robust ecosystem in data processing and AI, natively supporting modern asynchronous capabilities needed for high-speed API responses.
*   **FastAPI & Uvicorn (Backend Framework):** Selected for its extreme performance and built-in asynchronous support. FastAPI auto-generates Swagger API documentation which is invaluable for rapid development and testing, while Uvicorn acts as a lightning-fast ASGI server.
*   **HTML5, Vanilla JavaScript, Vanilla CSS (Frontend):** Used to keep the application lightweight, blazing fast, and free from external dependency bloat. A custom design system was created to ensure maximum flexibility and complete control over the UI/UX.
*   **MongoDB (Database):** A NoSQL document-based database ideal for storing highly variable and semi-structured data like carrier profiles, RFQs, and performance scorecards without being restricted by rigid SQL schemas.

### AI Frameworks & Algorithms
*   **LangChain (AI/LLM Framework):** Utilized to orchestrate the AI Agent. LangChain significantly simplifies the creation of our conversational agent, RAG pipelines, and the complex prompt chaining required to analyze, evaluate, and score carriers intelligently.
*   **Retrieval-Augmented Generation (RAG):** Implemented to ground the AI's responses in historical carrier data and factual documents, ensuring the natural language chat provides accurate, context-aware answers rather than hallucinated responses.
*   **Multi-Criteria Decision Analysis (MCDA) / Heuristic Scoring:** Used as the mathematical foundation alongside the AI to objectively evaluate and rank carriers across multiple weighted dimensions (Price, Reliability, Transit Time, Risk).
*   **Natural Language Processing (NLP):** Leveraged for parsing unstructured user chat queries (e.g., "Best carrier to Mumbai under ₹20k") and intelligently generating structured legal and business documents (Award Letters, RFQs).
*   **Decoupled API Architecture:** Separation of backend and frontend APIs with seamless CORS support, ensuring modularity, scalability, and ease of deployment.

## 📋 Prerequisites
*   **Python:** Version 3.11 or higher
*   **Git:** To clone the repository
*   **OS:** Windows, macOS, or Linux

## ⚡ How to Run
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/jenilia2786/CarrierIQ-AI-Procurement-Co-Pilot-Logistic-Now-.git
    cd CarrierIQ-AI-Procurement-Co-Pilot-Logistic-Now-
    ```

2.  **Start the Platform:**
    Run the multi-terminal launcher script which automatically sets up a python virtual environment, installs dependencies, and serves both the backend API and frontend UI.
    
    *On Windows:*
    ```cmd
    run_all.bat
    ```

## 🔗 Links to Test
Once the platform is running locally, you can access the application through the following links:
*   **Web App:** [http://localhost:3000](http://localhost:3000)
*   **Backend API Base URL:** [http://localhost:8000](http://localhost:8000)
*   **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
