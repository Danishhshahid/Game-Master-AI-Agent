
# 🎮 Fantasy Adventure Game

A multi-agent, text-based fantasy adventure game built with Python, LiteLLM, Google's Gemini 1.5 Flash model, and Chainlit for an interactive web interface.

## ✨ Features

- **Dynamic Storytelling**: The game's narrative is driven by AI, creating unique and immersive experiences.
- **Multi-Agent System**: Different AI agents (Story, Combat, Item) manage various aspects of the game.
- **Interactive Web Interface**: Powered by Chainlit, providing a rich chat-based gameplay experience.
- **Player Customization**: Players can input custom prompts to influence the AI's responses.
- **Dice Rolling Mechanic**: Incorporates a 20-sided dice roll for combat and item discovery.
- **Inventory & Health Management**: Tracks player's health and inventory throughout the adventure.

## 🚀 Getting Started

### Prerequisites

Before running the game, ensure you have the following installed:

- Python 3.9+
- `uv` (or `pip` for package management)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/danishhshahid/Game-Master-AI-Agent.git
    cd Game-Master-Agent
    ```

2.  **Install dependencies using `uv`:**

    ```bash
    uv sync
    ```

    *Alternatively, using `pip` (if `uv` is not installed):*

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your Google API Key:**

    The game uses Google's Gemini 1.5 Flash model. You need to obtain an API key from Google AI Studio.

    Set your API key as an environment variable:

    ```bash
    export GOOGLE_API_KEY='YOUR_API_KEY'
    # For Windows (Command Prompt):
    # set GOOGLE_API_KEY=YOUR_API_KEY
    # For Windows (PowerShell):
    # $env:GOOGLE_API_KEY='YOUR_API_KEY'
    ```

    Replace `YOUR_API_KEY` with your actual Google API Key.

### Running the Game

To start the game, run the `app.py` file using Chainlit:

```bash
chainlit run app.py -w
```

This will open the Chainlit web interface in your browser, where you can start playing.

## 🎮 How to Play

Once the Chainlit interface is open:

-   Type your actions naturally (e.g., "I explore the forest", "I attack the goblin").
-   The AI will respond, guiding you through the story.

### Special Commands

-   **`status`**: Show your current health and inventory.
-   **`history`**: See recent conversation history.
-   **`restart`**: Start a new game.
-   **`prompt: your message`**: Send a custom prompt directly to the AI to influence its response.

## 📁 Project Structure

-   `app.py`: The main application logic, containing the game engine and AI agent definitions.
-   `main.py`: (Optional) Can be used for additional scripts or local testing.
-   `chainlit.md`: Chainlit-specific markdown for welcome messages or UI elements.
-   `pyproject.toml`: Project metadata and dependencies (for `uv`).
-   `uv.lock`: Locked dependencies for reproducible builds (`uv`).
-   `README.md`: This file.