# discord-play-renamer

A small Discord bot that watches a specific text channel, deletes plain YouTube links, and reposts them prefixed with a configurable command (default `!p`) to trigger a music bot.

## Features
- Accepts only bare YouTube links (`https://www.youtube.com/watch?v=...` or `https://youtu.be/...`).
- Ignores messages with extra text, multiple links, or non-YouTube URLs.
- Optional deletion of the triggering message (requires the **Manage Messages** permission).
- Configurable channel ID, command prefix, cooldown, and deletion behavior via environment variables.
- Logging for key actions and failure cases.

## Configuration
Set the following environment variables before running the bot:

| Variable | Required | Description | Default |
| --- | --- | --- | --- |
| `DISCORD_TOKEN` | Yes | Bot token from the Discord developer portal. | — |
| `REPOST_CHANNEL_ID` | Yes | ID of the text channel to monitor. | — |
| `COMMAND_PREFIX` | No | Prefix used when reposting the link. | `!p` |
| `DELETE_ORIGINAL` | No | Delete the triggering message (`true`/`false`). | `true` |
| `COOLDOWN_SECONDS` | No | Minimum seconds between reposts to reduce spam. | `0` (disabled) |

> The bot requires the **Message Content Intent** and, if `DELETE_ORIGINAL=true`, the **Manage Messages** permission in the target channel.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running
```bash
export DISCORD_TOKEN="<your token>"
export REPOST_CHANNEL_ID="<channel id>"
# Optional overrides:
# export COMMAND_PREFIX="!p"
# export DELETE_ORIGINAL="true"
# export COOLDOWN_SECONDS="2"
python bot.py
```

## How it works
- The bot listens to `on_message` events in the configured channel and ignores all bot users.
- Incoming content is trimmed and validated against the YouTube regex:
  - `^(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}(?:[^\s]*)|https?://youtu\.be/[\w-]{11}(?:[^\s]*)?)$`
- If it matches and doesn't already start with the command prefix, the bot reposts it as `<COMMAND_PREFIX> <original_link>`.
- When enabled and permitted, the original message is deleted after reposting. Cooldowns (if configured) skip reposting when triggered too quickly.
