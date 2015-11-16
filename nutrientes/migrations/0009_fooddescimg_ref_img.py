# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0008_auto_20151021_1408'),
    ]

    operations = [
        migrations.AddField(
            model_name='fooddescimg',
            name='ref_img',
            field=models.URLField(null=True, blank=True),
        ),
    ]
