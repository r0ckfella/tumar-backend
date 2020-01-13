# Generated by Django 2.1.15 on 2020-01-13 11:05

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('socialaccount', '0003_extra_data_default_dict'),
        ('users', '0006_auto_20200110_1955'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialAccountExtra',
            fields=[
                ('socialaccount', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='socialaccount_extra', serialize=False, to='socialaccount.SocialAccount', verbose_name='Social Account')),
                ('has_phone_number', models.BooleanField(default=False, verbose_name='Has Phone Number?')),
            ],
            options={
                'verbose_name': 'Social Account Extra',
                'verbose_name_plural': 'Social Accounts Extra',
            },
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that phone number already exists.'}, help_text="Required. Phone number must be entered in the format: '+77076143537'. Up to 15 digits allowed.", max_length=16, null=True, unique=True, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+77076143537'. Up to 15 digits allowed.", regex='^(\\+7|8)\\d?\\d{10,15}$')], verbose_name='phone number'),
        ),
    ]
