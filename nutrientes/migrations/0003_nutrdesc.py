# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0002_auto_20150921_1715'),
    ]

    operations = [
        migrations.CreateModel(
            name='NutrDesc',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nutr_no_t', models.TextField(unique=True)),
                ('desc', models.TextField()),
                ('group', models.TextField()),
            ],
        ),
    ]
