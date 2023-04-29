import csv
import re

import requests
from esi.clients import EsiClientProvider

from . import models, providers


class CSVLoader:
    def __init__(self, url):
        self.url = url
        self.data = []
        self.load_data()

    def load_data(self):
        with requests.get(self.url) as r:
            import re
            pattern = re.compile(r'".*?"', re.DOTALL)
            out = pattern.sub(lambda x: x.group().replace('\n', ''), r.text)
            self.data = csv.DictReader(out.split("\r\n"))


class EVEClient(EsiClientProvider):

    @staticmethod
    def chunk_ids(l, n=750):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def load_map_sde(self):
        regions = []
        print("Loading Regions")
        region_data = CSVLoader(
            "https://www.fuzzwork.co.uk/dump/latest/mapRegions.csv")
        for r in region_data.data:
            regions.append(models.Region(
                id=r['regionID'], name=r['regionName']))
        # create anything new
        models.Region.objects.bulk_create(
            regions, batch_size=1000, ignore_conflicts=True)
        # update anything not
        models.Region.objects.bulk_update(
            regions, batch_size=1000, fields=["name"])

        print("Loading Constellations")
        constellation_data = CSVLoader(
            "https://www.fuzzwork.co.uk/dump/latest/mapConstellations.csv")
        constellations = []
        for r in constellation_data.data:
            constellations.append(models.Constellation(
                id=r['constellationID'], name=r['constellationName'], region_id=r['regionID']))
        # create anything new
        models.Constellation.objects.bulk_create(
            constellations, batch_size=1000, ignore_conflicts=True)
        # update anything not
        models.Constellation.objects.bulk_update(
            constellations, batch_size=1000, fields=["name", "region"])

        print("Loading Systems")
        system_data = CSVLoader(
            "https://www.fuzzwork.co.uk/dump/latest/mapSolarSystems.csv")
        systems = []
        for r in system_data.data:
            systems.append(models.System(id=r['solarSystemID'], name=r['solarSystemName'],
                           region_id=r['regionID'], constellation_id=r['constellationID']))
        # create anything new
        models.System.objects.bulk_create(
            systems, batch_size=1000, ignore_conflicts=True)
        # update anything not
        models.System.objects.bulk_update(systems, batch_size=1000, fields=[
                                          "name", "region", "constellation"])


esi = EVEClient()
