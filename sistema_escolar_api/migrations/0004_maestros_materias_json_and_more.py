# Generated by Django 5.0.2 on 2025-03-12 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sistema_escolar_api', '0003_alumnos_maestros'),
    ]

    operations = [
        migrations.AddField(
            model_name='maestros',
            name='materias_json',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='maestros',
            name='area_investigacion',
            field=models.JSONField(default=list),
        ),
    ]
