# Generated by Django 4.0.1 on 2022-03-24 07:42

from django.db import migrations, models
import django.db.models.deletion
import posts.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
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
            name='Comment',
            fields=[
                ('type', models.CharField(default='comment', max_length=50)),
                ('contentType', models.CharField(choices=[('text/markdown', 'Markdown'), ('text/plain', 'Plain')], default='text/plain', max_length=50)),
                ('published', models.DateTimeField(auto_now_add=True)),
                ('id', models.CharField(default=uuid.uuid4, editable=False, max_length=8, primary_key=True, serialize=False, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('type', models.CharField(default='post', max_length=50)),
                ('title', models.CharField(max_length=200)),
                ('id', models.CharField(default=uuid.uuid4, editable=False, max_length=8, primary_key=True, serialize=False, unique=True)),
                ('source', models.CharField(blank=True, max_length=300)),
                ('origin', models.CharField(blank=True, max_length=300)),
                ('description', models.CharField(blank=True, default='No description', max_length=300, null=True)),
                ('content_type', models.CharField(choices=[('text/markdown', 'Markdown'), ('text/plain', 'Plain'), ('application/base64', 'Application'), ('image/png;base64', 'Png'), ('image/jpeg;base64', 'Jpeg')], default='text/plain', max_length=50)),
                ('content', models.TextField(blank=True, default='')),
                ('image', models.ImageField(blank=True, null=True, upload_to=posts.models.Post.image_upload_path)),
                ('published', models.DateTimeField(auto_now_add=True)),
                ('visibility', models.CharField(choices=[('public', 'Public'), ('private', 'Private'), ('friends', 'Friends')], default='public', max_length=30)),
                ('visibleTo', models.CharField(blank=True, max_length=200)),
                ('unlisted', models.BooleanField(default=False)),
                ('categories', models.ManyToManyField(blank=True, to='posts.Category')),
            ],
        ),
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('summary', models.CharField(max_length=300)),
                ('type', models.CharField(default='Like', max_length=50)),
                ('comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='posts.comment')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='posts.post')),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commentsSrc', to='posts.post'),
        ),
    ]
