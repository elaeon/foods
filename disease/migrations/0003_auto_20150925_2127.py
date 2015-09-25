# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('disease', '0002_auto_20150925_2119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='causamortality',
            name='cie_10',
            field=models.CharField(unique=True, max_length=50),
        ),
    ]
