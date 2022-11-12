
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
        name = "Test Map"
        if not BattleMap.objects.filter(name=name).exists():
            print("creating " + name)
            bm = BattleMap.objects.create(
                is_draft=False,
                name=name,
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
                service_radius_meters=95,
                collision_radius_meters=15,
                name="Central Gas n' Go",
            )
        else:
            print("skipping " + name)

        # Create Orion's Battle Axe
        name = "Orion's Battle Axe"
        if not BattleMap.objects.filter(name=name).exists():
            bm = BattleMap.objects.create(
                is_draft=False,
                name=name,
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
                service_radius_meters=95,
                collision_radius_meters=15,
                name="Central Gas n' Go",
            )
            MapSpaceStation.objects.create(
                battle_map=bm,
                position_meters_x=3800,
                position_meters_y=8500,
                service_radius_meters=95,
                collision_radius_meters=15,
                name="Space Depot North",
            )
            MapSpaceStation.objects.create(
                battle_map=bm,
                position_meters_x=3800,
                position_meters_y=500,
                service_radius_meters=95,
                collision_radius_meters=15,
                name="Space Depot South",
            )
            MapMiningLocation.objects.create(
                battle_map=bm,
                starting_ore_amount_kg=500,
                position_meters_x=7500,
                position_meters_y=6500,
                service_radius_meters=100,
                collision_radius_meters=15,
                name="Johnson Mine",
            )
            MapMiningLocation.objects.create(
                battle_map=bm,
                starting_ore_amount_kg=500,
                position_meters_x=1000,
                position_meters_y=8000,
                service_radius_meters=100,
                collision_radius_meters=15,
                name="North West Mine",
            )
            MapMiningLocation.objects.create(
                battle_map=bm,
                starting_ore_amount_kg=500,
                position_meters_x=7500,
                position_meters_y=2500,
                service_radius_meters=100,
                collision_radius_meters=15,
                name="Doorson's Deposit",
            )
            MapMiningLocation.objects.create(
                battle_map=bm,
                starting_ore_amount_kg=500,
                position_meters_x=1000,
                position_meters_y=1000,
                service_radius_meters=100,
                collision_radius_meters=15,
                name="South West Mine",
            )
        else:
            print("skipping " + name)


        # Create Small FFA Map
        name = "Royal Arena"
        if not BattleMap.objects.filter(name=name).exists():
            print("creating " + name)
            bm = BattleMap.objects.create(
                is_draft=False,
                name=name,
                meters_x=2000,
                meters_y=2000,
                size=BattleMap.SIZE_SMALL,
            )
            BattleMapSpawnPoint.objects.create(
                battle_map=bm,
                position_meters_x=200,
                position_meters_y=200,
            )
            BattleMapSpawnPoint.objects.create(
                battle_map=bm,
                position_meters_x=1800,
                position_meters_y=1800,
            )
            BattleMapSpawnPoint.objects.create(
                battle_map=bm,
                position_meters_x=200,
                position_meters_y=1800,
            )
            BattleMapSpawnPoint.objects.create(
                battle_map=bm,
                position_meters_x=1800,
                position_meters_y=200,
            )
            MapSpaceStation.objects.create(
                battle_map=bm,
                position_meters_x=1000,
                position_meters_y=1000,
                service_radius_meters=95,
                collision_radius_meters=15,
                name="Outpost 87",
            )
            MapMiningLocation.objects.create(
                battle_map=bm,
                starting_ore_amount_kg=2000,
                position_meters_x=300,
                position_meters_y=1000,
                service_radius_meters=100,
                collision_radius_meters=15,
                name="Lucky's Deposit",
            )
            MapMiningLocation.objects.create(
                battle_map=bm,
                starting_ore_amount_kg=250,
                position_meters_x=1700,
                position_meters_y=1000,
                service_radius_meters=100,
                collision_radius_meters=15,
                name="Fool's Ore Mine",
            )
        else:
            print("skipping " + name)