# Generated by Django 5.1.4 on 2024-12-25 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0003_rename_left_score_normalmatch_left_player_score_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='normalmatch',
            name='unique_id',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
