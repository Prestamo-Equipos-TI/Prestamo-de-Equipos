from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0002_registrogestionusuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='debe_cambiar_clave',
            field=models.BooleanField(default=False),
        ),
    ]
