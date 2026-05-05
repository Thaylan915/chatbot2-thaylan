from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0008_backfill_conversa_titulos'),
    ]

    operations = [
        migrations.AddField(
            model_name='mensagem',
            name='respondida',
            field=models.BooleanField(
                blank=True,
                null=True,
                help_text=(
                    "Apenas para role='assistant'. True quando o modelo encontrou resposta "
                    "no contexto; False quando declarou desconhecimento. NULL para mensagens "
                    "do usuário ou registros antigos (pré-instrumentação)."
                ),
            ),
        ),
    ]
