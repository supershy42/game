# Generated by Django 5.1.3 on 2024-11-30 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GameRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('password', models.CharField(blank=True, max_length=255, null=True)),
                ('max_players', models.PositiveIntegerField(default=2)),
            ],
        ),
    ]
