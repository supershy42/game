# Generated by Django 5.1.4 on 2024-12-24 23:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0002_alter_normalmatch_state'),
    ]

    operations = [
        migrations.RenameField(
            model_name='normalmatch',
            old_name='left_score',
            new_name='left_player_score',
        ),
        migrations.RenameField(
            model_name='normalmatch',
            old_name='right_score',
            new_name='right_player_score',
        ),
    ]
