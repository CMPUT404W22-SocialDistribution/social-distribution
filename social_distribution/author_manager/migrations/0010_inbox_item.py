# Generated by Django 4.0.1 on 2022-03-21 02:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author_manager', '0009_inbox_likes'),
    ]

    operations = [
        migrations.AddField(
            model_name='inbox',
            name='item',
            field=models.JSONField(default=dict),
        ),
    ]
