# Notification Processing System

A modular, in-memory notification processing engine built in Python. This system orchestrates the delivery of messages across multiple channels, utilizing customizable retry strategies and dynamic object instantiation.

## System Architecture

*   **Processor:** The central orchestrator that manages the notification lifecycle and delegates execution protocols.
*   **Notification Factory:** Dynamically instantiates the appropriate communication channels (Email, SMS, Push) based on the incoming request payload.
*   **Retry Strategies:** Encapsulates failure-handling logic (e.g., `FixedRetry`) to gracefully manage transient delivery errors without polluting the core processor logic.
*   **Notification Repository:** An in-memory data store that maintains delivery states, records attempt counts, and logs failure reasons.
*   **Channels:** Concrete implementations of the notification mediums, adhering to a common foundational interface.

## Setup and Testing

This project utilizes a virtual environment for dependency management and `pytest` for executing the test suite.

1. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate