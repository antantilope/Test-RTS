# Generated by Django 3.2.9 on 2021-11-08 21:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_player_is_superuser'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='player',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='player',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='room',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='room',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='team',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='team',
            name='updated_at',
        ),
    ]
