# Generated by Django 3.2.25 on 2024-04-01 00:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0051_democomment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='democomment',
            old_name='body',
            new_name='comment',
        ),
    ]