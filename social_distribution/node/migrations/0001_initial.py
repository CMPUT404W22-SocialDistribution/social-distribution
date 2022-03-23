# Generated by Django 4.0.1 on 2022-03-23 07:13

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
                ('incoming_username', models.CharField(max_length=20, null=True)),
                ('incoming_password', models.CharField(max_length=20, null=True)),
                ('outgoing_username', models.CharField(max_length=50)),
                ('outgoing_password', models.CharField(max_length=100)),
            ],
        ),
    ]
