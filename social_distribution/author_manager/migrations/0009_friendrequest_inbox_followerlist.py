# Generated by Django 4.0.1 on 2022-02-23 12:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('author_manager', '0008_author_about_author_birthday_author_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='FriendRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(default='follow', editable=False, max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actor', to='author_manager.author')),
                ('object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='object', to='author_manager.author')),
            ],
        ),
        migrations.CreateModel(
            name='Inbox',
            fields=[
                ('type', models.CharField(default='inbox', editable=False, max_length=30)),
                ('author', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='author_manager.author')),
                ('follows', models.ManyToManyField(blank=True, to='author_manager.FriendRequest')),
            ],
        ),
        migrations.CreateModel(
            name='FollowerList',
            fields=[
                ('type', models.CharField(default='followers', editable=False, max_length=50)),
                ('author', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='author_manager.author')),
                ('items', models.ManyToManyField(blank=True, null=True, related_name='items', to='author_manager.Author')),
            ],
        ),
    ]
