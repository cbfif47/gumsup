# Generated by Django 3.2.23 on 2023-11-17 21:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_squashed_0010_auto_20231114_1926','0002_auto_20231117_1051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posted_by', to=settings.AUTH_USER_MODEL, verbose_name='Gummed By'),
        ),
        migrations.AlterField(
            model_name='post',
            name='what',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='post',
            name='why',
            field=models.TextField(max_length=250),
        ),
        migrations.AlterField(
            model_name='savedpost',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_post', to='base.post'),
        ),
        migrations.AlterField(
            model_name='savedpost',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_by', to=settings.AUTH_USER_MODEL, verbose_name='Saved By'),
        ),
        migrations.AlterField(
            model_name='user',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
