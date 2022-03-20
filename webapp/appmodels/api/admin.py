
from django.contrib import admin

from .models import (
    BattleMap,
    BattleMapFeature,
    BattleMapSpawnPoint,
)

admin.site.register([
    BattleMap,
    BattleMapFeature,
    BattleMapSpawnPoint,
])

