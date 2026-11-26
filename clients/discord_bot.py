import asyncio
import os

import discord

from bank import ask_bank


def main():
    allowed_channel = int(os.environ["DISCORD_ALLOWED_CHANNEL_ID"])
    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Client(intents=intents, allowed_mentions=discord.AllowedMentions.none())
    pending = asyncio.Semaphore(1)

    @bot.event
    async def on_message(message):
        if (message.author.bot or message.channel.id != allowed_channel
                or not message.content.startswith("!bank ")):
            return
        async with pending:
            answer = await asyncio.to_thread(ask_bank, message.content.removeprefix("!bank "))
            await message.reply(answer[:1900], mention_author=False)

    bot.run(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    main()
