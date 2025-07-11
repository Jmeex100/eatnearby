# Generated by Django 5.1 on 2025-05-10 02:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_paymenthistory_transaction_id'),
        ('staffs', '0003_notification_notification_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('new_order', 'New Order'), ('delivery_almost_complete', 'Delivery Almost Complete'), ('delivery_completed', 'Delivery Completed'), ('alert', 'Alert')], default='new_order', max_length=30),
        ),
        migrations.CreateModel(
            name='StaffAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('delivery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_assignments', to='payments.deliveryinfo')),
                ('staff', models.ForeignKey(limit_choices_to={'user_type': 'staff'}, on_delete=django.db.models.deletion.CASCADE, related_name='delivery_assignments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Staff Assignment',
                'verbose_name_plural': 'Staff Assignments',
                'unique_together': {('staff', 'delivery')},
            },
        ),
    ]
