# TinyGen

TinyGen is a FastAPI application that leverages OpenAI's API to generate code modifications based on a given codebase and prompt. It can clone Git repositories, analyze their content, and propose changes.

## Development Setup

To set up TinyGen for local development, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd tinygen
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set your OpenAI API Key:**
    Ensure you have your OpenAI API key set as an environment variable named `OPENAI_API_KEY`.
    ```bash
    export OPENAI_API_KEY="your_openai_api_key_here"
    ```
    (Replace `"your_openai_api_key_here"` with your actual key.)

5.  **Set your Supabase Credentials (Optional):**
    If you are using Supabase, set your URL and public `anon` key as environment variables.
    ```bash
    export SUPABASE_URL="your_supabase_url_here"
    export SUPABASE_KEY="your_supabase_anon_key_here"
    ```

6.  **Run the application with auto-reload:**
    ```bash
    python3 main.py
    ```
    The application will run on `http://0.0.0.0:8000` (or `http://127.0.0.1:8000`). The `reload=True` option in `main.py` ensures that the server restarts automatically on code changes.

## Deployment with Docker

For deployment, you can use the provided Docker image.

1.  **Build the Docker image:**
    Navigate to the root directory of the project where the `Dockerfile` is located and run:
    ```bash
    docker build -t tinygen:latest .
    ```

2.  **Run the Docker container:**
    When running the container, you must provide your environment variables using the `-e` option. Map the container's port 8000 to a desired host port (e.g., 8080).

    ```bash
    docker run -d -p 8080:8000 \
      -e OPENAI_API_KEY="your_openai_api_key_here" \
      -e SUPABASE_URL="your_supabase_url_here" \
      -e SUPABASE_KEY="your_supabase_anon_key_here" \
      tinygen:latest
    ```
    (Replace the placeholder values with your actual credentials.)

    This command will:
    *   `-d`: Run the container in detached mode (in the background).
    *   `-p 8080:8000`: Map port 8080 on your host to port 8000 inside the container.
    *   `-e VARIABLE="value"`: Pass your OpenAI API key and optional Supabase credentials as environment variables to the container.
    *   `tinygen:latest`: Specify the name and tag of the Docker image to use.

The application will then be accessible on `http://localhost:8080` (or your host's IP address on port 8080).
