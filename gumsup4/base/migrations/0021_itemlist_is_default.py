# Generated by Django 3.2.23 on 2023-12-30 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0020_auto_20231229_1723'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemlist',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
    ]