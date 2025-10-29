# LightCrew OpenAI Minimal Demo

A minimal example that uses the LightCrew framework to call OpenAI and answer a simple user query.

## Prerequisites

- Python 3.8+
- An OpenAI API key with access to the chosen model

## Install

```
pip install -r showcases/openai_minimal/requirements.txt
```

## Set API key

Export your API key (recommended):

- macOS/Linux:
  - `export OPENAI_API_KEY=your_key_here`
- Windows (PowerShell):
  - `$Env:OPENAI_API_KEY = "your_key_here"`

Alternatively, pass `--api-key` flag to the script.

## Run

- One-off query:
```
python showcases/openai_minimal/main.py --query "What is the capital of France?" --model gpt-4o-mini
```

- Interactive mode:
```
python showcases/openai_minimal/main.py --interactive --model gpt-4o-mini
```

Notes:
- The script uses the LightCrew `Agent`, `Task`, and `Crew` to orchestrate a single OpenAI call.
- The model defaults to `gpt-4o-mini`; you can change with `--model`.
- If `--api-key` is omitted, the script uses `OPENAI_API_KEY` from the environment.
