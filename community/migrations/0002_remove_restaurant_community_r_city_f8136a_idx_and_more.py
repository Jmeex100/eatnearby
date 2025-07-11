# Generated by Django 5.2.1 on 2025-06-16 00:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='restaurant',
            name='community_r_city_f8136a_idx',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='postal_code',
        ),
        migrations.RemoveField(
            model_name='restaurant',
            name='state',
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='country',
            field=models.CharField(default='Zambia', max_length=100),
        ),
        migrations.AddIndex(
            model_name='restaurant',
            index=models.Index(fields=['city', 'country'], name='community_r_city_059990_idx'),
        ),
    ]
