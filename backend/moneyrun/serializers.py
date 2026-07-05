from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Badge, BankConnection, Contribution, Expense, FeedEvent, GameReward, Goal, Member, Penalty, Poke, RunGroup, UserProfile


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'display_name', 'avatar_url', 'level', 'points')

    def get_display_name(self, obj):
        return obj.first_name or obj.username

    def _profile(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return profile

    def get_avatar_url(self, obj):
        profile = self._profile(obj)
        if not profile.avatar:
            return ''
        request = self.context.get('request')
        url = profile.avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_level(self, obj):
        return self._profile(obj).level

    def get_points(self, obj):
        return self._profile(obj).points


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=6, write_only=True)
    name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class RunGroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    owner_name = serializers.CharField(source='owner.first_name', read_only=True)
    group_type_label = serializers.CharField(source='get_group_type_display', read_only=True)
    room_mode_label = serializers.CharField(source='get_room_mode_display', read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = RunGroup
        fields = '__all__'
        read_only_fields = ('owner', 'invite_code', 'created_at')

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.owner_id == request.user.id)


class MemberSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    role_label = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Member
        fields = '__all__'
        read_only_fields = ('user', 'created_at')


class GoalSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    progress_percent = serializers.FloatField(read_only=True)
    days_left = serializers.IntegerField(read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Goal
        fields = '__all__'


class ContributionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.name', read_only=True)
    goal_title = serializers.CharField(source='goal.title', read_only=True)

    class Meta:
        model = Contribution
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.name', read_only=True)
    category_label = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Expense
        fields = '__all__'


class PenaltySerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.name', read_only=True)
    goal_title = serializers.CharField(source='goal.title', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Penalty
        fields = '__all__'


class BadgeSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = Badge
        fields = '__all__'


class FeedEventSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.name', read_only=True)
    event_type_label = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = FeedEvent
        fields = '__all__'



class PokeSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source='target_member.name', read_only=True)
    target_emoji = serializers.CharField(source='target_member.emoji', read_only=True)
    sender_name = serializers.SerializerMethodField()
    group_name = serializers.CharField(source='group.name', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Poke
        fields = '__all__'
        read_only_fields = ('sender', 'status', 'created_at')

    def get_sender_name(self, obj):
        if not obj.sender:
            return '머니런'
        return obj.sender.first_name or obj.sender.username


class BankConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankConnection
        fields = '__all__'
        read_only_fields = ('user', 'connected_at', 'updated_at')


class GameRewardSerializer(serializers.ModelSerializer):
    game_type_label = serializers.CharField(source='get_game_type_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = GameReward
        fields = '__all__'
        read_only_fields = ('user', 'group', 'goal', 'reward_amount', 'success', 'created_at')
