# Renumerada de 0005 para 0010 após merge: depende de 0009_mensagem_respondida.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0009_mensagem_respondida'),
    ]

    operations = [
        migrations.AddField(
            model_name='mensagem',
            name='feedback',
            field=models.CharField(blank=True, choices=[('positive', 'Positivo'), ('negative', 'Negativo')], max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='mensagem',
            name='foi_reformulada',
            field=models.BooleanField(default=False),
        ),
    ]
