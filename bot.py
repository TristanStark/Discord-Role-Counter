import logging
import os
from collections.abc import Iterable

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path


def _parse_guild_ids(raw: str | None) -> Iterable[int]:
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


ROLE_TRACKED = "553529330488049665"


def update_html(modification: int) -> None:
    """Met à jour le fichier HTML avec le nouveau nombre de modifications."""
    try:
        path = Path("index.html")
        text = path.read_text(encoding="utf-8")
        first_position = text.find("<span id=\"goal-current\">") + len("<span id=\"goal-current\">")
        last_position = text.find("</span>", first_position)
        current_value = int(text[first_position:last_position])
        new_text = f"{text[:first_position]}{current_value + modification}{text[last_position:]}"
        path.write_text(new_text, encoding="utf-8")

    except Exception as e:
        logging.getLogger(__name__).exception("Erreur lors de la mise à jour du fichier HTML : %s", e)



def create_bot() -> commands.Bot:

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
    logger = logging.getLogger(__name__)


    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix="!", intents=intents)


    guild_ids = _parse_guild_ids(os.getenv("GUILD_IDS"))


    @bot.event
    async def on_ready():
        logger.info("✅ Connecté en tant que %s", bot.user)
        try:
            if guild_ids:
                synced = []
                for gid in guild_ids:
                    g = discord.Object(id=gid)
                    synced.extend(await bot.tree.sync(guild=g))
            else:
                synced = await bot.tree.sync()
                logger.info("✅ %d commandes slash synchronisées.", len(synced))
        except Exception as e: # noqa: BLE001
            logger.exception("[ERROR] Erreur de sync : %s", e)


    @bot.event
    async def on_member_update(before: discord.Member, after: discord.Member):
        """Changement sur un membre."""
        
        roles_before = set(before.roles)
        roles_after = set(after.roles)

        # Unique
        added = roles_after - roles_before
        removed = roles_before - roles_after

        # Rien n'a changé sur les roles
        if not added and not removed:
            return

        # Send messages
        if added:
            for role in added:
                if role.id == int(ROLE_TRACKED):
                    update_html(+1)
                    return
        
        if removed:
            for role in removed:
                if role.id == int(ROLE_TRACKED):
                    update_html(-1)
                    return
    return bot




def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN manquant (voir .env.example)")

    bot = create_bot()
    bot.run(token)




if __name__ == "__main__":
    main()
