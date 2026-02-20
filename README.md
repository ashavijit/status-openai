# status-openai

Monitor status feeds with ETag support.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.json` to add feeds and set check interval (seconds):

```json
{
    "check_interval": 60,
    "feeds": {
        "OpenAI": "https://status.openai.com/history.rss"
    }
}
```

## Usage

```bash
python status.py
```

The script polls feeds and prints updates to stdout.
