# Generated by Django 4.0.1 on 2022-02-19 23:40

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('author_manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('type', models.CharField(default='post', max_length=50)),
                ('title', models.CharField(max_length=200)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source', models.CharField(blank=True, max_length=300)),
                ('origin', models.CharField(blank=True, max_length=300)),
                ('description', models.CharField(blank=True, max_length=300, null=True)),
                ('content_type', models.CharField(choices=[('text/markdown', 'Markdown'), ('text/plain', 'Plain'), ('application/base64', 'Application'), ('image/png;base64', 'Png'), ('image/jpeg;base64', 'Jpeg')], default='text/plain', max_length=50)),
                ('content', models.TextField()),
                ('published', models.DateTimeField(auto_now_add=True)),
                ('visibility', models.CharField(choices=[('public', 'Public'), ('private', 'Private'), ('friends', 'Friends')], default='public', max_length=30)),
                ('unlisted', models.BooleanField(default=False)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='author_manager.author')),
                ('categories', models.ManyToManyField(blank=True, to='posts.Category')),
            ],
        ),
    ]
