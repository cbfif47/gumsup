# Generated by Django 3.2.25 on 2024-04-18 02:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0059_demofolder_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='item_type',
            field=models.CharField(choices=[('WATCH', 'watch'), ('READ', 'read'), ('EAT', 'eat'), ('LISTEN', 'listen'), ('MISC', 'misc')], default='WATCH', max_length=50, verbose_name='Type'),
        ),
        migrations.DeleteModel(
            name='DemoShareKey',
        ),
    ]