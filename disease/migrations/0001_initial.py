# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CausaMortality',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=100)),
                ('cie_10', models.CharField(unique=True, max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='MortalityYears',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.PositiveIntegerField()),
                ('amount', models.PositiveIntegerField()),
                ('causa_mortality', models.ForeignKey(to='disease.CausaMortality')),
            ],
        ),
    ]
