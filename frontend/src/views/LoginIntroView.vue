<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import projectLogo from '../../../image/logo.svg'
import projectBg from '../../../image/background.jpg'
import paragraph1Image from '../../../image/paragraph1.png'
import paragraph2Image from '../../../image/paragraph2.jpg'
import paragraph3Image from '../../../image/paragraph3.png'

const router = useRouter()
const AUTH_KEY = 'disaster_auth_ok'
const USER_KEY = 'disaster_users_v1'

const panelOpen = ref(false)
const mode = ref('login')
const message = ref('')
const phase = ref('idle') // idle | moving | loading | shrinking
const bootMoveActive = ref(false)
const progress = ref(0)
const chipLogoRef = ref(null)
const returnLogoVisible = ref(false)
const returnLogoMoving = ref(false)
const returnLogoStyle = ref({ '--to-x': '0px', '--to-y': '0px' })
const bootStartStyle = ref({ '--boot-from-x': '0px', '--boot-from-y': '0px' })
const shapes = ['diamond', 'triangle', 'ring', 'line']
const particles = Array.from({ length: 30 }, (_, idx) => {
  const left = 4 + ((idx * 37) % 92)
  const size = 8 + (idx % 5) * 3
  const duration = 8 + (idx % 8)
  const delay = (idx % 9) * 0.55
  const drift = ((idx % 7) - 3) * 16
  const rotate = (idx % 2 === 0 ? 1 : -1) * (8 + (idx % 6) * 6)
  const opacity = 0.32 + (idx % 4) * 0.12
  const shape = shapes[idx % shapes.length]
  return { id: idx, left, size, duration, delay, drift, opacity, rotate, shape }
})

const loginForm = ref({ account: '', password: '' })
const registerForm = ref({ account: '', password: '', confirmPassword: '' })

let timerId = null

function getParticleStyle(particle) {
  return {
    left: `${particle.left}%`,
    width: `${particle.size}px`,
    height: `${particle.size}px`,
    opacity: particle.opacity,
    '--float-duration': `${particle.duration}s`,
    '--float-delay': `${particle.delay}s`,
    '--pulse-delay': `${particle.delay * 0.4}s`,
    '--drift-x': `${particle.drift}px`,
    '--spin-deg': `${particle.rotate}deg`
  }
}

function ensureUsers() {
  const raw = localStorage.getItem(USER_KEY)
  if (raw) return
  localStorage.setItem(
    USER_KEY,
    JSON.stringify([
      {
        account: 'admin',
        password: '123456'
      }
    ])
  )
}

function getUsers() {
  ensureUsers()
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || '[]')
  } catch {
    return []
  }
}

function openPanel(initialMode = 'login') {
  mode.value = initialMode
  panelOpen.value = true
  message.value = ''
}

function closePanel() {
  panelOpen.value = false
  message.value = ''
}

function switchMode(nextMode) {
  mode.value = nextMode
  message.value = ''
}

function onRegister() {
  const account = registerForm.value.account.trim()
  const password = registerForm.value.password.trim()
  const confirmPassword = registerForm.value.confirmPassword.trim()
  if (!account || !password || !confirmPassword) {
    message.value = '请完整填写注册信息。'
    return
  }
  if (password !== confirmPassword) {
    message.value = '两次输入的密码不一致。'
    return
  }
  const users = getUsers()
  if (users.some((u) => u.account === account)) {
    message.value = '账号已存在，请更换账号。'
    return
  }
  users.push({ account, password })
  localStorage.setItem(USER_KEY, JSON.stringify(users))
  message.value = '注册成功，请使用新账号登录。'
  mode.value = 'login'
  loginForm.value.account = account
  loginForm.value.password = ''
}

function runBootAnimation() {
  const logoRect = chipLogoRef.value?.getBoundingClientRect?.()
  if (logoRect) {
    const fromX = logoRect.left + logoRect.width / 2 - window.innerWidth / 2
    const fromY = logoRect.top + logoRect.height / 2 - window.innerHeight / 2
    bootStartStyle.value = {
      '--boot-from-x': `${fromX}px`,
      '--boot-from-y': `${fromY}px`
    }
  }
  phase.value = 'moving'
  bootMoveActive.value = false
  progress.value = 0
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      bootMoveActive.value = true
    })
  })
  window.setTimeout(() => {
    startBootLoading()
  }, 520)
}

function startBootLoading() {
  phase.value = 'loading'
  bootMoveActive.value = false
  const duration = 2000
  const step = 20
  const totalSteps = duration / step
  let current = 0
  timerId = window.setInterval(() => {
    current += 1
    progress.value = Math.min(100, (current / totalSteps) * 100)
    if (current >= totalSteps) {
      window.clearInterval(timerId)
      timerId = null
      phase.value = 'shrinking'
      sessionStorage.setItem(AUTH_KEY, '1')
      window.setTimeout(() => {
        router.push('/')
      }, 560)
    }
  }, step)
}

function onLogin() {
  const account = loginForm.value.account.trim()
  const password = loginForm.value.password.trim()
  if (!account || !password) {
    message.value = '请输入账号和密码。'
    return
  }
  const users = getUsers()
  const ok = users.some((u) => u.account === account && u.password === password)
  if (!ok) {
    message.value = '账号或密码错误，请重试。'
    return
  }
  panelOpen.value = false
  message.value = ''
  registerForm.value = { account: '', password: '', confirmPassword: '' }
  runBootAnimation()
}

const progressText = computed(() => `${Math.round(progress.value)}%`)

onMounted(async () => {
  const shouldAnimate = sessionStorage.getItem('disaster_logout_transition') === '1'
  if (!shouldAnimate) return
  await nextTick()
  const logoRect = chipLogoRef.value?.getBoundingClientRect?.()
  if (!logoRect) return
  const toX = logoRect.left + logoRect.width / 2 - window.innerWidth / 2
  const toY = logoRect.top + logoRect.height / 2 - window.innerHeight / 2
  returnLogoStyle.value = {
    '--to-x': `${toX}px`,
    '--to-y': `${toY}px`
  }
  returnLogoVisible.value = true
  window.setTimeout(() => {
    returnLogoMoving.value = true
  }, 30)
  window.setTimeout(() => {
    returnLogoVisible.value = false
    returnLogoMoving.value = false
    sessionStorage.removeItem('disaster_logout_transition')
  }, 760)
})

onBeforeUnmount(() => {
  if (timerId) window.clearInterval(timerId)
})
</script>

<template>
  <section class="login-page">
    <div class="particle-layer" aria-hidden="true">
      <span
        v-for="item in particles"
        :key="item.id"
        class="particle-dot"
        :class="`shape-${item.shape}`"
        :style="getParticleStyle(item)"
      />
    </div>
    <header class="hero" :style="{ '--hero-bg': `url(${projectBg})` }">
      <div class="hero-mask">
        <div class="hero-title">
          <h1>自然灾害可视化预警平台</h1>
          <p>风雨未至数先知</p>
        </div>
        <button class="login-chip" type="button" @click="openPanel('login')">
          <img ref="chipLogoRef" :src="projectLogo" alt="logo" />
          <span>登录系统</span>
        </button>
      </div>
    </header>

    <main class="intro">
      <section class="intro-copy intro-left intro-with-image">
        <div class="intro-text">
          <h2>项目痛点</h2>
          <p>灾害数据跨源分散、区域粒度不统一、趋势研判滞后，导致预警响应常常偏慢。</p>
          <ul>
            <li>历史数据来源多样，统计口径难对齐。</li>
            <li>省域和组合地区混杂，决策参考不够精准。</li>
            <li>图表孤立呈现，无法形成可执行建议链路。</li>
          </ul>
        </div>
        <div class="intro-image-wrap">
          <img :src="paragraph1Image" alt="灾害救援现场" class="intro-image-soft" />
        </div>
      </section>

      <section class="intro-copy intro-right intro-with-image intro-with-image-reverse">
        <div class="intro-image-wrap">
          <img :src="paragraph2Image" alt="大数据分析流程示意" class="intro-image-soft" />
        </div>
        <div class="intro-text">
          <h2>项目优势</h2>
          <p>基于 Hadoop + Spark + Python 的分析链路，把数据治理、预测评估与可视化联动打通。</p>
          <ul>
            <li>省级数据归一与拆分处理，确保统计一致性。</li>
            <li>多模块联动图表，支持趋势、损失、地图、监控一体化查看。</li>
            <li>按地区输出分群建议，覆盖农业、企业、政府三类角色。</li>
          </ul>
        </div>
      </section>

      <section class="intro-copy intro-left intro-with-image">
        <div class="intro-text">
          <h2>平台能力</h2>
          <p>从数据入湖到研判展示，形成可持续更新的防灾减灾业务闭环。</p>
          <ul>
            <li>HDFS 存储灾害数据，Spark 进行分布式统计分析。</li>
            <li>前端 ECharts 高可读图表，支持区域切换与重点研判。</li>
            <li>可查看 Spark UI 与 NameNode，分析过程透明可追踪。</li>
          </ul>
        </div>
        <div class="intro-image-wrap">
          <img :src="paragraph3Image" alt="平台能力链路示意" class="intro-image-soft" />
        </div>
      </section>
    </main>
    <div class="scroll-shadow-overlay" />

    <Transition name="auth-pop">
      <div v-if="panelOpen" class="auth-overlay">
        <section class="auth-panel">
          <div class="auth-tabs">
            <button :class="{ active: mode === 'login' }" type="button" @click="switchMode('login')">登录</button>
            <button :class="{ active: mode === 'register' }" type="button" @click="switchMode('register')">注册</button>
            <button class="close-btn" type="button" @click="closePanel">关闭</button>
          </div>

          <div v-if="mode === 'login'" class="form-wrap">
            <input v-model.trim="loginForm.account" placeholder="请输入账号" />
            <input v-model.trim="loginForm.password" type="password" placeholder="请输入密码" />
            <button type="button" class="submit-btn" @click="onLogin">登入</button>
          </div>

          <div v-else class="form-wrap">
            <input v-model.trim="registerForm.account" placeholder="设置账号" />
            <input v-model.trim="registerForm.password" type="password" placeholder="设置密码" />
            <input v-model.trim="registerForm.confirmPassword" type="password" placeholder="确认密码" />
            <button type="button" class="submit-btn" @click="onRegister">注册并返回登录</button>
          </div>

          <p v-if="message" class="msg">{{ message }}</p>
          <p class="tips">默认体验账号：admin / 123456</p>
        </section>
      </div>
    </Transition>

    <Transition name="boot-fade">
      <div v-if="phase !== 'idle'" class="boot-overlay" :class="[phase, { 'move-active': bootMoveActive }]" :style="bootStartStyle">
        <img :src="projectLogo" alt="启动logo" class="boot-logo" />
        <div class="boot-progress">
          <div class="bar"><span :style="{ width: progressText }" /></div>
          <em>{{ progressText }}</em>
        </div>
      </div>
    </Transition>

    <Transition name="return-logo-fade">
      <div v-if="returnLogoVisible" class="return-logo-overlay">
        <img :src="projectLogo" alt="回退logo" class="return-logo" :class="{ moving: returnLogoMoving }" :style="returnLogoStyle" />
      </div>
    </Transition>
  </section>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  color: #d4e4f6;
  position: relative;
}

.particle-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 20;
  overflow: hidden;
}

.particle-dot {
  position: absolute;
  bottom: -20px;
  transform-origin: center;
  animation:
    particleFloat var(--float-duration) linear var(--float-delay) infinite,
    particlePulse 2.2s ease-in-out var(--pulse-delay) infinite alternate;
}

.particle-dot.shape-diamond {
  background: rgba(120, 214, 255, 0.28);
  border: 1px solid rgba(143, 226, 255, 0.74);
  box-shadow: 0 0 10px rgba(115, 214, 255, 0.4);
  transform: rotate(45deg);
}

.particle-dot.shape-triangle {
  width: 0 !important;
  height: 0 !important;
  border-left: 7px solid transparent;
  border-right: 7px solid transparent;
  border-bottom: 12px solid rgba(145, 229, 255, 0.5);
  filter: drop-shadow(0 0 6px rgba(115, 214, 255, 0.45));
}

.particle-dot.shape-ring {
  border-radius: 50%;
  border: 1px solid rgba(155, 232, 255, 0.78);
  box-shadow: inset 0 0 6px rgba(133, 219, 255, 0.24), 0 0 10px rgba(115, 214, 255, 0.42);
}

.particle-dot.shape-line {
  width: 20px !important;
  height: 2px !important;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(120, 214, 255, 0), rgba(139, 225, 255, 0.85), rgba(120, 214, 255, 0));
  box-shadow: 0 0 8px rgba(115, 214, 255, 0.4);
}

@keyframes particleFloat {
  0% {
    transform: translate3d(0, 0, 0) rotate(0deg) scale(0.72);
  }
  50% {
    transform: translate3d(var(--drift-x), -52vh, 0) rotate(var(--spin-deg)) scale(1);
  }
  100% {
    transform: translate3d(calc(var(--drift-x) * -0.5), -110vh, 0) rotate(calc(var(--spin-deg) * -1)) scale(0.82);
  }
}

@keyframes particlePulse {
  0% {
    opacity: 0.25;
  }
  100% {
    opacity: 0.9;
  }
}

.hero {
  height: 400px;
  width: min(1980px, 100%);
  margin: 0 auto;
  background-image: var(--hero-bg);
  background-size: cover;
  background-position: center 40%;
  border-bottom: 1px solid rgba(148, 169, 195, 0.28);
  position: relative;
  z-index: 9;
}

.hero-mask {
  height: 100%;
  padding: 28px 38px;
  position: relative;
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  background:
    linear-gradient(180deg, rgba(8, 16, 28, 0.38), rgba(8, 16, 28, 0.62)),
    radial-gradient(circle at 20% 22%, rgba(41, 196, 214, 0.2), transparent 46%);
}

.hero-title {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  width: min(92vw, 980px);
}

.hero-title h1 {
  font-size: clamp(2.2rem, 4.4vw, 4.1rem);
  letter-spacing: 0.12em;
  color: #f7fbff;
  margin-bottom: 14px;
  text-shadow: 0 0 26px rgba(255, 255, 255, 0.3), 0 0 42px rgba(41, 196, 214, 0.26);
}

.hero-title p {
  color: #ffcc7a;
  font-family: 'SimSun', 'STSong', 'Songti SC', serif;
  font-size: clamp(1.55rem, 2.8vw, 2.45rem);
  font-weight: 900;
  letter-spacing: 0.22em;
  text-shadow: 0 0 16px rgba(249, 158, 11, 0.46), 0 0 26px rgba(255, 204, 122, 0.32);
}

.login-chip {
  border: 1px solid rgba(162, 186, 216, 0.36);
  border-radius: 999px;
  padding: 8px 14px;
  background: rgba(12, 24, 38, 0.54);
  display: flex;
  align-items: center;
  gap: 9px;
  color: #e5f0ff;
  cursor: pointer;
}

.login-chip img {
  width: 22px;
  height: 22px;
  filter: brightness(0) invert(1);
}

.intro {
  padding: 200px 150px calc(62px + 44vh);
  display: grid;
  gap: 200px;
  background:
    linear-gradient(180deg, rgba(11, 28, 48, 0.98) 0%, rgba(13, 45, 72, 0.96) 38%, rgba(34, 48, 70, 0.96) 72%, rgba(52, 46, 62, 0.96) 100%);
  position: relative;
  z-index: 9;
}

.intro-copy {
  width: min(760px, 100%);
  padding: 8px 2px;
  transition: transform 0.35s ease, opacity 0.35s ease;
  opacity: 1;
  filter: none;
  position: relative;
  z-index: 1;
}

.intro-with-image {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 560px);
  align-items: start;
  column-gap: 28px;
}

.intro-text {
  max-width: 760px;
}

.intro-with-image-reverse .intro-text {
  justify-self: end;
}

.intro-with-image-reverse {
  grid-template-columns: minmax(360px, 560px) minmax(0, 1fr);
}

.intro-with-image-reverse .intro-image-wrap {
  justify-self: start;
}

.intro-image-wrap {
  justify-self: end;
  width: min(560px, 100%);
  position: relative;
}

.intro-image-wrap::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 14px;
  pointer-events: none;
  box-shadow:
    inset 0 0 64px rgba(5, 12, 22, 0.72),
    inset 0 0 132px rgba(6, 14, 26, 0.48),
    inset 0 0 180px rgba(4, 10, 18, 0.28),
    0 20px 42px rgba(0, 0, 0, 0.38);
}

.intro-image-soft {
  width: 100%;
  display: block;
  border-radius: 14px;
  border: 1px solid rgba(162, 183, 209, 0.36);
  box-shadow: 0 0 28px rgba(56, 128, 189, 0.2);
  mask-image: radial-gradient(170% 145% at 50% 45%, #000 50%, rgba(0, 0, 0, 0.58) 72%, rgba(0, 0, 0, 0.2) 86%, transparent 100%);
  -webkit-mask-image: radial-gradient(170% 145% at 50% 45%, #000 50%, rgba(0, 0, 0, 0.58) 72%, rgba(0, 0, 0, 0.2) 86%, transparent 100%);
}

.intro-left {
  justify-self: start;
  text-align: left;
}

.intro-right {
  justify-self: end;
  text-align: left;
  width: min(560px, 100%);
}

.intro-with-image.intro-right {
  width: 100%;
}

.intro-copy h2 {
  margin-bottom: 12px;
  color: #f3f8ff;
  font-size: clamp(1.25rem, 2vw, 1.95rem);
  text-shadow: 0 0 14px rgba(72, 162, 213, 0.26);
}

.intro-copy p {
  margin-bottom: 10px;
  line-height: 1.9;
  color: #d9e7f7;
  font-size: 1.02rem;
}

.intro-copy ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.9;
  color: #c6d9ee;
}

.scroll-shadow-overlay {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: 44vh;
  pointer-events: none;
  z-index: 12;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, rgba(2, 7, 14, 0.48) 56%, rgba(2, 6, 12, 0.92) 100%);
}

.auth-overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(6, 12, 21, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-panel {
  width: min(430px, 92vw);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(164, 188, 219, 0.35);
  background: linear-gradient(160deg, rgba(18, 30, 47, 0.86), rgba(14, 23, 35, 0.94));
  box-shadow: 0 24px 56px rgba(0, 0, 0, 0.35);
}

.auth-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.auth-tabs button {
  border: 1px solid rgba(122, 143, 168, 0.45);
  background: rgba(23, 38, 57, 0.64);
  color: #d4e4f6;
  border-radius: 10px;
  padding: 6px 10px;
  cursor: pointer;
}

.auth-tabs button.active {
  color: #fff;
  border-color: rgba(249, 115, 22, 0.58);
  background: rgba(249, 115, 22, 0.24);
}

.auth-tabs .close-btn {
  margin-left: auto;
}

.form-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-wrap input {
  border: 1px solid rgba(109, 139, 171, 0.6);
  border-radius: 10px;
  padding: 10px 12px;
  color: #f0f6ff;
  background: rgba(8, 16, 26, 0.7);
}

.submit-btn {
  border: 1px solid rgba(249, 115, 22, 0.62);
  border-radius: 10px;
  padding: 10px 12px;
  color: #fff;
  background: rgba(249, 115, 22, 0.34);
  cursor: pointer;
}

.msg {
  margin-top: 10px;
  color: #fde68a;
}

.tips {
  margin-top: 6px;
  color: #90a4c2;
  font-size: 0.84rem;
}

.boot-overlay {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 18px;
  background: rgba(6, 13, 22, 0.92);
}

.boot-logo {
  width: 240px;
  height: 240px;
  object-fit: contain;
  filter: brightness(0) invert(1);
  transition: transform 0.56s cubic-bezier(0.2, 0.8, 0.2, 1);
  will-change: transform, opacity;
}

.boot-overlay.moving .boot-logo {
  transform: translate(var(--boot-from-x), var(--boot-from-y)) scale(0.16);
  opacity: 0.32;
  transition: transform 0.52s cubic-bezier(0.22, 0.86, 0.24, 1), opacity 0.52s ease;
}

.boot-overlay.moving.move-active .boot-logo {
  transform: translate(0, 0) scale(1);
  opacity: 1;
}

.boot-overlay.loading .boot-logo,
.boot-overlay.shrinking .boot-logo {
  transform: translate(0, 0) scale(1);
}

.boot-progress {
  width: min(420px, 72vw);
}

.boot-progress .bar {
  height: 8px;
  border-radius: 999px;
  background: rgba(19, 36, 56, 0.9);
  border: 1px solid rgba(42, 255, 117, 0.28);
  overflow: hidden;
}

.boot-progress .bar span {
  display: block;
  height: 100%;
  width: 0;
  background: linear-gradient(90deg, #22c55e, #86efac);
  transition: width 20ms linear;
}

.boot-progress em {
  margin-top: 6px;
  display: inline-block;
  color: #8df0a8;
  font-style: normal;
  font-family: 'JetBrains Mono', monospace;
}

.boot-overlay.shrinking .boot-logo {
  transform: translate(-42vw, -38vh) scale(0.24);
}

.auth-pop-enter-active,
.auth-pop-leave-active {
  transition: opacity 0.28s ease;
}

.auth-pop-enter-from,
.auth-pop-leave-to {
  opacity: 0;
}

.auth-pop-enter-active .auth-panel,
.auth-pop-leave-active .auth-panel {
  transition: transform 0.32s cubic-bezier(0.22, 0.86, 0.24, 1), opacity 0.28s ease;
  transform-origin: top right;
}

.auth-pop-enter-from .auth-panel,
.auth-pop-leave-to .auth-panel {
  transform: translate(30vw, -34vh) scale(0.16);
  opacity: 0;
}

.boot-fade-enter-active,
.boot-fade-leave-active {
  transition: opacity 0.25s ease;
}

.boot-fade-enter-from,
.boot-fade-leave-to {
  opacity: 0;
}

.return-logo-overlay {
  position: fixed;
  inset: 0;
  z-index: 95;
  pointer-events: none;
}

.return-logo {
  position: fixed;
  left: 50%;
  top: 50%;
  width: 220px;
  height: 220px;
  transform: translate(-50%, -50%) scale(1);
  filter: brightness(0) invert(1);
  transition: transform 0.72s cubic-bezier(0.22, 0.86, 0.24, 1), opacity 0.28s ease;
  opacity: 1;
}

.return-logo.moving {
  transform: translate(calc(-50% + var(--to-x)), calc(-50% + var(--to-y))) scale(0.1);
  opacity: 0.92;
}

.return-logo-fade-enter-active,
.return-logo-fade-leave-active {
  transition: opacity 0.25s ease;
}

.return-logo-fade-enter-from,
.return-logo-fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .hero {
    height: 340px;
  }

  .hero-mask {
    padding: 18px 16px;
  }

  .hero-title h1 {
    font-size: clamp(1.55rem, 7vw, 2.2rem);
  }

  .intro {
    padding: 120px 20px calc(28px + 44vh);
    gap: 90px;
  }

  .intro-copy {
    width: 100%;
  }

  .intro-with-image {
    grid-template-columns: 1fr;
    row-gap: 16px;
  }

  .intro-with-image-reverse .intro-text {
    justify-self: start;
  }

  .intro-image-wrap {
    justify-self: start;
    width: 100%;
  }

  .intro-right,
  .intro-left {
    justify-self: start;
  }
}
</style>
