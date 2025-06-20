# Generated by Django 5.1 on 2025-05-10 01:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_paymenthistory_transaction_id'),
        ('staffs', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-created_at'], 'verbose_name': 'Notification', 'verbose_name_plural': 'Notifications'},
        ),
        migrations.RemoveField(
            model_name='notification',
            name='delivery_info',
        ),
        migrations.RemoveField(
            model_name='notification',
            name='notification_type',
        ),
        migrations.AddField(
            model_name='notification',
            name='related_delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='payments.deliveryinfo'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='recipient',
            field=models.ForeignKey(limit_choices_to={'user_type': 'staff'}, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL),
        ),
    ]
