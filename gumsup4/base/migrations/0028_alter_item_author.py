# Generated by Django 3.2.23 on 2024-01-18 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0027_auto_20240118_0951'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='author',
            field=models.CharField(blank=True, default='', max_length=40, null=True),
        ),
    ]