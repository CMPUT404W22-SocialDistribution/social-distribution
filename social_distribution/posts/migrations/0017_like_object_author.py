# Generated by Django 4.0.1 on 2022-03-18 04:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('author_manager', '0008_inbox_likes'),
        ('posts', '0016_rename_postlike_like'),
    ]

    operations = [
        migrations.AddField(
            model_name='like',
            name='object_author',
            field=models.ForeignKey(default='2680f90c', on_delete=django.db.models.deletion.CASCADE, related_name='object_author', to='author_manager.author'),
            preserve_default=False,
        ),
    ]
