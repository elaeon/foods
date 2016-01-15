# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-15 18:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disease', '0004_cancer_cancer5yrsurvivalrate_canceragent_canceragentrelation'),
    ]

    operations = [
        migrations.AddField(
            model_name='cancer',
            name='name_es',
            field=models.CharField(default=None, max_length=100, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cancer',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
