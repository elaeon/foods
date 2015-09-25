# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('disease', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='mortalityyears',
            unique_together=set([('causa_mortality', 'year')]),
        ),
    ]
