# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0007_fooddescimg_essencial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fooddescimg',
            name='essencial',
        ),
        migrations.AddField(
            model_name='nutrdesc',
            name='essencial',
            field=models.BooleanField(default=False),
        ),
    ]
