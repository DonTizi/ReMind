# reMind - Your Local Artificial Memory Assistant

Welcome to reMind! This application captures and indexes your digital activities, transcribing and summarizing them for easy recall. reMind uses advanced AI models to provide detailed summaries of your daily activities and to answer questions based on your digital history. It is at its first version, a more optimal and runnable version will be uploaded in mid-June 2024.

##  I just created a Discord server to allow everyone to communicate and have a better option to discuss changes with everyone. [Join the server here](https://discord.gg/fVDXVyeR).

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Capture Digital Activities**: Records screenshots, audio, and other digital activities.
- **Text Transcription**: Transcribes text from captured screenshots.
- **Indexing**: Uses vector databases to index and retrieve documents.
- **Summarization**: Provides detailed summaries of daily activities.
- **Interactive Chat**: Interact with the application using a chat interface to query your digital history.

## Installation

To get started with reMind, follow these steps:

1. **Clone the Repository**
    ```sh
    git clone https://github.com/DonTizi/reMind.git
    cd reMind
    ```
    
2. **Install Ollama**
    Download and install Ollama from [here](https://ollama.com/download/Ollama-darwin.zip).


3. **Install the Remind Application**
    Download and install the Remind application from [here](https://www.recallmemory.io/download).


4. **Run the Installer Script**
    To perform the installation, run the following command in the directory of the cloned repository:
    ```sh
    python installer.py
    ```

## Usage


1. **Launch the RemindEnchanted Background Service**
    In the terminal, run the command:
    ```sh
    remindbg start
    ```

2. **Interact with the Application**
    Launch the Remind application to ask questions about your digital activity. Please wait for about 20-30 minutes the first time to allow the application to gather digital activities into its vector database.


## Contributing

We welcome contributions from the community! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a pull request.

## License

This project is licensed under the apache-2.0 License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, please open an issue in the GitHub repository or contact me at [elyes.melbouci@gmail.com](mailto:elyes.melbouci@gmail.com).

---

Thank you for using reMind! We hope it helps you manage and recall your digital activities effortlessly. By making reMind open-source, we aim to foster a collaborative environment where developers can contribute to and improve this innovative application. Happy coding!
