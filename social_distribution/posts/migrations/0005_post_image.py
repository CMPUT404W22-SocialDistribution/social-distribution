# Generated by Django 4.0.1 on 2022-02-24 21:07

from django.db import migrations, models
import posts.models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_alter_post_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=posts.models.Post.image_upload_path),
        ),
    ]