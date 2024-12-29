# Generated by Django 5.1.4 on 2024-12-23 16:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0002_alter_tournament_name_tournamentmatch_delete_match'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tournamentmatch',
            name='tournament',
        ),
        migrations.AlterField(
            model_name='tournamentmatch',
            name='match_number',
            field=models.PositiveIntegerField(),
        ),
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_number', models.PositiveIntegerField()),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.tournament')),
            ],
        ),
        migrations.AlterField(
            model_name='tournamentmatch',
            name='round',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournament.round'),
        ),
    ]