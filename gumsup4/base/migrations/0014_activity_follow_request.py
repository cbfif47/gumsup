# Generated by Django 3.2.23 on 2023-11-23 01:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0013_alter_followrequest_auto_denied'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='follow_request',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='follow_request_activity', to='base.followrequest'),
        ),
    ]
