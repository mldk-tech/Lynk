# Lynk
Home assignment - Feature creator

lynk_yaml_generator/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app, endpoints
│   │   ├── models.py       # Pydantic models for Lynk features
│   │   ├── logic.py        # Core chat logic, state management, YAML generation
│   │   └── utils.py        # Helper functions
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── style.css
│   └── script.js
└── docker-compose.yml

**Running the Application:**
1.  Ensure Docker and Docker Compose are installed.
2.  Navigate to the root `Lynk/` directory in your terminal.
3.  Run `docker-compose up --build`.
4.  Open your browser to `http://localhost:8080` for the frontend.
5.  The backend will be accessible at `http://localhost:8000`.

**Key Considerations & Next Steps:**

1.  **Refine Pydantic Models & Logic:** The accuracy of YAML generation depends entirely on how well the Pydantic models match Lynk's actual schema and how the `logic.py` handles the fields (especially nested ones like `metric_spec`, `formula_spec`, etc., and optional fields). The provided `logic.py` is a starting point and will need careful testing and refinement.
2.  **User Input Parsing:** The current `logic.py` uses very simple keyword matching. For "I would like to create a formula feature with SQL ….", it might pick up "formula" but won't parse the SQL directly. A more advanced approach would involve:
    * Better intent recognition (e.g., to understand if the user is providing the feature type or a value for a field).
    * Basic entity extraction (e.g., trying to find "asset my\_asset" to pre-fill `asset_id`). This could use regex or simple NLP.
3.  **State Management:** The current `conversation_state` is global in `logic.py`. For multiple concurrent users, this needs to be session-based (e.g., using a dictionary keyed by a session ID passed from the client or managed via cookies/tokens).
4.  **Error Handling:** The `logic.py` has basic error handling. This should be made more robust to guide the user better if they provide invalid data.
5.  **"Scanning the documentation":** This task is interpreted as the developer *manually understanding* the documentation to create the Pydantic models and logic. If the goal was for the *agent itself* to dynamically parse the live documentation website to figure out fields, that would be a significantly more complex AI/NLP task (likely involving web scraping, HTML parsing, and information extraction with an LLM).
6.  **Optional Fields:** The logic for handling optional fields (allowing users to "skip") needs to be robust.
7.  **YAML Order:** While YAML is generally unordered, for readability, Lynk might expect a certain order (e.g., `name`, `type`, `asset_id` before specs). `yaml.dump(..., sort_keys=False)` helps, but you might need to construct the dictionary in the desired order before dumping. The `ordered_output` in `logic.py` is a step towards this.

This plan provides a solid foundation for building the Lynk feature YAML generator. The most iterative part will be refining `models.py` and `logic.py` based on the exact Lynk documentation details and testing the conversational flow.