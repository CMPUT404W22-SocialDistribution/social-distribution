# Generated by Django 4.0.1 on 2022-03-18 02:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('author_manager', '0007_delete_followerlist'),
        ('posts', '0015_postlike_comment_delete_commentlike'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PostLike',
            new_name='Like',
        ),
    ]