# Cog Stuff
import logging
from collections import defaultdict
from typing import Optional

from aadiscordbot.cogs.utils.decorators import is_admin
from aadiscordbot.tasks import send_channel_message_by_discord_id
from allianceauth.eveonline.evelinks import dotlan
from allianceauth.services.modules.discord.models import DiscordUser
from discord import (AutocompleteContext, ButtonStyle, Embed, Interaction,
                     SlashCommandGroup, option, ui)
from discord.embeds import Embed
from discord.ext import commands
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rapidfuzz import fuzz, process

from .. import app_settings, models, tasks

logger = logging.getLogger(__name__)

BLUE = 0x3498db
MAGENTA = 0xe91e63
GREYPLE = 0x99aab5
RED = 0x992d22


class ESSView(ui.View):
    embed_text = None
    created = None

    def __init__(self,
                 *items: ui.Item,
                 found_by_uid: int = 0,
                 found_by: str = "",
                 system: str = "",
                 timeout: Optional[float] = 60*60*24,  # 24h from last click
                 embed: Optional[Embed] = None,
                 bot=None
                 ):
        if embed:
            if isinstance(embed, dict):
                self.embed_text = Embed.from_dict(embed)
            elif isinstance(embed, Embed):
                self.embed_text = embed
        self.bot = bot
        self.created = timezone.now()
        super().__init__(*items, timeout=timeout)
        logger.debug(self.id)

    @ui.button(label="FC Claim", style=ButtonStyle.blurple)
    async def claim(self, button: ui.Button, interaction: Interaction):
        logger.debug(self.id)
        view = self
        view.children[0].disabled = True
        message = f"{interaction.user.nick if interaction.user.nick else interaction.user.name}"
        embed = interaction.message.embeds[0]
        embed.color = MAGENTA
        embed.add_field(name="Claimed By", value=message, inline=False)

        await interaction.response.edit_message(embed=embed, view=view)

    @ui.button(label="Safe", style=ButtonStyle.success)
    async def run(self, button: ui.Button, interaction: Interaction):
        logger.debug(self.id)
        message = f"{interaction.user.nick if interaction.user.nick else interaction.user.name}"
        embed = interaction.message.embeds[0]
        embed.color = GREYPLE
        embed.add_field(name="Declared Safe by", value=message, inline=False)
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self) -> None:
        print(vars(self))
        await super().on_timeout()


class EssLinks(commands.Cog):
    Systems = []  # load strings on startup of bot.

    """
    Ess Notify
    """

    async def search_systems(ctx: AutocompleteContext):
        """Returns a list of systems that begin with the characters entered so far."""
        logger.error(process.extract(
            ctx.value, ctx.cog.Systems, scorer=fuzz.WRatio, limit=10))
        return [i[0] for i in process.extract(ctx.value, ctx.cog.Systems, scorer=fuzz.WRatio, limit=10)]

    def sync_systems(self):
        config: models.SiteClaimConfiguration = models.SiteClaimConfiguration.get_solo()

        if config.valid_ess_regions.all().count():
            self.Systems = list(models.System.objects.filter(
                region__in=config.valid_site_regions.all()).values_list('name', flat=True))
        else:
            self.Systems = list(
                models.System.objects.all().values_list('name', flat=True))

        logger.error(self.Systems)

    @commands.slash_command(name='ess', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    @option("system", description="What System has been linked?", autocomplete=search_systems)
    @option("key_type", required=False, description="15min or 45min?")
    @option("message", required=False, description="anything else to add?")
    async def ess_slash(self,
                        ctx,
                        system: str,
                        key_type: str,
                        message: str):
        """
            Notify FC's that an ESS being linked!
        """
        await ctx.defer(ephemeral=True)

        user = ctx.author

        # no dupes!
        exist = await self.bot.redis.get(f"ess-claimbot-{system}")
        if exist:
            return await ctx.respond(f"ESS in `{system}` has already been pinged!", ephemeral=True)
        else:
            await self.bot.redis.set(f"ess-claimbot-{system}", user.name, ex=60*15)

        config: models.SiteClaimConfiguration = models.SiteClaimConfiguration.get_solo()
        output_channel = config.ess_output_channel if config.ess_output_channel else ctx.channel.id
        e = Embed(title="ESS Event Reported!", color=RED)

        msg = [f"System: [{system}]({dotlan.solar_system_url(system)})"]
        extra_message = ""
        if key_type:
            msg.append(f"Reported Key Type: `{key_type}`")
        if message:
            msg.append(f"Notes: {message}")
        if len(msg):
            extra_message = "\n".join(msg)

        e.description = extra_message
        e.add_field(name="Reported By",
                    value=f"{user.nick if user.nick else user.name} <@{user.id}>", inline=False)

        view_str = "siteclaim.cogs.ess.ESSView"

        send_channel_message_by_discord_id.delay(
            output_channel,
            "@here" if config.ess_ping_at_here else "",
            embed=e.to_dict(),
            view_class=view_str,
            view_kwargs={"found_by": f"{ctx.author.nick if ctx.author.nick else ctx.author.name}",
                         "found_by_uid": ctx.author.id,
                         "system": system}
        )

        return await ctx.respond(f"sent message!", ephemeral=True)

    ess_commands = SlashCommandGroup("ess_notify", "Site Claim Admin Commands", guild_ids=[
        int(settings.DISCORD_GUILD_ID)])

    @ess_commands.command(name='sync', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    async def slash_sync(
        self,
        ctx: Interaction,
    ):
        """
            Sync all settings and update bot cache.
        """
        await ctx.defer(ephemeral=True)
        self.sync_systems()
        return await ctx.respond(f"All Done!", ephemeral=True)

    @ess_commands.command(name='channel_select', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    async def slash_channel_select(
        self,
        ctx: Interaction,
    ):
        """
            Set the channel the site notifications will be sent to.
        """
        await ctx.defer(ephemeral=True)
        config: models.SiteClaimConfiguration = models.SiteClaimConfiguration.get_solo()
        config.ess_output_channel = ctx.channel.id
        config.save()
        return await ctx.respond(f"Set this channel <#{ctx.channel.id}> to receive all ess notifications.!", ephemeral=True)

    @ess_commands.command(name='sync_map', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    async def slash_map_load(
        self,
        ctx: Interaction,
    ):
        """
            Run a task to sync the map.
        """
        await ctx.defer(ephemeral=True)
        tasks.siteclaim_sync_map.delay()
        return await ctx.respond(f"Task added to queue for processing!", ephemeral=True)

    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()


def setup(bot):
    cog = EssLinks(bot)
    cog.sync_systems()
    bot.add_cog(cog)
