from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from moneyrun import views

router = DefaultRouter()
router.register(r'groups', views.RunGroupViewSet, basename='groups')
router.register(r'members', views.MemberViewSet, basename='members')
router.register(r'goals', views.GoalViewSet, basename='goals')
router.register(r'contributions', views.ContributionViewSet, basename='contributions')
router.register(r'expenses', views.ExpenseViewSet, basename='expenses')
router.register(r'penalties', views.PenaltyViewSet, basename='penalties')
router.register(r'badges', views.BadgeViewSet, basename='badges')
router.register(r'feed', views.FeedEventViewSet, basename='feed')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/signup/', views.signup, name='signup'),
    path('api/auth/login/', views.login, name='login'),
    path('api/auth/logout/', views.logout, name='logout'),
    path('api/auth/me/', views.me, name='me'),
    path('api/auth/avatar/', views.upload_avatar, name='upload-avatar'),
    path('api/dashboard/', views.dashboard, name='dashboard'),
    path('api/coach/', views.ai_coach, name='ai-coach'),
    path('api/mission-complete/', views.complete_mission, name='complete-mission'),
    path('api/invitations/<str:code>/', views.invitation_preview, name='invitation-preview'),
    path('api/invitations/<str:code>/join/', views.join_invitation, name='join-invitation'),
    path('api/notifications/', views.notifications, name='notifications'),
    path('api/notifications/read/', views.read_notifications, name='read-notifications'),
    path('api/pokes/', views.poke_member, name='poke-member'),
    path('api/bank/status/', views.bank_status, name='bank-status'),
    path('api/bank/connect/', views.connect_bank, name='connect-bank'),
    path('api/bank/transfer/', views.bank_transfer, name='bank-transfer'),
    path('api/game-reward/', views.game_reward, name='game-reward'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
