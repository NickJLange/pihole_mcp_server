
## todo.md Checklist

```markdown
# MCP Server Implementation Checklist

## Phase 1: Foundation & Setup

-   [x] Initialize project structure (Poetry/pipenv/venv)
-   [x] Add initial dependencies (`fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, `toml`)
-   [x] Create basic FastAPI app (`main.py`) with root endpoint (`/`)
-   [x] Implement configuration loading (`config.py`) from `config.toml` and environment variables (using Pydantic)
-   [x] Create sample `config.toml` and `.env.example`
-   [x] Implement logging configuration (`logging_config.py`) based on config (level, file, console)
-   [x] Integrate config loading and logging into `main.py` startup
-   [x] Define basic Pydantic models (`models.py`: `QueryRequest`, `SuccessResponse`, `ErrorResponse`)
-   [x] Write basic test for root endpoint (`/`)

## Phase 2: API Endpoint & Authentication

-   [x] Create `auth.py`
-   [x] Implement API Key dependency (`get_api_key`) checking `X-API-Key` header against config
-   [x] Implement `POST /query` endpoint skeleton in `main.py`
-   [x] Apply API key dependency to `/query`
-   [x] Write tests for `/query` authentication (valid key, invalid key, missing key)

## Phase 3: Pi-hole Client Module

-   [x] Create `pihole_client.py`
-   [x] Add `requests` dependency
-   [x] Define custom exceptions (`PiholeApiError`, `PiholeConnectionError`)
-   [x] Implement private `_make_request` helper (handles URL, auth header, method, error checking)
-   [x] Implement `get_blocking_status(config)`
-   [ ] Implement `set_blocking_status(config, action, duration)`
-   [ ] Implement `get_groups(config)`
-   [ ] Implement `get_group_by_name(config, group_name)`
-   [ ] Implement `add_groups(config, names, comment, enabled)`
-   [ ] Implement `modify_group(config, target_group_name, new_name, comment, enabled)`
-   [ ] Implement `delete_group(config, group_name)`
-   [ ] Implement `delete_groups_batch(config, group_names)`
-   [ ] Implement `get_summary(config)`
-   [ ] Implement `get_top_domains(config, count, blocked)`
-   [ ] Implement `get_top_clients(config, count, blocked)`
-   [ ] Implement `get_recent_blocked(config, count)`
-   [x] Write unit tests (using mocks) for `get_blocking_status`
-   [ ] Write unit tests (using mocks) for all other Pi-hole client functions

## Phase 4: RAG Implementation

-   [x] Add `pymilvus`, `sentence-transformers` dependencies
-   [x] Create `rag.py`
-   [x] Define Milvus constants (collection name, dimension)
-   [x] Add Milvus connection details to `config.toml`
-   [x] Implement `connect_milvus(config)`
-   [x] Implement `get_collection(collection_name)` (with schema definition & index creation)
-   [x] Implement `initialize_embedding_model()` and `embed_text(text, model)`
-   [x] Create `load_intents.py` script
-   [x] Define intent data structure in `load_intents.py` (from spec)
-   [x] Implement logic in `load_intents.py` to embed and load data into Milvus
-   [x] Implement `find_matching_intent(query_text, config, threshold)`
-   [ ] Define `RagIntentNotFoundError` exception in `rag.py`
-   [x] Write unit tests (mocking Milvus/embeddings) for `rag.py` functions
-   [x] Run `load_intents.py` to populate database

## Phase 5: NER Implementation

-   [x] Create `ner.py`
-   [x] Define `NerParameterError` exception
-   [x] Implement `extract_blocking_params(query_text)` using regex
-   [ ] Implement `extract_group_name(query_text)`
-   [ ] Implement `extract_multiple_group_names(query_text)`
-   [ ] Implement `extract_add_group_params(query_text)`
-   [ ] Implement `extract_modify_group_params(query_text)`
-   [ ] Implement `extract_stats_params(query_text)`
-   [x] Write unit tests for `extract_blocking_params`
-   [ ] Write unit tests for all other NER functions

## Phase 6: Integration & Logic

-   [x] Integrate `rag.find_matching_intent` into `/query` endpoint
-   [x] Add basic handling for intent not found (400 error)
-   [x] Add basic handling for unimplemented intents (501 error)
-   [x] Integrate `ner.extract_blocking_params` for `POST /blocking` intent
-   [x] Add handling for NER failure (422 error)
-   [x] Integrate `pihole_client.set_blocking_status` call
-   [x] Add basic handling for Pi-hole client errors (500, 502)
-   [x] Format success response for `POST /blocking`
-   [ ] Implement dispatch logic (if/elif or dict) in `/query` based on `endpoint_name`
-   [ ] Implement feature flag checks from config for each intent path
-   [ ] Integrate NER calls for Group Management intents
-   [ ] Integrate Pi-hole client calls for Group Management intents
-   [ ] Format success responses for Group Management intents
-   [ ] Integrate NER calls for Statistics intents
-   [ ] Integrate Pi-hole client calls for Statistics intents
-   [ ] Format success responses for Statistics intents
-   [x] Write initial integration tests for the blocking flow (mocking RAG, NER, Pi-hole)
-   [ ] Write integration tests for Group Management flows
-   [ ] Write integration tests for Statistics flows
-   [ ] Write integration tests for feature flag logic

## Phase 7: Error Handling & Refinement

-   [ ] Implement FastAPI exception handlers for `PiholeConnectionError`, `PiholeApiError`, `NerParameterError`, `RagIntentNotFoundError`, generic `Exception`
-   [ ] Move error response generation from `/query` endpoint logic to exception handlers
-   [ ] Review and enhance logging messages throughout the application (ensure clarity, safety)
-   [ ] Expand unit tests for edge cases (NER, Pi-hole client responses)
-   [ ] Expand integration tests for varied queries, parameter interactions, Pi-hole edge cases

## Phase 8: Finalization & Documentation

-   [ ] Ensure dependencies are finalized (`pyproject.toml` or `requirements.txt`)
-   [ ] Write comprehensive `README.md` (overview, setup, config, secrets, run intents script, run server, API usage, run tests)
-   [x] Create this `todo.md` checklist
-   [ ] Perform final code cleanup (remove debug code, unused imports, format code)
-   [ ] Ensure type hints are complete and linters pass (`flake8`, `mypy`, `black`, `isort`)

