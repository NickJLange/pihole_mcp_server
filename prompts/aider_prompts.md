Okay, let's break this down into a detailed blueprint, iterative steps, LLM prompts, and a TODO checklist.

## MCP Server Blueprint

**1. Project Setup & Foundation:**
    *   Initialize Python project structure (e.g., using `poetry` or `pipenv`).
    *   Set up basic FastAPI application (`main.py`).
    *   Implement configuration loading from `config.toml` (`config.py`).
    *   Implement robust logging setup (to console and optional file) based on config (`logging_config.py`).
    *   Define basic Pydantic models for request/response structures.

**2. API Endpoint & Authentication:**
    *   Create the `POST /query` endpoint in FastAPI.
    *   Implement API Key authentication using FastAPI's dependency injection (`auth.py`). Read authorized keys from config. Return `403` on failure.

**3. Pi-hole Client Module:**
    *   Create a dedicated module (`pihole_client.py`) to handle all interactions with the Pi-hole API.
    *   Implement a base function to make authenticated requests (`requests` library) using the Pi-hole API URL and Application Password from config.
    *   Implement functions for each required Pi-hole API endpoint specified in the scope (e.g., `get_blocking_status`, `set_blocking_status`, `get_groups`, etc.).
    *   Handle potential connection errors and Pi-hole API errors gracefully within this module, returning structured results or raising specific exceptions.

**4. RAG Implementation:**
    *   Create a RAG module (`rag.py`).
    *   Integrate `pymilvus` client. Implement functions to connect/disconnect from Milvus.
    *   Define the Milvus collection schema (vector field, metadata field for endpoint name/description).
    *   Implement function to get/initialize the Milvus collection.
    *   Choose and integrate a sentence transformer model for embedding (e.g., from `sentence-transformers` library).
    *   Implement an embedding function (`embed_text`).
    *   Create a utility script or function (`load_intents.py` or function within `rag.py`) to:
        *   Read intent descriptions from the specification (or a separate config file).
        *   Embed the descriptions.
        *   Load/update the embeddings and associated metadata (endpoint name) into the Milvus collection.
    *   Implement the core RAG search function (`find_matching_intent`) that takes a user query, embeds it, and performs a similarity search in Milvus, returning the best match (endpoint name) and confidence score.

**5. NER Implementation:**
    *   Create an NER module (`ner.py`).
    *   Choose an NER approach (e.g., spaCy for flexibility, or focused Regex for simpler cases initially).
    *   Implement specific extraction functions for each Pi-hole endpoint that requires parameters (e.g., `extract_blocking_params`, `extract_group_name`, `extract_add_group_params`, etc.).
    *   These functions should take the user query text and the identified target endpoint (from RAG) as input.
    *   Use the "Natural Language Name(s)" from the spec to guide extraction.
    *   Handle variations (e.g., "10 minutes", "5 sec", "1 hour") and convert to required formats (e.g., total seconds for duration).
    *   Handle optional parameters and default values.
    *   Return structured parameter data or raise specific exceptions if required parameters are missing.

**6. Core Logic Integration (`/query` Endpoint):**
    *   Wire together the components within the `/query` endpoint handler.
    *   Receive the user query.
    *   Call `rag.find_matching_intent`. Handle cases where no clear intent is found (return `400 Bad Request`).
    *   Check feature flags in `config.toml` based on the matched intent. If disabled, return `501 Not Implemented`.
    *   Based on the matched intent (endpoint):
        *   If parameters are needed, call the corresponding `ner.extract_...` function. Handle parameter extraction failures (return `422 Unprocessable`).
        *   Call the appropriate `pihole_client` function with extracted parameters (if any).
        *   Handle errors returned from the `pihole_client` (e.g., connection issues -> `502`, Pi-hole API errors -> `500`).
    *   Format the successful response from the `pihole_client` into the specified JSON structure.
    *   Format error responses according to the spec.

**7. Error Handling & Refinement:**
    *   Implement FastAPI exception handlers to catch custom exceptions raised by `rag`, `ner`, `pihole_client` and map them to the correct HTTP status codes and JSON error responses defined in the spec.
    *   Ensure all edge cases (invalid input, connection timeouts, API errors, missing config) are handled gracefully.
    *   Refine logging messages for clarity and debugging.

**8. Testing:**
    *   Implement unit tests for `config`, `logging`, `auth`, `pihole_client` (using mocking for actual API calls), `rag` (mocking Milvus/embedding), and `ner`.
    *   Implement integration tests for the `/query` endpoint, simulating various user queries and checking responses, including error conditions. Use `pytest` and `httpx` for testing FastAPI applications.

**9. Packaging & Documentation:**
    *   Create `requirements.txt` or manage dependencies via `pyproject.toml` (Poetry/Pipenv).
    *   Write a comprehensive `README.md` covering setup, configuration (`config.toml` details, environment variables for secrets), API usage, and how to run the server/tests.
    *   Create the `todo.md` checklist.

## Iterative Breakdown (Refined Steps)

**Iteration 1: Project Foundation**
*   **Step 1.1:** Initialize project (`poetry init` or `pipenv install`), add `fastapi`, `uvicorn`, `python-dotenv`, `toml`. Create basic `main.py` with a root (`/`) endpoint.
*   **Step 1.2:** Create `config.py`. Implement function to load settings from `config.toml` and environment variables (for secrets like passwords/keys). Define Pydantic models for config structure. Create initial `config.toml`.
*   **Step 1.3:** Create `logging_config.py`. Configure Python `logging` based on settings from `config.py` (level, file path). Integrate into `main.py` on startup. Log basic startup message.
*   **Step 1.4:** Define basic Pydantic models for `/query` request (`QueryRequest`) and standard success/error responses (`SuccessResponse`, `ErrorResponse`) in `models.py`.

**Iteration 2: API Endpoint & Auth**
*   **Step 2.1:** Create `auth.py`. Implement FastAPI dependency (`get_api_key`) that reads `X-API-Key` header, compares against `authorized_api_keys` from config, and raises `HTTPException` (403) if invalid/missing.
*   **Step 2.2:** Create the `POST /query` endpoint skeleton in `main.py`. Apply the `get_api_key` dependency. Accept `QueryRequest` body. Return a dummy success response for now. Test with valid/invalid keys.

**Iteration 3: Basic Pi-hole Interaction**
*   **Step 3.1:** Create `pihole_client.py`. Add `requests` dependency. Implement a private helper `_make_request` handling common logic (base URL, headers including auth token, basic error checking).
*   **Step 3.2:** Implement `get_blocking_status(config)` in `pihole_client.py`. Uses `_make_request` to call `GET /blocking`. Reads URL/token from the passed config object. Handles potential `requests.exceptions.RequestException` and basic Pi-hole JSON response errors.
*   **Step 3.3:** *Temporarily* modify the `/query` endpoint (or add a test endpoint) to call `get_blocking_status` and return its result. Test connectivity and authentication with Pi-hole.

**Iteration 4: RAG Setup & Intent Loading**
*   **Step 4.1:** Add `pymilvus`, `sentence-transformers` dependencies.
*   **Step 4.2:** Create `rag.py`. Implement `connect_milvus`, `get_collection` (creates if not exists with correct schema: `id`, `endpoint_name`, `description`, `embedding`).
*   **Step 4.3:** Implement `embed_text(text)` using a chosen sentence transformer model in `rag.py`.
*   **Step 4.4:** Create `load_intents.py` script. Define intent data (from spec). Use `rag.py` functions to connect, get collection, embed descriptions, and insert/upsert into Milvus. Make this runnable independently. Run it to populate Milvus.
*   **Step 4.5:** Implement `find_matching_intent(query_text, config, threshold)` in `rag.py`. Embeds query, searches Milvus, returns the `endpoint_name` of the best match above a confidence threshold (read from config?), else `None`.

**Iteration 5: Basic NER**
*   **Step 5.1:** Create `ner.py`. Add dependencies if needed (e.g., `spacy`, or just use `re`).
*   **Step 5.2:** Implement `extract_blocking_params(query_text)` in `ner.py`. Use regex to find enable/disable keywords and time expressions ("X minutes", "Y seconds"). Convert time to total seconds. Return a dictionary `{"action": bool, "duration": int | None}`. Raise `ValueError` if extraction fails but seems intended (e.g., "disable for").

**Iteration 6: Integrate RAG & Basic NER/Pi-hole Flow**
*   **Step 6.1:** Modify `/query` endpoint in `main.py`. Remove temporary Pi-hole call.
*   **Step 6.2:** Call `rag.find_matching_intent` with the user's query. If `None`, return `400 Bad Request` (using `ErrorResponse` model).
*   **Step 6.3:** Implement `set_blocking_status(config, action: bool, duration: int = None)` in `pihole_client.py` (calls `POST /blocking`).
*   **Step 6.4:** In `/query`, if matched intent is `POST /blocking`:
    *   Call `ner.extract_blocking_params`. If it raises `ValueError`, return `422 Unprocessable Entity`.
    *   Call `pihole_client.set_blocking_status` with extracted params.
    *   Handle potential exceptions from `pihole_client` (map to `500`/`502`).
    *   Format and return `SuccessResponse`.
*   **Step 6.5:** Add initial Pi-hole error handling in `/query`: Catch exceptions from `pihole_client` calls and return appropriate `500` or `502` `ErrorResponse`.
*   **Step 6.6:** Test the end-to-end flow for enabling/disabling blocking (e.g., "disable pihole for 10 minutes").

**Iteration 7: Expand Pi-hole Client & NER (Groups)**
*   **Step 7.1:** Implement Pi-hole client functions for `GET /api/groups`, `GET /api/groups/{name}`, `POST /api/groups/direct`, `PUT /api/groups/{name}`, `DELETE /api/groups/{name}`, `POST /api/groups/batchDelete` in `pihole_client.py`. Ensure proper parameter handling and error checking.
*   **Step 7.2:** Implement corresponding NER functions in `ner.py`: `extract_group_name`, `extract_add_group_params`, `extract_modify_group_params`, `extract_delete_groups_params`. Use regex or more advanced NER as needed. Handle required/optional params (name(s), comment, enabled status). Raise `ValueError` on failure.

**Iteration 8: Expand Pi-hole Client & NER (Stats)**
*   **Step 8.1:** Implement Pi-hole client functions for `GET /summary`, `GET /top_domains`, `GET /top_clients`, `GET /recent_blocked` in `pihole_client.py`. Handle query parameters like `count`, `blocked`.
*   **Step 8.2:** Implement corresponding NER functions in `ner.py`: `extract_stats_params` (handles optional `count`, `blocked_flag` based on context/keywords like "blocked", "active", "top 5").

**Iteration 9: Full Integration in `/query`**
*   **Step 9.1:** Refactor `/query` endpoint. Use a dictionary mapping `endpoint_name` (from RAG) to handler functions (or logic blocks).
*   **Step 9.2:** Implement logic for each supported intent: Check feature flags (return `501` if disabled), call appropriate NER function, call corresponding `pihole_client` function, format success/error response.
*   **Step 9.3:** Ensure consistent response formatting (`SuccessResponse`, `ErrorResponse`) across all flows.
*   **Step 9.4:** Thoroughly test all supported user phrasings from the spec via the API.

**Iteration 10: Error Handling & Testing**
*   **Step 10.1:** Implement FastAPI exception handlers (`@app.exception_handler(...)`) for custom exceptions raised by different modules (e.g., `PiholeConnectionError`, `NerParameterError`, `RagIntentNotFoundError`) and map them cleanly to the specified HTTP errors.
*   **Step 10.2:** Add comprehensive unit tests (`pytest`) for `config.py`, `auth.py`, `rag.py` (mocking Milvus/embeddings), `ner.py` (various query inputs), `pihole_client.py` (mocking `requests`).
*   **Step 10.3:** Add integration tests (`pytest` + `httpx`) for the `/query` endpoint. Test valid/invalid API keys, different queries covering all intents/params, expected success responses, and specific error conditions (400, 403, 422, 500, 501, 502).

**Iteration 11: Finalization**
*   **Step 11.1:** Generate `requirements.txt` (or ensure `pyproject.toml`/`Pipfile` is up-to-date).
*   **Step 11.2:** Write `README.md` with setup, config instructions (emphasize env vars for secrets), usage examples, and how to run/test.
*   **Step 11.3:** Create `todo.md` checklist.
*   **Step 11.4:** Code review, cleanup, remove any temporary code/endpoints. Ensure logging is informative.

## LLM Prompts (TDD Approach)

**Prompt 1: Project Setup & Config**

```text
We are starting a new Python project called "MCP Server" using FastAPI. The goal is to create an intermediary server for Pi-hole control via a chatbot.

**Task:**
1.  Initialize a Python project structure. Suggest using Poetry or standard pip/venv. Create necessary files: `main.py`, `config.py`, `logging_config.py`, `models.py`, `.env`, `config.toml`, `.gitignore`.
2.  In `config.py`, implement loading settings from `config.toml` and `.env` (for secrets). Use Pydantic for defining the configuration structure based on the spec's `config.toml` example. Prioritize environment variables over `config.toml` for secrets like `pihole.application_password` and `mcp_server.authorized_api_keys`.
3.  Create a sample `config.toml` and `.env` file (with placeholder values).
4.  In `logging_config.py`, set up Python's `logging` module. Configure it based on `[logging]` settings loaded via `config.py` (level, file path). Ensure logs go to stdout/stderr *and* the specified file (if any). Use a clear log format (timestamp, level, message).
5.  In `models.py`, define basic Pydantic models: `QueryRequest` (with a `query: str` field), `SuccessResponse` (based on spec), and `ErrorResponse` (with `message: str`, `status: str = "error"`).
6.  In `main.py`, create a basic FastAPI app instance. Load config and setup logging on startup. Add a simple root endpoint (`GET /`) that returns `{"message": "MCP Server Online"}`.
7.  Add basic dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `python-dotenv`, `toml`.
8.  Write a simple test (e.g., using `pytest` and `httpx`) to check if the root endpoint (`/`) is reachable and returns the expected message.

**Constraints:**
- Use type hints extensively.
- Follow FastAPI best practices.
- Ensure config loading is robust (handles missing file/values gracefully where appropriate, raises errors for critical missing settings).
- Log a message indicating successful startup and config loading.
```

**Prompt 2: API Endpoint & Authentication**

```text
Continuing with the MCP Server project. We have the basic FastAPI app, config loading, logging, and basic models set up from the previous step (`main.py`, `config.py`, `logging_config.py`, `models.py`).

**Task:**
1.  Create a new file `auth.py`.
2.  Inside `auth.py`, implement a FastAPI dependency function called `get_api_key`. This function should:
    *   Accept the `Request` object from `fastapi` as an argument.
    *   Read the `X-API-Key` header from the request.
    *   Load the list of `authorized_api_keys` from the application's configuration (which should be accessible, perhaps via a global config object loaded in `main.py` or passed via dependency injection).
    *   If the header is missing or the provided key is *not* in the authorized list, raise an `HTTPException` with status code `403 Forbidden` and a detail message like "Forbidden: Invalid or missing API Key.".
    *   If the key is valid, the dependency function can simply return `None` or the key itself (though returning nothing is common for auth checks).
3.  In `main.py`, import the `get_api_key` dependency and the `QueryRequest`, `SuccessResponse`, `ErrorResponse` models.
4.  Create the `POST /query` endpoint:
    *   It should depend on `get_api_key` (`Depends(get_api_key)`).
    *   It should accept a JSON body conforming to the `QueryRequest` model.
    *   For now, it should just return a dummy `SuccessResponse` like `{"message": "Query received", "status": "success", "pihole_status_code": None, "raw_response": None}` if authentication succeeds.
5.  Write tests using `pytest` and `httpx` for the `/query` endpoint:
    *   Test that a request without the `X-API-Key` header returns a `403` status code.
    *   Test that a request with an *invalid* `X-API-Key` header returns a `403` status code.
    *   Test that a request with a *valid* `X-API-Key` header (ensure one is defined in your test config/env) returns a `200` status code and the dummy success JSON body.

**Constraints:**
- Use the existing config loading mechanism.
- Ensure the dependency correctly integrates with FastAPI.
- Follow security best practices for handling API keys (comparison should be safe against timing attacks if possible, though simple list lookup is usually fine here).
```

**Prompt 3: Basic Pi-hole Client**

```text
Building on the MCP Server: We now have a FastAPI app with config, logging, models, and a `/query` endpoint protected by API key authentication (`main.py`, `config.py`, `logging_config.py`, `models.py`, `auth.py`).

**Task:**
1.  Create a new file `pihole_client.py`.
2.  Add `requests` to the project dependencies.
3.  Define custom exception classes in `pihole_client.py` (e.g., `PiholeApiError(Exception)`, `PiholeConnectionError(PiholeApiError)`).
4.  Implement a private helper function `_make_request(config, method, endpoint_path, params=None, json_data=None, timeout=10)` within `pihole_client.py`. This function should:
    *   Accept the loaded configuration object (`config`).
    *   Construct the full URL using `config.pihole.api_url` and `endpoint_path`.
    *   Add the `X-Pi-hole-App-Password` header using `config.pihole.application_password`.
    *   Use the `requests` library to make the HTTP call (`GET`, `POST`, `PUT`, `DELETE`).
    *   Include appropriate headers (`Content-Type: application/json` for POST/PUT).
    *   Handle potential `requests.exceptions.RequestException` (like connection errors, timeouts) and raise `PiholeConnectionError` with an informative message.
    *   Check the HTTP status code of the response. If it's an error code (e.g., >= 400), try to parse the response body for error details and raise `PiholeApiError` including the status code and Pi-hole's response.
    *   If successful, return the parsed JSON response (or raw text if JSON parsing fails but status is OK).
5.  Implement a public function `get_blocking_status(config)` in `pihole_client.py`. This function should:
    *   Call `_make_request` with `method='GET'`, `endpoint_path='/blocking'`.
    *   Return the result from `_make_request`.
6.  Write unit tests for `pihole_client.py` using `pytest` and the `unittest.mock` library (or `pytest-mock`):
    *   Test `get_blocking_status` successfully retrieves data (mock `requests.request` to return a successful response simulating Pi-hole's `/blocking` output).
    *   Test that `get_blocking_status` raises `PiholeConnectionError` if `requests.request` raises a connection error.
    *   Test that `get_blocking_status` raises `PiholeApiError` if the mocked response has an error status code (e.g., 401 Unauthorized if the password was wrong).
    *   Ensure the correct URL and headers (including `X-Pi-hole-App-Password`) are being sent in the mocked request.

**Constraints:**
- Pass the config object to client functions rather than relying on globals.
- Handle errors robustly within the client.
- Use mocking effectively for tests to avoid actual network calls.
```

**Prompt 4: RAG Setup & Intent Loading**

```text
Continuing the MCP Server project. We have the basic server, auth, and a foundational (but untested end-to-end) Pi-hole client (`pihole_client.py`).

**Task:**
1.  Add dependencies: `pymilvus`, `sentence-transformers`.
2.  Create `rag.py`.
3.  Define constants for the Milvus collection name (e.g., `MCP_INTENTS_COLLECTION`) and embedding dimension (depends on the chosen model, e.g., 384 for `all-MiniLM-L6-v2`).
4.  Implement Milvus connection logic:
    *   `connect_milvus(config)`: Connects using host/port details (add these to `config.toml` under a `[milvus]` section, e.g., `host="localhost"`, `port="19530"`). Handle connection errors.
    *   `get_collection(collection_name)`: Gets the collection instance. Includes logic to create it if it doesn't exist, defining the schema:
        *   `id`: Primary key, auto-incrementing INT64.
        *   `endpoint_name`: VARCHAR, max length (e.g., 100).
        *   `description`: VARCHAR, max length (e.g., 1024).
        *   `embedding`: FLOAT_VECTOR, dimension matching the model.
        *   Create an index (e.g., IVF_FLAT or HNSW) on the `embedding` field for efficient searching after creation. Remember to load the collection into memory (`collection.load()`) after creation or connection.
5.  Implement embedding logic in `rag.py`:
    *   `initialize_embedding_model(model_name="all-MiniLM-L6-v2")`: Loads and returns the sentence transformer model. Cache the model instance globally within the module for efficiency.
    *   `embed_text(text, model)`: Takes text and the loaded model, returns the embedding vector (list of floats).
6.  Create a separate script `load_intents.py`. This script should:
    *   Import necessary functions from `rag.py` and `config.py`.
    *   Load the application configuration.
    *   Define the intent data structure (using the "Endpoint" and "Intent Description for RAG Embedding" columns from the spec). Store this as a list of dictionaries.
    *   Connect to Milvus.
    *   Get the collection.
    *   Initialize the embedding model.
    *   Iterate through the intent data:
        *   Embed the `description`.
        *   Prepare the data entity (including `endpoint_name`, `description`, `embedding`).
        *   Insert the entity into the Milvus collection using `collection.insert()`. Handle potential duplicates if necessary (e.g., clear collection first or use upsert logic if available/needed, though simple insert is fine for initial load).
    *   Call `collection.flush()` after inserting.
    *   Print status messages during the process.
7.  Implement the search function in `rag.py`:
    *   `find_matching_intent(query_text, config, confidence_threshold=0.75)`:
        *   Connects to Milvus, gets collection, loads embedding model (reuse global instance).
        *   Embeds the `query_text`.
        *   Defines search parameters (metric type: L2 or IP, params for the index type).
        *   Performs the search using `collection.search()` with the query embedding, `output_fields=["endpoint_name"]`, `limit=1`.
        *   Extracts the top result's distance (score) and `endpoint_name`.
        *   Compares the score against the `confidence_threshold`. Note: Milvus distances might need interpretation (lower L2 is better, higher IP is better). Adjust comparison accordingly or normalize score if possible. If using IP, ensure embeddings are normalized. If using L2, a threshold might be like `< 1.0`. Let's assume for now lower score is better, so check `if score < confidence_threshold:`.
        *   Returns the `endpoint_name` if the match is confident enough, otherwise returns `None`. Handle potential errors during search.
8.  Write basic unit tests for `rag.py`:
    *   Mock `pymilvus` client and `sentence_transformers` model.
    *   Test `embed_text` returns a vector of the expected dimension.
    *   Test `find_matching_intent` calls embed, search, and correctly interprets mocked search results (both confident match and no confident match).
    *   Testing `load_intents.py` might be more involved (integration test or mocking Milvus interactions). Focus on unit testing `rag.py` functions first.

**Constraints:**
- Make Milvus host/port configurable.
- Handle potential errors during Milvus connection, collection handling, embedding, and searching.
- Ensure the script `load_intents.py` is runnable independently to populate the database.
```

**Prompt 5: Basic NER Implementation**

```text
Continuing the MCP Server project. We have the RAG components (`rag.py`, `load_intents.py`) defined and partially tested (unit tests with mocks).

**Task:**
1.  Create `ner.py`.
2.  Define a custom exception `NerParameterError(ValueError)` in `ner.py`.
3.  Implement the first NER function: `extract_blocking_params(query_text: str) -> dict`.
    *   Use Python's `re` module for this initial implementation.
    *   Identify keywords like "enable", "disable", "turn on", "turn off". Determine the `action` (boolean: `True` for enable, `False` for disable). If no clear action is found but duration is mentioned, maybe default to disable? Or raise error? Let's start by requiring an action keyword.
    *   Identify time duration patterns like "X minutes", "Y seconds", "Z hours", "N minute", "M second", "L hour". Handle plurals.
    *   Extract the numerical value (X, Y, Z) and the unit.
    *   Convert the extracted duration to *total seconds*.
    *   If time units are found but the numerical value is missing, or vice-versa, raise `NerParameterError("Incomplete duration specified.")`.
    *   If action keywords are missing, raise `NerParameterError("Could not determine action (enable/disable).")`.
    *   Return a dictionary: `{"action": bool, "duration": int | None}`. Duration is `None` if no time period was mentioned.
4.  Write unit tests for `extract_blocking_params` in `ner.py` using `pytest`:
    *   Test cases:
        *   "enable pihole" -> `{"action": True, "duration": None}`
        *   "disable pihole" -> `{"action": False, "duration": None}`
        *   "turn off pihole for 10 minutes" -> `{"action": False, "duration": 600}`
        *   "enable pihole for 30 seconds" -> `{"action": True, "duration": 30}`
        *   "disable for 1 hour" -> `{"action": False, "duration": 3600}`
        *   "disable for 5 min" -> `{"action": False, "duration": 300}` (handle abbreviations if easy)
        *   "enable blocking" -> `{"action": True, "duration": None}`
        *   Query with duration but no action ("for 10 minutes") -> Should raise `NerParameterError`.
        *   Query with action but incomplete duration ("disable for minutes") -> Should raise `NerParameterError`.
        *   Query with neither ("what is the status") -> Should raise `NerParameterError` (as this function is only for *setting* status).

**Constraints:**
- Start with regex, can be refined later if needed.
- Handle common time units (seconds, minutes, hours).
- Raise specific errors for failed/incomplete extraction.
- Return a structured dictionary.
```

**Prompt 6: Integrate RAG, NER, Pi-hole (Blocking Flow)**

```text
Building on the MCP Server: We have RAG (`rag.py`), basic NER for blocking (`ner.py`), Pi-hole client (`pihole_client.py`), auth (`auth.py`), and the main app (`main.py`).

**Task:**
1.  Ensure the Pi-hole client has the function `set_blocking_status(config, action: bool, duration: int | None)` implemented (it should call `POST /blocking` with parameters `action='enable'|'disable'` and optional `duration` in seconds). Update `_make_request` or `set_blocking_status` to handle sending JSON body correctly for POST requests. Add unit tests for `set_blocking_status` similar to how `get_blocking_status` was tested (mocking `requests`).
2.  Modify the `POST /query` endpoint handler in `main.py`:
    *   After successful authentication (`get_api_key`), get the `query` string from the `QueryRequest` body.
    *   Instantiate any necessary clients/models (consider how config/models are passed or accessed - maybe FastAPI dependencies?). Let's assume config is available. Initialize RAG model/Milvus connection as needed (maybe on app startup or via dependency).
    *   Call `rag.find_matching_intent(query, config)` to get the matched `endpoint_name`.
    *   If `endpoint_name` is `None`, return a `400 Bad Request` JSON response (`ErrorResponse` model: `{"message": "Error: Could not understand the request. Please rephrase.", "status": "error"}`).
    *   **If `endpoint_name == 'POST /blocking'`: **
        *   Try calling `ner.extract_blocking_params(query)`.
        *   If `ner.NerParameterError` is raised, catch it and return a `422 Unprocessable Entity` JSON response (`ErrorResponse` model: `{"message": f"Error: Missing required information for blocking. {e}", "status": "error"}`).
        *   If NER succeeds, extract `action` and `duration` from the result.
        *   Try calling `pihole_client.set_blocking_status(config, action=action, duration=duration)`.
        *   If `pihole_client.PiholeConnectionError` is raised, catch it and return a `502 Bad Gateway` JSON response (`ErrorResponse` model: `{"message": f"Error: Could not connect to the Pi-hole API backend. {e}", "status": "error"}`).
        *   If `pihole_client.PiholeApiError` is raised, catch it and return a `500 Internal Server Error` JSON response (`ErrorResponse` model, including details from the exception like Pi-hole status code and response if available: `{"message": f"Error: Failed to execute request on Pi-hole. {e}", "status": "error", "pihole_status_code": e.status_code, "raw_response": e.response_data}`).
        *   If the Pi-hole call succeeds, format a `SuccessResponse` based on the spec (e.g., `{"message": "Pi-hole blocking status updated successfully.", "status": "success", "pihole_status_code": 200, "raw_response": pihole_response}`). Use the actual response from `set_blocking_status` if it provides useful info.
    *   **Else (for other future intents):**
        *   For now, return a `501 Not Implemented` response: `{"message": f"Error: Feature for endpoint '{endpoint_name}' is not yet implemented.", "status": "error"}`.
3.  Refactor common error handling (e.g., Pi-hole connection/API errors) potentially using FastAPI exception handlers (`@app.exception_handler(...)`) later, but start with try/except blocks within the endpoint logic.
4.  Write integration tests for the `/query` endpoint using `pytest` and `httpx`:
    *   Mock `rag.find_matching_intent` to return `'POST /blocking'`.
    *   Mock `ner.extract_blocking_params` to return valid params (`{"action": False, "duration": 600}`).
    *   Mock `pihole_client.set_blocking_status` to return a successful response.
    *   --> Test that a query like "disable pihole for 10 minutes" results in a `200 OK` and the correct success JSON.
    *   Mock `ner.extract_blocking_params` to raise `NerParameterError`.
    *   --> Test that the query results in a `422` status code and corresponding error JSON.
    *   Mock `pihole_client.set_blocking_status` to raise `PiholeConnectionError`.
    *   --> Test that the query results in a `502` status code and corresponding error JSON.
    *   Mock `pihole_client.set_blocking_status` to raise `PiholeApiError`.
    *   --> Test that the query results in a `500` status code and corresponding error JSON.
    *   Mock `rag.find_matching_intent` to return `None`.
    *   --> Test that the query results in a `400` status code and corresponding error JSON.
    *   Mock `rag.find_matching_intent` to return a different endpoint (e.g., `'GET /blocking'`).
    *   --> Test that the query results in a `501` status code (for now).

**Constraints:**
- Ensure mocks are correctly applied for integration tests.
- Follow the error response formats specified.
- Structure the endpoint logic clearly.
```

**Prompt 7: Expand Pi-hole Client & NER (Groups)**

```text
Continuing the MCP Server project. We have the blocking flow integrated (`POST /blocking`). Now let's add support for Group Management functions.

**Task:**
1.  In `pihole_client.py`:
    *   Implement functions for:
        *   `get_groups(config)` -> `GET /api/groups`
        *   `get_group_by_name(config, group_name: str)` -> `GET /api/groups/{name}` (handle URL encoding for name)
        *   `add_groups(config, names: list[str], comment: str | None = None, enabled: bool = True)` -> `POST /api/groups/direct` (handle single name vs list of names in request body)
        *   `modify_group(config, target_group_name: str, new_name: str | None = None, comment: str | None = None, enabled: bool | None = None)` -> `PUT /api/groups/{name}` (handle URL encoding, only include fields in body if provided)
        *   `delete_group(config, group_name: str)` -> `DELETE /api/groups/{name}` (handle URL encoding)
        *   `delete_groups_batch(config, group_names: list[str])` -> `POST /api/groups/batchDelete`
    *   Ensure each function uses `_make_request`, handles parameters correctly (URL path params, query params, JSON body), and raises appropriate `PiholeApiError` / `PiholeConnectionError`.
    *   Add unit tests for each new function, mocking `requests.request` and verifying URLs, methods, headers, and bodies.
2.  In `ner.py`:
    *   Implement NER functions:
        *   `extract_group_name(query_text: str) -> str`: Extract a single group name (e.g., using regex for phrases like "group <name>", "named <name>"). Raise `NerParameterError` if not found.
        *   `extract_multiple_group_names(query_text: str) -> list[str]`: Extract a list of group names (e.g., from "groups <name1>, <name2>, and <name3>"). Handle conjunctions like "and". Raise `NerParameterError` if none found.
        *   `extract_add_group_params(query_text: str) -> dict`: Extract name(s) (using the functions above), optional comment (`with comment "<comment>"`), optional enabled status ("disabled", "enabled"). Return `{"names": list[str], "comment": str|None, "enabled": bool}`. Default enabled to `True`. Raise `NerParameterError` if name(s) are missing.
        *   `extract_modify_group_params(query_text: str) -> dict`: Extract target name (`extract_group_name`), optional new name (`rename to <new_name>`), optional comment (`set comment to "<comment>"`), optional enabled status (`set status to enabled/disabled`). Return `{"target_group_name": str, "new_name": str|None, "comment": str|None, "enabled": bool|None}`. Raise `NerParameterError` if target name is missing.
    *   Add unit tests for each new NER function with various phrasing examples.

**Constraints:**
- Handle potential ambiguity in NER carefully, favoring raising errors over making assumptions.
- Ensure Pi-hole client functions construct requests exactly as required by the Pi-hole API spec.
```

**Prompt 8: Expand Pi-hole Client & NER (Stats)**

```text
Continuing the MCP Server project. Group management functions (`pihole_client.py`, `ner.py`) are defined. Now add support for Statistics functions.

**Task:**
1.  In `pihole_client.py`:
    *   Implement functions for:
        *   `get_summary(config)` -> `GET /summary`
        *   `get_top_domains(config, count: int | None = None, blocked: bool | None = None)` -> `GET /top_domains` (pass `count` and `blocked` as query params if provided)
        *   `get_top_clients(config, count: int | None = None, blocked: bool | None = None)` -> `GET /top_clients` (pass `count` and `blocked` as query params if provided)
        *   `get_recent_blocked(config, count: int | None = None)` -> `GET /recent_blocked` (pass `count` as query param if provided)
    *   Ensure query parameters are correctly added using the `params` argument in `requests`.
    *   Add unit tests for each new function, mocking `requests.request` and verifying URLs and query parameters.
2.  In `ner.py`:
    *   Implement `extract_stats_params(query_text: str) -> dict`:
        *   Extract optional count (e.g., "top 5", "last 3", `<count> results`). Default if not found? (Pi-hole API might have defaults). Let's return `None` if not specified.
        *   Extract optional boolean flag based on keywords (e.g., "blocked domains" -> `blocked=True` for `top_domains`, "active clients" -> `blocked=False` for `top_clients`, "blocked clients" -> `blocked=True` for `top_clients`). This might depend on the *intent* determined by RAG. For now, try to extract keywords generally.
        *   Return `{"count": int|None, "blocked_flag": bool|None}`. Raise `NerParameterError` only if extraction is clearly attempted but fails (e.g., "top foo", where "foo" isn't a number).
    *   Add unit tests for `extract_stats_params` covering different phrasings for count and blocking filters.

**Constraints:**
- Pay attention to Pi-hole API default behaviors for query parameters.
- NER for stats might be simpler, focusing on numbers and keywords like "blocked".
```

**Prompt 9: Full Integration in `/query`**

```text
Building on the MCP Server: All required Pi-hole client functions and NER extractors are now defined and unit-tested. RAG identifies the intent. Let's fully integrate these into the `/query` endpoint.

**Task:**
1.  Refactor the `POST /query` endpoint handler in `main.py`.
2.  After identifying the `endpoint_name` using `rag.find_matching_intent`:
    *   Use a dictionary or if/elif/else structure to dispatch based on `endpoint_name`.
    *   **Feature Flags:** Before proceeding with NER/Pi-hole call for a given intent, check the corresponding feature flag in the `config.mcp_server.features` section (e.g., `config.mcp_server.features.group_management`). If the feature is set to `false`, return a `501 Not Implemented` JSON response (`ErrorResponse`: `{"message": "Error: This feature (<feature_name>) is currently disabled.", "status": "error"}`).
    *   **For each supported endpoint:**
        *   Call the appropriate `ner.extract_...` function(s) if parameters are needed for that endpoint. Handle `NerParameterError` by returning `422 Unprocessable Entity` with a specific message (e.g., "Error: Missing required group name.").
        *   Call the corresponding `pihole_client` function with the extracted parameters.
        *   Wrap the Pi-hole call in a try/except block to catch `PiholeConnectionError` (-> 502) and `PiholeApiError` (-> 500). Ensure the error response includes details from the exception.
        *   If successful, format the data returned by the Pi-hole client into the standard `SuccessResponse` structure. The `message` field should be a user-friendly summary (e.g., "Successfully retrieved 5 groups.", "Group 'MyGroup' deleted.", "Showing top 10 blocked domains."). The `raw_response` field should contain the actual data received from Pi-hole. Set `pihole_status_code` appropriately (usually 200 for GET/PUT, 201 for POST create, 204 for DELETE, etc., check Pi-hole docs or use the status from the client response).
3.  Ensure all code paths return a valid FastAPI response (either a `JSONResponse` with custom status/content or a Pydantic model).
4.  Update integration tests (`pytest` + `httpx`):
    *   Add tests for each supported intent (Groups, Stats).
    *   For each intent, mock RAG to return the correct `endpoint_name`.
    *   Mock NER to return expected parameters *or* raise `NerParameterError`.
    *   Mock the corresponding `pihole_client` function to return success data *or* raise `PiholeConnectionError`/`PiholeApiError`.
    *   Verify that the correct HTTP status code and JSON response body (success or error) are returned for each scenario.
    *   Add tests for the feature flag logic (mock config to disable a feature and ensure a `501` is returned when that intent is matched).

**Constraints:**
- Create user-friendly success messages.
- Handle all specified error conditions correctly.
- Map intents cleanly to NER/Pi-hole calls.
- Ensure tests cover the new logic and error paths.
```

**Prompt 10: Final Error Handling & Testing Refinement**

```text
Finalizing the MCP Server: Core functionality is integrated. Let's refine error handling and testing.

**Task:**
1.  Implement FastAPI exception handlers in `main.py` to centralize error response generation:
    *   Create handlers (`@app.exception_handler(...)`) for `PiholeConnectionError`, `PiholeApiError`, `NerParameterError`, and potentially a generic handler for unexpected `Exception`.
    *   Move the logic for creating the specific `JSONResponse` (with status code and `ErrorResponse` body) from the `/query` endpoint's `try/except` blocks into these handlers. This cleans up the main endpoint logic.
    *   Ensure the handlers still have access to exception details (e.g., status code and data from `PiholeApiError`) to populate the `ErrorResponse`.
    *   Also add a handler for `RagIntentNotFoundError` (you might need to define this exception in `rag.py` and raise it when `find_matching_intent` returns `None`) to return the `400 Bad Request` response.
2.  Review and enhance logging throughout the application. Ensure key steps (intent matched, NER params extracted, Pi-hole call initiated, success/error) are logged with relevant info, respecting the configured log level. Avoid logging sensitive data like API keys or passwords.
3.  Expand unit tests:
    *   Add more edge cases to `ner.py` tests (weird spacing, capitalization, complex sentences).
    *   Ensure `pihole_client.py` tests cover different Pi-hole API responses (e.g., empty lists, specific error messages).
    *   Add tests for the RAG threshold logic in `rag.py`.
4.  Expand integration tests:
    *   Test more varied user query phrasings for each intent.
    *   Test interactions between parameters (e.g., modifying a group name and status simultaneously).
    *   Test edge cases like deleting a non-existent group (how does the Pi-hole API respond? Ensure the client/server handles it).

**Constraints:**
- Exception handlers should simplify the main endpoint logic.
- Logging should be informative for debugging but safe for production.
- Tests should cover a wider range of inputs and potential failures.
```

**Prompt 11: Finalization & Documentation**

```text
Wrapping up the MCP Server project. All core logic, error handling, and testing are in place.

**Task:**
1.  Ensure all dependencies are correctly listed in `pyproject.toml` (if using Poetry) or generate/update `requirements.txt` (`pip freeze > requirements.txt`).
2.  Create a comprehensive `README.md` file including:
    *   Project overview and goal.
    *   Prerequisites (Python version, Milvus instance running).
    *   Setup instructions (cloning, installing dependencies using the chosen method).
    *   Configuration:
        *   Explain `config.toml` sections and parameters.
        *   Crucially, explain how to set secrets (`pihole.application_password`, `mcp_server.authorized_api_keys`) using environment variables (e.g., creating a `.env` file based on a provided `.env.example`). Provide the corresponding environment variable names (e.g., `PIHOLE_APP_PASSWORD`, `MCP_AUTHORIZED_KEYS`).
        *   How to run the `load_intents.py` script to populate Milvus.
    *   Running the server (using `uvicorn main:app --reload`).
    *   API Usage: Describe the `POST /query` endpoint, authentication (`X-API-Key` header), request body, and provide examples of success/error responses. List the supported natural language command types based on the implemented intents.
    *   Running tests (`pytest`).
3.  Create the `todo.md` checklist based on the steps we defined earlier.
4.  Perform final code cleanup: remove any commented-out code, print statements used for debugging, unused imports, or temporary test endpoints. Ensure code formatting is consistent (e.g., using `black` and `isort`).
5.  Add type hints where missing and ensure linters (`flake8`, `mypy`) pass.

**Constraints:**
- Documentation must be clear and accurate, especially regarding configuration and secrets management.
- The project should be clean and ready for use.
- `todo.md` should reflect the development process.
