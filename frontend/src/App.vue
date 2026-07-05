<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, getAuthToken, setAuthToken } from './services/api'
import brandLogo from './assets/moneyrun-logo-final.png'
import brandCharacters from './assets/moneyrun-characters-final.png'

const user = ref(null)
const authMode = ref('login')
const authForm = ref({ username: '', password: '', name: '', email: '' })
const authLoading = ref(false)
const authError = ref('')

const dashboard = ref(null)
const coachMessages = ref([])
const loading = ref(false)
const error = ref('')
const selectedGroupId = ref('')
const saving = ref(false)
const activeTab = ref('home')
const profileInput = ref(null)
const avatarUploading = ref(false)
const notifications = ref([])
const bank = ref(null)
const pokeForm = ref({ amount: '10,000', message: '입금 잊지 말고 같이 완주하자!' })
const gameLoading = ref(false)
const serviceMode = ref('challenge')
const transferForm = ref({ amount: '10,000', memo: '이번 주 자동 적립' })
const bankForm = ref({ bank_name: '카카오뱅크' })

const bankOptions = [
  'KB국민은행', '신한은행', '하나은행', '우리은행', 'NH농협은행', 'IBK기업은행',
  '카카오뱅크', '토스뱅크', '케이뱅크', 'SC제일은행', '부산은행', '대구은행',
  '광주은행', '전북은행', '새마을금고', '신협', '우체국',
]

const quiz = {
  title: '오늘의 금융 퀴즈',
  question: '목표 달성률을 가장 꾸준히 올리는 방법은?',
  options: ['한 번에 크게 모으기', '작은 금액을 자주 적립하기', '소비 기록 안 하기'],
  answer: 1,
}

const groupForm = ref({ name: '', description: '', room_mode: 'challenge', group_type: 'friend', member_name: '' })
const goalForm = ref({
  title: '',
  target_amount: '300,000',
  end_date: '',
  mission_rule: '주 2회 무지출, 실패 시 약속금 3천 원',
  reward_text: '목표 달성 시 우리끼리 리워드 받기',
})
const missionForm = ref({ member: '', mission: '오늘 커피 대신 물 마시기', amount: '5,000' })
const expenseForm = ref({ member: '', amount: '8,000', category: 'cafe', memo: '아이스라떼' })

const pendingInviteCode = ref(getInviteCodeFromUrl())
const invitePreview = ref(null)
const toast = ref('')

const tabs = [
  { id: 'home', label: '홈', icon: '🏠' },
  { id: 'groups', label: '그룹', icon: '👥' },
  { id: 'coach', label: 'AI 코치', icon: '🤖' },
  { id: 'challenge', label: '챌린지', icon: '🏆' },
  { id: 'my', label: '마이', icon: '👤' },
]

const parseMoneyInput = (value) => Number(String(value ?? '').replace(/[^0-9]/g, '')) || 0
const formatNumber = (value) => new Intl.NumberFormat('ko-KR').format(parseMoneyInput(value))
const formatWon = (value) => formatNumber(value) + '원'

function formatMoneyInput(form, key) {
  const raw = String(form[key] ?? '').replace(/[^0-9]/g, '')
  form[key] = raw ? new Intl.NumberFormat('ko-KR').format(Number(raw)) : ''
}
const progress = computed(() => dashboard.value?.goal?.progress_percent || 0)
const progressStyle = computed(() => ({ width: `${progress.value}%` }))
const myGroups = computed(() => dashboard.value?.groups || [])
const currentGroup = computed(() => dashboard.value?.group || null)
const currentGoal = computed(() => dashboard.value?.goal || null)
const currentRoomMode = computed(() => currentGroup.value?.room_mode || serviceMode.value)
const unreadNotifications = computed(() => notifications.value.filter((item) => item.status !== 'read').length)
const myMember = computed(() => dashboard.value?.members?.find((member) => member.is_me) || dashboard.value?.members?.[0] || null)
const leftAmount = computed(() => {
  if (!currentGoal.value) return 0
  return Math.max(currentGoal.value.target_amount - currentGoal.value.current_amount, 0)
})
const mySavedAmount = computed(() => myMember.value?.saved || 0)
const teamSavedAmount = computed(() => currentGoal.value?.current_amount || 0)
const teamTargetAmount = computed(() => currentGoal.value?.target_amount || 0)
const bankConnected = computed(() => Boolean(bank.value?.is_connected))
const inviteUrl = computed(() => {
  if (!currentGroup.value?.invite_code) return ''
  return `${window.location.origin}/invite/${currentGroup.value.invite_code}`
})
const riskLevel = computed(() => {
  const score = dashboard.value?.risk_score || 0
  if (score >= 70) return '위험'
  if (score >= 40) return '주의'
  return '안정'
})
const riskClass = computed(() => {
  const score = dashboard.value?.risk_score || 0
  if (score >= 70) return 'danger'
  if (score >= 40) return 'warn'
  return 'safe'
})
const dailyTarget = computed(() => {
  if (!currentGoal.value?.days_left) return leftAmount.value
  return Math.ceil(leftAmount.value / Math.max(currentGoal.value.days_left, 1))
})
const topSaver = computed(() => {
  const members = dashboard.value?.members || []
  return [...members].sort((a, b) => b.saved - a.saved)[0] || null
})
const categoryTotal = computed(() => (dashboard.value?.category_spending || []).reduce((sum, item) => sum + item.amount, 0))
const categoryMax = computed(() => Math.max(...(dashboard.value?.category_spending || []).map((item) => item.amount), 1))
const recommendedMission = computed(() => {
  const score = dashboard.value?.risk_score || 0
  if (score >= 70) return '오늘은 배달/카페 지출을 멈추고 7천 원 스퍼트 저축'
  if (score >= 40) return '가장 자주 쓰는 카테고리 하나만 쉬고 5천 원 적립'
  return '작은 성공 유지: 1원 게임과 소비 기록 체크인'
})

function getInviteCodeFromUrl() {
  const match = window.location.pathname.match(/\/invite\/([A-Z0-9]+)/i)
  return match?.[1]?.toUpperCase() || ''
}

function setToast(message) {
  toast.value = message
  setTimeout(() => {
    if (toast.value === message) toast.value = ''
  }, 2600)
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    setToast('초대 링크를 복사했어요.')
  } catch (_) {
    setToast(text)
  }
}

function initKakao() {
  const key = import.meta.env.VITE_KAKAO_JS_KEY
  if (!key || !window.Kakao) return false
  if (!window.Kakao.isInitialized()) window.Kakao.init(key)
  return true
}

async function shareKakao() {
  const url = inviteUrl.value
  if (!url || !currentGroup.value) return

  if (initKakao()) {
    window.Kakao.Share.sendDefault({
      objectType: 'feed',
      content: {
        title: `머니런 ${currentGroup.value.name} 초대`,
        description: '같이 목표 세우고, 미션 깨고, 돈 관리 완주하자!',
        imageUrl: 'https://dummyimage.com/800x400/86efac/111827&text=MoneyRun',
        link: { mobileWebUrl: url, webUrl: url },
      },
      buttons: [{ title: '초대 참여하기', link: { mobileWebUrl: url, webUrl: url } }],
    })
    return
  }

  if (navigator.share) {
    await navigator.share({ title: '머니런 초대', text: `${currentGroup.value.name}에 참여해줘!`, url })
    return
  }

  await copyText(url)
  setToast('카카오 키가 없어 링크 복사로 대체했어요.')
}

async function loadInvitePreview() {
  if (!pendingInviteCode.value) return
  try {
    invitePreview.value = await api.invitePreview(pendingInviteCode.value)
  } catch (err) {
    invitePreview.value = null
    setToast(err.message)
  }
}

async function tryAutoJoinInvite() {
  if (!pendingInviteCode.value || !user.value) return
  try {
    const result = await api.joinInvite(pendingInviteCode.value, { name: user.value.display_name })
    pendingInviteCode.value = ''
    invitePreview.value = null
    window.history.replaceState({}, '', '/')
    selectedGroupId.value = result.group.id
    activeTab.value = 'home'
    setToast(result.detail)
    await loadData(result.group.id)
  } catch (err) {
    setToast(err.message)
  }
}

async function loginOrSignup() {
  authLoading.value = true
  authError.value = ''
  try {
    const payload = authMode.value === 'login'
      ? { username: authForm.value.username, password: authForm.value.password }
      : authForm.value
    const result = authMode.value === 'login' ? await api.login(payload) : await api.signup(payload)
    setAuthToken(result.token)
    user.value = result.user
    await tryAutoJoinInvite()
    if (!dashboard.value) await loadData()
  } catch (err) {
    authError.value = err.message
    authForm.value.password = ''
  } finally {
    authLoading.value = false
  }
}

async function logout() {
  try { await api.logout() } catch (_) {}
  setAuthToken('')
  user.value = null
  dashboard.value = null
  selectedGroupId.value = ''
}

async function restoreSession() {
  if (!getAuthToken()) return
  try {
    const result = await api.me()
    user.value = result.user
  } catch (_) {
    setAuthToken('')
  }
}

async function loadData(groupId = selectedGroupId.value) {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await api.dashboard(groupId)
    notifications.value = dashboard.value.notifications || []
    bank.value = dashboard.value.bank || null
    if (dashboard.value.group) {
      selectedGroupId.value = dashboard.value.group.id
      serviceMode.value = dashboard.value.group.room_mode || 'challenge'
    }
    const coach = await api.coach(selectedGroupId.value)
    coachMessages.value = coach.messages || []
    if (!missionForm.value.member && dashboard.value.members?.length) missionForm.value.member = dashboard.value.members[0].id
    if (!expenseForm.value.member && dashboard.value.members?.length) expenseForm.value.member = dashboard.value.members[0].id
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function switchGroup(groupId) {
  selectedGroupId.value = groupId
  missionForm.value.member = ''
  expenseForm.value.member = ''
  activeTab.value = 'home'
  await loadData(groupId)
}

async function createGroup() {
  if (!groupForm.value.name) return setToast('그룹명을 입력해주세요.')
  saving.value = true
  try {
    const group = await api.createGroup({
      name: groupForm.value.name,
      description: groupForm.value.description,
      room_mode: groupForm.value.room_mode,
      group_type: groupForm.value.group_type,
      member_name: groupForm.value.member_name || user.value.display_name,
    })
    groupForm.value = { name: '', description: '', room_mode: 'challenge', group_type: 'friend', member_name: '' }
    selectedGroupId.value = group.id
    activeTab.value = 'challenge'
    setToast('새 그룹을 만들었어요. 이제 목표를 생성해보세요.')
    await loadData(group.id)
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

async function createGoal() {
  if (!currentGroup.value) return
  if (!goalForm.value.title || !goalForm.value.end_date) return setToast('목표명과 종료일을 입력해주세요.')
  saving.value = true
  try {
    await api.createGoal({ ...goalForm.value, group: currentGroup.value.id, target_amount: parseMoneyInput(goalForm.value.target_amount) })
    goalForm.value.title = ''
    goalForm.value.target_amount = '300,000'
    activeTab.value = 'home'
    setToast('새 목표를 시작했어요.')
    await loadData(currentGroup.value.id)
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

async function completeMission() {
  if (!currentGoal.value || !missionForm.value.member) return setToast('진행 중인 목표와 러너가 필요해요.')
  saving.value = true
  try {
    await api.completeMission({
      member: missionForm.value.member,
      goal: currentGoal.value.id,
      mission: missionForm.value.mission,
      amount: parseMoneyInput(missionForm.value.amount),
    })
    setToast('미션 완료! 저축 게이지가 올라갔어요.')
    await loadData(currentGroup.value.id)
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

async function addExpense() {
  if (!expenseForm.value.member) return setToast('러너를 선택해주세요.')
  saving.value = true
  try {
    await api.createExpense({ ...expenseForm.value, amount: parseMoneyInput(expenseForm.value.amount) })
    setToast('소비 기록을 추가했어요.')
    await loadData(currentGroup.value.id)
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}


async function pokeMember(member) {
  if (!currentGroup.value || !member) return
  if (member.is_me) return setToast('나 자신은 찌를 수 없어요.')
  saving.value = true
  try {
    const result = await api.pokeMember({
      group: currentGroup.value.id,
      target_member: member.id,
      amount: parseMoneyInput(pokeForm.value.amount),
      message: pokeForm.value.message,
    })
    setToast(result.detail)
    await loadData(currentGroup.value.id)
  } catch (err) {
    setToast(err.message)
  } finally {
    saving.value = false
  }
}

async function connectKakaoBankDemo() {
  saving.value = true
  try {
    const bankName = bankForm.value.bank_name || '카카오뱅크'
    const result = await api.connectBank({
      bank_name: bankName,
      account_alias: currentRoomMode.value === 'account' ? '머니런 모임통장' : '머니런 자동 적립 계좌',
      account_masked: bankName.includes('카카오') ? '3333-**-****2026' : '110-***-**2026',
    })
    bank.value = result.bank
    setToast(result.detail)
    if (currentGroup.value) await loadData(currentGroup.value.id)
  } catch (err) {
    setToast(err.message)
  } finally {
    saving.value = false
  }
}

async function transferFromBank() {
  if (!currentGroup.value || !currentGoal.value) return setToast('먼저 그룹과 목표를 만들어주세요.')
  if (!bankConnected.value) {
    await connectKakaoBankDemo()
    if (!bankConnected.value) return
  }
  saving.value = true
  try {
    const result = await api.transferFromBank({
      group: currentGroup.value.id,
      goal: currentGoal.value.id,
      member: myMember.value?.id || missionForm.value.member,
      amount: parseMoneyInput(transferForm.value.amount),
      memo: transferForm.value.memo,
      transfer_type: currentRoomMode.value === 'account' ? 'meeting_account' : 'challenge',
    })
    bank.value = result.bank
    setToast(result.detail)
    await loadData(currentGroup.value.id)
  } catch (err) {
    setToast(err.message)
  } finally {
    saving.value = false
  }
}

async function markNotificationsRead() {
  try {
    await api.readNotifications({ ids: notifications.value.map((item) => item.id) })
    notifications.value = notifications.value.map((item) => ({ ...item, status: 'read' }))
    setToast('찌르기 알림을 확인했어요.')
  } catch (err) {
    setToast(err.message)
  }
}

async function submitQuiz(index) {
  if (!currentGroup.value) return setToast('먼저 그룹을 만들어야 1원 적립을 할 수 있어요.')
  gameLoading.value = true
  try {
    const success = index === quiz.answer
    const result = await api.gameReward({
      group: currentGroup.value.id,
      game_type: 'quiz',
      title: quiz.title,
      success,
    })
    if (result.user) user.value = result.user
    setToast(result.detail)
    await loadData(currentGroup.value.id)
  } catch (err) {
    setToast(err.message)
  } finally {
    gameLoading.value = false
  }
}

async function completeMiniGame() {
  if (!currentGroup.value) return setToast('먼저 그룹을 만들어야 미니게임 보상을 받을 수 있어요.')
  gameLoading.value = true
  try {
    const result = await api.gameReward({ group: currentGroup.value.id, game_type: 'mini', title: '동전 잡기 미니게임', success: true })
    if (result.user) user.value = result.user
    setToast(result.detail)
    await loadData(currentGroup.value.id)
  } catch (err) {
    setToast(err.message)
  } finally {
    gameLoading.value = false
  }
}

function openProfilePicker() {
  profileInput.value?.click()
}

async function uploadProfileImage(event) {
  const file = event.target.files?.[0]
  if (!file) return
  avatarUploading.value = true
  try {
    const result = await api.uploadAvatar(file)
    user.value = result.user
    setToast('프로필 사진을 변경했어요.')
  } catch (err) {
    setToast(err.message)
  } finally {
    avatarUploading.value = false
    event.target.value = ''
  }
}

onMounted(async () => {
  const future = new Date()
  future.setDate(future.getDate() + 30)
  goalForm.value.end_date = future.toISOString().slice(0, 10)
  await loadInvitePreview()
  await restoreSession()
  if (user.value) {
    await tryAutoJoinInvite()
    if (!dashboard.value) await loadData()
  }
})
</script>

<template>
  <main class="phone-shell">
    <div v-if="toast" class="toast">{{ toast }}</div>

    <section v-if="!user" class="auth-screen">
      <div class="auth-visual">
        <span class="mini-badge">AI 공동 금융 챌린지</span>
        <img class="brand-image auth-logo" :src="brandLogo" alt="MoneyRun 머니런" />
        <p>함께 모으고, 함께 목표달성! 💚</p>
        <img class="character-line auth-characters" :src="brandCharacters" alt="머니런 캐릭터들" />
        <div v-if="invitePreview" class="invite-preview">
          <strong>{{ invitePreview.group.name }}</strong>
          <span>초대가 도착했어요. 로그인하면 바로 참여해요.</span>
        </div>
      </div>

      <article class="auth-card card">
        <div class="segmented">
          <button :class="{ active: authMode === 'login' }" @click="authMode = 'login'; authError = ''">로그인</button>
          <button :class="{ active: authMode === 'signup' }" @click="authMode = 'signup'; authError = ''">회원가입</button>
        </div>
        <label>아이디<input v-model="authForm.username" placeholder="minji" /></label>
        <label>비밀번호<input v-model="authForm.password" type="password" placeholder="moneyrun1234" /></label>
        <template v-if="authMode === 'signup'">
          <label>이름<input v-model="authForm.name" placeholder="민지" /></label>
          <label>이메일 선택<input v-model="authForm.email" placeholder="moneyrun@example.com" /></label>
        </template>
        <p v-if="authError" class="notice error">{{ authError }}</p>
        <button class="primary full" :disabled="authLoading" @click="loginOrSignup">
          {{ authLoading ? '처리 중...' : authMode === 'login' ? '로그인하고 달리기' : '회원가입하고 시작하기' }}
        </button>
        <p class="hint" v-if="authMode === 'login'">시연 계정: <b>minji</b> / <b>moneyrun1234</b></p>
      </article>
    </section>

    <template v-else>
      <header class="app-top">
        <button class="round-icon" @click="activeTab = 'my'">🔔<span v-if="unreadNotifications"></span></button>
        <div class="coin-pill">🪙 {{ formatNumber(user.points || 12450) }}</div>
        <button class="round-icon" @click="activeTab = 'my'">🎁</button>
      </header>

      <p v-if="loading" class="notice">데이터를 불러오는 중입니다...</p>
      <p v-if="error" class="notice error">{{ error }}</p>

      <section v-show="activeTab === 'home'" class="screen home-screen">
        <section class="hero-visual">
          <img class="brand-image hero-logo" :src="brandLogo" alt="MoneyRun 머니런" />
          <p>{{ currentGoal ? currentGoal.title : '함께 모으고, 함께 목표달성!' }}</p>
          <div class="goal-flag">🚩</div>
          <img class="character-line hero-characters" :src="brandCharacters" alt="머니런 캐릭터 팀" />
        </section>

        <section class="mode-switch" aria-label="머니런 이용 방식">
          <button :class="{ active: currentRoomMode === 'challenge' }" @click="serviceMode = 'challenge'">
            <strong>목표 챌린지</strong>
            <span>개인이 알아서 적립하고 서로 응원</span>
          </button>
          <button :class="{ active: currentRoomMode === 'account' }" @click="serviceMode = 'account'">
            <strong>모임통장</strong>
            <span>공동 통장에 함께 입금하고 관리</span>
          </button>
        </section>

        <section class="today-panel">
          <article>
            <span>오늘 페이스</span>
            <strong>{{ currentGoal ? formatWon(dailyTarget) : '목표 대기' }}</strong>
            <small>{{ currentGoal ? `${currentGoal.days_left}일 남음` : '챌린지 탭에서 시작' }}</small>
          </article>
          <article>
            <span>AI 위험도</span>
            <strong>{{ dashboard?.risk_score || 0 }}%</strong>
            <small>{{ riskLevel }}</small>
          </article>
          <article>
            <span>선두 러너</span>
            <strong>{{ topSaver?.name || '-' }}</strong>
            <small>{{ topSaver ? formatWon(topSaver.saved) : '기록 없음' }}</small>
          </article>
        </section>

        <article class="card bank-transfer-card">
          <div class="bank-copy">
            <span class="small-pill">{{ currentRoomMode === 'account' ? '모임통장 방' : '목표 챌린지 방' }}</span>
            <h2>{{ currentRoomMode === 'account' ? '은행 계좌에서 모임통장으로 입금' : '내 은행 계좌에서 개인 목표로 적립' }}</h2>
            <p>
              {{ bankConnected ? `${bank.bank_name} · ${bank.account_masked}` : '시중 은행을 선택해 계좌 연동 흐름을 시작하세요.' }}
            </p>
          </div>
          <div class="saving-ledger">
            <div><span>{{ currentRoomMode === 'account' ? '내 입금' : '내 적립' }}</span><strong>{{ formatWon(mySavedAmount) }}</strong></div>
            <div><span>{{ currentRoomMode === 'account' ? '모임통장 잔액' : '팀 총 적립' }}</span><strong>{{ formatWon(teamSavedAmount) }}</strong></div>
            <div><span>목표</span><strong>{{ teamTargetAmount ? formatWon(teamTargetAmount) : '-' }}</strong></div>
          </div>
          <div class="transfer-form">
            <label>연동 은행
              <select v-model="bankForm.bank_name">
                <option v-for="bankName in bankOptions" :key="bankName" :value="bankName">{{ bankName }}</option>
              </select>
            </label>
            <label>이체 금액<input v-model="transferForm.amount" inputmode="numeric" @input="formatMoneyInput(transferForm, 'amount')" /></label>
            <label>메모<input v-model="transferForm.memo" /></label>
          </div>
          <div class="button-row">
            <button class="kakao" :disabled="saving" @click="connectKakaoBankDemo">{{ bankConnected ? '계좌 변경/연결' : '은행 앱 연동' }}</button>
            <button class="primary" :disabled="saving || !currentGoal" @click="transferFromBank">{{ currentRoomMode === 'account' ? '모임통장 입금' : '개인 목표 적립' }}</button>
          </div>
        </article>

        <article class="card action-card">
          <div>
            <h2>오늘의 완주 플랜</h2>
            <p>{{ recommendedMission }}</p>
          </div>
          <div class="quick-actions">
            <button class="primary" @click="activeTab = currentGoal ? 'challenge' : 'groups'">{{ currentGoal ? '미션 완료' : '그룹 만들기' }}</button>
            <button class="secondary" @click="activeTab = 'coach'">AI 코치</button>
          </div>
        </article>

        <article v-if="currentGroup" class="card group-card" @click="activeTab = 'groups'">
          <div class="group-thumb brand-thumb"><img :src="brandCharacters" alt="" /><small>우리 함께<br/>저축중!</small></div>
          <div class="card-copy">
            <div class="row-title"><h2>{{ currentGroup.name }}</h2><span class="small-pill">{{ currentGroup.member_count }}명</span></div>
            <p>{{ currentGroup.description || '이번 주도 함께 화이팅!' }}</p>
            <div class="avatar-stack">
              <span v-for="member in dashboard?.members?.slice(0, 4)" :key="member.id">{{ member.emoji }}</span>
              <span v-if="currentGroup.member_count > 4">+{{ currentGroup.member_count - 4 }}</span>
            </div>
          </div>
          <b>›</b>
        </article>

        <article v-else class="card empty-card">
          <h2>첫 그룹을 만들어볼까요?</h2>
          <p>친구, 연인, 스터디와 함께 돈 목표를 달성해요.</p>
          <button class="primary" @click="activeTab = 'groups'">그룹 만들기</button>
        </article>

        <article v-if="notifications.length" class="card poke-alert-card">
          <div class="card-header"><h2>콕 찌르기 알림 🔔</h2><span class="small-pill">{{ unreadNotifications }}개</span></div>
          <p v-for="item in notifications.slice(0, 2)" :key="item.id">{{ item.sender_name }} → {{ item.target_name }}: {{ item.message }}</p>
        </article>

        <article class="card progress-card">
          <div class="progress-info">
            <h2>{{ currentRoomMode === 'account' ? '모임통장 현황' : '내 저축 현황' }} 🌱</h2>
            <p v-if="currentGoal">목표 달성까지</p>
            <strong v-if="currentGoal">{{ formatWon(leftAmount) }} 남았어요!</strong>
            <strong v-else>아직 목표가 없어요</strong>
          </div>
          <div class="jar">🫙</div>
          <div class="progress-meta" v-if="currentGoal">
            <span>{{ progress }}%</span><em>목표 {{ formatWon(currentGoal.target_amount) }}</em>
          </div>
          <div class="progress-bar"><div class="progress-fill" :style="progressStyle"></div></div>
        </article>

        <article v-if="dashboard?.members?.length" class="card squad-card">
          <div class="card-header"><h2>러너 페이스</h2><span class="small-pill">{{ dashboard.members.length }}명 완주 중</span></div>
          <div class="squad-grid">
            <div v-for="member in dashboard.members" :key="member.id" class="squad-member">
              <span>{{ member.emoji }}</span>
              <strong>{{ member.name }}</strong>
              <small>{{ formatWon(member.saved) }}</small>
              <i :style="{ width: `${Math.min(member.budget_rate, 100)}%` }"></i>
            </div>
          </div>
        </article>

        <article v-if="dashboard?.category_spending?.length" class="card spending-card">
          <div class="card-header"><h2>이번 주 소비 신호</h2><span class="small-pill">{{ formatWon(categoryTotal) }}</span></div>
          <div class="spending-list">
            <div v-for="item in dashboard.category_spending" :key="item.category">
              <span>{{ item.category }}</span>
              <b>{{ formatWon(item.amount) }}</b>
              <i><em :style="{ width: `${Math.max((item.amount / categoryMax) * 100, 8)}%` }"></em></i>
            </div>
          </div>
        </article>

        <article class="card coach-preview" @click="activeTab = 'coach'">
          <div class="ai-face"><img :src="brandCharacters" alt="" /></div>
          <div>
            <h2>AI 코치 한마디 ✨</h2>
            <p>{{ coachMessages[0] || '목표를 만들면 AI 코치가 달성 전략을 알려줘요.' }}</p>
          </div>
          <button class="soft-btn">더보기</button>
        </article>
      </section>

      <section v-show="activeTab === 'groups'" class="screen">
        <div class="screen-title"><span>👥</span><div><h1>그룹</h1><p>여러 그룹을 만들고 전환할 수 있어요.</p></div></div>

        <article class="card">
          <div class="card-header"><h2>내 그룹 {{ myGroups.length }}개</h2><button class="soft-btn" @click="loadData()">새로고침</button></div>
          <div class="group-list">
            <button v-for="group in myGroups" :key="group.id" class="group-row" :class="{ selected: selectedGroupId === group.id }" @click="switchGroup(group.id)">
              <span>{{ group.room_mode === 'account' ? '🏦' : group.group_type === 'couple' ? '💑' : group.group_type === 'study' ? '📚' : group.group_type === 'family' ? '🏡' : '👟' }}</span>
              <div><strong>{{ group.name }}</strong><small>{{ group.room_mode_label || '목표 챌린지' }} · {{ group.group_type_label }} · {{ group.member_count }}명</small></div>
              <b>›</b>
            </button>
          </div>
        </article>

        <article v-if="currentGroup" class="card invite-card">
          <h2>친구 초대하기</h2>
          <p>초대코드 <b>{{ currentGroup.invite_code }}</b></p>
          <div class="button-row">
            <button class="kakao" @click="shareKakao">카카오톡 초대</button>
            <button class="secondary" @click="copyText(inviteUrl)">링크 복사</button>
          </div>
        </article>

        <article class="card form-card">
          <h2>새 그룹 만들기</h2>
          <div class="room-mode-picker">
            <button :class="{ active: groupForm.room_mode === 'challenge' }" @click="groupForm.room_mode = 'challenge'" type="button">
              <strong>목표 챌린지 방</strong>
              <span>목표는 각자 달라도 함께 응원하며 완주</span>
            </button>
            <button :class="{ active: groupForm.room_mode === 'account' }" @click="groupForm.room_mode = 'account'" type="button">
              <strong>모임통장 방</strong>
              <span>공동 계좌에 함께 입금하고 총액 관리</span>
            </button>
          </div>
          <label>그룹명<input v-model="groupForm.name" placeholder="제주런 4인팟" /></label>
          <label>그룹 유형
            <select v-model="groupForm.group_type">
              <option value="friend">친구</option><option value="couple">커플</option><option value="study">스터디</option><option value="family">가족</option><option value="etc">기타</option>
            </select>
          </label>
          <label>설명<textarea v-model="groupForm.description" :placeholder="groupForm.room_mode === 'account' ? '여행비, 회비, 공동 예산을 함께 모으는 모임통장' : '각자 목표 금액을 모으며 서로 응원하는 완주 방'"></textarea></label>
          <button class="primary full" :disabled="saving" @click="createGroup">그룹 생성</button>
        </article>
      </section>

      <section v-show="activeTab === 'coach'" class="screen">
        <div class="screen-title"><span>🤖</span><div><h1>AI 코치</h1><p>소비 속도와 목표 달성률을 분석해요.</p></div></div>
        <article class="card risk-card" :class="riskClass">
          <p>실패 위험도</p>
          <strong>{{ dashboard?.risk_score || 0 }}%</strong>
          <span>{{ riskLevel }}</span>
          <div class="risk-meter"><i :style="{ width: `${dashboard?.risk_score || 0}%` }"></i></div>
        </article>
        <article class="card">
          <h2>코치 메시지</h2>
          <ul class="coach-list"><li v-for="message in coachMessages" :key="message">{{ message }}</li></ul>
        </article>
        <article class="card">
          <h2>러너 상태</h2>
          <div class="runner-list">
            <div v-for="member in dashboard?.members || []" :key="member.id" class="runner-row">
              <span class="avatar">{{ member.emoji }}</span>
              <div><strong>{{ member.name }} <small v-if="member.is_me">나</small></strong><p>{{ member.role }} · 이번 주 {{ formatWon(member.weekly_spent) }}</p></div>
              <div class="runner-actions"><em :class="member.status">{{ member.status }}</em><button v-if="!member.is_me" class="poke-btn" :disabled="saving" @click="pokeMember(member)">콕 찌르기</button></div>
            </div>
          </div>
        </article>
        <article class="card poke-card">
          <h2>입금 잊은 친구 찌르기</h2>
          <p>버튼을 누르면 앱 안 알림과 그룹 피드에 콕 찌르기 메시지가 남아요.</p>
          <label>요청 금액<input v-model="pokeForm.amount" inputmode="numeric" @input="formatMoneyInput(pokeForm, 'amount')" /></label>
          <label>메시지<input v-model="pokeForm.message" /></label>
        </article>
      </section>

      <section v-show="activeTab === 'challenge'" class="screen">
        <div class="screen-title"><span>🏆</span><div><h1>챌린지</h1><p>미션을 깨고 저축 게이지를 올려요.</p></div></div>

        <article class="card game-card">
          <div class="card-header"><h2>1원 적립 게임 🎮</h2><span class="small-pill">성공 시 +1원</span></div>
          <p class="quiz-question">{{ quiz.question }}</p>
          <div class="quiz-options">
            <button v-for="(option, index) in quiz.options" :key="option" class="secondary" :disabled="gameLoading" @click="submitQuiz(index)">{{ option }}</button>
          </div>
          <button class="soft-btn full" :disabled="gameLoading" @click="completeMiniGame">동전 잡기 미니게임 성공 처리</button>
          <p class="hint">시연용으로는 1원이 목표 저축액과 런 포인트에 바로 반영돼요.</p>
        </article>

        <article v-if="!currentGoal" class="card form-card">
          <h2>목표 만들기</h2>
          <p v-if="!currentGroup" class="hint">먼저 그룹을 만들어야 목표를 시작할 수 있어요.</p>
          <label>목표명<input v-model="goalForm.title" placeholder="제주도 여행비 30만 원 모으기" /></label>
          <label>목표 금액<input v-model="goalForm.target_amount" inputmode="numeric" placeholder="300,000" @input="formatMoneyInput(goalForm, 'target_amount')" /></label>
          <label>종료일<input v-model="goalForm.end_date" type="date" /></label>
          <label>미션 규칙<input v-model="goalForm.mission_rule" /></label>
          <label>보상 문구<input v-model="goalForm.reward_text" /></label>
          <button class="primary full" :disabled="saving || !currentGroup" @click="createGoal">목표 시작하기</button>
        </article>

        <template v-else>
          <article class="card mission-card">
            <h2>오늘의 미션 클리어</h2>
            <label>러너 선택<select v-model="missionForm.member"><option v-for="member in dashboard.members" :key="member.id" :value="member.id">{{ member.emoji }} {{ member.name }}</option></select></label>
            <label>미션명<input v-model="missionForm.mission" /></label>
            <label>보상 저축액<input v-model="missionForm.amount" inputmode="numeric" placeholder="5,000" @input="formatMoneyInput(missionForm, 'amount')" /></label>
            <button class="primary full" :disabled="saving" @click="completeMission">미션 완료</button>
          </article>

          <article class="card form-card">
            <h2>소비 기록</h2>
            <label>러너 선택<select v-model="expenseForm.member"><option v-for="member in dashboard.members" :key="member.id" :value="member.id">{{ member.emoji }} {{ member.name }}</option></select></label>
            <label>카테고리<select v-model="expenseForm.category"><option value="food">식비</option><option value="cafe">카페</option><option value="transport">교통</option><option value="shopping">쇼핑</option><option value="culture">문화</option><option value="etc">기타</option></select></label>
            <label>금액<input v-model="expenseForm.amount" inputmode="numeric" placeholder="8,000" @input="formatMoneyInput(expenseForm, 'amount')" /></label>
            <label>메모<input v-model="expenseForm.memo" /></label>
            <button class="secondary full" :disabled="saving" @click="addExpense">기록 추가</button>
          </article>
        </template>

        <article class="card">
          <h2>그룹 피드</h2>
          <div class="feed-list"><div v-for="item in dashboard?.feed || []" :key="item.id" class="feed-item"><i></i><p>{{ item.message }}</p></div></div>
        </article>
      </section>

      <section v-show="activeTab === 'my'" class="screen">
        <div class="screen-title"><span>👤</span><div><h1>마이</h1><p>프로필을 꾸미고 내 정보를 확인해요.</p></div></div>
        <article class="card profile-card">
          <div class="profile-photo" @click="openProfilePicker">
            <img v-if="user.avatar_url" :src="user.avatar_url" alt="프로필 사진" />
            <span v-else>📷</span>
          </div>
          <input ref="profileInput" class="hidden-file" type="file" accept="image/*" @change="uploadProfileImage" />
          <h2>{{ user.display_name }}</h2>
          <p>@{{ user.username }} · Lv.{{ user.level || 1 }}</p>
          <button class="primary" :disabled="avatarUploading" @click="openProfilePicker">
            {{ avatarUploading ? '업로드 중...' : '핸드폰 갤러리에서 사진 선택' }}
          </button>
        </article>

        <article class="card stats-card">
          <div><strong>{{ myGroups.length }}</strong><span>참여 그룹</span></div>
          <div><strong>{{ formatNumber(user.points || 12450) }}</strong><span>런 포인트</span></div>
          <div><strong>{{ dashboard?.badges?.length || 0 }}</strong><span>배지</span></div>
        </article>

        <article v-if="notifications.length" class="card notification-card">
          <div class="card-header">
            <h2>나에게 온 찌르기</h2>
            <button class="soft-btn" :disabled="!unreadNotifications" @click="markNotificationsRead">모두 확인</button>
          </div>
          <div class="notification-list">
            <div v-for="item in notifications" :key="item.id" :class="{ read: item.status === 'read' }">
              <strong>{{ item.sender_name }} → {{ item.target_name }}</strong>
              <p>{{ item.message }}</p>
              <small v-if="item.amount">{{ formatWon(item.amount) }} 요청</small>
            </div>
          </div>
        </article>

        <article class="card bank-card">
          <div class="card-header"><h2>카카오뱅크 연동</h2><span class="small-pill">데모</span></div>
          <template v-if="bank?.is_connected">
            <p><b>{{ bank.bank_name }}</b> · {{ bank.account_masked }}</p>
            <p>{{ bank.account_alias }} 연결됨</p>
          </template>
          <template v-else>
            <p>실제 이체 없이 계좌 연결 흐름을 시연하는 데모예요.</p>
            <button class="kakao full" :disabled="saving" @click="connectKakaoBankDemo">카카오뱅크 연결하기</button>
          </template>
        </article>

        <article class="card">
          <h2>획득 배지</h2>
          <div class="badge-list"><div v-for="badge in dashboard?.badges || []" :key="badge.id" class="badge-item"><span>{{ badge.icon }}</span><div><strong>{{ badge.name }}</strong><p>{{ badge.description }}</p></div></div></div>
        </article>
        <button class="logout-btn" @click="logout">로그아웃</button>
      </section>

      <nav class="bottom-nav">
        <button v-for="tab in tabs" :key="tab.id" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
          <span>{{ tab.icon }}</span><small>{{ tab.label }}</small><i v-if="tab.id === 'challenge'"></i>
        </button>
      </nav>
    </template>
  </main>
</template>
