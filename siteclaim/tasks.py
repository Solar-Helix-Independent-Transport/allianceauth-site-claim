import logging

from celery import shared_task

from .providers import esi

logger = logging.getLogger(__name__)


@shared_task
def siteclaim_sync_map():
    esi.load_map_sde()
