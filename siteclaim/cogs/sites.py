# Cog Stuff
import datetime
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


class ClaimView(ui.View):
    """
        Click Counter View for tracking an embeds views and returning ALL the data about it
    """

    embed_text = None
    message_text = ""
    created = None

    def __init__(self,
                 *items: ui.Item,
                 found_by_uid: int = 0,
                 found_by: str = "",
                 site_id: str = "",
                 system: str = "",
                 timeout: Optional[float] = 60*60*24,  # 24h from last click
                 embed: Optional[Embed] = None,
                 message: Optional[str] = None,
                 bot=None
                 ):
        if embed:
            if isinstance(embed, dict):
                self.embed_text = Embed.from_dict(embed)
            elif isinstance(embed, Embed):
                self.embed_text = embed
        if message:
            self.message_text = message
        self.bot = bot
        self.created = timezone.now()
        super().__init__(*items, timeout=timeout)
        logger.debug(self.id)
        db_model = models.Site.objects.create(
            interaction_id=self.id,
            found_by_discord_uid=found_by_uid,
            found_by_discord=found_by,
            system_provided=system,
            site_id=site_id,

        )
        try:
            db_model.found_by = DiscordUser.objects.get(
                uid=found_by_uid).user.profile.main_character
        except:
            logger.warning('user not registered')
        try:
            db_model.system = models.System.objects.get(name=system)
        except:
            logger.warning('system not found')
        db_model.save()

    @ui.button(label="Claim", style=ButtonStyle.blurple)
    async def claim(self, button: ui.Button, interaction: Interaction):
        logger.debug(self.id)
        view = self
        view.children[0].disabled = True
        message = f"{interaction.user.nick if interaction.user.nick else interaction.user.name}"
        embed = interaction.message.embeds[0]
        embed.color = MAGENTA
        embed.add_field(name="Claimed By", value=message, inline=False)

        await interaction.response.edit_message(embed=embed, view=view)
        db_model = models.Site.objects.get(interaction_id=self.id)
        db_model.claimed_by_discord_uid = interaction.user.id
        db_model.claimed_by_discord = f"{interaction.user.nick if interaction.user.nick else interaction.user.name}"
        db_model.message_id = interaction.message.id
        try:
            db_model.claimed_by = DiscordUser.objects.get(
                uid=interaction.user.id).user.profile.main_character
        except:
            logger.warning('user not registered')
            pass
        db_model.save()

    @ui.button(label="Run by us", style=ButtonStyle.success)
    async def run(self, button: ui.Button, interaction: Interaction):
        logger.debug(self.id)
        message = f"Notified By: {interaction.user.nick if interaction.user.nick else interaction.user.name}"
        embed = interaction.message.embeds[0]
        embed.color = GREYPLE
        embed.add_field(name="Run By Us", value=message, inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
        db_model = models.Site.objects.get(interaction_id=self.id)
        db_model.run_by_notified_by_discord_uid = interaction.user.id
        db_model.run_by_notified_by_discord = f"{interaction.user.nick if interaction.user.nick else interaction.user.name}"
        db_model.run_by_us = True
        db_model.message_id = interaction.message.id
        try:
            db_model.run_by_notified_by = DiscordUser.objects.get(
                uid=interaction.user.id).user.profile.main_character
        except:
            logger.warning('user not registered')
            pass
        db_model.save()

    @ui.button(label="Run by someone else", style=ButtonStyle.danger)
    async def missed(self, button: ui.Button, interaction: Interaction):
        logger.debug(self.id)
        message = f"Notified By: {interaction.user.nick if interaction.user.nick else interaction.user.name}"
        embed = interaction.message.embeds[0]
        embed.color = GREYPLE
        embed.add_field(name="Run by someone else",
                        value=message, inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
        db_model = models.Site.objects.get(interaction_id=self.id)
        db_model.run_by_notified_by_discord_uid = interaction.user.id
        db_model.run_by_notified_by_discord = f"{interaction.user.nick if interaction.user.nick else interaction.user.name}"
        db_model.message_id = interaction.message.id
        try:
            db_model.run_by_notified_by = DiscordUser.objects.get(
                uid=interaction.user.id).user.profile.main_character
        except:
            logger.warning('user not registered')
            pass
        db_model.save()

    async def on_timeout(self) -> None:
        print(vars(self))
        await super().on_timeout()


class SiteClaim(commands.Cog):
    Systems = []  # load strings on startup of bot.

    """
    SiteClaim
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

    @commands.slash_command(name='new_site', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    @option("system", description="System Name", autocomplete=search_systems)
    @option("site", description="Site ID", max_length=7)
    async def slash_add_site(
        self,
        ctx: Interaction,
        system: str,
        site: str,
    ):
        """
            New Site Found
        """
        await ctx.defer(ephemeral=True)
        user = ctx.author
        msg_test = f"System:[{system}]({dotlan.solar_system_url(system)})\n\nSite ID:`{site}`"
        after = timezone.now() - datetime.timedelta(hours=24)
        # no dupes!
        if models.Site.objects.filter(
            system_provided=system,
            site_id=site,
            updated__gte=after
        ).exists():
            return await ctx.respond(f"`{system}`:`{site}` has already been pinged!", ephemeral=True)

        config: models.SiteClaimConfiguration = models.SiteClaimConfiguration.get_solo()
        output_channel = config.site_claim_output_channel if config.site_claim_output_channel else ctx.channel.id
        e = Embed(title="New Site", color=BLUE)
        e.description = msg_test
        e.add_field(name="Reported By",
                    value=f"{user.nick if user.nick else user.name}", inline=False)

        view_str = "siteclaim.cogs.sites.ClaimView"

        send_channel_message_by_discord_id.delay(
            output_channel,
            "",
            embed=e.to_dict(),
            view_class=view_str,
            view_kwargs={"message": msg_test,
                         "found_by": f"{ctx.author.nick if ctx.author.nick else ctx.author.name}",
                         "found_by_uid": ctx.author.id,
                         "site_id": site,
                         "system": system}
        )

        return await ctx.respond(f"sent message!", ephemeral=True)

    claim_commands = SlashCommandGroup("siteclaim", "Site Claim Admin Commands", guild_ids=[
        int(settings.DISCORD_GUILD_ID)])

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
            Set the channel the site notifications will be sent to.
        """
        await ctx.defer(ephemeral=True)
        config: models.SiteClaimConfiguration = models.SiteClaimConfiguration.get_solo()
        config.site_claim_output_channel = ctx.channel.id
        config.save()
        return await ctx.respond(f"Set this channel <#{ctx.channel.id}> to receive all site notifications.!", ephemeral=True)

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

    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()


def setup(bot):
    cog = SiteClaim(bot)
    cog.sync_systems()
    bot.add_cog(cog)
