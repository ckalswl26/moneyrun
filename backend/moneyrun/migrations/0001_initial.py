# Generated for MoneyRun MVP
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import moneyrun.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RunGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('description', models.TextField(blank=True)),
                ('group_type', models.CharField(choices=[('friend', '친구'), ('couple', '커플'), ('study', '스터디'), ('family', '가족'), ('etc', '기타')], default='friend', max_length=20)),
                ('invite_code', models.CharField(default=moneyrun.models.generate_invite_code, max_length=12, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_run_groups', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('role', models.CharField(choices=[('runner', '러너'), ('pacer', '페이서'), ('treasurer', '금고지기')], default='runner', max_length=20)),
                ('weekly_budget', models.PositiveIntegerField(default=100000)),
                ('emoji', models.CharField(default='🏃', max_length=8)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='moneyrun.rungroup')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='run_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['id']},
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('target_amount', models.PositiveIntegerField()),
                ('current_amount', models.PositiveIntegerField(default=0)),
                ('start_date', models.DateField(default=moneyrun.models.timezone.localdate)),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('active', '진행중'), ('success', '성공'), ('failed', '실패')], default='active', max_length=20)),
                ('mission_rule', models.CharField(blank=True, max_length=160)),
                ('reward_text', models.CharField(blank=True, max_length=160)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goals', to='moneyrun.rungroup')),
            ],
        ),
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('description', models.CharField(max_length=160)),
                ('icon', models.CharField(default='🏅', max_length=8)),
                ('earned_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='badges', to='moneyrun.rungroup')),
            ],
        ),
        migrations.CreateModel(
            name='Contribution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField()),
                ('memo', models.CharField(blank=True, max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('goal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contributions', to='moneyrun.goal')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contributions', to='moneyrun.member')),
            ],
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField()),
                ('category', models.CharField(choices=[('food', '식비'), ('cafe', '카페'), ('transport', '교통'), ('shopping', '쇼핑'), ('culture', '문화'), ('etc', '기타')], default='etc', max_length=20)),
                ('memo', models.CharField(blank=True, max_length=120)),
                ('expense_date', models.DateField(default=moneyrun.models.timezone.localdate)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='moneyrun.member')),
            ],
        ),
        migrations.CreateModel(
            name='FeedEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('contribution', '저축'), ('warning', '경고'), ('cheer', '응원'), ('penalty', '약속금'), ('badge', '배지'), ('mission', '미션'), ('join', '참여'), ('group', '그룹')], max_length=20)),
                ('message', models.CharField(max_length=240)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feed_events', to='moneyrun.rungroup')),
                ('member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feed_events', to='moneyrun.member')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Penalty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(default=3000)),
                ('reason', models.CharField(max_length=160)),
                ('status', models.CharField(choices=[('requested', '요청'), ('paid', '납부완료'), ('waived', '면제')], default='requested', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('goal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penalties', to='moneyrun.goal')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penalties', to='moneyrun.member')),
            ],
        ),
    ]
