# Generated by Django 2.1.15 on 2020-04-21 22:02

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_auto_20200421_2152'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsverification',
            name='phone_num',
            field=models.CharField(help_text="Required. Phone number must be entered in the format: '+77076143537'. Up to 15 digits allowed.", max_length=16, null=True, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+77076143537' or '77076143537'. Up to 15 digits allowed.", regex='^\\+\\d{11}$')], verbose_name='Phone Number'),
        ),
    ]
