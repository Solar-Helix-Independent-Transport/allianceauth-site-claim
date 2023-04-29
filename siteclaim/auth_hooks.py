from allianceauth import hooks

from .app_settings import SITE_CLAIM_ENABLE_ESS, SITE_CLAIM_ENABLE_SITES


@hooks.register('discord_cogs_hook')
def register_cogs():
    cogs = []
    if SITE_CLAIM_ENABLE_SITES:
        cogs.append('siteclaim.cogs.sites')
    if SITE_CLAIM_ENABLE_ESS:
        cogs.append('siteclaim.cogs.ess')
    return cogs
