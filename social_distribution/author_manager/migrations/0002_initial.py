# Generated by Django 4.0.1 on 2022-03-24 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('posts', '0001_initial'),
        ('author_manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='inbox',
            name='comments',
            field=models.ManyToManyField(blank=True, to='posts.Comment'),
        ),
        migrations.AddField(
            model_name='inbox',
            name='likes',
            field=models.ManyToManyField(blank=True, to='posts.Like'),
        ),
        migrations.AddField(
            model_name='inbox',
            name='posts',
            field=models.ManyToManyField(blank=True, to='posts.Post'),
        ),
    ]
