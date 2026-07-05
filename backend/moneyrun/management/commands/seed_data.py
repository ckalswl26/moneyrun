from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token

from moneyrun.models import Badge, BankConnection, Contribution, Expense, FeedEvent, GameReward, Goal, Member, Penalty, Poke, RunGroup, UserProfile


class Command(BaseCommand):
    help = 'MoneyRun 실제 앱 시연용 사용자/그룹/목표 더미 데이터를 생성합니다.'

    def handle(self, *args, **options):
        Poke.objects.all().delete()
        GameReward.objects.all().delete()
        BankConnection.objects.all().delete()
        Penalty.objects.all().delete()
        Contribution.objects.all().delete()
        Expense.objects.all().delete()
        FeedEvent.objects.all().delete()
        Badge.objects.all().delete()
        Goal.objects.all().delete()
        Member.objects.all().delete()
        RunGroup.objects.all().delete()
        Token.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        def make_user(username, name):
            user = User.objects.create_user(username=username, password='moneyrun1234', first_name=name)
            Token.objects.get_or_create(user=user)
            UserProfile.objects.get_or_create(user=user)
            return user

        minji_user = make_user('minji', '민지')
        hyunwoo_user = make_user('hyunwoo', '현우')
        jisoo_user = make_user('jisoo', '지수')
        taeho_user = make_user('taeho', '태호')

        group = RunGroup.objects.create(
            owner=minji_user,
            name='제주런 4인팟',
            description='제주도 여행비 120만 원을 함께 모으는 금융 러닝 챌린지',
            room_mode=RunGroup.RoomMode.CHALLENGE,
            group_type=RunGroup.GroupType.FRIEND,
            invite_code='RUN2026',
        )

        minji = Member.objects.create(group=group, user=minji_user, name='민지', role=Member.Role.PACER, weekly_budget=90000, emoji='🐰')
        hyunwoo = Member.objects.create(group=group, user=hyunwoo_user, name='현우', role=Member.Role.RUNNER, weekly_budget=110000, emoji='🦊')
        jisoo = Member.objects.create(group=group, user=jisoo_user, name='지수', role=Member.Role.TREASURER, weekly_budget=85000, emoji='🐱')
        taeho = Member.objects.create(group=group, user=taeho_user, name='태호', role=Member.Role.RUNNER, weekly_budget=100000, emoji='🐻')

        today = timezone.localdate()
        goal = Goal.objects.create(
            group=group,
            title='제주도 여행비 120만 원 모으기',
            target_amount=1200000,
            current_amount=0,
            start_date=today - timedelta(days=14),
            end_date=today + timedelta(days=28),
            mission_rule='주 2회 무지출, 카페 지출 2만 원 이하, 실패 시 약속금 3천 원',
            reward_text='목표 달성 시 제주 맛집 예산 10만 원 추가',
        )

        for member, amount in [(minji, 160000), (hyunwoo, 140000), (jisoo, 180000), (taeho, 120000)]:
            Contribution.objects.create(goal=goal, member=member, amount=amount, memo='정기 저축')

        expenses = [
            (minji, 5800, 'cafe', '아이스라떼', 0),
            (minji, 17000, 'food', '점심', 1),
            (minji, 12500, 'transport', '택시', 2),
            (hyunwoo, 28000, 'food', '배달', 0),
            (hyunwoo, 9400, 'cafe', '스터디 카페', 1),
            (jisoo, 4500, 'cafe', '커피', 0),
            (jisoo, 13000, 'food', '김밥/분식', 2),
            (taeho, 49000, 'shopping', '운동화 할인', 0),
            (taeho, 21000, 'culture', '영화', 1),
        ]
        for member, amount, category, memo, days_ago in expenses:
            Expense.objects.create(
                member=member,
                amount=amount,
                category=category,
                memo=memo,
                expense_date=today - timedelta(days=days_ago),
            )

        Penalty.objects.create(goal=goal, member=taeho, amount=3000, reason='쇼핑 예산 초과 위험')
        Poke.objects.create(group=group, goal=goal, sender=minji_user, target_member=taeho, amount=10000, message='태호야 오늘 1만 원만 넣으면 우리 페이스 회복!')
        GameReward.objects.create(user=minji_user, group=group, goal=goal, game_type=GameReward.GameType.QUIZ, title='오늘의 금융 퀴즈', reward_amount=1, success=True)
        BankConnection.objects.create(user=minji_user, is_connected=True, account_alias='머니런 공동 저축 계좌', account_masked='3333-**-****2026', demo_balance=600001, connected_at=timezone.now())
        Badge.objects.create(group=group, name='첫 러닝 시작', description='공동 금융 목표를 시작했어요', icon='🏁')
        Badge.objects.create(group=group, name='7일 연속 체크인', description='일주일 동안 소비 기록을 유지했어요', icon='🔥')
        FeedEvent.objects.create(group=group, member=jisoo, event_type=FeedEvent.EventType.CHEER, message='지수님이 모두에게 응원 이모티콘을 보냈어요. “이번 주도 완주하자!”')
        FeedEvent.objects.create(group=group, event_type=FeedEvent.EventType.WARNING, message='AI 페이서: 이번 주 쇼핑/카페 지출이 높아 목표 실패 위험이 상승했어요.')

        self.stdout.write(self.style.SUCCESS('MoneyRun 더미 데이터 생성 완료!'))
        self.stdout.write('시연 계정: minji / moneyrun1234')
        self.stdout.write(f'초대링크: http://localhost:5175/invite/{group.invite_code}')
