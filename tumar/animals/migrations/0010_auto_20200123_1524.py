# Generated by Django 2.1.15 on 2020-01-23 09:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("animals", "0009_auto_20200123_1515"),
    ]

    operations = [
        migrations.RemoveField(model_name="farm", name="breeding_stock",),
        migrations.RemoveField(model_name="farm", name="calves_number",),
    ]
