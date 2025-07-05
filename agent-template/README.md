# Agent Template

This project serves as a template for creating sophisticated AI agents using a modern Python stack. It's designed to be highly modular and extensible, allowing developers (and other AIs) to quickly build new agents by following the established patterns.

The core philosophy of this template is the separation of concerns into distinct components: **flows**, **tasks**, and **prompts**. This structure promotes code reuse, simplifies testing, and makes the agent's logic easy to follow.

## Key Technologies

- **Python 3.8+**: The foundation of the project.
- **`uv`**: A fast and modern Python package manager, used for dependency management.
- **`taskman`**: A custom library for orchestrating complex, asynchronous workflows (`flows`) composed of individual, retriable `tasks`.
- **`pydantic`**: For robust data validation and settings management.
- **`logging`**: Python's standard library for flexible event logging.
- **`python-dotenv`**: To manage environment variables for configuration.
- **Jinja2**: For templating prompts, allowing for dynamic content.
- **Asyncio**: Leveraged extensively for high-performance, concurrent task execution.

## Project Structure

The project is organized into the following key directories:

```
agent_template/
├── agent_template/
│   ├── __init__.py         # Initializes the package and TEMPLATES object
│   ├── main.py             # Main entry point for the application
│   ├── flows/
│   │   └── main_flow.py    # Orchestrates the execution of tasks
│   ├── tasks/
│   │   ├── geography_expert.py # Example task: Generates content
│   │   └── world_classifier.py # Example task: Classifies content
│   └── prompts/
│       ├── geography_expert_system.md  # System prompt for the expert
│       ├── geography_expert_user.j2    # User prompt for the expert (Jinja2)
│       ├── ...
├── pyproject.toml          # Project metadata and dependencies
├── .env.example            # Example environment variables
└── README.md               # This file
```

### Core Components

#### 1. `main.py`
This is the application's entry point. Its responsibilities include:
- Loading environment variables from a `.env` file.
- Setting up structured logging and caching directories, organized by a unique `run_id`.
- Initiating the main asynchronous workflow (`main_flow`).

#### 2. Flows (`flows/`)
Flows are high-level functions that define the overall logic of the agent. They orchestrate the execution of one or more tasks to achieve a larger goal.
- They are decorated with `@flow` from the `taskman` library. This decorator designates the function as a primary workflow, which can be important for logging, tracing, and overall organization. It clearly marks the starting point of the agent's business logic.
- They are asynchronous (`async def`).
- The primary flow is `main_flow` in `flows/main_flow.py`, which demonstrates how to run multiple task pipelines in parallel using `asyncio.gather`.

#### 3. Tasks (`tasks/`)
Tasks are the atomic units of work in the agent. Each task is a self-contained function responsible for a single, specific operation.
- They are decorated with `@task` from the `taskman` library. This is a powerful decorator that provides several key features for building robust applications.
- They are also asynchronous (`async def`).
- Tasks interact with AI models (e.g., `chat_completions` from the `models` library) to perform their function.
- They load their corresponding prompts from the central `TEMPLATES` object.

#### 4. Prompts (`prompts/`)
This directory holds all the prompts for the AI models, separating the prompt engineering from the application logic.
- **System Prompts**: Usually static Markdown files (`.md`) that define the AI's role, personality, and high-level instructions.
- **User Prompts**: Often Jinja2 templates (`.j2`) that allow for dynamic data to be inserted into the prompt at runtime.

### `__init__.py` and Template Loading
The `agent_template/__init__.py` file is crucial for making prompts easily accessible throughout the application. It creates a `Jinja2` Environment and a `TEMPLATES` object that scans the `prompts/` directory, making any `.md` or `.j2` file available via `TEMPLATES.get_template("filename")`.

## Core Concepts and Framework Features

This template is built on a set of conventions and tools provided by the `taskman` and `models` libraries that simplify the development of complex agents.

### The `@task` Decorator
The `@task` decorator is the workhorse of this framework. It accepts several parameters to control its behavior:

-   `retries` (e.g., `retries=8`): Makes the task resilient. If the task fails (e.g., due to a network error or a temporary API outage), it will be automatically retried the specified number of times.
-   `retry_delay_seconds` (e.g., `retry_delay_seconds=exponential_backoff`): Controls the delay between retries. Using a function like `exponential_backoff` from `models.tools` is a best practice, as it gradually increases the delay, preventing the service from being overwhelmed.
-   `cache_on` (e.g., `cache_on=("arg1", "arg2")`): A powerful feature for efficiency and cost-saving. It caches the task's return value. If the task is called again with the exact same values for the arguments specified in the tuple, the cached result is returned instantly, skipping the task's execution. This is ideal for deterministic tasks and significantly speeds up development and testing.

### Asynchronous Logging with `append_log`
In an `asyncio` environment, standard logging can be tricky. The `taskman` library provides `append_log`, an asynchronous function that safely writes logs to a file. 
-   Logs are automatically directed to a file corresponding to the `run_id` established in `main.py`. This isolates logs from concurrent runs and makes debugging parallel pipelines much easier.
-   It's essential for logging detailed information, such as the exact prompts sent to a model and the raw responses received, which is invaluable for debugging and fine-tuning the agent's behavior.

### The `DRY_RUN` Convention
The `DRY_RUN` environment variable is a critical feature for development and testing.
-   **Purpose**: To test the entire application logic—including prompt generation, data transformations, and workflow orchestration—without making expensive and time-consuming calls to external AI models.
-   **Correct Implementation**: A `DRY_RUN` should **only** mock the external dependency (e.g., the `chat_completions` call). It should not bypass the rest of the task's logic. This ensures that the test run is as close to a real run as possible, verifying that prompts are built correctly and data is processed as expected. The task should still log its mocked request and response, maintaining full observability.

## How to Use This Template

1.  **Copy the Directory**: Copy the entire `agent_template` directory to a new location and rename it for your new project (e.g., `my_new_agent`).

2.  **Update `pyproject.toml`**: Change the `name` of the project inside `pyproject.toml` to match your new directory name.

3.  **Define Your Tasks**:
    -   Create new Python files in the `tasks/` directory for each new task your agent needs.
    -   Define your task function using the `@task` decorator and `async def`.
    -   Implement the logic, which will likely involve calling an AI model.

4.  **Create Your Prompts**:
    -   Add new system (`.md`) and user (`.j2`) prompts to the `prompts/` directory for your new tasks.

5.  **Build Your Flow**:
    -   Modify `flows/main_flow.py` (or create new flow files) to orchestrate your new tasks. Define the sequence or parallel execution logic that fits your agent's purpose.

6.  **Set Environment Variables**:
    -   Copy `.env.example` to a new `.env` file.
    -   Fill in the required environment variables. The most important are:
        -   `DRY_RUN=1`: As explained above, this is excellent for testing your flow logic without incurring API costs.
        -   `LOG_LEVEL`: Sets the application's logging verbosity. Can be `DEBUG`, `INFO`, `WARNING`, or `ERROR`.

7.  **Run the Agent**:
    -   Execute the `main.py` file to run your new agent: `python -m your_new_agent.main`.

By following this structure, you can rapidly develop new agents that are robust, maintainable, and built on a foundation of best practices.
