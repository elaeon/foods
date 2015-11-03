# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0004_fooddescimg'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fooddescimg',
            name='img',
            field=sorl.thumbnail.fields.ImageField(upload_to=b'food/'),
        ),
    ]
