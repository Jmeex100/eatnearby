# Generated by Django 5.1 on 2025-03-18 15:50

import auths.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auths', '0002_alter_user_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='image',
            field=models.ImageField(blank=True, default='auths/images/empty.png', null=True, upload_to=auths.models.User.user_directory_path, verbose_name='Profile Image'),
        ),
    ]
