# Generated by Django 4.0.1 on 2022-03-01 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author_manager', '0005_inbox_posts'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='url',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='author',
            name='host',
            field=models.CharField(blank=True, default='http://127.0.0.1:8000/', max_length=200),
        ),
    ]