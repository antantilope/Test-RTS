# Generated by Django 3.2.9 on 2022-10-17 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_mapmininglocation_starting_ore_amount_kg'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapmininglocation',
            name='collision_radius_meters',
            field=models.PositiveIntegerField(default=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='mapspacestation',
            name='collision_radius_meters',
            field=models.PositiveIntegerField(default=15),
            preserve_default=False,
        ),
    ]
