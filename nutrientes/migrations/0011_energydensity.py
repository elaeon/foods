# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0010_fooddescimg_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnergyDensity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ndb_no_t', models.TextField(unique=True)),
                ('energy_density', models.FloatField()),
            ],
        ),
    ]
