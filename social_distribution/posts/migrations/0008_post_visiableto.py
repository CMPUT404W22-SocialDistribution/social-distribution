# Generated by Django 4.0.1 on 2022-02-25 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_alter_post_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='visiableTo',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]