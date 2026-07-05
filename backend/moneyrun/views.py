from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Badge, BankConnection, Contribution, Expense, FeedEvent, GameReward, Goal, Member, Penalty, Poke, RunGroup, UserProfile
from .serializers import (
    BadgeSerializer,
    ContributionSerializer,
    ExpenseSerializer,
    FeedEventSerializer,
    GoalSerializer,
    LoginSerializer,
    MemberSerializer,
    PenaltySerializer,
    PokeSerializer,
    BankConnectionSerializer,
    GameRewardSerializer,
    RunGroupSerializer,
    SignupSerializer,
    UserSerializer,
)


EMOJIS = ['🏃', '🐰', '🦊', '🐱', '🐻', '🐼', '🐶', '🐹', '🦁', '🐯']


def _positive_int(value, default=0):
    try:
        number = int(str(value or '').replace(',', '').strip())
    except (TypeError, ValueError):
        return default
    return max(number, 0)


def _display_name(user):
    return user.first_name or user.username


def _user_groups(user):
    if not user.is_authenticated:
        return RunGroup.objects.none()
    return RunGroup.objects.filter(Q(owner=user) | Q(members__user=user)).distinct().order_by('-created_at')


def _has_group_access(user, group):
    return group and (group.owner_id == user.id or Member.objects.filter(group=group, user=user).exists())


def _ensure_member(user, group, name=None):
    member = Member.objects.filter(group=group, user=user).first()
    if member:
        return member, False
    count = Member.objects.filter(group=group).count()
    member = Member.objects.create(
        group=group,
        user=user,
        name=name or _display_name(user),
        role=Member.Role.RUNNER,
        emoji=EMOJIS[count % len(EMOJIS)],
        weekly_budget=100000,
    )
    return member, True


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username'].strip()
    password = serializer.validated_data['password']
    name = serializer.validated_data.get('name') or username
    email = serializer.validated_data.get('email') or ''

    if User.objects.filter(username=username).exists():
        return Response({'detail': '이미 사용 중인 아이디입니다.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
    token, _ = Token.objects.get_or_create(user=user)
    UserProfile.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UserSerializer(user, context={'request': request}).data}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(username=serializer.validated_data['username'], password=serializer.validated_data['password'])
    if not user:
        return Response({'detail': '아이디 또는 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)
    token, _ = Token.objects.get_or_create(user=user)
    UserProfile.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UserSerializer(user, context={'request': request}).data})


@api_view(['POST'])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response({'detail': '로그아웃되었습니다.'})


@api_view(['GET'])
def me(request):
    return Response({'user': UserSerializer(request.user, context={'request': request}).data})


@api_view(['POST'])
def upload_avatar(request):
    avatar = request.FILES.get('avatar')
    if not avatar:
        return Response({'detail': '업로드할 이미지를 선택해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    if not avatar.content_type.startswith('image/'):
        return Response({'detail': '이미지 파일만 업로드할 수 있어요.'}, status=status.HTTP_400_BAD_REQUEST)

    if avatar.size > 5 * 1024 * 1024:
        return Response({'detail': '프로필 이미지는 5MB 이하만 가능해요.'}, status=status.HTTP_400_BAD_REQUEST)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.avatar:
        profile.avatar.delete(save=False)
    profile.avatar = avatar
    profile.save(update_fields=['avatar', 'updated_at'])
    return Response({'user': UserSerializer(request.user, context={'request': request}).data})


class RunGroupViewSet(viewsets.ModelViewSet):
    serializer_class = RunGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _user_groups(self.request.user)

    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        member, _ = _ensure_member(
            self.request.user,
            group,
            name=self.request.data.get('member_name') or _display_name(self.request.user),
        )
        member.role = Member.Role.PACER
        member.save(update_fields=['role'])
        FeedEvent.objects.create(
            group=group,
            member=member,
            event_type=FeedEvent.EventType.GROUP,
            message=f'{member.name}님이 “{group.name}” 그룹을 만들었어요.',
        )

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        group = self.get_object()
        if group.owner_id == request.user.id:
            return Response({'detail': '방장은 그룹을 나갈 수 없습니다. 그룹 삭제 기능을 사용하세요.'}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = Member.objects.filter(group=group, user=request.user).delete()
        if deleted:
            FeedEvent.objects.create(group=group, event_type=FeedEvent.EventType.JOIN, message=f'{_display_name(request.user)}님이 그룹을 나갔어요.')
        return Response({'detail': '그룹에서 나갔습니다.'})


class MemberViewSet(viewsets.ModelViewSet):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Member.objects.select_related('group', 'user').filter(group__in=_user_groups(self.request.user)).order_by('id')
        group_id = self.request.query_params.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        return queryset

    def perform_create(self, serializer):
        group = serializer.validated_data['group']
        if not _has_group_access(self.request.user, group):
            raise permissions.PermissionDenied('이 그룹에 멤버를 추가할 권한이 없습니다.')
        serializer.save()


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Goal.objects.select_related('group').filter(group__in=_user_groups(self.request.user)).order_by('-created_at')
        group_id = self.request.query_params.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        return queryset

    def perform_create(self, serializer):
        group = serializer.validated_data['group']
        if not _has_group_access(self.request.user, group):
            raise permissions.PermissionDenied('이 그룹에 목표를 만들 권한이 없습니다.')
        goal = serializer.save()
        FeedEvent.objects.create(group=group, event_type=FeedEvent.EventType.MISSION, message=f'새 목표 “{goal.title}”가 시작됐어요.')


class ContributionViewSet(viewsets.ModelViewSet):
    serializer_class = ContributionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contribution.objects.select_related('goal', 'member').filter(goal__group__in=_user_groups(self.request.user)).order_by('-created_at')

    def perform_create(self, serializer):
        goal = serializer.validated_data['goal']
        member = serializer.validated_data['member']
        if not _has_group_access(self.request.user, goal.group) or member.group_id != goal.group_id:
            raise permissions.PermissionDenied('이 저축 기록을 추가할 권한이 없습니다.')
        serializer.save()


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Expense.objects.select_related('member', 'member__group').filter(member__group__in=_user_groups(self.request.user)).order_by('-expense_date')
        member_id = self.request.query_params.get('member')
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        return queryset

    def perform_create(self, serializer):
        member = serializer.validated_data['member']
        if not _has_group_access(self.request.user, member.group):
            raise permissions.PermissionDenied('이 소비 기록을 추가할 권한이 없습니다.')
        serializer.save()


class PenaltyViewSet(viewsets.ModelViewSet):
    serializer_class = PenaltySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Penalty.objects.select_related('goal', 'member').filter(goal__group__in=_user_groups(self.request.user)).order_by('-created_at')

    def perform_create(self, serializer):
        goal = serializer.validated_data['goal']
        member = serializer.validated_data['member']
        if not _has_group_access(self.request.user, goal.group) or member.group_id != goal.group_id:
            raise permissions.PermissionDenied('이 약속금을 요청할 권한이 없습니다.')
        serializer.save()


class BadgeViewSet(viewsets.ModelViewSet):
    serializer_class = BadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Badge.objects.select_related('group').filter(group__in=_user_groups(self.request.user)).order_by('-earned_at')
        group_id = self.request.query_params.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        return queryset


class FeedEventViewSet(viewsets.ModelViewSet):
    serializer_class = FeedEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = FeedEvent.objects.select_related('group', 'member').filter(group__in=_user_groups(self.request.user)).order_by('-created_at')
        group_id = self.request.query_params.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        return queryset[:30]


def _risk_score(goal, members):
    today = timezone.localdate()
    total_days = max((goal.end_date - goal.start_date).days, 1)
    passed_days = max((today - goal.start_date).days, 0)
    expected_progress = min(passed_days / total_days * 100, 100)
    progress_gap = max(expected_progress - goal.progress_percent, 0)

    week_start = today - timedelta(days=today.weekday())
    over_budget_members = 0
    for member in members:
        spent = Expense.objects.filter(member=member, expense_date__gte=week_start).aggregate(total=Sum('amount'))['total'] or 0
        if spent > member.weekly_budget * 0.8:
            over_budget_members += 1

    return round(min(progress_gap * 1.2 + over_budget_members * 12, 95), 1)


@api_view(['GET'])
def dashboard(request):
    groups = _user_groups(request.user)
    group_id = request.query_params.get('group')
    group = groups.filter(id=group_id).first() if group_id else groups.first()
    if not group:
        return Response({
            'groups': [],
            'group': None,
            'goal': None,
            'risk_score': 0,
            'members': [],
            'category_spending': [],
            'feed': [],
            'badges': [],
            'notifications': [],
            'bank': None,
        })

    goal = Goal.objects.filter(group=group, status=Goal.Status.ACTIVE).order_by('-created_at').first()
    if not goal:
        goal = Goal.objects.filter(group=group).order_by('-created_at').first()

    members = list(Member.objects.filter(group=group))
    week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())

    member_cards = []
    for member in members:
        spent = Expense.objects.filter(member=member, expense_date__gte=week_start).aggregate(total=Sum('amount'))['total'] or 0
        saved = Contribution.objects.filter(member=member, goal__group=group).aggregate(total=Sum('amount'))['total'] or 0
        budget_rate = round(spent / member.weekly_budget * 100, 1) if member.weekly_budget else 0
        member_cards.append({
            'id': member.id,
            'name': member.name,
            'emoji': member.emoji,
            'role': member.get_role_display(),
            'weekly_budget': member.weekly_budget,
            'weekly_spent': spent,
            'budget_rate': budget_rate,
            'saved': saved,
            'is_me': member.user_id == request.user.id,
            'status': '위험' if budget_rate >= 90 else '주의' if budget_rate >= 70 else '안정',
        })

    category_spending = defaultdict(int)
    for expense in Expense.objects.filter(member__group=group, expense_date__gte=week_start):
        category_spending[expense.get_category_display()] += expense.amount

    risk = _risk_score(goal, members) if goal else 0
    feed = FeedEventSerializer(FeedEvent.objects.filter(group=group)[:10], many=True).data
    badges = BadgeSerializer(Badge.objects.filter(group=group)[:8], many=True).data
    notifications = PokeSerializer(Poke.objects.filter(group=group, target_member__user=request.user)[:5], many=True).data
    bank, _ = BankConnection.objects.get_or_create(user=request.user)

    return Response({
        'groups': RunGroupSerializer(groups, many=True, context={'request': request}).data,
        'group': RunGroupSerializer(group, context={'request': request}).data,
        'goal': GoalSerializer(goal).data if goal else None,
        'risk_score': risk,
        'members': member_cards,
        'category_spending': [{'category': key, 'amount': value} for key, value in category_spending.items()],
        'feed': feed,
        'badges': badges,
        'notifications': notifications,
        'bank': BankConnectionSerializer(bank).data,
    })


@api_view(['GET'])
def ai_coach(request):
    group_id = request.query_params.get('group')
    groups = _user_groups(request.user)
    group = groups.filter(id=group_id).first() if group_id else groups.first()
    if not group:
        return Response({'messages': ['아직 참여 중인 그룹이 없습니다. 그룹을 만들거나 초대 링크로 참여해보세요.']})

    goal = Goal.objects.filter(group=group, status=Goal.Status.ACTIVE).order_by('-created_at').first()
    members = list(Member.objects.filter(group=group))
    if not goal:
        return Response({'messages': ['진행 중인 목표가 없습니다. 새 금융 러닝 목표를 만들어보세요.']})

    week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
    risk = _risk_score(goal, members)
    messages = [
        f'현재 {group.name} 목표 달성률은 {goal.progress_percent}%입니다. 남은 기간은 {goal.days_left}일이에요.',
        f'AI 페이서가 계산한 이번 주 실패 위험도는 {risk}%입니다.',
    ]

    for member in members:
        spent = Expense.objects.filter(member=member, expense_date__gte=week_start).aggregate(total=Sum('amount'))['total'] or 0
        if spent >= member.weekly_budget * 0.9:
            messages.append(f'{member.name}님은 주간 예산의 {round(spent / member.weekly_budget * 100)}%를 사용했어요. 오늘은 무지출 미션을 추천합니다.')
        elif spent >= member.weekly_budget * 0.7:
            messages.append(f'{member.name}님은 예산 소진 속도가 빨라요. 카페/배달 소비를 한 번만 줄이면 안정권입니다.')

    if goal.progress_percent < 50 and goal.days_left <= 14:
        messages.append('목표 기한이 가까운데 달성률이 낮습니다. 3일 단기 스퍼트 미션을 열어보세요.')
    if len(messages) == 2:
        messages.append('이번 주는 안정적입니다. 그룹 응원 피드로 분위기를 유지해보세요.')

    return Response({'messages': messages})


@api_view(['POST'])
def complete_mission(request):
    member_id = request.data.get('member')
    goal_id = request.data.get('goal')
    mission = request.data.get('mission', '오늘의 절약 미션')
    amount = _positive_int(request.data.get('amount'), 5000)

    if amount <= 0:
        return Response({'detail': '보상 저축액은 1원 이상이어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    member = Member.objects.filter(id=member_id).first()
    goal = Goal.objects.filter(id=goal_id).first()
    if not member or not goal or member.group_id != goal.group_id:
        return Response({'detail': 'member와 goal 정보가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)
    if not _has_group_access(request.user, goal.group):
        return Response({'detail': '이 그룹의 미션을 완료할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    Contribution.objects.create(member=member, goal=goal, amount=amount, memo=mission)
    FeedEvent.objects.create(
        group=goal.group,
        member=member,
        event_type=FeedEvent.EventType.MISSION,
        message=f'{member.name}님이 “{mission}” 미션을 클리어했어요. 보상 저축 {amount:,}원!',
    )

    if goal.progress_percent >= 25 and not Badge.objects.filter(group=goal.group, name='첫 번째 체크포인트').exists():
        Badge.objects.create(group=goal.group, name='첫 번째 체크포인트', description='목표 달성률 25% 돌파', icon='🚩')
    if goal.progress_percent >= 50 and not Badge.objects.filter(group=goal.group, name='하프 마라톤').exists():
        Badge.objects.create(group=goal.group, name='하프 마라톤', description='목표 달성률 50% 돌파', icon='🏃')
    if goal.progress_percent >= 100 and not Badge.objects.filter(group=goal.group, name='완주 성공').exists():
        Badge.objects.create(group=goal.group, name='완주 성공', description='공동 금융 목표 달성', icon='🏆')

    return Response({'detail': '미션 완료', 'goal': GoalSerializer(goal).data})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def invitation_preview(request, code):
    group = RunGroup.objects.filter(invite_code=code).first()
    if not group:
        return Response({'detail': '유효하지 않은 초대 링크입니다.'}, status=status.HTTP_404_NOT_FOUND)
    active_goal = Goal.objects.filter(group=group, status=Goal.Status.ACTIVE).order_by('-created_at').first()
    return Response({
        'group': RunGroupSerializer(group, context={'request': request}).data,
        'goal': GoalSerializer(active_goal).data if active_goal else None,
    })


@api_view(['POST'])
def join_invitation(request, code):
    group = RunGroup.objects.filter(invite_code=code).first()
    if not group:
        return Response({'detail': '유효하지 않은 초대 링크입니다.'}, status=status.HTTP_404_NOT_FOUND)
    member, created = _ensure_member(request.user, group, name=request.data.get('name') or _display_name(request.user))
    if created:
        FeedEvent.objects.create(
            group=group,
            member=member,
            event_type=FeedEvent.EventType.JOIN,
            message=f'{member.name}님이 초대 링크로 그룹에 참여했어요.',
        )
    return Response({
        'detail': '그룹에 참여했습니다.' if created else '이미 참여 중인 그룹입니다.',
        'group': RunGroupSerializer(group, context={'request': request}).data,
        'member': MemberSerializer(member).data,
    })



@api_view(['GET'])
def notifications(request):
    queryset = Poke.objects.select_related('group', 'target_member', 'sender').filter(target_member__user=request.user)[:30]
    return Response({'notifications': PokeSerializer(queryset, many=True).data})


@api_view(['POST'])
def read_notifications(request):
    ids = request.data.get('ids') or []
    qs = Poke.objects.filter(target_member__user=request.user)
    if ids:
        qs = qs.filter(id__in=ids)
    qs.update(status=Poke.Status.READ)
    return Response({'detail': '알림을 확인 처리했어요.'})


@api_view(['POST'])
def poke_member(request):
    target_member_id = request.data.get('target_member')
    group_id = request.data.get('group')
    amount = _positive_int(request.data.get('amount'), 0)
    message = request.data.get('message') or '입금 잊지 말고 같이 완주하자!'

    group = _user_groups(request.user).filter(id=group_id).first()
    if not group:
        return Response({'detail': '이 그룹에 접근할 수 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

    target = Member.objects.filter(id=target_member_id, group=group).first()
    if not target:
        return Response({'detail': '찌를 친구를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    if target.user_id == request.user.id:
        return Response({'detail': '자기 자신은 찌를 수 없어요.'}, status=status.HTTP_400_BAD_REQUEST)

    goal = Goal.objects.filter(group=group, status=Goal.Status.ACTIVE).order_by('-created_at').first()
    poke = Poke.objects.create(
        group=group,
        goal=goal,
        sender=request.user,
        target_member=target,
        amount=amount,
        message=message,
    )
    sender_name = _display_name(request.user)
    FeedEvent.objects.create(
        group=group,
        member=target,
        event_type=FeedEvent.EventType.POKE,
        message=f'{sender_name}님이 {target.name}님을 콕 찔렀어요. {message}',
    )
    share_text = f'머니런 알림: {sender_name}님이 {target.name}님을 콕 찔렀어요! {message}'
    if amount:
        share_text += f' 요청 금액 {amount:,}원'
    return Response({
        'detail': f'{target.name}님에게 찌르기 알림을 보냈어요.',
        'poke': PokeSerializer(poke).data,
        'share_text': share_text,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def bank_status(request):
    bank, _ = BankConnection.objects.get_or_create(user=request.user)
    return Response({'bank': BankConnectionSerializer(bank).data})


@api_view(['POST'])
def connect_bank(request):
    bank, _ = BankConnection.objects.get_or_create(user=request.user)
    bank.is_connected = True
    bank.bank_name = request.data.get('bank_name') or '카카오뱅크'
    bank.account_alias = request.data.get('account_alias') or '머니런 저축 계좌'
    bank.account_masked = request.data.get('account_masked') or '3333-**-****1234'
    bank.demo_balance = _positive_int(request.data.get('demo_balance'), bank.demo_balance or 0)
    bank.connected_at = timezone.now()
    bank.save()
    FeedEvent.objects.filter(group__in=_user_groups(request.user)).first()
    for group in _user_groups(request.user)[:3]:
        FeedEvent.objects.create(
            group=group,
            event_type=FeedEvent.EventType.BANK,
            message=f'{_display_name(request.user)}님이 {bank.bank_name} 계좌를 연결했어요. 이제 입금 인증 데모를 사용할 수 있어요.',
        )
    return Response({'detail': f'{bank.bank_name} 계좌 연결 데모가 완료됐어요.', 'bank': BankConnectionSerializer(bank).data})


@api_view(['POST'])
def bank_transfer(request):
    group_id = request.data.get('group')
    goal_id = request.data.get('goal')
    member_id = request.data.get('member')
    amount = _positive_int(request.data.get('amount'), 0)

    if amount <= 0:
        return Response({'detail': '이체 금액은 1원 이상이어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    group = _user_groups(request.user).filter(id=group_id).first()
    if not group:
        return Response({'detail': '이 그룹에 접근할 수 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
    transfer_type = 'meeting_account' if group.room_mode == RunGroup.RoomMode.ACCOUNT else 'challenge'
    memo = request.data.get('memo') or ('모임통장 입금' if transfer_type == 'meeting_account' else '목표 챌린지 적립')

    goal = Goal.objects.filter(id=goal_id, group=group).first()
    if not goal:
        goal = Goal.objects.filter(group=group, status=Goal.Status.ACTIVE).order_by('-created_at').first()
    if not goal:
        return Response({'detail': '입금할 목표 또는 모임통장을 먼저 만들어주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    member = Member.objects.filter(id=member_id, group=group).first()
    if not member:
        member, _ = _ensure_member(request.user, group)
    if member.group_id != group.id:
        return Response({'detail': '러너 정보가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    bank, _ = BankConnection.objects.get_or_create(user=request.user)
    if not bank.is_connected:
        return Response({'detail': '은행 계좌를 먼저 연결해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    bank.demo_balance = (bank.demo_balance or 0) + amount
    bank.save(update_fields=['demo_balance', 'updated_at'])
    contribution = Contribution.objects.create(member=member, goal=goal, amount=amount, memo=memo)
    FeedEvent.objects.create(
        group=group,
        member=member,
        event_type=FeedEvent.EventType.BANK,
        message=f'{member.name}님이 {bank.bank_name}에서 {amount:,}원을 {"모임통장에 입금" if transfer_type == "meeting_account" else "목표에 적립"}했어요.',
    )
    return Response({
        'detail': f'{amount:,}원이 {"모임통장에 입금" if transfer_type == "meeting_account" else "목표에 적립"}됐어요.',
        'bank': BankConnectionSerializer(bank).data,
        'contribution': ContributionSerializer(contribution).data,
        'goal': GoalSerializer(goal).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def game_reward(request):
    group_id = request.data.get('group')
    game_type = request.data.get('game_type') or GameReward.GameType.QUIZ
    title = request.data.get('title') or '오늘의 금융 퀴즈'
    success = bool(request.data.get('success', True))

    group = _user_groups(request.user).filter(id=group_id).first() if group_id else _user_groups(request.user).first()
    goal = Goal.objects.filter(group=group, status=Goal.Status.ACTIVE).order_by('-created_at').first() if group else None
    reward_amount = 1 if success else 0

    reward = GameReward.objects.create(
        user=request.user,
        group=group,
        goal=goal,
        game_type=game_type,
        title=title,
        success=success,
        reward_amount=reward_amount,
    )

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if success:
        profile.points += 1
        profile.save(update_fields=['points', 'updated_at'])
        if group:
            member, _ = _ensure_member(request.user, group)
            if goal:
                Contribution.objects.create(member=member, goal=goal, amount=1, memo=f'{title} 1원 리워드')
            FeedEvent.objects.create(
                group=group,
                member=member,
                event_type=FeedEvent.EventType.GAME,
                message=f'{member.name}님이 {title}에 성공해서 1원을 적립했어요. 작지만 확실한 완주 포인트!',
            )

    detail = '정답! 1원이 적립됐어요.' if success else '아쉽지만 다음 문제에 다시 도전해요.'
    return Response({'detail': detail, 'reward': GameRewardSerializer(reward).data, 'user': UserSerializer(request.user, context={'request': request}).data})
