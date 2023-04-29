from django.conf import settings

SITE_CLAIM_ENABLE_ESS = getattr(settings, 'SITE_CLAIM_ENABLE_ESS', True)
SITE_CLAIM_ENABLE_SITES = getattr(settings, 'SITE_CLAIM_ENABLE_SITES', True)
