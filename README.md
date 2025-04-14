# PiHole MCP Server

## Dear Lord, Why?

We are building this project to enhance the management experience of Pi-hole devices. We believe that natural language processing capabilities can make it easier for users to interact with their Pi-hole devices. We are also building this project to learn more about FastAPI and Retrieval-Augmented Generation (RAG) systems.

### **MCP Server Overview**
The **MCP Server** is designed to interact with Pi-hole devices using a RESTful API built with FastAPI, allowing for query-based management and retrieval of Pi-hole statistics through a Retrieval-Augmented Generation (RAG) system. This service aims to enhance the Pi-hole management experience with natural language processing capabilities.

##### **Installation**
1. **Clone the Repository:**
   ```sh
   git clone [your repository URL]
   cd mcp_server
   ```

2. **Set Up Virtual Environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configuration:**
   - Copy `config.toml.example` to `config.toml`.
   - Adjust the settings according to your Pi-hole setup, API keys, and Milvus database connection details.
   - For secrets like API keys, use an `.env` file:

##### **Running the Server**
```sh
uvicorn main:app --host 0.0.0.0 --port 8000
```

##### **API Usage**
- **Query Endpoint:** Use POST requests to `/query` with headers including `X-API-Key`. Example:
  ```http
  POST /query HTTP/1.1
  Host: yourserver.com
  X-API-Key: your_api_key_here
  Content-Type: application/json

  {
    "query": "Block internet for 10 minutes."
  }
  ```

- **Feature Flags:** Check `config.toml` for feature flag settings which control available functionalities.

#### **Documentation**
- Refer to the API documentation at `/docs` when the server is running for detailed endpoint usage.

---

## README for Developers

We are going to use the LLM to scan the API endpoint and generate the code automatically. We are then going to apply a patch from the last known working version and work through the breaks.

We'll keep previous LLM generated code in a separate branch for reference to ensure benchmarking is correct.

#### **Development Guidelines**
- **Structure**: The project uses FastAPI with dependencies managed via `pyproject.toml` or `requirements.txt`.
- **Logging**: Logging configurations are stored in `logging_config.py`. Ensure logs are clear and do not include sensitive information.
- **Testing**: Use `pytest` for writing and running tests. Mocking is encouraged for external services like Milvus and Pi-hole.

##### **Code Contribution**
1. **Fork the Repository:**
   ```sh
   git clone [your fork]
   ```

2. **Setup & Develop:**
   - Follow the installation guide above to set up your development environment.
   - Before committing:
     - Run tests:
       ```sh
       pytest
       ```
     - Ensure code style with linters (`flake8`, `mypy`, `black`, `isort`).

3. **Submit Pull Requests:**
   - Push changes to your fork, then open a pull request against the main branch.

##### **Error Handling**
- Customize and implement exception handlers for common errors like `PiholeConnectionError` or `RagIntentNotFoundError`.

##### **Documentation**
- Update `README.md` for changes in functionality or dependencies.
- Keep `todo.md` current with your development tasks.

---

### Build Policy Using LLM and Patches

**Overview:**
- We use an LLM (Language Model) to generate the initial codebase or provide solutions to new features or bug fixes, which is then refined through manual code review and patch application.

**Process:**
1. Start up pihole in the containers directory
2. ```cd prompts/; ./run_plan.sh```
3. Start new branch to compare gameplan.md for material differences
4. Use gameplan.md to generate the individual prompts for aider.md
6. Use aider to generate code for specific features or issues based on gameplan.md
7. Work the diff between the code generated and the previous llm version
8. Apply the patches from "Working" to clean up the mess
9. $$$$ profit

1. **Integration Testing:**
   - Ensure the new code works as expected by running full integration tests.

1. **Documentation Update:**
   - Document the new feature, fix, or changes, updating both user and developer documentation.

**Policy Notes:**
- Never directly commit LLM generated code without human review.
- Maintain a log of generated code sources for traceability.
- Prioritize security and efficiency when reviewing and patching LLM-generated code.
