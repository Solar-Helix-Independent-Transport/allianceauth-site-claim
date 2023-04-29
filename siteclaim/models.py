import logging

from allianceauth.eveonline.models import EveCharacter
from django.contrib.auth.models import Group
from django.db import models
from solo.models import SingletonModel

logger = logging.getLogger(__name__)


class Region(models.Model):
    """
    basic Solar System
    """
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=150)

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name


class Constellation(models.Model):
    """
    basic Solar System
    """
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=150)
    region = models.ForeignKey(Region, null=True, on_delete=models.SET_NULL)

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name


class System(models.Model):
    """
    basic Solar System
    """
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=150)
    constellation = models.ForeignKey(
        Constellation, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, null=True, on_delete=models.SET_NULL)

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name


class SiteClaimConfiguration(SingletonModel):
    # ess_groups = models.ManyToManyField(Group, blank=True)
    # site_groups = models.ManyToManyField(Group, blank=True)
    valid_site_regions = models.ManyToManyField(
        Region, blank=True, related_name="site_regions")
    site_claim_output_channel = models.BigIntegerField(
        null=True, blank=True, default=None)

    valid_ess_regions = models.ManyToManyField(
        Region, blank=True, related_name="ess_regions")
    ess_output_channel = models.BigIntegerField(
        null=True, blank=True, default=None)
    ess_ping_at_here = models.BooleanField(default=True)

    def __str__(self):
        return "Site Claim Configuration"

    class Meta:
        verbose_name = "Site Claim Configuration"


class Site(models.Model):
    """
        Site claim data for later use/leader board/payments
    """
    found_by_discord = models.CharField(max_length=200, default="", blank=True)
    found_by_discord_uid = models.BigIntegerField(
        null=True, default=None, blank=True, )
    found_by = models.ForeignKey(
        EveCharacter, null=True, default=None, blank=True, on_delete=models.SET_NULL, related_name="sites_found")

    claimed_by_discord = models.CharField(
        max_length=200, default="", blank=True)
    claimed_by_discord_uid = models.BigIntegerField(
        null=True, default=None, blank=True, )
    claimed_by = models.ForeignKey(
        EveCharacter, null=True, default=None, blank=True, on_delete=models.SET_NULL, related_name="sites_claimed")

    run_by_us = models.BooleanField(default=False, blank=True)

    run_by_notified_by_discord = models.CharField(
        max_length=200, default="", blank=True)
    run_by_notified_by_discord_uid = models.BigIntegerField(
        null=True, default=None, blank=True, )
    run_by_notified_by = models.ForeignKey(
        EveCharacter, null=True, default=None, blank=True, on_delete=models.SET_NULL, related_name="sites_notified")

    updated = models.DateTimeField(auto_now=True)
    message_id = models.BigIntegerField(null=True, default=None, blank=True, )
    interaction_id = models.CharField(max_length=100)

    system = models.ForeignKey(
        System, null=True, default=None, blank=True, on_delete=models.SET_NULL, )
    system_provided = models.CharField(max_length=100)
    site_id = models.CharField(max_length=25)
