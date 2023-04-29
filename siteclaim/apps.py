from django.apps import AppConfig

from . import __version__


class SiteClaimConfig(AppConfig):
    name = 'siteclaim'
    label = 'siteclaim'

    verbose_name = f"Site Claim v{__version__}"
