# Writing Style Emulation

## Setup

(From inside cloned directory)
```bash
python3 -m venv venv
source venv/bin/activate 
pip install -r requirements.txt
```

Then make a .env file and add your Claude API key as `CLAUDE_API_KEY=<your_api_key>`.


## Use

```bash
python pipeline.py
```

The script will guide you through the process of selecting files to construct the prompt.

## Examples

You can see examples of generations based on Scott Alexander's "Every Bay Area House Party" series in the `examples/scott` directory. `ai_company_all_hands` uses the same conditioning texts but prompts the model to write about a fictional AI company all hands meeting.