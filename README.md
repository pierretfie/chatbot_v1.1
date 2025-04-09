# TinyLlama Voice Chatbot

A voice-enabled chatbot using TinyLlama and Piper text-to-speech.

## Features

- Voice interaction using Piper text-to-speech
- GPU-accelerated inference with TinyLlama
- Resource management for optimal performance
- Modular architecture for easy maintenance

## Requirements

- Python 3.8+
- CUDA-capable GPU (recommended)
- Piper text-to-speech engine
- TinyLlama model (1.1B parameters)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tinyllama-voice-chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Piper text-to-speech:
- Follow instructions at https://github.com/rhasspy/piper-tts
- Place Piper models in `~/piper_models/`

4. Download TinyLlama model:
- Place the model at `~/tinyllama/tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf`

## Usage

Run the chatbot:
```bash
python main.py
```

## Project Structure

```
tinyllama-voice-chatbot/
├── main.py                 # Main chatbot script
├── modules/
│   ├── brain.py           # Reasoning module
│   ├── resource_manager.py # Resource management
│   ├── gpu_manager.py     # GPU management
│   └── prompt_template.py # Prompt templates
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Configuration

Adjust paths in `main.py`:
- `piper_dir`: Path to Piper executable
- `model_path`: Path to Piper model
- `tinyllama_path`: Path to TinyLlama model

## License

MIT License 