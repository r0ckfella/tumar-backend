# Generated by Django 2.2.12 on 2020-07-16 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('animals', '0021_auto_20200511_1929'),
    ]

    operations = [
        migrations.AddField(
            model_name='farm',
            name='url_type',
            field=models.PositiveSmallIntegerField(default=1, help_text='Возможные варианты 1 и 2.', verbose_name='Chinese API URL type'),
        ),
    ]
