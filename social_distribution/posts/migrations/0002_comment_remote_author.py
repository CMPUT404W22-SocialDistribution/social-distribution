# Generated by Django 4.0.1 on 2022-03-27 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='remote_author',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
