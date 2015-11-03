# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutrientes', '0003_nutrdesc'),
    ]

    operations = [
        migrations.CreateModel(
            name='FoodDescImg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ndb_no_t', models.TextField(unique=True)),
                ('img', models.ImageField(max_length=255, upload_to=b'food/')),
            ],
        ),
    ]
