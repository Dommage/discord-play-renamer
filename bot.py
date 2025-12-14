"""
Discord bot that reposts YouTube links with a play prefix.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from typing import Optional

import discord

# Configuration loading
TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = os.environ.get("REPOST_CHANNEL_ID")
COMMAND_PREFIX = os.environ.get("COMMAND_PREFIX", "!p").strip()
DELETE_ORIGINAL = os.environ.get("DELETE_ORIGINAL", "true").lower() in {"1", "true", "yes", "on"}
COOLDOWN_SECONDS = float(os.environ.get("COOLDOWN_SECONDS", "0"))

if CHANNEL_ID is None:
    raise ValueError("REPOST_CHANNEL_ID environment variable must be set.")

CHANNEL_ID = int(CHANNEL_ID)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable must be set.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("reposter")

# Regex to validate YouTube links that occupy the full message.
YOUTUBE_REGEX = re.compile(
    r"^(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}(?:[^\s]*)|https?://youtu\.be/[\w-]{11}(?:[^\s]*)?)$",
    re.IGNORECASE,
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

_last_processed: Optional[float] = None


def is_valid_youtube_link(content: str) -> bool:
    """Return True if the trimmed content is a single accepted YouTube URL."""
    return bool(YOUTUBE_REGEX.match(content))


async def handle_deletion(message: discord.Message) -> None:
    """Delete the triggering message if configured and permissions allow it."""
    if not DELETE_ORIGINAL:
        return

    if message.guild is None:
        logger.info("Skipping deletion because message is not in a guild.")
        return

    me = message.guild.me
    if me is None:
        logger.info("Skipping deletion because bot member could not be determined.")
        return

    permissions = message.channel.permissions_for(me)
    if not permissions.manage_messages:
        logger.warning("Missing 'Manage Messages' permission; cannot delete original message.")
        return

    try:
        await message.delete()
        logger.info("Deleted original message after reposting.")
    except discord.DiscordException as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to delete message: %s", exc)


@client.event
async def on_ready():
    logger.info("Logged in as %s (ID: %s)", client.user, client.user.id if client.user else "unknown")
    logger.info("Monitoring channel ID %s", CHANNEL_ID)


@client.event
async def on_message(message: discord.Message):
    # Ignore bots (including ourselves).
    if message.author.bot:
        return

    # Enforce channel scoping.
    if message.channel.id != CHANNEL_ID:
        return

    trimmed_content = message.content.strip()

    # Prevent loops if someone manually posts the command prefix.
    if trimmed_content.startswith(COMMAND_PREFIX):
        return

    if not is_valid_youtube_link(trimmed_content):
        return

    global _last_processed
    now = time.monotonic()
    if COOLDOWN_SECONDS > 0 and _last_processed is not None:
        elapsed = now - _last_processed
        if elapsed < COOLDOWN_SECONDS:
            logger.info("Ignoring message due to cooldown (%.2fs remaining)", COOLDOWN_SECONDS - elapsed)
            return

    repost = f"{COMMAND_PREFIX} {trimmed_content}"
    try:
        await message.channel.send(repost)
        logger.info("Reposted link with prefix in #%s", getattr(message.channel, "name", message.channel.id))
        _last_processed = now
        await handle_deletion(message)
    except discord.DiscordException as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to repost message: %s", exc)


def main():
    client.run(TOKEN)


if __name__ == "__main__":
    main()
