# Generated by Django 2.1.15 on 2019-12-12 13:19

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("animals", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="animal",
            options={"verbose_name": "Animal", "verbose_name_plural": "Animals"},
        ),
        migrations.AlterModelOptions(
            name="farm",
            options={"verbose_name": "Farm", "verbose_name_plural": "Farms"},
        ),
        migrations.AlterModelOptions(
            name="geolocation",
            options={
                "verbose_name": "Geo-location",
                "verbose_name_plural": "Geo-locations",
            },
        ),
        migrations.AlterField(
            model_name="animal",
            name="cow_code",
            field=models.CharField(
                blank=True, max_length=15, null=True, verbose_name="Animal ID"
            ),
        ),
        migrations.AlterField(
            model_name="animal",
            name="farm",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="animals",
                to="animals.Farm",
                verbose_name="farm",
            ),
        ),
        migrations.AlterField(
            model_name="farm",
            name="name",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="name"
            ),
        ),
        migrations.AlterField(
            model_name="geolocation",
            name="animal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="geolocation",
                to="animals.Animal",
                verbose_name="Animal",
            ),
        ),
        migrations.AlterField(
            model_name="geolocation",
            name="position",
            field=django.contrib.gis.db.models.fields.PointField(
                srid=3857, verbose_name="position"
            ),
        ),
        migrations.AlterField(
            model_name="geolocation",
            name="time",
            field=models.DateTimeField(verbose_name="time"),
        ),
        migrations.AlterUniqueTogether(
            name="geolocation", unique_together={("animal", "time")},
        ),
    ]
