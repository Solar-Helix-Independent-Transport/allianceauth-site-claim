# Cog Stuff
import datetime
import logging
from collections import defaultdict
from typing import Optional

from aadiscordbot.cogs.utils.decorators import has_perm, sender_is_admin
from aadiscordbot.tasks import send_channel_message_by_discord_id
from allianceauth.eveonline.evelinks import dotlan
from allianceauth.services.modules.discord.models import DiscordUser
from discord import (AutocompleteContext, ButtonStyle, Embed, Interaction,
                     Message, SlashCommandGroup, option, ui)
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


class IndyClaimView(ui.View):

    def __init__(self):
        super().__init__(timeout=None)  # timeout of the view must be set to None

    @ui.button(label="Add Producing", custom_id="button-producing-indycog", style=ButtonStyle.blurple)
    async def claim(self, button: ui.Button, interaction: Interaction):
        logger.debug(self.id)
        message = f"\n**Producing** {interaction.user.display_name if interaction.user.display_name else interaction.user.nick} <@{interaction.user.id}>"
        embed = interaction.message.embeds[0]
        embed.description += message
        await interaction.response.edit_message(embed=embed)
        self.producers.append(interaction.user.nick)
        await interaction.response.send_message("Added", ephemeral=True)

    @ui.button(label="Add Listed on Market", custom_id="button-market-indycog", style=ButtonStyle.success)
    async def listed(self, button: ui.Button, interaction: Interaction):
        logger.debug(self.id)
        message = f"\n**Listed on Market** {interaction.user.display_name if interaction.user.display_name else interaction.user.nick} <@{interaction.user.id}>"
        embed = interaction.message.embeds[0]
        embed.description += message
        await interaction.response.edit_message(embed=embed)
        self.marketers.append(interaction.user.nick)
        await interaction.response.send_message("zAdded", ephemeral=True)


class IndyClaim(commands.Cog):
    Systems = []  # load strings on startup of bot.

    """
    IndyClaim
    """

    async def search_systems(ctx: AutocompleteContext):
        """Returns a list of systems that begin with the characters entered so far."""
        logger.error(process.extract(
            ctx.value, ctx.cog.Systems, scorer=fuzz.WRatio, limit=10))
        return [i[0] for i in process.extract(ctx.value, ctx.cog.Systems, scorer=fuzz.WRatio, limit=10)]

    def sync_systems(self):
        config: models.SiteClaimConfiguration = models.SiteClaimConfiguration.get_solo()

        if config.valid_site_regions.all().count():
            self.Systems = list(models.System.objects.filter(
                region__in=config.valid_site_regions.all()).values_list('name', flat=True))
        else:
            self.Systems = list(
                models.System.objects.all().values_list('name', flat=True))

        logger.error(self.Systems)

    claim_commands = SlashCommandGroup("indyclaim", "Indy Claim Admin Commands", guild_ids=[
        int(settings.DISCORD_GUILD_ID)])

    @claim_commands.command(name='new_production', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    @option("system", description="System Name", autocomplete=search_systems)
    @option("items", description="Items Required")
    @option("message", description="Message")
    async def slash_add_site(
        self,
        ctx: Interaction,
        system: str,
        message: str,
        items: str,
    ):
        """
            New Production Request Found
        """
        await ctx.defer(ephemeral=True)
        user = ctx.author

        has_perm(user.id, "siteclaim.can_request_production")

        msg_test = f"System:[{system}]({dotlan.solar_system_url(system)})\n\n{message}\n\nItems: \n{items}\n\nUpdates:\n "

        config: models.SiteClaimConfiguration = models.SiteClaimConfiguration.get_solo()
        output_channel = config.indy_claim_output_channel if config.indy_claim_output_channel else ctx.channel.id
        e = Embed(title="New Production Request", color=BLUE)
        e.description = msg_test
        e.add_field(name="Requested By",
                    value=f"{user.nick if user.nick else user.name}", inline=False)

        view_str = "siteclaim.cogs.indy.IndyClaimView"

        send_channel_message_by_discord_id.delay(
            output_channel,
            "@everyone",
            embed=e.to_dict(),
            view_class=view_str,
            # view_kwargs={"message": msg_test,
            #              "requested_by": f"{ctx.author.nick if ctx.author.nick else ctx.author.name}",
            #              "requested_by_uid": ctx.author.id,
            #              "notes": items,
            #              "system": system}
        )

        return await ctx.respond(f"sent message!", ephemeral=True)

    @claim_commands.command(name='sync', guild_ids=[int(settings.DISCORD_GUILD_ID)])
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

    @claim_commands.command(name='channel_select', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    async def slash_channel_select(
        self,
        ctx: Interaction,
    ):
        """
            Set the channel the site requests will be sent to.
        """
        await ctx.defer(ephemeral=True)
        config: models.SiteClaimConfiguration = models.SiteClaimConfiguration.get_solo()
        config.indy_claim_output_channel = ctx.channel.id
        config.save()
        return await ctx.respond(f"Set this channel <#{ctx.channel.id}> to receive all indy notifications.!", ephemeral=True)

    @claim_commands.command(name='sync_map', guild_ids=[int(settings.DISCORD_GUILD_ID)])
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

    @commands.message_command(name="Close Production", guild_ids=[int(settings.DISCORD_GUILD_ID)])
    @sender_is_admin()
    async def close_production(self, ctx, message: Message):
        text_message = f"\n\n**Closed by** {ctx.user.nick if ctx.user.nick else ctx.user.name}"
        embed = message.embeds[0]
        embed.description += text_message
        await message.edit(embed=embed, view=None)
        await ctx.respond(f"done.", ephemeral=True)

    @commands.message_command(name="Reopen Production", guild_ids=[int(settings.DISCORD_GUILD_ID)])
    @sender_is_admin()
    async def refresh_view(self, ctx, message: Message):
        await message.edit(view=IndyClaimView())
        await ctx.respond(f"done.", ephemeral=True)

    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.Cog.listener("on_ready")
    async def on_bot_ready(self):
        self.bot.add_view(IndyClaimView())


def setup(bot):
    cog = IndyClaim(bot)
    cog.sync_systems()
    bot.add_cog(cog)
