# Generated by Django 5.1.4 on 2024-12-23 16:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0003_remove_tournamentmatch_tournament_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournamentmatch',
            name='parent_match',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tournament.tournamentmatch'),
        ),
        migrations.AddField(
            model_name='tournamentmatch',
            name='parent_match_player_slot',
            field=models.CharField(blank=True, choices=[('left', 'Left'), ('right', 'Right')], max_length=5, null=True),
        ),
    ]