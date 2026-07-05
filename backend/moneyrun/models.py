import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def generate_invite_code():
    return 'RUN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.FileField(upload_to='avatars/', blank=True, null=True)
    level = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField(default=12450)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} profile'


class RunGroup(models.Model):
    class GroupType(models.TextChoices):
        FRIEND = 'friend', '친구'
        COUPLE = 'couple', '커플'
        STUDY = 'study', '스터디'
        FAMILY = 'family', '가족'
        ETC = 'etc', '기타'

    class RoomMode(models.TextChoices):
        CHALLENGE = 'challenge', '목표 챌린지'
        ACCOUNT = 'account', '모임통장'

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_run_groups')
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    room_mode = models.CharField(max_length=20, choices=RoomMode.choices, default=RoomMode.CHALLENGE)
    group_type = models.CharField(max_length=20, choices=GroupType.choices, default=GroupType.FRIEND)
    invite_code = models.CharField(max_length=12, unique=True, default=generate_invite_code)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = generate_invite_code()
        while RunGroup.objects.filter(invite_code=self.invite_code).exclude(pk=self.pk).exists():
            self.invite_code = generate_invite_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Member(models.Model):
    class Role(models.TextChoices):
        RUNNER = 'runner', '러너'
        PACER = 'pacer', '페이서'
        TREASURER = 'treasurer', '금고지기'

    group = models.ForeignKey(RunGroup, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='run_memberships')
    name = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RUNNER)
    weekly_budget = models.PositiveIntegerField(default=100000)
    emoji = models.CharField(max_length=8, default='🏃')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.name}({self.group.name})'


class Goal(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', '진행중'
        SUCCESS = 'success', '성공'
        FAILED = 'failed', '실패'

    group = models.ForeignKey(RunGroup, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=120)
    target_amount = models.PositiveIntegerField()
    current_amount = models.PositiveIntegerField(default=0)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    mission_rule = models.CharField(max_length=160, blank=True)
    reward_text = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def progress_percent(self):
        if self.target_amount == 0:
            return 0
        return min(round(self.current_amount / self.target_amount * 100, 1), 100)

    @property
    def days_left(self):
        return max((self.end_date - timezone.localdate()).days, 0)

    def __str__(self):
        return self.title


class Contribution(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='contributions')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='contributions')
    amount = models.PositiveIntegerField()
    memo = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            goal = self.goal
            goal.current_amount += self.amount
            if goal.current_amount >= goal.target_amount:
                goal.status = Goal.Status.SUCCESS
            goal.save(update_fields=['current_amount', 'status'])
            FeedEvent.objects.create(
                group=goal.group,
                member=self.member,
                event_type=FeedEvent.EventType.CONTRIBUTION,
                message=f'{self.member.name}님이 {self.amount:,}원을 저축했어요.',
            )

    def __str__(self):
        return f'{self.member.name} +{self.amount}'


class Expense(models.Model):
    class Category(models.TextChoices):
        FOOD = 'food', '식비'
        CAFE = 'cafe', '카페'
        TRANSPORT = 'transport', '교통'
        SHOPPING = 'shopping', '쇼핑'
        CULTURE = 'culture', '문화'
        ETC = 'etc', '기타'

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='expenses')
    amount = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ETC)
    memo = models.CharField(max_length=120, blank=True)
    expense_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.member.name} {self.category} {self.amount}'


class Penalty(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', '요청'
        PAID = 'paid', '납부완료'
        WAIVED = 'waived', '면제'

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='penalties')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='penalties')
    amount = models.PositiveIntegerField(default=3000)
    reason = models.CharField(max_length=160)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            FeedEvent.objects.create(
                group=self.goal.group,
                member=self.member,
                event_type=FeedEvent.EventType.PENALTY,
                message=f'{self.member.name}님에게 약속금 {self.amount:,}원이 요청됐어요. 사유: {self.reason}',
            )

    def __str__(self):
        return f'{self.member.name} penalty {self.amount}'


class Badge(models.Model):
    group = models.ForeignKey(RunGroup, on_delete=models.CASCADE, related_name='badges')
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=160)
    icon = models.CharField(max_length=8, default='🏅')
    earned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FeedEvent(models.Model):
    class EventType(models.TextChoices):
        CONTRIBUTION = 'contribution', '저축'
        WARNING = 'warning', '경고'
        CHEER = 'cheer', '응원'
        PENALTY = 'penalty', '약속금'
        BADGE = 'badge', '배지'
        MISSION = 'mission', '미션'
        JOIN = 'join', '참여'
        GROUP = 'group', '그룹'
        POKE = 'poke', '찌르기'
        GAME = 'game', '게임보상'
        BANK = 'bank', '은행연동'

    group = models.ForeignKey(RunGroup, on_delete=models.CASCADE, related_name='feed_events')
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='feed_events')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    message = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message



class Poke(models.Model):
    class Status(models.TextChoices):
        SENT = 'sent', '전송'
        READ = 'read', '확인'

    group = models.ForeignKey(RunGroup, on_delete=models.CASCADE, related_name='pokes')
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name='pokes')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_pokes')
    target_member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='received_pokes')
    amount = models.PositiveIntegerField(default=0)
    message = models.CharField(max_length=180, default='입금 잊지 말고 같이 완주하자!')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.target_member.name} poke'


class BankConnection(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bank_connection')
    bank_name = models.CharField(max_length=40, default='카카오뱅크')
    account_alias = models.CharField(max_length=60, default='머니런 저축 계좌')
    account_masked = models.CharField(max_length=40, default='3333-**-****1234')
    is_connected = models.BooleanField(default=False)
    demo_balance = models.PositiveIntegerField(default=0)
    connected_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} {self.bank_name}'


class GameReward(models.Model):
    class GameType(models.TextChoices):
        QUIZ = 'quiz', '금융 퀴즈'
        MINI = 'mini', '미니 게임'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_rewards')
    group = models.ForeignKey(RunGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='game_rewards')
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name='game_rewards')
    game_type = models.CharField(max_length=20, choices=GameType.choices, default=GameType.QUIZ)
    title = models.CharField(max_length=120, default='오늘의 금융 퀴즈')
    reward_amount = models.PositiveIntegerField(default=1)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} +{self.reward_amount}'
