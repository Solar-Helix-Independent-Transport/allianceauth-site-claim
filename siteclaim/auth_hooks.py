from allianceauth import hooks

@hooks.register('discord_cogs_hook')
def register_cogs():
    return ['siteclaim.cogs.sites']
