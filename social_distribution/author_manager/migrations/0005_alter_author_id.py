# Generated by Django 4.0.1 on 2022-02-21 10:56

import author_manager.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author_manager', '0004_rename_uuid_author_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='id',
            field=models.UUIDField(default=author_manager.models.Author.short_uuid, editable=False, primary_key=True, serialize=False),
        ),
    ]
