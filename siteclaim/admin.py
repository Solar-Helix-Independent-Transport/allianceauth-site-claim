from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import SiteClaimConfiguration


class SiteClaimConfigurationAdmin(SingletonModelAdmin):
    filter_horizontal = ["valid_site_regions", "valid_ess_regions"]


admin.site.register(SiteClaimConfiguration, SiteClaimConfigurationAdmin)
