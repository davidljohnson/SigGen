# SigGen

## Overview
SigGen is a tool designed create Sigma rules dynamically from provided attack procedures extracted from given text or URLs pointing to threat intelligence reports. It allows users to select specific procedures to generate Sigma rules for intrusion detection. SigGen utilizes RAG (Retrieval-Augmented Generation) to draw examples from the SigmaHQ repository and uses models from both Anthropic and OpenAI to enhance rule generation.

## Prerequisites
Before running SigGen, users must ensure the following prerequisites are met:
- Docker and Docker Compose are installed on your machine.
- Clone or download this repository to your local machine.
- Obtain API keys from Anthropic and OpenAI.

## To Do List
- Local LLM capabilities and improved modularity for different APIs
- Configuration settings for desired log coverage
- Add a QA step to check on the quality of the generated Sigma rule
- Option to mix and match selected procedures to a single Sigma rule (rather that creating seperate ones)
- Ability to add API keys and manage models via the UI
- Local storage of created Sigma rules

## Installation
1. **API Keys Configuration**:
   - Create a `.env` file in the top-level directory (where the `docker-compose.yml` file resides).
   - Add your Anthropic and OpenAI API keys to the `.env` file:
     ```
     OPENAI_API_KEY=<your_openai_api_key_here>
     ANTHROPIC_API_KEY=<your_anthropic_api_key_here>
     ```

2. **Update Sigma Rules**:
   - Ensure the `update_sigma_rules.sh` script has execution privileges:
     ```bash
     chmod +x update_sigma_rules.sh
     ```
   - Run the `update_sigma_rules.sh` script to download and prepare the Sigma rules:
     ```bash
     ./update_sigma_rules.sh
     ```

3. **Build and Run Containers**:
   - Navigate to the directory containing the `docker-compose.yml` file.
   - Build and start the containers using Docker Compose:
     ```bash
     docker-compose up --build
     ```

## Usage
Once the application is running, access the SigGen interface by navigating to:
- **Frontend URL**: [http://localhost:3000](http://localhost:3000)

From the interface:
- **Extract Procedures**: Enter the text or URL of the threat intelligence report and click "Extract" to retrieve potential attack procedures.
- **Generate Sigma Rules**: Select the procedures for which you want Sigma rules generated, and then submit them for processing.

## Troubleshooting
- If you encounter issues related to network errors or access to APIs, ensure that your API keys are correct and that your internet connection is stable.
- For problems with Docker containers, ensure Docker is running properly on your machine and check the container logs for specific error messages:
  ```bash
  docker logs <container_name>
  ```