# Generated by Django 3.2.23 on 2023-11-22 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0012_auto_20231122_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='followrequest',
            name='auto_denied',
            field=models.BooleanField(default=False),
        ),
    ]
