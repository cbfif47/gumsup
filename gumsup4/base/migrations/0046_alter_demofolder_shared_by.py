# Generated by Django 3.2.24 on 2024-03-23 00:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0045_alter_demofolder_shared_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demofolder',
            name='shared_by',
            field=models.ForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shared_folders', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
