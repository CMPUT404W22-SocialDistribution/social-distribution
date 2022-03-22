# Generated by Django 4.0.1 on 2022-03-22 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('url', models.URLField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('outgoing_username', models.CharField(max_length=50)),
                ('outgoing_password', models.CharField(max_length=100)),
            ],
        ),
    ]
