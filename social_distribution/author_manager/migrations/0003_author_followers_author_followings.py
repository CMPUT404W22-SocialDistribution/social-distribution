# Generated by Django 4.0.1 on 2022-02-24 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author_manager', '0002_friendrequest_author_about_author_birthday_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='followers',
            field=models.ManyToManyField(blank=True, null=True, related_name='my_followers', to='author_manager.Author'),
        ),
        migrations.AddField(
            model_name='author',
            name='followings',
            field=models.ManyToManyField(blank=True, null=True, related_name='my_followings', to='author_manager.Author'),
        ),
    ]