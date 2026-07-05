# Generated for MoneyRun v3 social poke, bank demo, and 1 won game rewards
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('moneyrun', '0002_userprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(default='카카오뱅크', max_length=40)),
                ('account_alias', models.CharField(default='머니런 저축 계좌', max_length=60)),
                ('account_masked', models.CharField(default='3333-**-****1234', max_length=40)),
                ('is_connected', models.BooleanField(default=False)),
                ('demo_balance', models.PositiveIntegerField(default=0)),
                ('connected_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bank_connection', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GameReward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game_type', models.CharField(choices=[('quiz', '금융 퀴즈'), ('mini', '미니 게임')], default='quiz', max_length=20)),
                ('title', models.CharField(default='오늘의 금융 퀴즈', max_length=120)),
                ('reward_amount', models.PositiveIntegerField(default=1)),
                ('success', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('goal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='game_rewards', to='moneyrun.goal')),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='game_rewards', to='moneyrun.rungroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_rewards', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Poke',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(default=0)),
                ('message', models.CharField(default='입금 잊지 말고 같이 완주하자!', max_length=180)),
                ('status', models.CharField(choices=[('sent', '전송'), ('read', '확인')], default='sent', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('goal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pokes', to='moneyrun.goal')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pokes', to='moneyrun.rungroup')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_pokes', to=settings.AUTH_USER_MODEL)),
                ('target_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_pokes', to='moneyrun.member')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
