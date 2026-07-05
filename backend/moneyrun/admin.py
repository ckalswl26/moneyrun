from django.contrib import admin
from .models import Badge, BankConnection, Contribution, Expense, FeedEvent, GameReward, Goal, Member, Penalty, Poke, RunGroup, UserProfile


@admin.register(RunGroup)
class RunGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'room_mode', 'group_type', 'invite_code', 'created_at')
    search_fields = ('name', 'invite_code', 'owner__username')
    list_filter = ('room_mode', 'group_type')


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'group', 'role', 'weekly_budget')
    list_filter = ('role', 'group')
    search_fields = ('name', 'user__username', 'group__name')


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'target_amount', 'current_amount', 'status', 'end_date')
    list_filter = ('status', 'group')


admin.site.register(Contribution)
admin.site.register(Expense)
admin.site.register(Penalty)
admin.site.register(Badge)
admin.site.register(FeedEvent)
admin.site.register(Poke)
admin.site.register(BankConnection)
admin.site.register(GameReward)
admin.site.register(UserProfile)
