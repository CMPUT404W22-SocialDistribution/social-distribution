# Generated by Django 4.0.1 on 2022-02-22 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_alter_post_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='description',
            field=models.CharField(blank=True, default='No description', max_length=300, null=True),
        ),
    ]
