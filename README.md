🤖 Leave Request AI Evaluation System

An AI-powered leave request evaluation system that evaluates employee leave requests against a company’s Leave and Absence Policy.

The system combines FastAPI, LangGraph, RAG, Pinecone, Sentence Transformers, and GPT-4o to validate requests, retrieve relevant policy rules, analyze supporting documents, and generate a final policy-based decision.

Built as part of an AI Engineering Internship at Inspire for Solutions Development.

⸻-------------------------------------------------------------------------------------------------------------------

🚀 Key Highlights

*  Multi-step AI workflow using LangGraph
*  RAG pipeline for retrieving relevant policy rules
*  Pinecone vector database for semantic search
*  Sentence Transformers for generating embeddings
*  GPT-4o for document analysis and final evaluation
*  FastAPI REST API for serving the AI system
*  Pydantic validation for structured employee requests
*  Country-specific policy retrieval
*  Supporting-document verification and analysis
*  Explainable decisions with relevant policy evidence
*  Azure App Service + GitHub Actions deployment

⸻

🛠️ Tech Stack

Core technologies

* Python
* FastAPI
* Pydantic
* LangGraph
* LangChain Text Splitters
* Pinecone
* Sentence Transformers
* OpenAI GPT-4o
* PyPDF
* python-docx
* Uvicorn
* Gunicorn
* Azure App Service
* GitHub Actions

⸻

🧠 System Architecture

                         Employee
                            │
                            ▼
                       Frontend UI
                            │
                            ▼
                        FastAPI
                            │
                            ▼
                   Pydantic Validation
                            │
                            ▼
                    ┌───────────────┐
                    │   LangGraph  │
                    │    Workflow  │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       Request Validation          Policy Retrieval
                                      │
                                      ▼
                              Sentence Transformers
                                      │
                                      ▼
                                  Pinecone
                                      │
                                      ▼
                                Relevant Policy
                                      │
                                      ▼
                           Attachment Requirement
                                      │
                       ┌──────────────┴──────────────┐
                       │                             │
                      No                            Yes
                       │                             │
                       │                    Attachment Provided?
                       │                         /        \
                       │                       No          Yes
                       │                       │             │
                       │                       ▼             ▼
                       │                ATTACHMENT_     GPT-4o
                       │                 REQUIRED       Analysis
                       │                                     │
                       └──────────────────┬──────────────────┘
                                          ▼
                                  Final Evaluation
                                          │
                                          ▼
                              ┌──────────────────────┐
                              │ APPROVED             │
                              │ DENIED               │
                              │ REVIEW_REQUIRED      │
                              └──────────────────────┘

⸻

🔄 How It Works

1. Request Validation

The employee submits a leave request containing information such as:

* Employee information
* Country
* Leave type
* Start and end dates
* Reason
* Supporting attachment when required

The request is validated using Pydantic.

2. Policy Retrieval

The system retrieves the most relevant policy sections using a RAG pipeline.

The policy document is:

PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Embeddings
 ↓
Pinecone
 ↓
Semantic Retrieval

Country-specific metadata is used to improve retrieval accuracy and prevent unrelated policy sections from being returned.

3. Attachment Requirement

The workflow determines whether the selected leave type requires supporting documentation.

For example, a medical certificate may be required for certain sick-leave requests.

4. Attachment Analysis

If an attachment is required and provided, the document is analyzed using GPT-4o.

The analysis can be used alongside the retrieved policy evidence during the final evaluation.

5. Final Evaluation

The final evaluation combines:

Employee Request
       +
Retrieved Policy Evidence
       +
Attachment Analysis
       ↓
GPT-4o Evaluation
       ↓
Final Decision

Possible outcomes include:

APPROVED
DENIED
REVIEW_REQUIRED
ATTACHMENT_REQUIRED

The system also provides supporting policy evidence for the decision.

⸻

🌍 Supported Countries

The policy retrieval system supports:

* 🇪🇬 Egypt
* 🇸🇦 KSA
* 🇯🇴 Jordan
* 🇶🇦 Qatar
* 🇦🇪 UAE
* 🇱🇧 Lebanon

⸻

📂 Project Structure

leave-request-ai/
│
├── main.py
├── requirements.txt
│
├── graph/
│   ├── state.py
│   └── workflow.py
│
├── models/
│   ├── enums.py
│   └── leave_request.py
│
├── services/
│   ├── attachment_analyzer.py
│   ├── evaluator.py
│   └── policy_retriver.py
│
├── policy/
│   ├── leave_and_absence_policy.pdf
│   └── vector_store.py
│
├── ingestion/
│   └── ingest_policy.py
│
├── frontend/
│   └── ...
│
└── .github/
    └── workflows/

⸻

🔌 API

The backend is exposed through a FastAPI REST API.

After running the application locally, interactive API documentation is available at:

http://127.0.0.1:8000/docs

The API accepts structured leave requests and returns the AI evaluation result.

Example request structure

{
  "employee_id": "EMP001",
  "country": "Egypt",
  "leave_type": "Sick Leave",
  "start_date": "2026-09-01",
  "end_date": "2026-09-03",
  "reason": "Medical condition",
  "attachment": "medical_certificate.pdf"
}

Field names and accepted values should match the Pydantic models implemented in the project.

⸻

💻 Local Setup

1. Clone the repository

git clone https://github.com/Nada2oo4/leave-request-ai.git
cd leave-request-ai

2. Create a virtual environment

macOS / Linux

python -m venv .venv
source .venv/bin/activate

Windows

python -m venv .venv
.venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Create a .env file:

OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key

5. Run the FastAPI application

python -m uvicorn main:app --reload

API:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

6. Run the frontend

In another terminal:

python -m http.server 5500 --directory frontend

Then open:

http://127.0.0.1:5500

⸻

☁️ Deployment

The application is configured for deployment using:

GitHub
   │
   ▼
GitHub Actions
   │
   ▼
Azure App Service
   │
   ▼
FastAPI + LangGraph

The deployment workflow is triggered by pushes to the main branch.

The application uses Gunicorn with Uvicorn workers:

gunicorn --bind=0.0.0.0 --timeout 600 main:app -k uvicorn.workers.UvicornWorker

Environment variables such as API keys are configured through Azure App Service environment settings rather than stored in the repository.

⸻

🔐 Security

Sensitive credentials are stored as environment variables.

The following files and directories are excluded from Git:

.env
.venv/
__pycache__/
uploads/
*.log

API keys should never be committed to the repository.

⸻

📸 Screenshots / Demo

Screenshots and a short demo of the application can be added here.

System workflow

<img width="2900" height="2700" alt="LeaveAI_System_Flow_Dark" src="https://github.com/user-attachments/assets/05423483-96a7-4015-82eb-b053ccdc1452" />



Example Evaluation

<img width="1280" height="800" alt="Screenshot 2026-09-17 at 8 38 15 PM" src="https://github.com/user-attachments/assets/6700fcaf-4903-4803-8d9e-019826581fc8" />
<img width="1280" height="800" alt="Screenshot 2026-09-17 at 8 40 36 PM" src="https://github.com/user-attachments/assets/af167244-da41-4b39-bbdf-4f1d0ba1ce67" />
<img width="1280" height="800" alt="Screenshot 2026-09-17 at 8 22 23 PM" src="https://github.com/user-attachments/assets/3257ba6c-9c68-41eb-924d-3df03b26f511" />
<img width="1280" height="800" alt="Screenshot 2026-09-17 at 8 23 07 PM" src="https://github.com/user-attachments/assets/8dac2924-675b-4f9d-9551-e3ce474d5090" />
<img width="1280" height="800" alt="Screenshot 2026-09-17 at 8 23 18 PM" src="https://github.com/user-attachments/assets/6755f118-86f4-47b1-9dec-cf502e799f04" />


⸻

Future Improvements

Potential future improvements include:

* Persistent file storage using Azure Blob Storage
* Authentication and role-based access
* Database integration for employee and leave records
* Monitoring and observability

⸻

👩‍💻 Project Context

This project was developed during an AI Engineering Internship at Inspire for Solutions Development.

The project focuses on building an end-to-end AI application that combines:

LLMs + RAG + Vector Databases + Agentic Workflows + REST APIs + Cloud Deployment

It demonstrates the practical integration of modern AI engineering technologies into a real-world business workflow.
