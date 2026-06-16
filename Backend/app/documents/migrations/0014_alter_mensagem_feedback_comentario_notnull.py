from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0013_alter_mensagem_comentario_alter_mensagem_feedback'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mensagem',
            name='comentario',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='mensagem',
            name='feedback',
            field=models.CharField(blank=True, choices=[('positive', 'Positivo'), ('negative', 'Negativo')], default='', max_length=10),
        ),
    ]
