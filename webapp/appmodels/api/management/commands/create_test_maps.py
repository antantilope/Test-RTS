
from django.core.management.base import BaseCommand
from django.db import transaction


from api.models import (
    BattleMap,
    BattleMapSpawnPoint,
    MapSpaceStation,
    MapMiningLocation,
)

class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):

        # Create Small Test Map
        bm = BattleMap.objects.create(
            is_draft=False,
            name="Test Map",
            meters_x=1000,
            meters_y=1000,
            size=BattleMap.SIZE_SMALL,
        )
        BattleMapSpawnPoint.objects.create(
            battle_map=bm,
            position_meters_x=200,
            position_meters_y=200,
        )
        BattleMapSpawnPoint.objects.create(
            battle_map=bm,
            position_meters_x=800,
            position_meters_y=800,
        )
        MapSpaceStation.objects.create(
            battle_map=bm,
            position_meters_x=500,
            position_meters_y=500,
            service_radius_meters=120,
            name="Central Gas n' Go",
        )

        # Create Orion's Battle Axe
        bm = BattleMap.objects.create(
            is_draft=False,
            name="Orion's Battle Axe",
            meters_x=9000,
            meters_y=9000,
            size=BattleMap.SIZE_SMALL,
        )
        BattleMapSpawnPoint.objects.create(
            battle_map=bm,
            position_meters_x=4500,
            position_meters_y=500,
        )
        BattleMapSpawnPoint.objects.create(
            battle_map=bm,
            position_meters_x=4500,
            position_meters_y=8500,
        )
        MapSpaceStation.objects.create(
            battle_map=bm,
            position_meters_x=4500,
            position_meters_y=4500,
            service_radius_meters=120,
            name="Central Gas n' Go",
        )
        MapSpaceStation.objects.create(
            battle_map=bm,
            position_meters_x=3800,
            position_meters_y=8500,
            service_radius_meters=120,
            name="Space Depot North",
        )
        MapSpaceStation.objects.create(
            battle_map=bm,
            position_meters_x=3800,
            position_meters_y=500,
            service_radius_meters=120,
            name="Space Depot South",
        )
        MapMiningLocation.objects.create(
            battle_map=bm,
            starting_ore_amount_kg=500,
            position_meters_x=7500,
            position_meters_y=6500,
            service_radius_meters=100,
            name="Johnson Mine",
        )
        MapMiningLocation.objects.create(
            battle_map=bm,
            starting_ore_amount_kg=500,
            position_meters_x=1000,
            position_meters_y=8000,
            service_radius_meters=100,
            name="North West Mine",
        )
        MapMiningLocation.objects.create(
            battle_map=bm,
            starting_ore_amount_kg=500,
            position_meters_x=7500,
            position_meters_y=2500,
            service_radius_meters=100,
            name="Doorson's Deposit",
        )
        MapMiningLocation.objects.create(
            battle_map=bm,
            starting_ore_amount_kg=500,
            position_meters_x=1000,
            position_meters_y=1000,
            service_radius_meters=100,
            name="South West Mine",
        )
