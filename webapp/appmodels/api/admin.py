
from django.contrib import admin

from .models import (
    BattleMap,
    MapSpaceStation,
    MapMiningLocation,
    BattleMapSpawnPoint,
)

admin.site.register([
    BattleMap,
    MapSpaceStation,
    MapMiningLocation,
    BattleMapSpawnPoint,
])

