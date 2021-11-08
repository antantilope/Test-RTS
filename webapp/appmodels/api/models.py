
from django.db import models


class BaseModel(models.Model):
    uuid = models.UUIDField(primary_key=True)

    class Meta:
        abstract = True


class Room(BaseModel):
    name = models.TextField()
    port = models.PositiveSmallIntegerField()
    max_players = models.PositiveSmallIntegerField()


class Team(BaseModel):
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
