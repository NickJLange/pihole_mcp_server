Okay, let's build this MCP Server for Pi-hole chatbot integration.

## Project Blueprint: MCP Pi-hole Chatbot Server

This blueprint outlines the major components and the flow for building the server.

1.  **Foundation & Configuration:**
    *   Set up the Python project structure (directories, virtual environment).
    *   Define dependencies (`requirements.txt`).
    *   Implement configuration loading from `config.toml` using the `toml` library. Define a Pydantic model for validation.
    *   Set up basic structured logging (to stdout/stderr initially, file logging later) using the `logging` module.

2.  **Basic Web Server & Security:**
    *   Initialize a FastAPI application.
    *   Implement a basic health check endpoint (`/health`).
    *   Create FastAPI middleware for API key authentication (`X-API-Key` header check against `config.toml`). Return `403 Forbidden` on failure.

3.  **Pi-hole API Client Module:**
    *   Create a dedicated Python class (`PiholeClient`) to encapsulate interactions with the Pi-hole API.
    *   Use the `requests` library.
    *   Implement authentication using the `application_password` from the configuration. Add it as a query parameter (`?auth=<password>`) for authenticated requests.
    *   Start by implementing methods for the *simplest* Pi-hole endpoints:
        *   `get_blocking_status()` (`GET /blocking`)
        *   `get_summary()` (`GET /summary`)
    *   Include basic error handling for connection issues and non-2xx responses from Pi-hole.

4.  **RAG Setup & Initial Intent Matching:**
    *   Integrate `pymilvus` and a sentence-transformer library (e.g., `sentence-transformers`).
    *   Create functions/classes for:
        *   Connecting to Milvus (using connection details potentially added to `config.toml` or environment variables).
        *   Loading the chosen sentence embedding model.
        *   A setup/utility script to:
            *   Create the Milvus collection if it doesn't exist (defining schema for ID and vector).
            *   Load the intent descriptions from the specification table.
            *   Embed these descriptions using the sentence transformer.
            *   Insert the embeddings and corresponding endpoint identifiers (e.g., `GET /blocking`) into Milvus.
    *   Implement the core `match_intent(query: str)` function:
        *   Embed the incoming user query.
        *   Perform a similarity search against the Milvus collection.
        *   Return the identifier of the top matching intent (or None/raise exception if below a threshold).

5.  **NER Parameter Extraction (Initial):**
    *   Choose an NER approach (start simple with regex, potentially move to spaCy later if needed).
    *   Implement an initial parameter extraction function specifically for `POST /blocking`:
        *   `extract_blocking_params(query: str)`: Should identify enable/disable action, duration, and time unit (seconds, minutes, hours), converting duration to seconds. Return a structured dictionary or dataclass. Handle cases where duration is not provided (permanent enable/disable).

6.  **Core `/query` Endpoint Logic:**
    *   Implement the `POST /query` endpoint in FastAPI.
    *   It should perform the following sequence:
        *   Validate the incoming request body (`{"query": "..."}`).
        *   Call `match_intent()` to determine the target Pi-hole operation.
        *   If no intent is matched clearly, return a `400 Bad Request`.
        *   Based on the matched intent:
            *   **If parameters are needed (e.g., `POST /blocking`):** Call the appropriate NER function (e.g., `extract_blocking_params`). If required parameters are missing, return `422 Unprocessable Entity`.
            *   **Call the corresponding `PiholeClient` method**, passing extracted parameters if necessary.
            *   Handle potential exceptions from the `PiholeClient` (connection errors, API errors) and return appropriate server errors (`502 Bad Gateway`, `500 Internal Server Error`).
            *   Format the successful response from `PiholeClient` into the specified JSON structure.
            *   Return the formatted response.

7.  **Expand Pi-hole Client & RAG/NER Coverage:**
    *   Iteratively add methods to `PiholeClient` for *all* specified Pi-hole endpoints (`GET /api/groups`, `POST /api/groups/direct`, etc.). Include tests for each method.
    *   Ensure the RAG setup script includes intent descriptions for *all* endpoints.
    *   Implement specific NER functions for *each* endpoint requiring parameter extraction (e.g., `extract_group_name`, `extract_top_domain_params`, etc.). Use regex or more advanced NER as needed. Test each extractor thoroughly.
    *   Update the `/query` endpoint logic to handle all new intents and call the corresponding NER functions and `PiholeClient` methods.

8.  **Refined Error Handling & Logging:**
    *   Implement all specific error responses outlined in the specification (403, 502, 400, 422, 500, 501 based on feature flags).
    *   Enhance logging:
        *   Implement file logging based on `config.toml`.
        *   Ensure logs capture: incoming requests, matched intents, extracted parameters, calls to Pi-hole, Pi-hole responses (or errors), and final responses sent to the client. Mask sensitive data like API keys/passwords in logs.

9.  **Testing:**
    *   Write unit tests for:
        *   Configuration loading.
        *   API key authentication middleware.
        *   Each `PiholeClient` method (mocking `requests`).
        *   RAG intent matching function (mocking Milvus client/search results).
        *   Each NER parameter extraction function.
    *   Write integration tests for:
        *   The `/query` endpoint, testing the full flow for various intents and scenarios (mocking `PiholeClient` and RAG/NER components initially, then potentially running against a test Pi-hole/Milvus instance).
        *   Error handling scenarios.

10. **Final Touches:**
    *   Add docstrings and type hints.
    *   Refactor code for clarity and efficiency.
    *   Create a `README.md` with setup and usage instructions.
    *   Consider containerization (Dockerfile).

## Iterative Breakdown into Smaller Steps

Let's break this down further into manageable, testable chunks.

**Phase 1: Core Setup & Basic Server**

*   **Step 1.1:** Project Structure & Dependencies: Create directories (`app`, `tests`), `__init__.py` files, `requirements.txt` (add `fastapi`, `uvicorn`, `python-dotenv`, `toml`, `pydantic`), setup virtual env.
*   **Step 1.2:** Configuration Loading: Create `config.toml.example`, `config.toml` (`.gitignore` this!). Create a Pydantic model for config validation. Write a function `load_config()` to load and validate `config.toml`. Write unit tests for `load_config()`.
*   **Step 1.3:** Basic Logging: Configure Python's `logging` module for basic INFO level logging to `stdout` based on config.
*   **Step 1.4:** Basic FastAPI App: Create `main.py`. Initialize FastAPI app. Add a simple `/health` endpoint returning `{"status": "ok"}`. Write a test for the `/health` endpoint using `TestClient`.
*   **Step 1.5:** API Key Authentication Middleware: Implement FastAPI middleware to check `X-API-Key` against `mcp_server.authorized_api_keys` in config. Return 403 if invalid/missing. Apply middleware to the app. Write tests for the middleware (valid key, invalid key, missing key).

**Phase 2: Basic Pi-hole Interaction**

*   **Step 2.1:** Simple Pi-hole Client Structure: Create `app/pihole_client.py`. Define `PiholeClient` class. Initialize with Pi-hole API URL and password from config. Add `requests` to `requirements.txt`.
*   **Step 2.2:** Implement `get_blocking_status`: Add a method to `PiholeClient` to call `GET /blocking` on Pi-hole (passing `auth` parameter). Handle basic `requests` exceptions (ConnectionError) and non-200 responses. Return the JSON response or raise a custom exception.
*   **Step 2.3:** Test `get_blocking_status`: Write unit tests for this method, mocking the `requests.get` call to simulate success, connection errors, and Pi-hole API errors (e.g., 401 Unauthorized).
*   **Step 2.4:** Implement `get_summary`: Add a method to `PiholeClient` to call `GET /summary`. Handle errors similarly.
*   **Step 2.5:** Test `get_summary`: Write unit tests for this method, mocking `requests.get`.

**Phase 3: Basic RAG & Endpoint Integration (Status Check Only)**

*   **Step 3.1:** RAG Dependencies & Setup Script: Add `pymilvus`, `sentence-transformers` to `requirements.txt`. Create `scripts/setup_rag.py`.
*   **Step 3.2:** Milvus Connection & Model Loading: In `app/rag_processor.py`, add functions `get_milvus_connection()` and `load_embedding_model()`. (For now, connection details can be hardcoded/simple for local testing, use config later).
*   **Step 3.3:** Embed Initial Intents: Update `scripts/setup_rag.py` to:
    *   Connect to Milvus, create a simple collection (e.g., `pihole_intents`) if needed.
    *   Define *only* the intent descriptions for `GET /blocking` and `POST /blocking`.
    *   Load the embedding model.
    *   Embed the descriptions.
    *   Insert into Milvus with identifiers "GET /blocking" and "POST /blocking". Add basic error handling.
*   **Step 3.4:** Implement `match_intent` Function: In `app/rag_processor.py`, create `match_intent(query: str)` function. It should: load model, embed query, connect to Milvus, search the collection, return the ID of the best match (or None). Add a similarity threshold check.
*   **Step 3.5:** Test `match_intent`: Write unit tests mocking the Milvus client's search results to test matching logic.
*   **Step 3.6:** Basic `/query` Endpoint: Create the `POST /query` endpoint in `main.py`. It takes `{"query": "..."}`. For now, just log the query and return a placeholder success. Add basic input validation (Pydantic model for request body). Test endpoint structure.
*   **Step 3.7:** Integrate RAG & Pi-hole Status: Modify `/query`:
    *   Call `match_intent(request.query)`.
    *   If intent is "GET /blocking":
        *   Instantiate `PiholeClient`.
        *   Call `pihole_client.get_blocking_status()`.
        *   Format the response as specified (success case).
        *   Handle potential `PiholeClient` exceptions and return 500/502 errors.
    *   If intent is not "GET /blocking" or match fails, return `400 Bad Request`.
*   **Step 3.8:** Test `/query` for Status Check: Write integration tests for `/query` sending queries expected to match "GET /blocking", mocking `PiholeClient` and `match_intent` initially, then potentially just mocking `PiholeClient`. Test the error paths (match fail, Pi-hole client error).

**Phase 4: NER & Pi-hole Blocking Control**

*   **Step 4.1:** Simple NER for Blocking: In `app/ner_processor.py`, create `extract_blocking_params(query: str)` using primarily **regex** to find keywords ("enable", "disable"), numbers, and time units ("seconds", "minutes", "hours"). Return a dict `{"action": "enable"|"disable", "duration_seconds": int | None}`. Handle cases with no duration.
*   **Step 4.2:** Test `extract_blocking_params`: Write unit tests with various phrasings ("disable for 10 minutes", "enable pihole", "turn off blocking 30 sec", "disable indefinitely").
*   **Step 4.3:** Implement `enable_disable_blocking` in Client: Add method to `PiholeClient` for `POST /blocking`. It takes `action: str` ("enable" or "disable") and optional `duration_seconds: int`. Construct the correct query parameters (`enable`, `disable=<seconds>`, or just `disable`). Handle Pi-hole responses (e.g., `{"status": "enabled"}`).
*   **Step 4.4:** Test `enable_disable_blocking`: Write unit tests mocking `requests.post`.
*   **Step 4.5:** Integrate NER & Blocking into `/query`: Update `/query` endpoint:
    *   If `match_intent` returns "POST /blocking":
        *   Call `extract_blocking_params(request.query)`.
        *   If extraction fails to determine action, return `422 Unprocessable Entity`.
        *   Instantiate `PiholeClient`.
        *   Call `pihole_client.enable_disable_blocking()` with extracted params.
        *   Format success/error responses.
*   **Step 4.6:** Test `/query` for Blocking Control: Write integration tests sending queries like "disable pihole for 5 minutes", mocking the `PiholeClient` call. Test missing parameter cases (handled by NER/endpoint logic).

**Phase 5: Expand Coverage Incrementally**

*   **Step 5.1: Group Listing (`GET /api/groups`)**
    *   **RAG:** Add intent description to `scripts/setup_rag.py`. Re-run script.
    *   **Client:** Add `list_groups()` method to `PiholeClient`. Test it (mocking `requests`).
    *   **Endpoint:** Update `/query` to handle "GET /api/groups" intent. Test end-to-end (mocking client).
*   **Step 5.2: Group Detail (`GET /api/groups/{name}`)**
    *   **RAG:** Add intent description to `scripts/setup_rag.py`. Re-run script.
    *   **NER:** Add `extract_group_name(query: str)` to `ner_processor.py` (simple regex for text in quotes or after "group"). Test NER.
    *   **Client:** Add `get_group_details(name: str)` method to `PiholeClient` (URL needs formatting). Test it.
    *   **Endpoint:** Update `/query`: Handle intent, call NER, check for extracted name (return 422 if missing), call client. Test end-to-end.
*   **Step 5.3: Add Group (`POST /api/groups/direct`)**
    *   **RAG:** Add intent. Re-run setup.
    *   **NER:** Add `extract_add_group_params(query: str)` (extract name(s), optional comment, enabled status). Test NER. Handle single vs multiple names.
    *   **Client:** Add `add_groups(groups_data: list or dict)` method. Test it.
    *   **Endpoint:** Update `/query`. Handle intent, call NER, validate params, call client. Test end-to-end.
*   **Step 5.4 - 5.X: Repeat for Remaining Endpoints**
    *   Follow the pattern: Update RAG -> Implement/Test NER -> Implement/Test Client Method -> Update/Test Endpoint Logic.
    *   Endpoints: `PUT /api/groups/{name}`, `DELETE /api/groups/{name}`, `POST /api/groups/batchDelete`, `GET /summary` (client already done, just add RAG/Endpoint), `GET /top_domains`, `GET /top_clients`, `GET /recent_blocked`. Pay attention to parameter types (lists, booleans, optional integers).

**Phase 6: Finalization & Refinement**

*   **Step 6.1:** Implement Full Error Handling: Review the `/query` endpoint and `PiholeClient`. Ensure all specified HTTP error codes (400, 403, 422, 500, 502, 501) are returned correctly based on the scenarios (RAG fail, NER fail, bad key, Pi-hole down, Pi-hole error, feature disabled via config). Add tests for each error case.
*   **Step 6.2:** Feature Flags: Implement checks in `/query` based on `mcp_server.features` in config. Return `501 Not Implemented` if a requested feature category is disabled. Test this.
*   **Step 6.3:** Enhance Logging: Configure file logging handler if `log_file` is set in config. Ensure sensitive data (Pi-hole password, API keys) is masked or not logged. Add more detailed logging messages throughout the request lifecycle. Test logging output.
*   **Step 6.4:** Refactor & Docstrings: Review all code. Add type hints and docstrings. Refactor for clarity and potentially consolidate helper functions.
*   **Step 6.5:** README & Final Tests: Create `README.md`. Run all tests. Perform manual testing if possible. Consider adding basic Dockerfile.

This iterative approach ensures that you always have a working (though incomplete) server, allowing for testing and validation at each stage. Complexity is added gradually.

## LLM Prompts for Code Generation (TDD Approach)

Here are the prompts, designed to be used sequentially. Each prompt asks for code *and* tests.

**(Start New Session/Clear Context Before First Prompt)**

---

```text
Prompt 1: Project Setup & Config Loading

Goal: Set up the basic Python project structure and implement reliable configuration loading from a `config.toml` file using Pydantic for validation.

Requirements:
1.  Create the following directory structure:
    ```
    mcp-pihole-server/
    ├── app/
    │   ├── __init__.py
    │   └── config.py
    ├── tests/
    │   ├── __init__.py
    │   └── test_config.py
    ├── .env.example
    ├── .gitignore
    ├── config.toml.example
    ├── config.toml
    └── requirements.txt
    ```
2.  Populate `requirements.txt` with `python-dotenv`, `toml`, and `pydantic`.
3.  Create `config.toml.example` based on Section 10 of the specification. Include placeholders.
4.  Create `.env.example` suggesting environment variables for sensitive data like `PIHOLE_PASSWORD` and `MCP_API_KEYS` (comma-separated string).
5.  Add `config.toml`, `.env`, `__pycache__/`, `*.pyc`, `.venv/` to `.gitignore`.
6.  In `app/config.py`:
    *   Define Pydantic models mirroring the structure in `config.toml` (e.g., `PiholeConfig`, `MCPServerFeaturesConfig`, `MCPServerConfig`, `LoggingConfig`, `RootConfig`). Use appropriate types (e.g., `HttpUrl` for `api_url`, `SecretStr` for passwords/keys where appropriate, `List[SecretStr]` for API keys, `Literal` for log levels).
    *   Implement a function `load_config(config_path: str = "config.toml") -> RootConfig`:
        *   It should load `.env` using `dotenv`.
        *   Read the `config.toml` file.
        *   Override config values with environment variables if they are set (e.g., `pihole.application_password` from `PIHOLE_PASSWORD`, `mcp_server.authorized_api_keys` from `MCP_API_KEYS`). Handle the comma-separated string for API keys.
        *   Validate the loaded configuration using the Pydantic `RootConfig` model.
        *   Return the validated config object.
        *   Raise informative errors if the file is not found or validation fails.
7.  In `tests/test_config.py`:
    *   Write unit tests for `load_config()` using `pytest`.
    *   Test cases:
        *   Successful loading with a valid `config.toml`.
        *   Validation error for missing required fields.
        *   Validation error for incorrect data types.
        *   Successful override of password and API keys from environment variables (use `unittest.mock.patch.dict` for environment variables).
        *   Handling of comma-separated API keys from env var.
        *   File not found error.

Provide the contents of `app/config.py`, `tests/test_config.py`, `config.toml.example`, `.env.example`, `.gitignore`, and `requirements.txt`. Assume `config.toml` is a copy of the example for testing purposes.
```

---

```text
Prompt 2: Basic Logging Setup

Goal: Set up basic Python logging configured via the loaded configuration object.

Requirements:
1.  Assume the `app/config.py` and `load_config` function from the previous step exist.
2.  Create a new file `app/logging_config.py`.
3.  Implement a function `setup_logging(config: RootConfig)`:
    *   It should configure the root logger.
    *   Set the logging level based on `config.logging.level`.
    *   Use a standard logging format including timestamp, level name, and message (e.g., `%(asctime)s - %(levelname)s - %(message)s`).
    *   Configure logging to output **only** to `stdout`/`stderr` for now. (File logging will be added later).
    *   Ensure the configuration is applied globally.
4.  Create a placeholder test file `tests/test_logging_config.py` with a simple test that calls `setup_logging` with a mock config and checks if a basic log message can be emitted (e.g., using `caplog` fixture in pytest if available, or just ensuring no exceptions). Add `pytest` to `requirements.txt`.

Provide the contents of `app/logging_config.py` and `tests/test_logging_config.py`. Update `requirements.txt` if necessary.
```

---

```text
Prompt 3: Basic FastAPI App & Health Check

Goal: Create a minimal FastAPI application with a health check endpoint.

Requirements:
1.  Assume `app/config.py`, `app/logging_config.py`, and the `load_config`, `setup_logging` functions exist.
2.  Add `fastapi` and `uvicorn[standard]` to `requirements.txt`.
3.  Create `app/main.py`:
    *   Import necessary modules (`FastAPI`, `config`, `logging_config`, `logging`).
    *   Load the configuration using `load_config()`.
    *   Setup logging using `setup_logging(config)`.
    *   Get a logger instance (`logging.getLogger(__name__)`).
    *   Create a FastAPI app instance.
    *   Define a GET endpoint `/health` that returns a JSON response `{"status": "ok"}` with a 200 status code.
    *   Add a startup log message (e.g., "MCP Server starting...").
4.  Create `tests/test_main.py`:
    *   Import `TestClient` from `fastapi.testing`.
    *   Import the `app` instance from `app.main`.
    *   Write a test function `test_health_check`:
        *   Create a `TestClient` instance.
        *   Make a GET request to `/health`.
        *   Assert the status code is 200.
        *   Assert the JSON response is `{"status": "ok"}`.

Provide the contents of `app/main.py` and `tests/test_main.py`. Update `requirements.txt`.
```

---

```text
Prompt 4: API Key Authentication Middleware

Goal: Implement FastAPI middleware to protect endpoints by requiring a valid API key in the `X-API-Key` header.

Requirements:
1.  Assume the FastAPI app setup in `app/main.py` and the config loading (`app/config.py`) exist. The config object `config` is available in `app/main.py` and contains `config.mcp_server.authorized_api_keys` (a list of `SecretStr`).
2.  In `app/main.py` (or a new `app/security.py` if preferred, then import into `main.py`):
    *   Define an asynchronous middleware function (e.g., `verify_api_key`).
    *   This middleware should apply to all routes *except* `/health` (and potentially `/docs`, `/openapi.json` if you want to allow access). You can check `request.url.path`.
    *   It should extract the value from the `X-API-Key` HTTP header.
    *   If the header is missing or the provided key is *not* present in the `config.mcp_server.authorized_api_keys` list (remember to compare the *plain text* value using `.get_secret_value()` on the `SecretStr` objects), it must return an **immediate** `JSONResponse` with:
        *   `status_code=403` (Forbidden)
        *   `content={"detail": "Forbidden: Invalid or missing API Key."}`
    *   If the key is valid, it should call `await call_next(request)` to pass the request to the next handler/route.
    *   Add this middleware to the FastAPI app instance *before* defining routes that need protection (e.g., using `@app.middleware("http")`).
3.  In `tests/test_main.py`:
    *   Add new tests for the API key middleware. Assume there's a dummy protected endpoint `/protected` for testing purposes (you can add one temporarily if needed, or test against the upcoming `/query` endpoint later).
    *   Test case 1: Accessing `/protected` without the `X-API-Key` header -> assert status 403, assert response content.
    *   Test case 2: Accessing `/protected` with an *invalid* `X-API-Key` header -> assert status 403, assert response content.
    *   Test case 3: Accessing `/protected` with a *valid* `X-API-Key` header -> assert status is *not* 403 (e.g., 404 if the route doesn't exist yet, or 200 if you add a dummy route).
    *   Test case 4: Accessing `/health` without an API key -> assert status 200.
    *   Make sure to configure mock API keys for testing. You might need to mock the `load_config` function or provide a test-specific config.

Provide the updated `app/main.py` (or new `app/security.py` and updated `app/main.py`) and the updated `tests/test_main.py`.
```

---

```text
Prompt 5: Simple Pi-hole Client (Status & Summary)

Goal: Create a client class to interact with the Pi-hole API, starting with methods for getting blocking status and summary statistics.

Requirements:
1.  Assume `app/config.py` and the `load_config` function exist.
2.  Add `requests` to `requirements.txt`.
3.  Create `app/pihole_client.py`:
    *   Import `requests`, `logging`, relevant types, and the config models. Use `SecretStr`.
    *   Define custom exception classes: `PiholeClientError(Exception)` and `PiholeAPIError(PiholeClientError)`.
    *   Define the `PiholeClient` class:
        *   `__init__(self, api_url: str, password: SecretStr, timeout: int = 10)`: Store API URL, password, and request timeout. Get a logger instance.
        *   `_make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None, needs_auth: bool = True) -> dict`:
            *   Internal helper method for making requests.
            *   Construct the full URL.
            *   Prepare query parameters. If `needs_auth` is True, add `auth=self.password.get_secret_value()` to the params.
            *   Use `requests.request` with the specified method, URL, params, data, and timeout.
            *   Handle `requests.exceptions.RequestException` (like ConnectionError, Timeout) -> Log the error and raise `PiholeClientError`.
            *   Check if the response status code is >= 400. If so, log the error (status code, response text) and raise `PiholeAPIError`, potentially including the status code and response text/JSON in the exception.
            *   If successful (status < 400):
                *   Try to parse the response as JSON. If parsing fails (e.g., empty response for disable), handle gracefully (maybe return None or an empty dict depending on context, log a warning). If JSON is expected but fails, maybe raise an error.
                *   Return the parsed JSON dictionary or relevant data.
        *   `get_blocking_status(self) -> dict`:
            *   Call `_make_request` with `method='GET'`, `endpoint='/blocking'`, `needs_auth=True`.
            *   Return the result.
        *   `get_summary(self) -> dict`:
            *   Call `_make_request` with `method='GET'`, `endpoint='/summary'`, `needs_auth=True`.
            *   Return the result.
4.  Create `tests/test_pihole_client.py`:
    *   Import `pytest`, `requests`, `PiholeClient`, `PiholeClientError`, `PiholeAPIError`, `SecretStr`. Use `unittest.mock` (`patch`, `MagicMock`).
    *   Create test fixtures or setup methods to instantiate `PiholeClient` with dummy data.
    *   Test `get_blocking_status`:
        *   Mock `requests.request` to return a successful response (status 200, valid JSON like `{"status": "enabled"}`). Assert the correct dictionary is returned. Verify `requests.request` was called with correct args (URL, method, params including `auth`).
        *   Mock `requests.request` to raise `requests.exceptions.ConnectionError`. Assert `PiholeClientError` is raised.
        *   Mock `requests.request` to return an error status (e.g., 401 Unauthorized). Assert `PiholeAPIError` is raised.
    *   Test `get_summary`:
        *   Similar tests as above, mocking a success response (status 200, JSON like `{"domains_being_blocked": 1000}`), connection error, and API error.

Provide the contents of `app/pihole_client.py` and `tests/test_pihole_client.py`. Update `requirements.txt`.
```

---

```text
Prompt 6: RAG Setup (Milvus Connection, Model Loading, Initial Embedding Script)

Goal: Set up the connection to Milvus, load a sentence embedding model, and create a script to embed the initial intent descriptions for blocking status and control.

Requirements:
1.  Add `pymilvus` and `sentence-transformers` to `requirements.txt`.
2.  Update `config.toml.example` and `app/config.py` to include a `[milvus]` section with `host`, `port`, and `collection_name` (e.g., "pihole_intents"). Make these optional or provide defaults suitable for local Docker setup (e.g., host="localhost", port="19530"). Add a `[models]` section with `embedding_model_name` (e.g., "all-MiniLM-L6-v2"). Update `load_config` and Pydantic models.
3.  Create `app/rag_processor.py`:
    *   Import `pymilvus`, `sentence_transformers`, `logging`, config models.
    *   Define `MilvusConnectionError(Exception)`.
    *   Define a function `get_milvus_connection(host: str, port: str)`: Connects to Milvus using the provided host/port. Handle connection errors and raise `MilvusConnectionError`. Return the connection alias/handle. Log success/failure.
    *   Define a function `load_embedding_model(model_name: str)`: Loads and returns a `SentenceTransformer` model. Handle potential loading errors. Log model loading.
    *   Define constants for vector dimension (depends on the model, e.g., 384 for all-MiniLM-L6-v2) and the Milvus index parameters (e.g., `metric_type="L2"`, `index_type="IVF_FLAT"`, `params={"nlist": 128}`).
4.  Create `scripts/setup_rag.py`:
    *   Import necessary modules from `app.config`, `app.rag_processor`, `app.pihole_client` (maybe not needed yet), `logging`, `pymilvus`.
    *   Load configuration. Setup logging.
    *   Define the initial intent data as a list of dictionaries:
      ```python
      intents = [
          {"id": "GET /blocking", "description": "Check if Pi-hole blocking is currently enabled or disabled..."}, # Use full description from spec
          {"id": "POST /blocking", "description": "Use this endpoint to enable or disable Pi-hole blocking..."}, # Use full description from spec
      ]
      ```
    *   Load the embedding model using `load_embedding_model`.
    *   Connect to Milvus using `get_milvus_connection`.
    *   Check if the collection specified in the config exists.
    *   If it exists, log a message and optionally offer to drop/recreate or exit. (For simplicity now, maybe just log and continue, assuming upsert or overwrite later).
    *   If it doesn't exist:
        *   Define the schema: `id` (VARCHAR, primary_key, max_length=100), `embedding` (FLOAT_VECTOR, dim=...).
        *   Create the collection using `pymilvus.Collection`. Log creation.
        *   Create an index on the `embedding` field using the defined index parameters. Log index creation.
        *   Load the collection after index creation.
    *   Extract descriptions and IDs from the `intents` list.
    *   Embed the descriptions using the loaded model (`model.encode(...)`).
    *   Prepare data for insertion: `[ [intent_ids], [embeddings] ]`.
    *   Insert the data into the Milvus collection using `collection.insert()`. Log the number of inserted entities. Handle potential insertion errors.
    *   Flush the collection `collection.flush()`.
    *   (Optional but recommended) Load the collection into memory if not already loaded `collection.load()`.
    *   Add `if __name__ == "__main__":` block to run the setup.
5.  Create placeholder test file `tests/test_rag_processor.py` (actual testing of Milvus connection/embedding might be complex for unit tests, focus on testing the `match_intent` logic in the next step).

Provide contents of updated `app/config.py`, `config.toml.example`, `app/rag_processor.py`, `scripts/setup_rag.py`. Update `requirements.txt`.
```

---

```text
Prompt 7: RAG Intent Matching Logic & Basic /query Endpoint Integration

Goal: Implement the function to match user queries against the embedded intents in Milvus and integrate this into a basic `/query` endpoint that only handles the Pi-hole status check for now.

Requirements:
1.  Assume `app/config.py`, `app/rag_processor.py` (with connection/model loading), `app/pihole_client.py`, `app/main.py` (with FastAPI app, auth middleware) exist. The Milvus collection is populated by `scripts/setup_rag.py`.
2.  In `app/rag_processor.py`:
    *   Add a function `match_intent(query: str, model, collection, top_k: int = 1, threshold: float = 0.75) -> str | None`:
        *   Takes the user query, loaded embedding model, loaded Milvus collection object, number of results to fetch (`top_k`), and a similarity threshold.
        *   Embed the user query using `model.encode([query])[0]`.
        *   Define search parameters (e.g., `{"metric_type": "L2", "params": {"nprobe": 10}}`).
        *   Perform the search on the collection: `collection.search(data=[query_embedding], anns_field="embedding", param=search_params, limit=top_k, output_fields=["id"])`.
        *   Handle potential errors during search.
        *   Check if any results were returned and if the distance/similarity of the top result meets the `threshold`. Milvus L2 distance is lower for more similar items. You might need to normalize or experiment to find a good threshold, or invert the logic (distance < threshold). For cosine similarity (if using IP metric), similarity > threshold. Let's stick with L2 for now and assume lower is better. Check `results[0].distances[0]`.
        *   If a good match is found, return the `id` of the top hit (`results[0].ids[0]`).
        *   Otherwise, return `None`.
        *   Log the query, top match ID, and distance/score for debugging.
3.  In `app/main.py`:
    *   Import necessary functions/classes from `app.rag_processor`, `app.pihole_client`, `pymilvus`.
    *   Modify the app startup logic (or create dependency injection) to:
        *   Load the embedding model once.
        *   Connect to Milvus and get the collection object once. Ensure it's loaded (`collection.load()`). Store these (model, collection) so they can be accessed by the endpoint. FastAPI dependencies are a good way to manage this.
    *   Define the request body model for `/query`: `class QueryRequest(BaseModel): query: str`
    *   Define the success response model (start simple): `class QueryResponse(BaseModel): message: str; status: str; pihole_status_code: int; raw_response: Any`
    *   Define the error response model: `class ErrorResponse(BaseModel): detail: str`
    *   Implement the `POST /query` endpoint:
        *   Apply the API key middleware implicitly (it's app-level).
        *   Takes the `QueryRequest` body.
        *   Get the logger, loaded model, and collection (e.g., via FastAPI dependencies).
        *   Call `rag_processor.match_intent()` with the user query, model, and collection.
        *   **If the matched intent ID is exactly `"GET /blocking"`:**
            *   Instantiate `PiholeClient` (or get via dependency).
            *   Try to call `pihole_client.get_blocking_status()`.
            *   On success, format a `QueryResponse` (e.g., message="Successfully fetched blocking status.", status="success", pihole_status_code=200, raw_response=pihole_result). Return it.
            *   Handle `PiholeAPIError`: Log error, return `JSONResponse(status_code=500, content={"detail": "Error from Pi-hole API..."})` (refine message later). Include Pi-hole status/response if possible.
            *   Handle `PiholeClientError` (connection): Log error, return `JSONResponse(status_code=502, content={"detail": "Could not connect to Pi-hole."})`.
        *   **If the matched intent is anything else or `None`:**
            *   Log the mismatch/failure.
            *   Return `JSONResponse(status_code=400, content={"detail": "Error: Could not understand the request. Please rephrase."})`.
4.  In `tests/test_rag_processor.py`:
    *   Write unit tests for `match_intent`.
    *   Mock the `model.encode` call.
    *   Mock the `collection.search` call, simulating different return values:
        *   Successful match above threshold.
        *   Match below threshold.
        *   No results returned.
        *   Milvus search error.
    *   Assert the correct intent ID or `None` is returned.
5.  In `tests/test_main.py`:
    *   Write integration tests for the `/query` endpoint specifically for the "GET /blocking" intent.
    *   Use `TestClient`. Provide a valid API Key.
    *   Mock the `app.rag_processor.match_intent` function to return `"GET /blocking"` or `None` or other IDs.
    *   Mock the `app.pihole_client.PiholeClient` (specifically `get_blocking_status`) to simulate success and failure scenarios (PiholeAPIError, PiholeClientError).
    *   Assert the correct HTTP status codes (200, 400, 500, 502) and response bodies are returned based on the mocked outcomes.

Provide updated `app/rag_processor.py`, `app/main.py`, `tests/test_rag_processor.py`, `tests/test_main.py`, and `requirements.txt`.
```

---

```text
Prompt 8: NER for Blocking Control & Pi-hole Client Update

Goal: Implement NER (using Regex) to extract parameters for enabling/disabling Pi-hole blocking and update the Pi-hole client to handle this action.

Requirements:
1.  Assume previous steps are complete.
2.  Create `app/ner_processor.py`:
    *   Import `re`, `logging`, maybe `typing`.
    *   Define a function `extract_blocking_params(query: str) -> dict | None`:
        *   Use regex patterns to identify:
            *   Action: Look for keywords like "enable", "start", "turn on" vs "disable", "stop", "turn off".
            *   Duration: Look for numbers preceding time units.
            *   Time Unit: Look for "seconds", "sec", "minutes", "min", "hours", "hr".
        *   Determine the primary action (enable or disable). If ambiguous, return `None` or raise an error.
        *   If a duration and unit are found, calculate the total duration in seconds.
        *   Return a dictionary like `{"action": "enable" | "disable", "duration_seconds": int | None}`. If only action is found, `duration_seconds` should be `None`.
        *   If no clear action is found, return `None`. Log the query and extraction result/failure.
3.  In `app/pihole_client.py`:
    *   Import necessary types.
    *   Add a method `enable_disable_blocking(self, action: str, duration_seconds: int | None = None) -> dict`:
        *   Validate the `action` parameter ("enable" or "disable").
        *   Prepare the query parameters for the Pi-hole API:
            *   If `action == "enable"`, params should be `{"enable": ""}`.
            *   If `action == "disable"` and `duration_seconds` is `None`, params should be `{"disable": ""}`.
            *   If `action == "disable"` and `duration_seconds` is not `None`, params should be `{"disable": duration_seconds}`.
        *   Call `_make_request` with `method='GET'`, `endpoint='/'`, `params=params`, `needs_auth=True`. (Note: Pi-hole docs use GET for enable/disable, even though POST might seem more appropriate. Let's stick to GET as per common examples, but double-check official current API docs if available. If POST is correct use `method='POST'` and potentially `data=params` or `json=params`). *Correction based on spec: Spec says `POST /blocking`. Let's assume POST is correct.* Call `_make_request` with `method='POST'`, `endpoint='/blocking'`, `data=params`, `needs_auth=True`.
        *   Return the result dictionary (e.g., `{"status": "enabled"}` or `{"status": "disabled"}`).
4.  Create `tests/test_ner_processor.py`:
    *   Import `pytest`, `extract_blocking_params`.
    *   Write unit tests for `extract_blocking_params` covering various phrasings:
        *   "enable pihole" -> `{"action": "enable", "duration_seconds": None}`
        *   "disable pihole" -> `{"action": "disable", "duration_seconds": None}`
        *   "disable pihole for 10 minutes" -> `{"action": "disable", "duration_seconds": 600}`
        *   "turn off blocking 30 sec" -> `{"action": "disable", "duration_seconds": 30}`
        *   "enable blocking for 1 hour" -> `{"action": "enable", "duration_seconds": None}` (Enable doesn't take duration in Pi-hole API)
        *   "start blocking" -> `{"action": "enable", "duration_seconds": None}`
        *   "what is the status" -> `None` (or should not match blocking intent anyway)
        *   Ambiguous query -> `None`
5.  In `tests/test_pihole_client.py`:
    *   Add tests for `enable_disable_blocking`.
    *   Mock `requests.request` (using POST).
    *   Test enabling: Verify correct params (`data={"enable": ""}`) are sent. Simulate success response.
    *   Test disabling permanently: Verify correct params (`data={"disable": ""}`) are sent. Simulate success.
    *   Test disabling temporarily: Verify correct params (`data={"disable": 600}`) are sent for 10 minutes. Simulate success.
    *   Test error handling (connection error, API error).

Provide `app/ner_processor.py`, updated `app/pihole_client.py`, `tests/test_ner_processor.py`, and updated `tests/test_pihole_client.py`.
```

---

```text
Prompt 9: Integrate NER & Blocking Control into /query Endpoint

Goal: Update the main `/query` endpoint to handle the "POST /blocking" intent, call the NER processor, and execute the corresponding Pi-hole client method.

Requirements:
1.  Assume `app/main.py`, `app/rag_processor.py`, `app/ner_processor.py`, `app/pihole_client.py` are updated from previous steps.
2.  In `app/main.py`:
    *   Import `extract_blocking_params` from `app.ner_processor`.
    *   Modify the `POST /query` endpoint logic:
        *   After `match_intent` is called:
        *   Add an `elif matched_intent == "POST /blocking":` block.
        *   Inside this block:
            *   Call `params = extract_blocking_params(request.query)`.
            *   If `params is None`:
                *   Log the NER failure.
                *   Return `JSONResponse(status_code=422, content={"detail": "Error: Missing required information for enable/disable action."})`.
            *   If params are extracted:
                *   Instantiate `PiholeClient` (or get via dependency).
                *   Try to call `pihole_client.enable_disable_blocking(action=params['action'], duration_seconds=params.get('duration_seconds'))`.
                *   On success, format a `QueryResponse` (e.g., message=f"Pi-hole blocking successfully {params['action']}d.", status="success", pihole_status_code=200, raw_response=pihole_result). Return it.
                *   Handle `PiholeAPIError` and `PiholeClientError` similarly to the "GET /blocking" case (return 500 or 502).
        *   Ensure the existing "GET /blocking" logic and the fallback 400 error remain.
3.  In `tests/test_main.py`:
    *   Add new integration tests for the `/query` endpoint targeting the "POST /blocking" intent.
    *   Use `TestClient`. Provide a valid API Key. Send queries like "disable for 10 mins", "enable now".
    *   Mock `app.rag_processor.match_intent` to return `"POST /blocking"`.
    *   Mock `app.ner_processor.extract_blocking_params` to return expected dictionaries (e.g., `{"action": "disable", "duration_seconds": 600}`) or `None`.
    *   Mock `app.pihole_client.PiholeClient.enable_disable_blocking` to simulate success and failure.
    *   Test scenarios:
        *   Successful enable. Assert 200 status and response body.
        *   Successful disable with duration. Assert 200.
        *   NER fails to extract params. Assert 422 status and response body.
        *   Pi-hole client raises `PiholeAPIError`. Assert 500.
        *   Pi-hole client raises `PiholeClientError`. Assert 502.

Provide the updated `app/main.py` and `tests/test_main.py`.
```

---

```text
Prompt 10: Expand Pi-hole Client, RAG, NER for Group Management (List, Get Specific)

Goal: Extend functionality to list all groups and get details for a specific group.

Requirements:
1.  **RAG Data:** Update `scripts/setup_rag.py`:
    *   Add intent descriptions for `GET /api/groups` and `GET /api/groups/{name}` to the `intents` list.
    *   Ensure the script can be re-run safely (e.g., by checking if IDs already exist or optionally clearing the collection).
2.  **Pi-hole Client (`app/pihole_client.py`):**
    *   Add method `list_groups(self) -> dict`: Calls `_make_request('GET', '/api/groups', needs_auth=True)`.
    *   Add method `get_group_details(self, group_name: str) -> dict`: Calls `_make_request('GET', f'/api/groups/{group_name}', needs_auth=True)`. URL encode the group name if necessary.
3.  **NER Processor (`app/ner_processor.py`):**
    *   Add function `extract_group_name_param(query: str) -> dict | None`:
        *   Use regex to find a group name, potentially looking for patterns like "group <name>", "details for <name>", "<name> group". Prioritize quoted names if found.
        *   Return `{"group_name": "extracted_name"}` or `None` if not found.
4.  **Main Endpoint (`app/main.py`):**
    *   Add `elif matched_intent == "GET /api/groups":` block:
        *   Call `pihole_client.list_groups()`.
        *   Format success (200) or handle errors (500/502).
    *   Add `elif matched_intent == "GET /api/groups/{name}":` block:
        *   Call `params = extract_group_name_param(request.query)`.
        *   If `params is None` or not `params.get("group_name")`: Return 422 error ("Missing group name").
        *   Call `pihole_client.get_group_details(group_name=params["group_name"])`.
        *   Format success (200) or handle errors (500/502 - including 404 from Pi-hole if group not found, which might raise PiholeAPIError).
5.  **Tests:**
    *   Update `tests/test_pihole_client.py`: Add tests for `list_groups` and `get_group_details` (success, API error, connection error). Mock `requests.request`.
    *   Update `tests/test_ner_processor.py`: Add tests for `extract_group_name_param` with various phrasings.
    *   Update `tests/test_main.py`: Add integration tests for `/query` targeting these new intents. Mock RAG, NER, and Client methods appropriately. Test success, NER failure (missing name -> 422), client errors (500/502).

Provide the updated `scripts/setup_rag.py`, `app/pihole_client.py`, `app/ner_processor.py`, `app/main.py`, `tests/test_pihole_client.py`, `tests/test_ner_processor.py`, and `tests/test_main.py`.
```

---

**(Continue this pattern for subsequent endpoints)**

*   **Prompt 11:** Add Group (`POST /api/groups/direct`) - RAG, NER (name(s), optional comment/enabled), Client, Endpoint, Tests.
*   **Prompt 12:** Modify Group (`PUT /api/groups/{name}`) - RAG, NER (target name, optional new name/comment/enabled), Client, Endpoint, Tests.
*   **Prompt 13:** Delete Group (`DELETE /api/groups/{name}`) - RAG, NER (name), Client, Endpoint, Tests.
*   **Prompt 14:** Batch Delete Groups (`POST /api/groups/batchDelete`) - RAG, NER (list of names), Client, Endpoint, Tests.
*   **Prompt 15:** Summary Stats (`GET /summary`) - RAG update (Client method already exists), Endpoint, Tests.
*   **Prompt 16:** Top Domains (`GET /top_domains`) - RAG, NER (optional count, blocked flag), Client, Endpoint, Tests.
*   **Prompt 17:** Top Clients (`GET /top_clients`) - RAG, NER (optional count, blocked flag), Client, Endpoint, Tests.
*   **Prompt 18:** Recent Blocked (`GET /recent_blocked`) - RAG, NER (optional count), Client, Endpoint, Tests.

---

```text
Prompt 19: Comprehensive Error Handling & Feature Flags

Goal: Implement the full range of specified error responses and add checks for feature flags from the configuration.

Requirements:
1.  Assume all previous steps integrating endpoints are complete. The `config` object contains the `mcp_server.features` sub-section.
2.  **Error Handling (`app/main.py`):**
    *   Review the `/query` endpoint logic.
    *   Ensure the following status codes and messages are returned in the correct scenarios:
        *   `403 Forbidden`: Handled by middleware (already done).
        *   `502 Bad Gateway`: Returned when `PiholeClientError` (connection/timeout) is caught. Use message: "Error: Could not connect to the Pi-hole API backend."
        *   `400 Bad Request`: Returned when RAG (`match_intent`) returns `None` or below threshold. Use message: "Error: Could not understand the request. Please rephrase."
        *   `422 Unprocessable Entity`: Returned when NER fails to extract *required* parameters for a matched intent. Use message: "Error: Missing required information (e.g., group name)." (Tailor message slightly if possible based on intent).
        *   `500 Internal Server Error`: Returned when `PiholeAPIError` is caught (indicating an error *from* Pi-hole). Format the response to potentially include Pi-hole's error details: `{"detail": "Error: Failed to execute request on Pi-hole.", "pihole_status_code": <status_code_from_exception>, "pihole_response": <raw_response_from_exception>}`. You may need to enhance `PiholeAPIError` to store this info.
    *   Refine the `try...except` blocks around `PiholeClient` calls to distinguish between `PiholeAPIError` and `PiholeClientError`.
3.  **Feature Flags (`app/main.py`):**
    *   Before calling NER or the Pi-hole client for a matched intent, check the corresponding feature flag in `config.mcp_server.features`.
    *   Map intents to feature categories (e.g., `GET /blocking`, `POST /blocking` -> `dns_blocking`; `/api/groups/*` -> `group_management`; `/summary`, `/top_*`, `/recent_blocked` -> `statistics`).
    *   If the required feature flag is set to `false`:
        *   Log that the feature is disabled.
        *   Return `JSONResponse(status_code=501, content={"detail": f"Error: This feature ({matched_intent}) is currently disabled."})`.
4.  **Update Pi-hole Client Error (`app/pihole_client.py`):**
    *   Modify `PiholeAPIError` to accept and store the status code and raw response text/JSON from the failed Pi-hole request. Update the `_make_request` method to capture and pass this information when raising `PiholeAPIError`.
5.  **Tests (`tests/test_main.py`):**
    *   Add specific integration tests for each error scenario: RAG fail (400), NER fail (422), Pi-hole connection error (502), Pi-hole API error (500 - check for included pihole details), Feature disabled (501).
    *   Ensure existing tests still pass. Mock config/features as needed for testing disabled flags.

Provide the updated `app/main.py`, `app/pihole_client.py`, and `tests/test_main.py`.
```

---

```text
Prompt 20: Logging Enhancement & Final Touches

Goal: Implement file logging, mask sensitive data, add more detailed logging messages, add docstrings, and create a README.

Requirements:
1.  **File Logging (`app/logging_config.py`):**
    *   Modify `setup_logging(config: RootConfig)`:
        *   Check if `config.logging.log_file` is set.
        *   If it is, add a `logging.FileHandler` to the root logger, pointing to that file path.
        *   Ensure the same formatter and level are used for the file handler.
        *   Handle potential errors during file handler creation (e.g., permissions).
2.  **Sensitive Data Masking:**
    *   Review all logging statements (`logging.info`, `logging.error`, etc.) throughout the code (`main.py`, `pihole_client.py`, `rag_processor.py`, `ner_processor.py`).
    *   Ensure that sensitive values like the Pi-hole password (`SecretStr.get_secret_value()`) and user API keys (`X-API-Key` header value, `SecretStr` values from config) are **never** logged directly. Log placeholders like `"<api_key_masked>"` or `"<password_masked>"` instead.
3.  **Detailed Logging:**
    *   Add more informative log messages at key stages:
        *   `main.py`: Log incoming query, matched intent (or failure), extracted params (or failure), feature flag check results, Pi-hole client call initiation, final response status code being sent.
        *   `pihole_client.py`: Log outgoing request details (method, URL *without* auth token), log successful response status, log errors clearly before raising exceptions.
        *   `rag_processor.py`: Log search parameters, number of results found, distance/score of top hit.
        *   `ner_processor.py`: Log the query being processed and the extracted parameters (or failure).
4.  **Docstrings & Type Hints:**
    *   Review all functions and classes in `app/`.
    *   Add comprehensive docstrings explaining purpose, arguments, and return values.
    *   Ensure type hints are present and correct for function signatures and variables where beneficial.
5.  **README:**
    *   Create `README.md` in the project root.
    *   Include:
        *   Project goal description.
        *   Setup instructions (Python version, virtual env, `pip install -r requirements.txt`).
        *   Configuration steps (`config.toml`, `.env` file usage for sensitive data).
        *   How to run the RAG setup script (`python scripts/setup_rag.py`).
        *   How to run the server (`uvicorn app.main:app --reload`).
        *   API usage example (curl command for `/query` including `X-API-Key` header).
        *   How to run tests (`pytest`).
6.  **Final `requirements.txt`:** Update `requirements.txt` with all necessary dependencies. `pip freeze > requirements.txt`.

Provide the updated `app/logging_config.py`, `README.md`, and the final `requirements.txt`. Indicate where logging statements and docstrings should be added/checked in other files (`app/main.py`, `app/pihole_client.py`, etc.), but you don't need to provide the full content of those files again unless significant changes beyond logging/docs were needed.
```

---

This series of prompts builds the application incrementally, focusing on testing at each stage and ensuring all components are integrated as they are built.

## todo.md Checklist

```markdown
# MCP Pi-hole Chatbot Server - TODO List

## Phase 1: Core Setup & Basic Server

*   [ ] **1.1: Project Structure & Dependencies**
    *   [ ] Create directories (`app`, `tests`, `scripts`)
    *   [ ] Create `__init__.py` files
    *   [ ] Create `requirements.txt`
    *   [ ] Add initial dependencies (`python-dotenv`, `toml`, `pydantic`, `pytest`) to `requirements.txt`
    *   [ ] Set up virtual environment
    *   [ ] Create `.gitignore` (add `.venv`, `__pycache__`, `*.pyc`, `config.toml`, `.env`)
*   [ ] **1.2: Configuration Loading**
    *   [ ] Create `config.toml.example` (based on spec section 10)
    *   [ ] Create `.env.example` (for `PIHOLE_PASSWORD`, `MCP_API_KEYS`)
    *   [ ] Implement Pydantic models in `app/config.py` for config structure
    *   [ ] Implement `load_config()` in `app/config.py` (load `.env`, read TOML, override from env, validate with Pydantic)
    *   [ ] Write unit tests for `load_config()` in `tests/test_config.py` (success, validation errors, env override, file not found)
*   [ ] **1.3: Basic Logging**
    *   [ ] Create `app/logging_config.py`
    *   [ ] Implement `setup_logging(config)` function (stdout handler, level from config, formatter)
    *   [ ] Write basic test for `setup_logging` in `tests/test_logging_config.py`
*   [ ] **1.4: Basic FastAPI App**
    *   [ ] Add `fastapi`, `uvicorn[standard]` to `requirements.txt`
    *   [ ] Create `app/main.py`
    *   [ ] Initialize FastAPI app in `app/main.py`
    *   [ ] Load config and setup logging on startup
    *   [ ] Implement `GET /health` endpoint
    *   [ ] Write test for `/health` endpoint in `tests/test_main.py` using `TestClient`
*   [ ] **1.5: API Key Authentication Middleware**
    *   [ ] Implement API key middleware (`X-API-Key` check against config) in `app/main.py` or `app/security.py`
    *   [ ] Apply middleware to the FastAPI app (excluding `/health`)
    *   [ ] Write tests for middleware in `tests/test_main.py` (valid key, invalid key, missing key, unprotected route)

## Phase 2: Basic Pi-hole Interaction

*   [ ] **2.1: Simple Pi-hole Client Structure**
    *   [ ] Add `requests` to `requirements.txt`
    *   [ ] Create `app/pihole_client.py`
    *   [ ] Define `PiholeClientError` and `PiholeAPIError` exceptions
    *   [ ] Define `PiholeClient` class (`__init__`, `_make_request` helper)
*   [ ] **2.2: Implement `get_blocking_status`**
    *   [ ] Add `get_blocking_status()` method to `PiholeClient` (call `_make_request` for `GET /blocking`)
*   [ ] **2.3: Test `get_blocking_status`**
    *   [ ] Write unit tests in `tests/test_pihole_client.py` (mock `requests`, test success, connection error, API error)
*   [ ] **2.4: Implement `get_summary`**
    *   [ ] Add `get_summary()` method to `PiholeClient` (call `_make_request` for `GET /summary`)
*   [ ] **2.5: Test `get_summary`**
    *   [ ] Write unit tests in `tests/test_pihole_client.py` (mock `requests`, test success, connection error, API error)

## Phase 3: Basic RAG & Endpoint Integration (Status Check Only)

*   [ ] **3.1: RAG Dependencies & Setup Script**
    *   [ ] Add `pymilvus`, `sentence-transformers` to `requirements.txt`
    *   [ ] Create `scripts/setup_rag.py`
*   [ ] **3.2: Milvus Connection & Model Loading**
    *   [ ] Update `config.toml.example` and `app/config.py` with `[milvus]` and `[models]` sections
    *   [ ] Create `app/rag_processor.py`
    *   [ ] Implement `get_milvus_connection()` and `load_embedding_model()` in `app/rag_processor.py`
    *   [ ] Define `MilvusConnectionError`
*   [ ] **3.3: Embed Initial Intents**
    *   [ ] Update `scripts/setup_rag.py` to load config, connect Milvus, load model
    *   [ ] Define intent data for `GET /blocking` and `POST /blocking` in script
    *   [ ] Implement logic to create Milvus collection and index if needed
    *   [ ] Embed descriptions and insert into Milvus
    *   [ ] Add `if __name__ == "__main__":` block
*   [ ] **3.4: Implement `match_intent` Function**
    *   [ ] Implement `match_intent()` in `app/rag_processor.py` (embed query, search Milvus, check threshold, return ID or None)
*   [ ] **3.5: Test `match_intent`**
    *   [ ] Write unit tests in `tests/test_rag_processor.py` (mock Milvus search results)
*   [ ] **3.6: Basic `/query` Endpoint**
    *   [ ] Define `QueryRequest`, `QueryResponse`, `ErrorResponse` Pydantic models in `app/main.py`
    *   [ ] Implement `POST /query` endpoint structure in `app/main.py` (accepts query, basic logging)
    *   [ ] Write basic structure test for `/query` endpoint in `tests/test_main.py`
*   [ ] **3.7: Integrate RAG & Pi-hole Status**
    *   [ ] Load model & Milvus collection on app startup (use FastAPI dependencies)
    *   [ ] Update `/query` to call `match_intent`
    *   [ ] If intent is `GET /blocking`, call `pihole_client.get_blocking_status`
    *   [ ] Format success response (200)
    *   [ ] Handle `PiholeClientError` (502) and `PiholeAPIError` (500)
    *   [ ] Return 400 if intent doesn't match or fails
*   [ ] **3.8: Test `/query` for Status Check**
    *   [ ] Write integration tests in `tests/test_main.py` (mock RAG & Client, test 200, 400, 500, 502 responses)

## Phase 4: NER & Pi-hole Blocking Control

*   [ ] **4.1: Simple NER for Blocking**
    *   [ ] Create `app/ner_processor.py`
    *   [ ] Implement `extract_blocking_params()` using regex (action, duration, unit -> seconds)
*   [ ] **4.2: Test `extract_blocking_params`**
    *   [ ] Write unit tests in `tests/test_ner_processor.py` covering various phrasings
*   [ ] **4.3: Implement `enable_disable_blocking` in Client**
    *   [ ] Add `enable_disable_blocking()` method to `PiholeClient` (call `_make_request` for `POST /blocking` with correct data)
*   [ ] **4.4: Test `enable_disable_blocking`**
    *   [ ] Write unit tests in `tests/test_pihole_client.py` (mock `requests`, test enable, disable perm, disable temp, errors)
*   [ ] **4.5: Integrate NER & Blocking into `/query`**
    *   [ ] Update `/query` endpoint: add `elif matched_intent == "POST /blocking"`
    *   [ ] Call `extract_blocking_params`
    *   [ ] Return 422 if NER fails
    *   [ ] Call `pihole_client.enable_disable_blocking`
    *   [ ] Format success (200) or handle client errors (500/502)
*   [ ] **4.6: Test `/query` for Blocking Control**
    *   [ ] Write integration tests in `tests/test_main.py` (mock RAG, NER, Client; test success, NER fail -> 422, client errors -> 500/502)

## Phase 5: Expand Coverage Incrementally

*   [ ] **5.1: Group Listing (`GET /api/groups`)**
    *   [ ] RAG: Add intent to `scripts/setup_rag.py` & re-run
    *   [ ] Client: Implement & Test `list_groups()` in `app/pihole_client.py`
    *   [ ] Endpoint: Update & Test `/query` logic in `app/main.py`
*   [ ] **5.2: Group Detail (`GET /api/groups/{name}`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] NER: Implement & Test `extract_group_name_param()` in `app/ner_processor.py`
    *   [ ] Client: Implement & Test `get_group_details()` in `app/pihole_client.py`
    *   [ ] Endpoint: Update & Test `/query` logic (handle NER fail -> 422)
*   [ ] **5.3: Add Group (`POST /api/groups/direct`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] NER: Implement & Test `extract_add_group_params()`
    *   [ ] Client: Implement & Test `add_groups()`
    *   [ ] Endpoint: Update & Test `/query` logic (handle NER fail -> 422)
*   [ ] **5.4: Modify Group (`PUT /api/groups/{name}`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] NER: Implement & Test `extract_modify_group_params()`
    *   [ ] Client: Implement & Test `modify_group()`
    *   [ ] Endpoint: Update & Test `/query` logic (handle NER fail -> 422)
*   [ ] **5.5: Delete Group (`DELETE /api/groups/{name}`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] NER: Implement & Test `extract_group_name_param()` (reuse if suitable)
    *   [ ] Client: Implement & Test `delete_group()`
    *   [ ] Endpoint: Update & Test `/query` logic (handle NER fail -> 422)
*   [ ] **5.6: Batch Delete Groups (`POST /api/groups/batchDelete`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] NER: Implement & Test `extract_batch_delete_group_names()`
    *   [ ] Client: Implement & Test `batch_delete_groups()`
    *   [ ] Endpoint: Update & Test `/query` logic (handle NER fail -> 422)
*   [ ] **5.7: Summary Stats (`GET /summary`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] Endpoint: Update & Test `/query` logic (client method exists)
*   [ ] **5.8: Top Domains (`GET /top_domains`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] NER: Implement & Test `extract_top_domain_params()` (count, blocked)
    *   [ ] Client: Implement & Test `get_top_domains()`
    *   [ ] Endpoint: Update & Test `/query` logic
*   [ ] **5.9: Top Clients (`GET /top_clients`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] NER: Implement & Test `extract_top_client_params()` (count, blocked)
    *   [ ] Client: Implement & Test `get_top_clients()`
    *   [ ] Endpoint: Update & Test `/query` logic
*   [ ] **5.10: Recent Blocked (`GET /recent_blocked`)**
    *   [ ] RAG: Add intent & re-run setup
    *   [ ] NER: Implement & Test `extract_recent_blocked_params()` (count)
    *   [ ] Client: Implement & Test `get_recent_blocked()`
    *   [ ] Endpoint: Update & Test `/query` logic

## Phase 6: Finalization & Refinement

*   [ ] **6.1: Implement Full Error Handling**
    *   [ ] Review `/query` and `PiholeClient` error handling
    *   [ ] Ensure 400, 403, 422, 500, 502 responses match spec
    *   [ ] Enhance `PiholeAPIError` to store status/response from Pi-hole
    *   [ ] Update `_make_request` to populate enhanced error
    *   [ ] Format 500 response to include Pi-hole details
    *   [ ] Write/update tests in `tests/test_main.py` for each specific error code path
*   [ ] **6.2: Feature Flags**
    *   [ ] Add checks in `/query` based on `config.mcp_server.features` before calling NER/Client
    *   [ ] Map intents to feature categories (`dns_blocking`, `group_management`, `statistics`)
    *   [ ] Return 501 response if feature is disabled
    *   [ ] Write tests in `tests/test_main.py` for disabled features
*   [ ] **6.3: Enhance Logging**
    *   [ ] Implement file logging in `app/logging_config.py` based on config
    *   [ ] Add `FileHandler` if `log_file` is set
    *   [ ] Review all logging statements for sensitive data (mask passwords, API keys)
    *   [ ] Add detailed log messages at key points (query received, intent matched, params extracted, client called, response sent)
    *   [ ] Test logging output (stdout and file if configured)
*   [ ] **6.4: Refactor & Docstrings**
    *   [ ] Add comprehensive docstrings to all functions/classes in `app/`
    *   [ ] Ensure type hints are present and correct
    *   [ ] Review code for clarity, duplication, and efficiency
*   [ ] **6.5: README & Final Tests**
    *   [ ] Create `README.md` with Goal, Setup, Config, Running RAG script, Running Server, API Usage, Running Tests
    *   [ ] Run all tests (`pytest`)
    *   [ ] Perform manual end-to-end testing if possible
    *   [ ] `pip freeze > requirements.txt`
    *   [ ] (Optional) Create `Dockerfile`
```
