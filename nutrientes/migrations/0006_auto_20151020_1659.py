# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0005_auto_20151020_1619'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nutrdesc',
            name='desc',
            field=models.TextField(null=True, blank=True),
        ),
    ]
