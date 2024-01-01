# Generated by Django 3.2.23 on 2024-01-01 22:21

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0022_alter_itemlist_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, error_messages={'unique': 'username taken :('}, max_length=20, null=True, unique=True, validators=[django.core.validators.RegexValidator('^([A-Za-z0-9])+(?:-\\w*)*$', 'username can only have letters, digits, underscores and hyphens'), django.core.validators.MinLengthValidator(3, 'username needs to be at least 3 characters')], verbose_name='username'),
        ),
    ]
