# Generated by Django 4.0.1 on 2022-03-28 04:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('author_manager', '0002_initial'),
        ('posts', '0002_like_remote_author'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='author_manager.author'),
        ),
    ]