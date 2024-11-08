from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Outbox',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('event_type', models.CharField(max_length=255)),
                ('event_date_time', models.DateTimeField(auto_now_add=True)),
                ('environment', models.CharField(max_length=255)),
                ('event_context', models.JSONField()),
                ('metadata_version', models.BigIntegerField()),
                ('processed', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'outbox',
                'indexes': [models.Index(fields=['processed'], name='processed_idx')],
            },
        ),
    ]
