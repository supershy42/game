# Generated by Django 5.1.4 on 2024-12-24 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0004_tournamentmatch_parent_match_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tournamentmatch',
            old_name='parent_match_player_slot',
            new_name='parent_match_player_team',
        ),
        migrations.AlterField(
            model_name='tournamentmatch',
            name='state',
            field=models.CharField(choices=[('pending', 'Pending'), ('ready', 'Ready to Start'), ('finished', 'Finished')], default='pending', max_length=20),
        ),
    ]