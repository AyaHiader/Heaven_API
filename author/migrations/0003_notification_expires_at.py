# Generated by Django 5.1.3 on 2024-12-10 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('author', '0002_notification_delete_visit'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
