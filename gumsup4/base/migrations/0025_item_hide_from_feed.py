# Generated by Django 3.2.23 on 2024-01-05 22:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0024_auto_20240103_2022'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='hide_from_feed',
            field=models.BooleanField(default=False),
        ),
    ]
