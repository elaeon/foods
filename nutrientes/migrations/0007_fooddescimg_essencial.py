# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0006_auto_20151020_1659'),
    ]

    operations = [
        migrations.AddField(
            model_name='fooddescimg',
            name='essencial',
            field=models.BooleanField(default=False),
        ),
    ]
