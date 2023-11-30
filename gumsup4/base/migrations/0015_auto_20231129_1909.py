# Generated by Django 3.2.23 on 2023-11-30 03:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0014_activity_follow_request'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='mention',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mention_activity', to='base.post'),
        ),
        migrations.AlterField(
            model_name='post',
            name='category',
            field=models.CharField(choices=[('CULTURE', 'culture'), ('LIFE', 'life'), ('PLACES', 'places'), ('STUFF', 'stuff')], default='LIFE', max_length=50, verbose_name='Category'),
        ),
    ]