# Generated by Django 3.2.24 on 2024-03-23 00:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0043_demodemo_demofolder_demosong'),
    ]

    operations = [
        migrations.AddField(
            model_name='demofolder',
            name='folder_type',
            field=models.CharField(default='dropbox', max_length=80),
        ),
    ]
