
import uuid

from django.db import models


class BaseModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True, blank=True, default=uuid.uuid4, editable=False
    )

    class Meta:
        abstract = True


class BattleMap(BaseModel):
    is_draft = models.BooleanField(blank=True, default=False)
    name = models.CharField(max_length=100)
    meters_x = models.PositiveBigIntegerField()
    meters_y = models.PositiveBigIntegerField()

    SIZE_SMALL = 'small'
    SIZE_MEDIUM = 'medium'
    SIZE_LARGE = 'large'
    BATTLE_MAP_SIZES = (
        (SIZE_SMALL, "Small",),
        (SIZE_MEDIUM, "Medium",),
        (SIZE_LARGE, "Large",),
    )
    size = models.CharField(max_length=10, choices=BATTLE_MAP_SIZES)

    def __str__(self):
        return self.name + " " + f"({self.size})"


class BattleMapSpawnPoint(BaseModel):
    battle_map = models.ForeignKey(BattleMap, on_delete=models.CASCADE)
    position_meters_x = models.PositiveBigIntegerField()
    position_meters_y = models.PositiveBigIntegerField()


    def __str__(self):
        return f"SPAWN {self.battle_map.name} ({self.position_meters_x}, {self.position_meters_y})"

class BaseBattleMapFeature(BaseModel):
    battle_map = models.ForeignKey(BattleMap, on_delete=models.CASCADE)
    position_meters_x = models.PositiveBigIntegerField()
    position_meters_y = models.PositiveBigIntegerField()
    service_radius_meters = models.PositiveIntegerField()
    name = models.CharField(max_length=100, blank=True, null=True, default=None)

    class Meta:
        abstract = True

class MapSpaceStation(BaseBattleMapFeature):
    def __str__(self):
        return f"Space Station ({self.position_meters_x}, {self.position_meters_y}) on {self.battle_map.name}"

class MapMiningLocation(BaseBattleMapFeature):
    def __str__(self):
        return f"Mining location ({self.position_meters_x}, {self.position_meters_y}) on {self.battle_map.name}"


class Room(BaseModel):
    name = models.TextField()
    port = models.PositiveSmallIntegerField()
    pid = models.PositiveSmallIntegerField()
    max_players = models.PositiveSmallIntegerField()
    room_owner = models.CharField(max_length=100)
    battle_map = models.ForeignKey(BattleMap, on_delete=models.PROTECT, blank=True, null=True, default=None)

    PHASE_LOBBY = '0-lobby'
    PHASE_STARTING = '1-starting'
    PHASE_LIVE = '2-live'
    PHASE_COMPLETE = '3-complete'
    PHASES = (
        (PHASE_LOBBY, '0 Lobby',),
        (PHASE_STARTING, '1 Starting',),
        (PHASE_LIVE, '2 Live',),
        (PHASE_COMPLETE, '3 Complete',),
    )
    phase = models.CharField(max_length=12, choices=PHASES, default=PHASE_LOBBY)


class Team(BaseModel):
    is_observer = models.BooleanField(default=False)
    room = models.ForeignKey(
        'api.Room',
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE
    )


class Player(BaseModel):
    is_superuser = models.BooleanField(default=False)

    handle = models.CharField(max_length=12)
    login_code = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        default=None
    )
    team = models.ForeignKey(
        'api.Team',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL
    )
