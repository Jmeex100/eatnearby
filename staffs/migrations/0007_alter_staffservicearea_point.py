# Generated by Django 5.2.1 on 2025-06-07 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staffs', '0006_alter_notification_notification_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffservicearea',
            name='point',
            field=models.CharField(choices=[('evelynhone', 'Evelyn Hone College'), ('zambia_police', 'Zambia Police Headquarters'), ('zambia_accountancy', 'Zambia Centre for Accountancy'), ('mukuba_house', 'Mukuba Pension House'), ('bus_terminus', 'Lusaka Intercity Bus Terminus'), ('national_museum', 'Lusaka National Museum')], help_text='Which delivery point this staff covers', max_length=30),
        ),
    ]
