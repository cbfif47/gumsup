# Generated by Django 3.2.23 on 2023-11-10 23:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_auto_20231110_2318'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_private',
            field=models.BooleanField(default=False),
        ),
    ]
