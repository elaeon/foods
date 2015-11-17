# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0009_fooddescimg_ref_img'),
    ]

    operations = [
        migrations.AddField(
            model_name='fooddescimg',
            name='name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
