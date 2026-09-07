# Home Assistant (HA) YAML Linter

A simple, foolproof, and visual YAML linter designed specifically for Home Assistant configuration files. 

Home Assistant configurations frequently use modular split files with custom YAML tags (e.g., `!include`, `!secret`). Standard YAML linters often fail to parse these tags or offer cryptic, unhelpful errors when indentation is off. This tool specializes in detecting, explaining, and suggesting "most likely" fixes for indentation issues (the #1 source of HA configuration headaches) and provides multiple ways to ingest files (CLI, stdin, and a clean Web UI).

## Core Features

- **HA-Specific Parsing:** Native support for Home Assistant custom tags (`!include`, `!secret`, `!include_dir_list`, etc.) so the parser never chokes on valid HA configurations.
- **Definitive Indentation Analyzer:** A robust, first-pass indentation engine that identifies inconsistent indentation levels, mismatched list markers (`-`), and incorrectly aligned dictionary blocks.
- **Mixed Style Detection & Auto-Unification:** Automatically detects if a file mixes sequence indentation styles (Compact vs. Nested) and offers one-click or command-line auto-unification options to make formatting 100% consistent.
- **Interactive Style Warning Panel:** Web UI automatically highlights mixed styles with an amber alert and offers instant one-click unification options.
- **"Download Tidied File" Button:** Safely download your fully repaired or unified YAML configuration file directly from the browser, retaining the original uploaded file name (e.g., `test.yaml`).
- **Smart "Most Likely" Fix Suggestions:** Instead of just reporting a syntax error, the linter analyzes surrounding lines to suggest the exact column adjustment required.
- **Flexible Ingestion:**
  - **CLI File Input:** Check local files.
  - **Standard Input (stdin):** Easily pipe or paste copied snippets.
  - **Web Frontend:** A lightweight, visual web interface featuring synchronized line numbers, drag-and-drop file upload, real-time error highlighting, and smart one-click auto-fixes.

## Technology Stack

- **Backend:** Python 3 with a lightweight web framework (Flask) and `ruamel.yaml` (selected for native YAML 1.2 support, comment/formatting preservation, and precise line/column tracking for indentation analysis).
- **Frontend (Web UI):** Clean, modern, vanilla HTML/CSS/JS with a visual code editor/highlighting interface.

## Installation & Getting Started

### 🚀 1. Install as a Home Assistant OS App / Add-on (Recommended)

> 💡 **Note:** Recent Home Assistant updates refer to add-ons as **"Apps"** inside the store and Supervisor logs. This linter is fully compatible with both the traditional Add-ons store and the new Apps terminology.

You can run this linter securely and locally on your Raspberry Pi or Home Assistant device with **zero performance impact**. It embeds directly as an option in your Home Assistant left sidebar right next to your dashboards!

1. In Home Assistant, navigate to **Settings** > **Add-ons** (or **Apps**).
2. Click **Add-on Store** (or **Apps Store**) in the bottom right corner.
3. Click the **three dots** in the top-right corner and select **Repositories**.
4. Paste the URL of this repository:
   ```
   https://github.com/thatguyinoz/ha-yaml-linter
   ```
   and click **Add**.
5. Close the popup. The store will automatically refresh.
6. Scroll down or search for **"ha-yaml-linter"** and select **HA YAML Indentation Linter**.
7. Click **Install** (or **Install App**).
8. Once installed, toggle **"Show in sidebar"** and click **Start**!

---

### 💻 2. Manual/Developer Installation (Local Machine)

#### Prerequisites
- Python 3.11+
- On Debian/Ubuntu systems, if you encounter virtual environment setup issues due to a missing system `ensurepip` package, use the manual bootstrapping steps below.

#### Manual Installation & Setup
To set up the project environment and install dependencies:

```bash
# Create the virtual environment (bypassing missing ensurepip)
python3 -m venv --without-pip .venv

# Bootstrap pip securely
python3 -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', 'get-pip.py')"
.venv/bin/python3 get-pip.py
rm get-pip.py

# Install dependencies
.venv/bin/pip install -r requirements.txt
```

### 3. Activating the Virtual Environment
To work with the virtual environment, activate it in your terminal:
```bash
source .venv/bin/activate
```

### 4. Running the Linter
Once the environment is configured and active, you can run the linter components:

#### Running Tests
To run the automated test suite and verify the installation:
```bash
PYTHONPATH=. pytest
```

#### CLI Linter
Validate any local YAML file:
```bash
python3 -m src.cli path/to/your/file.yaml
```

#### Web Interface
Launch the lightweight web application:
```bash
python3 -m src.server
```
Once started, open your browser and navigate to `http://localhost:5000` (or `http://<your-server-ip>:5000`).

---

## File Ingestion & Validation Workflows

This linter provides three foolproof mechanisms to load and validate Home Assistant configuration files:

### 1. User Copied (Clipboard Copy-Paste)
Perfect for quick, ad-hoc checks of single automations, scripts, or configuration snippets.
*   **Via Web Interface:** Open the web UI, paste the copied YAML snippet directly into the **YAML Source Editor**, and click **Validate Configuration**. If there's an error, click the green **Click to Auto-Fix Indentation** button to apply the suggestion instantly.
*   **Via Terminal CLI (stdin):** You can run the CLI without any arguments. It will wait for your clipboard paste:
    ```bash
    python3 -m src.cli
    ```
    Paste your YAML directly into the terminal window, then press `Ctrl+D` (on Linux/macOS) or `Ctrl+Z` then `Enter` (on Windows) to run the analysis instantly.

### 2. SCP Copied (Remote Linter Server)
Ideal if you are working on a local workstation but want to validate configuration files directly on your remote Home Assistant server.
*   Copy your configuration file to the machine hosting the linter via secure copy:
    ```bash
    scp path/to/local/configuration.yaml user@your-server-ip:/path/to/linter-folder/file.yaml
    ```
*   SSH into your server and run the CLI against the copied file:
    ```bash
    python3 -m src.cli /path/to/linter-folder/file.yaml
    ```

### 3. Web Front End File Ingestion
Perfect for uploading entire configuration files or modular files (e.g., `automations.yaml`, `sensors.yaml`) directly from a web browser.
*   Open the web interface in your browser.
*   Drag any `.yaml` or `.yml` file from your local file explorer and drop it onto the **Drag & Drop Zone** at the top of the editor.
*   The file will be read instantly, populated in the editor, and validated automatically with clear visual carets highlighting any mistakes.
