**MCP Server Specification for Pi-hole Chatbot Integration**

**1. Goal:**
Create a secure, user-friendly Python server (MCP Server) that acts as an intermediary between a chatbot client and a Pi-hole instance. The MCP server will translate natural language user requests (received from the chatbot) into specific Pi-hole API calls using a Retrieval-Augmented Generation (RAG) framework with a vector database (`pymilvus`) and Named Entity Recognition (NER).

**2. Interaction Flow:**
    *   An end-user provides a natural language command to a chatbot (e.g., "disable pihole for 10 minutes").
    *   The chatbot client sends this command to the MCP Server's API endpoint.
    *   The MCP Server validates the chatbot client's credentials.
    *   The MCP Server processes the natural language query using RAG and NER to identify the corresponding Pi-hole API endpoint and necessary parameters.
    *   The MCP Server authenticates with the Pi-hole API using its own pre-configured credentials.
    *   The MCP Server executes the Pi-hole API call.
    *   The MCP Server formats the Pi-hole response (success or error) into a structured JSON format.
    *   The MCP Server sends the structured response back to the chatbot client.

**3. MCP Server API Endpoint:**
    *   **Method:** `POST`
    *   **Path:** `/query` (or similar, e.g., `/v1/process`)
    *   **Authentication:** Requires an API key specific to the chatbot client, provided in the `X-API-Key` HTTP header. Invalid or missing keys result in a `403 Forbidden` error.
    *   **Request Body:**
        ```json
        {
          "query": "<The user's natural language query string>"
        }
        ```
    *   **Response Body (Success):**
        ```json
        {
          "message": "<User-friendly summary of the result>",
          "status": "success",
          "pihole_status_code": <HTTP status code received from Pi-hole (e.g., 200, 201, 204)>,
          "raw_response": <Raw response data from Pi-hole (can be JSON object, text string, null)>
        }
        ```
    *   **Response Body (Error - See Section 8 for details):** Structured JSON indicating the error type.

**4. Core Logic - RAG & NER:**
    *   **RAG Intent Matching:**
        *   Use a vector database (specifically `pymilvus`).
        *   Embed simple English descriptions (defined below) capturing the intent of each supported Pi-hole API endpoint.
        *   Embed the incoming user query (multilingual support desirable for embedding model).
        *   Perform nearest neighbor search in `pymilvus` to match the user query embedding against the embedded API intent descriptions.
    *   **NER Parameter Extraction:**
        *   Once intent is matched, use NER (e.g., spaCy, regex, or other suitable library) to extract required and optional parameters from the user's query based on the target endpoint (parameter list defined below).
        *   Use natural language parameter names (defined below) to guide NER and potentially for disambiguation.

**5. Pi-hole Authentication:**
    *   The MCP server authenticates to the Pi-hole API using an Application Password configured in its `config.toml` file.

**6. Initial Scope - Supported Pi-hole Functions:**
    *   **DNS Blocking Control:**
        *   Check status (`GET /blocking`)
        *   Enable/Disable/Temporary Disable (`POST /blocking`)
    *   **Group Management:**
        *   List all (`GET /api/groups`)
        *   Get specific (`GET /api/groups/{name}`)
        *   Add single/multiple (`POST /api/groups/direct`)
        *   Modify/Rename (`PUT /api/groups/{name}`)
        *   Delete specific (`DELETE /api/groups/{name}`)
        *   Delete multiple (`POST /api/groups/batchDelete`)
    *   **Statistics Export:**
        *   Get 24h summary (`GET /summary`)
        *   Get top domains (permitted/blocked) (`GET /top_domains`)
        *   Get top clients (active/blocked) (`GET /top_clients`)
        *   Get recent blocked domain(s) (`GET /recent_blocked`)
    *   *Other Pi-hole API functions are out of scope for the initial version.*

**7. RAG Intent Descriptions & Example Phrasings:**

    | Endpoint                   | Intent Description for RAG Embedding                                                                                                                                                                                            | 4 Example User Phrasings (Placeholders: `<...>` )                                                                                                                                                                                                                                                                                          |
    | :------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | `GET /blocking`            | "Check if Pi-hole blocking is currently enabled or disabled. This endpoint retrieves the blocking status and indicates if there is an active timer. Use this to confirm the current state of the Pi-hole's blocking feature."   | 1. "Is Pi-hole blocking ads?" <br> 2. "What's the blocking status?" <br> 3. "Can you tell me if Pi-hole is currently blocking?" <br> 4. "Check if ads are being blocked by Pi-hole."                                                                                                                                                |
    | `POST /blocking`           | "Use this endpoint to enable or disable Pi-hole blocking. You can also optionally set a timer to temporarily disable blocking for a specified duration (in seconds). This allows for flexible management of blocking functionality." | 1. "Please enable pihole." <br> 2. "Disable pihole for 10 minutes." <br> 3. "Turn off ad blocking." <br> 4. "Enable blocking permanently."                                                                                                                                                                                        |
    | `GET /api/groups`          | "Retrieve a list of all configured groups in Pi-hole. This endpoint provides an overview of the current group settings, allowing users to see all available groups at a glance."                                                    | 1. "Can you show me all the groups?" <br> 2. "What groups are configured?" <br> 3. "List all groups in Pi-hole." <br> 4. "Show me the current group settings."                                                                                                                                                                     |
    | `GET /api/groups/{name}`   | "Retrieve detailed information about a specific group in Pi-hole using its name. This endpoint provides the group's ID, name, comment, enabled status, and relevant dates. The group name must be included as a parameter."      | 1. "What are the details for group `<group_name>`?" <br> 2. "Can you provide information about `<group_name>`?" <br> 3. "Show me the settings for `<group_name>` group." <br> 4. "Tell me about the group named `<group_name>`."                                                                                                   |
    | `POST /api/groups/direct`  | "Use this endpoint to create one or more new groups in Pi-hole. The request body can contain a single `name` or an array of `name`s, along with optional `comment` and `enabled` status."                                         | 1. "Create a group named `<group_name>` with comment `<comment>`." <br> 2. "Add a new group called `<group_name>`." <br> 3. "Could you create groups: `<group_name1>`, `<group_name2>`?" <br> 4. "Set up a group named `<group_name>`."                                                                                             |
    | `PUT /api/groups/{name}`   | "Use this endpoint to modify an existing group in Pi-hole identified by its name. You can change the group's name (effectively renaming it), `comment`, or its `enabled` status by providing the desired properties."          | 1. "Rename group `<current_group_name>` to `<new_group_name>`." <br> 2. "Update the `<current_group_name>` group status to `<status: enabled/disabled>`." <br> 3. "Set the comment for group `<current_group_name>` to `<comment>`." <br> 4. "Modify group `<current_group_name>`: rename it to `<new_group_name>` and disable it." |
    | `DELETE /api/groups/{name}`| "Use this endpoint to delete an existing group in Pi-hole identified by its name. This allows for easy deletes of a group."                                                                                                   | 1. "Can you delete the group named `<group_name>`?" <br> 2. "I want to remove the `<group_name>` group." <br> 3. "Please delete the group called `<group_name>`." <br> 4. "Remove `<group_name>` from the list of groups."                                                                                                             |
    | `POST /api/groups/batchDelete` | "Use this endpoint to delete multiple existing groups in Pi-hole by providing an array of group names in the request body. This allows for efficient removal of several groups at once."                                      | 1. "Delete the groups `<group_name1>`, `<group_name2>` and `<group_name3>`." <br> 2. "Remove the groups `<group_name1>` and `<group_name2>`." <br> 3. "Delete groups `<group_name1>`, `<group_name2>`, and `<group_name3>`." <br> 4. "Remove `<group_name1>`, `<group_name2>` from my groups."                                          |
    | `GET /summary`             | "Use this endpoint to retrieve a 24-hour overview of statistics in Pi-hole, including total/blocked queries, percentages, unique domains, forwarded/cached counts, client counts, gravity details, and update times."         | 1. "Give me the 24-hour summary stats." <br> 2. "Show the Pi-hole activity overview for today." <br> 3. "What are the overall stats for the last 24 hours?" <br> 4. "Get the Pi-hole summary report."                                                                                                                           |
    | `GET /top_domains`         | "Use this endpoint to retrieve the most frequently queried domains. Specify `blocked=true` for blocked domains. Control the number returned with the `count` parameter."                                                       | 1. "Show the top `<count>` most requested domains." <br> 2. "What are the top `<count>` blocked domains?" <br> 3. "List the 5 most frequent domains." <br> 4. "Get the top blocked sites."                                                                                                                                         |
    | `GET /top_clients`         | "Use this endpoint to retrieve the clients making the most queries. Specify `blocked=true` for clients hitting the blocklist most. Control the number returned with the `count` parameter."                                     | 1. "Which are the top `<count>` most active clients?" <br> 2. "Show the top `<count>` clients hitting the blocklist." <br> 3. "List the top 3 clients overall." <br> 4. "Get the clients that are blocked most often."                                                                                                            |
    | `GET /recent_blocked`      | "Use this endpoint to retrieve the domain name(s) that were most recently blocked by Pi-hole. Control how many recent domains are returned using the `count` parameter (default 1)."                                          | 1. "Show the most recent `<count>` blocked domains." <br> 2. "What was the last domain blocked?" <br> 3. "Give me the latest `<count>` blocked domains." <br> 4. "Get the `<count>` most recently blocked domains."                                                                                                                  |

**8. NER Parameter Extraction Details:**

    | Endpoint                   | Parameter (Internal) | Natural Language Name(s)              | Extraction Notes                                           |
    | :------------------------- | :------------------- | :------------------------------------ | :--------------------------------------------------------- |
    | `POST /blocking`           | `enable_disable_flag`| "desired blocking state", "action"    | Boolean (True for enable, False for disable)               |
    |                            | `duration`           | "duration", "time period"             | Numerical value (e.g., 10, 5)                            |
    |                            | `time_unit`          | "duration", "time period"             | Unit (seconds, minutes, hours). Convert to total seconds.  |
    | `GET /api/groups/{name}`   | `group_name`         | "group name"                          | String                                                     |
    | `POST /api/groups/direct`  | `group_name(s)`      | "new group name(s)"                   | String or List of Strings                                  |
    |                            | `comment` (Opt)      | "comment", "description"              | String                                                     |
    |                            | `enabled_status` (Opt)| "enabled status", "active state"    | Boolean (Defaults True)                                    |
    | `PUT /api/groups/{name}`   | `target_group_name`  | "current group name"                  | String (from user query, maps to URL path)               |
    |                            | `new_group_name` (Opt)| "new group name", "updated name"      | String (for renaming)                                      |
    |                            | `comment` (Opt)      | "comment", "description"              | String                                                     |
    |                            | `enabled_status` (Opt)| "enabled status", "active state"    | Boolean                                                    |
    | `DELETE /api/groups/{name}`| `group_name`         | "group name"                          | String                                                     |
    | `POST /api/groups/batchDelete`| `group_names`    | "list of group names"                 | List of Strings                                            |
    | `GET /top_domains`         | `count` (Opt)        | "count", "number of results"          | Integer                                                    |
    |                            | `blocked_flag` (Opt) | "filter type", "statistic type"       | Boolean (True for blocked, False for permitted/queried)    |
    | `GET /top_clients`         | `count` (Opt)        | "count", "number of results"          | Integer                                                    |
    |                            | `blocked_flag` (Opt) | "filter type", "statistic type"       | Boolean (True for blocked, False for active)               |
    | `GET /recent_blocked`      | `count` (Opt)        | "count", "number of results"          | Integer                                                    |

**9. Error Handling:**

    | Scenario                         | HTTP Status Code | Response Body (`message` field example)                                        | Notes                                                         |
    | :------------------------------- | :--------------- | :----------------------------------------------------------------------------- | :------------------------------------------------------------ |
    | Invalid/Missing `X-API-Key`      | `403 Forbidden`    | "Forbidden: Invalid or missing API Key."                                         | No interaction with Pi-hole.                                  |
    | Cannot Connect to Pi-hole        | `502 Bad Gateway`  | "Error: Could not connect to the Pi-hole API backend."                           | Problem between MCP server and Pi-hole.                       |
    | RAG Intent Match Failed          | `400 Bad Request`  | "Error: Could not understand the request. Please rephrase."                  | User query too ambiguous.                                     |
    | NER Parameter Extraction Failed  | `422 Unprocessable`| "Error: Missing required information (e.g., group name)."                      | Intent clear, but params missing from query.                  |
    | Pi-hole API Returns Error        | `500 Internal Server Error` | "Error: Failed to execute request on Pi-hole." (Include Pi-hole error details) | Include `pihole_status_code` & `raw_response` from Pi-hole. |
    | Requested Feature Disabled       | `501 Not Implemented` | "Error: This feature (<feature_name>) is currently disabled."                | Based on `config.toml` feature flags.                       |

**10. Configuration (`config.toml`):**

    ```toml
    [pihole]
    api_url = "http://pi.hole/api" # Must point to FTL API
    application_password = "your_pihole_app_password_here" # Use Env Var in Prod

    [mcp_server]
    authorized_api_keys = ["chatbot_api_key_1"] # Use Env Var in Prod

    [mcp_server.features]
    dns_blocking = true
    group_management = true
    statistics = true

    [logging]
    level = "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_file = "mcp_server.log" # Path to log file, empty disables file logging
    #	 Optional: Add rotation settings later if needed
    ```

**11. Logging:**
    *   Use standard Python `logging` module.
    *   Configure level based on `config.toml`.
    *   Log output **must** go to `stdout`/`stderr`.
    *   Log output **must** go to the file specified in `config.toml` (if provided).
    *   Logs should include timestamp, level, and informative messages about requests, processing steps, Pi-hole interactions, and errors.

**12. Technology Stack Hints:**
    *   Python 3.x
    *   Web Framework: FastAPI or Flask recommended.
    *   Vector Database Client: `pymilvus`
    *   Embedding Model: A suitable multilingual sentence transformer model.
    *   NER: spaCy, Regex, or similar.
    *   Configuration Parsing: `toml` library.
    *   HTTP Requests: `requests` library.
