
from django.db import models


class BaseModel(models.Model):
    uuid = models.UUIDField(primary_key=True)

    class Meta:
        abstract = True


class Room(BaseModel):
    name = models.TextField()
    port = models.PositiveSmallIntegerField()
    pid = models.PositiveSmallIntegerField()
    max_players = models.PositiveSmallIntegerField()
    room_owner = models.CharField(max_length=100)

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
