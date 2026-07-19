<template>
  <div class="min-h-screen bg-slate-100 text-slate-900">
    <div v-if="!isLoggedIn" class="grid min-h-screen lg:grid-cols-[1.15fr_0.85fr]">
      <section class="flex flex-col justify-between bg-slate-950 px-6 py-8 text-white sm:px-10 lg:px-14 lg:py-12">
        <div class="space-y-8">
          <div class="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200">
            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-white text-sm font-semibold text-slate-950">AI</span>
            内容工作台
          </div>

          <div class="max-w-2xl space-y-5">
            <p class="text-sm font-medium uppercase tracking-[0.24em] text-slate-400">Tailwind UI Rewrite</p>
            <h1 class="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              从选题到成稿，再到配图，放到一个干净的工作界面里。
            </h1>
            <p class="max-w-xl text-base leading-7 text-slate-300 sm:text-lg">
              这套界面为内容运营场景重排了工作流，重点把历史任务、当前进度、草稿审核和结果产出放在同一个视图里，减少切换成本。
            </p>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-2xl border border-white/10 bg-white/5 p-6">
            <p class="text-sm font-medium text-white">工作流阶段</p>
            <div class="mt-5 space-y-4">
              <div v-for="(step, index) in steps.slice(0, 4)" :key="step" class="flex items-center gap-4">
                <span class="flex h-10 w-10 items-center justify-center rounded-full border border-white/15 bg-white/10 text-sm font-semibold">
                  {{ index + 1 }}
                </span>
                <div>
                  <p class="text-sm font-medium text-white">{{ step }}</p>
                  <p class="text-sm text-slate-400">{{ stepDescriptions[index] }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-white/10 bg-white/5 p-6">
            <p class="text-sm font-medium text-white">这次重写的重点</p>
            <div class="mt-5 grid gap-4">
              <div class="rounded-xl border border-white/10 bg-slate-900/70 p-4">
                <p class="text-xs uppercase tracking-[0.22em] text-slate-500">Layout</p>
                <p class="mt-2 text-lg font-semibold text-white">三栏工作台</p>
                <p class="mt-2 text-sm leading-6 text-slate-400">左侧任务历史，中间工作主线，右侧状态与运行日志。</p>
              </div>
              <div class="rounded-xl border border-white/10 bg-slate-900/70 p-4">
                <p class="text-xs uppercase tracking-[0.22em] text-slate-500">Focus</p>
                <p class="mt-2 text-lg font-semibold text-white">更适合持续运营</p>
                <p class="mt-2 text-sm leading-6 text-slate-400">把一次性生成器改成可回看、可切换、可复用的生产台。</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="flex items-center justify-center px-6 py-10 sm:px-10">
        <div class="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/70 sm:p-10">
          <div class="space-y-2">
            <p class="text-sm font-medium uppercase tracking-[0.22em] text-slate-400">
              {{ isLoginMode ? '登录' : '注册' }}
            </p>
            <h2 class="text-3xl font-semibold tracking-tight text-slate-950">继续进入内容工作台</h2>
            <p class="text-sm leading-6 text-slate-500">
              使用账号进入你的项目空间，继续管理历史任务和新的内容生产流程。
            </p>
          </div>

          <form class="mt-8 space-y-5" @submit.prevent="handleAuth">
            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-700">用户名</label>
              <input
                v-model.trim="authForm.username"
                type="text"
                minlength="3"
                required
                placeholder="请输入用户名"
                class="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-200"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-700">密码</label>
              <input
                v-model="authForm.password"
                type="password"
                minlength="6"
                required
                placeholder="请输入密码"
                class="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-200"
              />
            </div>

            <div v-if="authError" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {{ authError }}
            </div>

            <button
              type="submit"
              :disabled="authLoading"
              class="inline-flex h-12 w-full items-center justify-center rounded-xl bg-slate-950 px-4 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {{ authLoading ? '处理中...' : (isLoginMode ? '登录并进入' : '注册并进入') }}
            </button>
          </form>

          <div class="mt-6 flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            <span>{{ isLoginMode ? '还没有账号？' : '已经有账号？' }}</span>
            <button
              type="button"
              class="font-medium text-slate-950 transition hover:text-slate-700"
              @click="isLoginMode = !isLoginMode"
            >
              {{ isLoginMode ? '去注册' : '去登录' }}
            </button>
          </div>
        </div>
      </section>
    </div>

    <div v-else class="flex min-h-screen">
      <aside
        class="hidden border-r border-slate-200 bg-white/90 backdrop-blur lg:flex lg:flex-col"
        :class="sidebarOpen ? 'w-80' : 'w-20'"
      >
        <div class="flex items-center justify-between border-b border-slate-200 px-4 py-4">
          <div v-if="sidebarOpen" class="min-w-0">
            <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Workspace</p>
            <h2 class="mt-2 text-lg font-semibold text-slate-950">历史任务</h2>
          </div>
          <button
            type="button"
            class="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-sm font-semibold text-slate-700 transition hover:border-slate-900 hover:text-slate-950"
            @click="sidebarOpen = !sidebarOpen"
          >
            {{ sidebarOpen ? '←' : '→' }}
          </button>
        </div>

        <div class="flex-1 overflow-hidden p-4">
          <button
            type="button"
            class="inline-flex h-11 w-full items-center justify-center rounded-xl bg-slate-950 px-4 text-sm font-medium text-white transition hover:bg-slate-800"
            @click="handleNewWorkflow"
          >
            {{ sidebarOpen ? '新建内容任务' : '+' }}
          </button>

          <div class="mt-4 h-[calc(100vh-13rem)] overflow-y-auto">
            <div
              v-if="loadingThreads"
              class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500"
            >
              正在加载任务列表...
            </div>

            <div
              v-else-if="threadList.length === 0"
              class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm leading-6 text-slate-500"
            >
              {{ sidebarOpen ? '还没有历史任务，先创建第一条内容工作流。' : '空' }}
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="thread in threadList"
                :key="thread.thread_id"
                role="button"
                tabindex="0"
                class="group relative w-full rounded-2xl border px-4 py-4 text-left transition"
                :class="thread.thread_id === threadId ? 'border-slate-900 bg-slate-950 text-white shadow-lg shadow-slate-200' : 'border-slate-200 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50'"
                @click="handleSwitchThread(thread.thread_id)"
                @keydown.enter.prevent="handleSwitchThread(thread.thread_id)"
                @keydown.space.prevent="handleSwitchThread(thread.thread_id)"
              >
                <div v-if="sidebarOpen" class="space-y-2 pr-8">
                  <div class="flex items-center gap-2">
                    <span
                      class="h-2.5 w-2.5 rounded-full"
                      :class="thread.is_completed ? 'bg-emerald-400' : 'bg-amber-400'"
                    ></span>
                    <p class="truncate text-sm font-medium">
                      {{ getThreadTitle(thread) }}
                    </p>
                  </div>
                  <p
                    class="truncate text-xs"
                    :class="thread.thread_id === threadId ? 'text-slate-300' : 'text-slate-500'"
                  >
                    {{ getThreadSubtitle(thread) }}
                  </p>
                </div>

                <div v-else class="flex items-center justify-center text-sm font-semibold">
                  {{ getThreadTitle(thread).slice(0, 1) }}
                </div>

                <button
                  v-if="sidebarOpen"
                  type="button"
                  class="absolute right-3 top-3 inline-flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 opacity-0 transition group-hover:opacity-100 hover:bg-white/80 hover:text-rose-600"
                  @click.stop="handleDeleteThread(thread.thread_id)"
                >
                  ×
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="border-t border-slate-200 p-4">
          <div
            class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3"
            :class="sidebarOpen ? '' : 'justify-center'"
          >
            <span class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
              {{ userInitial }}
            </span>
            <div v-if="sidebarOpen" class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-slate-950">{{ currentUsername }}</p>
              <p class="text-xs text-slate-500">已登录</p>
            </div>
            <button
              v-if="sidebarOpen"
              type="button"
              class="rounded-lg px-2 py-1 text-sm font-medium text-slate-600 transition hover:text-slate-950"
              @click="handleLogout"
            >
              退出
            </button>
          </div>
        </div>
      </aside>

      <main class="flex min-w-0 flex-1 flex-col">
        <header class="border-b border-slate-200 bg-white/80 px-4 py-4 backdrop-blur sm:px-6">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div class="min-w-0">
              <div class="flex items-center gap-3">
                <span class="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-sm font-semibold text-white">
                  AI
                </span>
                <div class="min-w-0">
                  <h1 class="truncate text-2xl font-semibold tracking-tight text-slate-950">内容生产工作台</h1>
                  <p class="truncate text-sm text-slate-500">
                    {{ topicDirection || '输入一个方向，开始新的内容工作流。' }}
                  </p>
                </div>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <span class="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700">
                {{ runStatusLabel }}
              </span>
              <span
                v-if="selectedTopic"
                class="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600"
              >
                {{ selectedTopic }}
              </span>
              <button
                type="button"
                class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950 lg:hidden"
                @click="fetchThreadList"
              >
                刷新任务
              </button>
            </div>
          </div>
        </header>

        <div class="flex-1 px-4 py-4 sm:px-6">
          <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
            <section class="min-w-0 space-y-6">
              <div
                v-if="message"
                class="rounded-2xl border px-4 py-3 text-sm shadow-sm"
                :class="messageToneClass"
              >
                {{ message }}
              </div>

              <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Workflow</p>
                    <h2 class="mt-2 text-xl font-semibold tracking-tight text-slate-950">当前进度</h2>
                  </div>
                  <div class="flex flex-wrap gap-3">
                    <button
                      v-if="loading"
                      type="button"
                      class="inline-flex h-10 items-center justify-center rounded-xl border border-rose-200 bg-rose-50 px-4 text-sm font-medium text-rose-700 transition hover:border-rose-300 hover:bg-rose-100"
                      @click="handleCancelTask"
                    >
                      取消当前任务
                    </button>
                    <button
                      type="button"
                      class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950"
                      @click="handleReset"
                    >
                      重置当前任务
                    </button>
                  </div>
                </div>

                <div class="mt-6 overflow-x-auto">
                  <div class="flex min-w-max items-center gap-3">
                    <template v-for="(step, index) in steps" :key="step">
                      <div class="flex items-center gap-3">
                        <span
                          class="flex h-10 w-10 items-center justify-center rounded-full border text-sm font-semibold"
                          :class="getStepCircleClass(index)"
                        >
                          {{ currentStep > index ? '✓' : index + 1 }}
                        </span>
                        <div>
                          <p
                            class="text-sm font-medium"
                            :class="currentStep >= index ? 'text-slate-950' : 'text-slate-400'"
                          >
                            {{ step }}
                          </p>
                          <p class="text-xs text-slate-400">{{ stepDescriptions[index] }}</p>
                        </div>
                      </div>
                      <div
                        v-if="index < steps.length - 1"
                        class="h-px w-10 bg-slate-200"
                        :class="currentStep > index ? 'bg-slate-900' : 'bg-slate-200'"
                      ></div>
                    </template>
                  </div>
                </div>
              </div>

              <div v-if="currentStep === 0" class="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_320px]">
                <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                  <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                    <div class="max-w-2xl">
                      <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">New Workflow</p>
                      <h3 class="mt-3 text-3xl font-semibold tracking-tight text-slate-950">新建一条内容生产任务</h3>
                      <p class="mt-4 text-sm leading-7 text-slate-500">
                        先给出内容方向，再从候选选题里挑一条继续推进。文章草稿、审核反馈和配图结果会统一回收在这个工作台里。
                      </p>
                    </div>
                    <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                      当前模式: <span class="font-medium text-slate-950">{{ resolvedContentMode || '请填写自定义模式' }}</span>
                    </div>
                  </div>

                  <div class="mt-8">
                    <label class="text-sm font-medium text-slate-700">内容模式</label>
                    <div class="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                      <button
                        v-for="mode in contentModes"
                        :key="mode"
                        type="button"
                        class="rounded-2xl border px-4 py-3 text-sm font-medium transition"
                        :class="activeMode === mode ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'"
                        @click="activeMode = mode"
                      >
                        {{ mode }}
                      </button>
                    </div>
                    <div v-if="activeMode === CUSTOM_MODE_LABEL" class="mt-4">
                      <input
                        v-model="customContentMode"
                        type="text"
                        maxlength="40"
                        placeholder="输入你的内容模式，例如：品牌故事、行业观察"
                        class="h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-200"
                        @keyup.enter="handleStart"
                      />
                      <p class="mt-2 text-xs text-slate-500">自定义模式会和内容方向一起交给 AI，控制文章的写作方式。</p>
                    </div>
                  </div>

                  <div class="mt-8 space-y-4">
                    <label class="text-sm font-medium text-slate-700">内容方向</label>
                    <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_180px]">
                      <input
                        v-model="topicDirection"
                        type="text"
                        placeholder="例如：AI Agent 实战、Python 自动化、求职成长、小红书运营"
                        class="h-14 rounded-2xl border border-slate-200 bg-white px-5 text-base text-slate-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-200"
                        @keyup.enter="handleStart"
                      />
                      <button
                        type="button"
                        :disabled="!topicDirection.trim() || (activeMode === CUSTOM_MODE_LABEL && !customContentMode.trim()) || loading"
                        class="inline-flex h-14 items-center justify-center rounded-2xl bg-slate-950 px-5 text-base font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                        @click="handleStart"
                      >
                        {{ loading ? '生成中...' : '开始生成选题' }}
                      </button>
                    </div>
                  </div>

                  <div class="mt-8 grid gap-4 md:grid-cols-3">
                    <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p class="text-sm font-medium text-slate-900">历史任务</p>
                      <p class="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{{ threadList.length }}</p>
                      <p class="mt-2 text-sm text-slate-500">可以随时切回旧工作流继续推进。</p>
                    </div>
                    <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p class="text-sm font-medium text-slate-900">配图输出</p>
                      <p class="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{{ imageUrls.length }}</p>
                      <p class="mt-2 text-sm text-slate-500">最终阶段会把图片结果一起展示出来。</p>
                    </div>
                    <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p class="text-sm font-medium text-slate-900">运行日志</p>
                      <p class="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{{ streamLogs.length }}</p>
                      <p class="mt-2 text-sm text-slate-500">右侧会保留最近的工作流事件。</p>
                    </div>
                  </div>
                </div>

                <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Quick Start</p>
                      <h3 class="mt-2 text-xl font-semibold tracking-tight text-slate-950">常用主题模板</h3>
                    </div>
                    <span class="text-sm text-slate-400">{{ quickPrompts.length }} 条</span>
                  </div>

                  <div class="mt-6 space-y-3">
                    <button
                      v-for="prompt in quickPrompts"
                      :key="prompt"
                      type="button"
                      class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-4 text-left text-sm leading-6 text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                      @click="applyTemplate(prompt)"
                    >
                      {{ prompt }}
                    </button>
                  </div>
                </div>
              </div>

              <div v-else-if="currentStep === 1" class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Topic Selection</p>
                    <h3 class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">选择一个继续写的选题</h3>
                    <p class="mt-2 text-sm text-slate-500">系统会根据你输入的方向生成候选标题，选择一个后继续进入写稿阶段。</p>
                  </div>
                  <button
                    type="button"
                    class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950"
                    @click="handleReset"
                  >
                    重新开始
                  </button>
                </div>

                <div
                  v-if="loading && generatedTopics.length === 0"
                  class="mt-8 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-16 text-center"
                >
                  <div class="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900"></div>
                  <p class="mt-4 text-sm text-slate-500">AI 正在整理候选选题...</p>
                </div>

                <div v-else class="mt-8 grid gap-4">
                  <button
                    v-for="topic in generatedTopics"
                    :key="topic"
                    type="button"
                    class="rounded-2xl border p-5 text-left transition"
                    :class="selectedTopic === topic ? 'border-slate-900 bg-slate-950 text-white shadow-lg shadow-slate-200' : 'border-slate-200 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50'"
                    @click="selectedTopic = topic"
                  >
                    <div class="flex items-start gap-4">
                      <span
                        class="mt-1 flex h-5 w-5 items-center justify-center rounded-full border"
                        :class="selectedTopic === topic ? 'border-white bg-white text-slate-950' : 'border-slate-300 bg-white text-transparent'"
                      >
                        •
                      </span>
                      <div class="min-w-0">
                        <p class="text-base font-medium">{{ topic }}</p>
                        <p class="mt-2 text-sm" :class="selectedTopic === topic ? 'text-slate-300' : 'text-slate-500'">
                          选择后将立即生成文章草稿，并进入审核环节。
                        </p>
                      </div>
                    </div>
                  </button>

                  <div
                    class="rounded-2xl border p-5 transition"
                    :class="isCustomTopicSelected ? 'border-slate-900 bg-slate-950 text-white shadow-lg shadow-slate-200' : 'border-slate-200 bg-white text-slate-900'"
                  >
                    <div class="flex items-start gap-4">
                      <span
                        class="mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border"
                        :class="isCustomTopicSelected ? 'border-white bg-white text-slate-950' : 'border-slate-300 bg-white text-transparent'"
                      >
                        •
                      </span>
                      <div class="min-w-0 flex-1">
                        <p class="text-base font-medium">自定义选题</p>
                        <input
                          v-model="customTopic"
                          type="text"
                          maxlength="200"
                          placeholder="不使用以上候选，输入你想写的选题"
                          class="mt-3 h-12 w-full rounded-xl border px-4 text-sm outline-none transition"
                          :class="isCustomTopicSelected ? 'border-slate-600 bg-slate-900 text-white placeholder:text-slate-400 focus:border-white' : 'border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:border-slate-900 focus:bg-white'"
                          @focus="selectCustomTopic"
                          @input="selectCustomTopic"
                          @keyup.enter="handleSelectTopic"
                        />
                        <p class="mt-2 text-sm" :class="isCustomTopicSelected ? 'text-slate-300' : 'text-slate-500'">
                          输入后将直接按你的选题生成文章草稿。
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="mt-8 flex justify-end">
                  <button
                    type="button"
                    :disabled="!selectedTopic.trim() || loading"
                    class="inline-flex h-12 items-center justify-center rounded-xl bg-slate-950 px-5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                    @click="handleSelectTopic"
                  >
                    {{ loading ? '生成草稿中...' : '确认并生成草稿' }}
                  </button>
                </div>
              </div>

              <div v-else-if="currentStep === 2" class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Draft Review</p>
                    <h3 class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">审核文章草稿</h3>
                    <p class="mt-2 text-sm text-slate-500">可以直接复制全文、导出 Markdown，或者给出修改意见后重写。</p>
                  </div>
                  <div class="flex flex-wrap gap-3">
                    <button
                      type="button"
                      class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950"
                      @click="copyArticle"
                    >
                      复制全文
                    </button>
                    <button
                      type="button"
                      class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950"
                      @click="exportArticle"
                    >
                      导出 Markdown
                    </button>
                    <button
                      type="button"
                      class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950"
                      @click="handleRegenerate"
                    >
                      重新生成
                    </button>
                  </div>
                </div>

                <div
                  v-if="loading && !articleContent"
                  class="mt-8 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-16 text-center"
                >
                  <div class="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900"></div>
                  <p class="mt-4 text-sm text-slate-500">AI 正在写稿...</p>
                </div>

                <template v-else>
                  <div class="mt-8 overflow-hidden rounded-3xl border border-slate-200">
                    <div class="border-b border-slate-200 bg-slate-50 px-5 py-4">
                      <p class="text-sm font-medium text-slate-700">文章内容</p>
                    </div>
                    <div class="max-h-[36rem] overflow-y-auto px-5 py-5">
                      <div class="whitespace-pre-wrap text-sm leading-7 text-slate-700">
                        {{ articleContent }}<span v-if="loading" class="ml-1 inline-block h-4 w-0.5 animate-pulse bg-slate-900"></span>
                      </div>
                    </div>
                  </div>

                  <div class="mt-6 space-y-3">
                    <label class="text-sm font-medium text-slate-700">修改意见</label>
                    <textarea
                      v-model="feedback"
                      rows="4"
                      placeholder="例如：开头更像真实经验分享，增加案例，减少口号式表达。"
                      class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-200"
                    ></textarea>
                  </div>

                  <div class="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
                    <button
                      type="button"
                      :disabled="loading"
                      class="inline-flex h-12 items-center justify-center rounded-xl border border-slate-200 bg-white px-5 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                      @click="handleReject"
                    >
                      退回并重写
                    </button>
                    <button
                      type="button"
                      :disabled="loading"
                      class="inline-flex h-12 items-center justify-center rounded-xl bg-slate-950 px-5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                      @click="handleApprove"
                    >
                      审核通过并生成配图
                    </button>
                  </div>
                </template>
              </div>

              <div v-else-if="currentStep === 3" class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Visual Generation</p>
                    <h3 class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                      {{ imageReviewReady ? '配图已生成，请审核' : '正在生成配图' }}
                    </h3>
                  </div>
                  <span
                    class="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium"
                    :class="imageReviewReady ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'"
                  >
                    {{ imageReviewReady ? '待审核' : '处理中' }}
                  </span>
                </div>

                <div v-if="visualPoints.length" class="mt-8 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                  <p class="text-sm font-medium text-slate-900">配图摘要</p>
                  <div class="mt-4 space-y-3">
                    <div v-for="(point, index) in visualPoints" :key="point + index" class="flex items-start gap-3">
                      <span class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                        {{ index + 1 }}
                      </span>
                      <p class="text-sm leading-6 text-slate-600">{{ point }}</p>
                    </div>
                  </div>
                </div>

                <div class="mt-8 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p class="text-sm font-medium text-slate-900">{{ imageProgressMessage }}</p>
                      <p class="mt-1 text-sm text-slate-500">
                        已完成 {{ imageProgress.completed || 0 }}/{{ imageProgress.total || 1 }}
                      </p>
                    </div>
                    <span class="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600">
                      {{ imageProgressPercent }}%
                    </span>
                  </div>

                  <div class="mt-4 h-2 overflow-hidden rounded-full bg-slate-200">
                    <div
                      class="h-full rounded-full bg-slate-950 transition-all duration-300"
                      :style="{ width: `${imageProgressPercent}%` }"
                    ></div>
                  </div>

                  <p v-if="imageProgress.visualPoint" class="mt-4 text-sm leading-6 text-slate-600">
                    {{ imageProgress.visualPoint }}
                  </p>

                </div>

                  <div v-if="imageReviewReady" class="mt-8 rounded-3xl border border-slate-200 bg-white p-5">
                  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p class="text-sm font-medium text-slate-900">审核配图</p>
                      <p class="mt-1 text-sm text-slate-500">确认合适后即可进入任务完成页，不合适可以单张重生成。</p>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <button
                        v-if="canFillMissingImages"
                        type="button"
                        class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950 disabled:cursor-not-allowed disabled:text-slate-300"
                        :disabled="loading"
                        @click="handleFillMissingImages"
                      >
                        补齐剩余配图
                      </button>
                      <button
                        type="button"
                        class="inline-flex h-10 items-center justify-center rounded-xl bg-slate-950 px-4 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                        :disabled="loading"
                        @click="handleApproveImages"
                      >
                        全部通过
                      </button>
                    </div>
                  </div>

                  <div class="mt-5 grid justify-start gap-4 [grid-template-columns:repeat(auto-fit,minmax(220px,280px))]">
                    <div
                      v-for="(url, index) in imageUrls"
                      :key="url + index"
                      class="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50"
                    >
                      <img :src="url" :alt="`生成图片 ${index + 1}`" class="aspect-[3/4] w-full object-cover" />
                      <div class="border-t border-slate-200 px-4 py-3">
                        <div class="flex items-center justify-between gap-3 text-sm text-slate-500">
                          <span>{{ imageRoleLabels[index] || `配图 ${index + 1}` }}</span>
                          <a
                            :href="url"
                            :download="`xhs-image-${index + 1}.png`"
                            class="font-medium text-slate-700 transition hover:text-slate-950"
                          >
                            下载图片
                          </a>
                        </div>

                        <p v-if="visualPoints[index]" class="mt-3 max-h-20 overflow-y-auto text-sm leading-6 text-slate-600">
                          {{ visualPoints[index] }}
                        </p>

                        <div class="mt-4 space-y-3">
                          <textarea
                            v-model="imageFeedbacks[index]"
                            rows="2"
                            class="w-full resize-none rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                            :placeholder="`说明第 ${index + 1} 张哪里不合适`"
                          ></textarea>
                          <button
                            type="button"
                            class="inline-flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950 disabled:cursor-not-allowed disabled:text-slate-300"
                            :disabled="loading"
                            @click="handleRegenerateImage(index)"
                          >
                            {{ regeneratingImageIndex === index ? '重生成中' : '重生成这张' }}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="currentStep === 4" class="space-y-6">
                <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                  <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Completed</p>
                      <h3 class="mt-2 text-3xl font-semibold tracking-tight text-slate-950">内容任务已完成</h3>
                      <p class="mt-2 text-sm text-slate-500">下面是最终文章与配图结果，可以继续复制、导出或切换到其他任务。</p>
                    </div>
                    <div class="space-y-3">
                      <div class="flex flex-wrap justify-end gap-3">
                        <button
                          type="button"
                          class="inline-flex h-10 items-center justify-center rounded-xl bg-slate-950 px-4 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                          :disabled="exportingPackage || !threadId"
                          @click="handleExportPublishPackage"
                        >
                          {{ exportingPackage ? '正在打包' : '一键导出发布包' }}
                        </button>
                        <button
                          type="button"
                          class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950"
                          @click="copyArticle"
                        >
                          复制全文
                        </button>
                        <button
                          type="button"
                          class="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950"
                          @click="exportArticle"
                        >
                          导出 Markdown
                        </button>
                      </div>
                  <div class="grid grid-cols-2 gap-3">
                    <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p class="text-xs uppercase tracking-[0.2em] text-slate-400">耗时</p>
                      <p class="mt-2 text-lg font-semibold text-slate-950">{{ totalDuration }}</p>
                    </div>
                    <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Token</p>
                      <p class="mt-2 text-lg font-semibold text-slate-950">{{ totalTokens }}</p>
                    </div>
                    <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p class="text-xs uppercase tracking-[0.2em] text-slate-400">图片模型</p>
                      <p class="mt-2 text-sm font-semibold text-slate-950">{{ imageModel || '本地兜底' }}</p>
                    </div>
                    <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p class="text-xs uppercase tracking-[0.2em] text-slate-400">预估花费</p>
                      <p class="mt-2 text-lg font-semibold text-slate-950">{{ estimatedCost }}</p>
                      <p class="mt-1 text-xs text-slate-400">根据 Token 与图片数量估算</p>
                    </div>
                  </div>
                </div>
                  </div>

                  <div class="mt-8 overflow-hidden rounded-3xl border border-slate-200">
                    <div class="border-b border-slate-200 bg-slate-50 px-5 py-4">
                      <p class="text-sm font-medium text-slate-700">最终文章</p>
                    </div>
                    <div class="max-h-[36rem] overflow-y-auto px-5 py-5">
                      <div class="whitespace-pre-wrap text-sm leading-7 text-slate-700">
                        {{ articleContent }}
                      </div>
                    </div>
                  </div>
                </div>

                <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Images</p>
                      <h3 class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">配图结果</h3>
                    </div>
                    <div class="flex items-center gap-2">
                      <span
                        class="rounded-full border px-3 py-1.5 text-sm"
                        :class="needsImageReview ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-slate-200 bg-slate-50 text-slate-600'"
                      >
                        {{ needsImageReview ? '待审核' : `${imageUrls.length} 张` }}
                      </span>
                      <button
                        v-if="needsImageReview"
                        type="button"
                        class="inline-flex h-9 items-center justify-center rounded-xl bg-slate-950 px-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                        :disabled="loading"
                        @click="handleApproveImages"
                      >
                        全部通过
                      </button>
                    </div>
                  </div>

                  <div v-if="imageUrls.length" class="mt-6 grid justify-start gap-4 [grid-template-columns:repeat(auto-fit,minmax(220px,280px))]">
                    <div
                      v-for="(url, index) in imageUrls"
                      :key="url + index"
                      class="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50"
                    >
                      <img :src="url" :alt="`生成图片 ${index + 1}`" class="aspect-[3/4] w-full object-cover" />
                      <div class="border-t border-slate-200 px-4 py-3">
                        <div class="flex items-center justify-between gap-3 text-sm text-slate-500">
                          <span>{{ imageRoleLabels[index] || `配图 ${index + 1}` }}</span>
                          <a
                            :href="url"
                            :download="`xhs-image-${index + 1}.png`"
                            class="font-medium text-slate-700 transition hover:text-slate-950"
                          >
                            下载图片
                          </a>
                        </div>

                        <p v-if="visualPoints[index]" class="mt-3 max-h-20 overflow-y-auto text-sm leading-6 text-slate-600">
                          {{ visualPoints[index] }}
                        </p>

                        <div v-if="needsImageReview" class="mt-4 space-y-3">
                          <textarea
                            v-model="imageFeedbacks[index]"
                            rows="2"
                            class="w-full resize-none rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                            :placeholder="`说明第 ${index + 1} 张哪里不合适`"
                          ></textarea>
                          <button
                            type="button"
                            class="inline-flex h-9 items-center justify-center rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition hover:border-slate-900 hover:text-slate-950 disabled:cursor-not-allowed disabled:text-slate-300"
                            :disabled="loading"
                            @click="handleRegenerateImage(index)"
                          >
                            {{ regeneratingImageIndex === index ? '重生成中' : '重生成这张' }}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div
                    v-else
                    class="mt-6 rounded-3xl border border-dashed border-slate-200 bg-slate-50 px-4 py-12 text-center text-sm text-slate-500"
                  >
                    当前任务没有返回图片结果。
                  </div>

                  <div v-if="visualPoints.length" class="mt-8 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                    <p class="text-sm font-medium text-slate-900">配图摘要</p>
                    <div class="mt-4 space-y-3">
                      <div v-for="(point, index) in visualPoints" :key="point + index" class="flex items-start gap-3">
                        <span class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                          {{ index + 1 }}
                        </span>
                        <p class="text-sm leading-6 text-slate-600">{{ point }}</p>
                      </div>
                    </div>
                  </div>

                  <div v-if="imageHistory.length" class="mt-5 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                    <p class="text-sm font-medium text-slate-900">重生成记录</p>
                    <div class="mt-3 space-y-2 text-sm text-slate-600">
                      <p v-for="item in imageHistory.slice(-3).reverse()" :key="`${item.index}-${item.regenerated_at}-${item.url}`">
                        第 {{ Number(item.index) + 1 }} 张 · {{ item.regenerated_at || '刚刚' }} · {{ item.feedback || '无额外反馈' }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <aside class="min-w-0 space-y-6">
              <div class="min-w-0 overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Session</p>
                    <h3 class="mt-2 text-xl font-semibold tracking-tight text-slate-950">运行摘要</h3>
                  </div>
                  <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">
                    {{ currentStepLabel }}
                  </span>
                </div>

                <div class="mt-5 space-y-4">
                  <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p class="text-xs uppercase tracking-[0.2em] text-slate-400">主题方向</p>
                    <p class="mt-2 text-sm font-medium leading-6 text-slate-900">{{ topicDirection || '暂未设置' }}</p>
                  </div>
                  <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p class="text-xs uppercase tracking-[0.2em] text-slate-400">当前选题</p>
                    <p class="mt-2 text-sm font-medium leading-6 text-slate-900">{{ selectedTopic || '暂未选择' }}</p>
                  </div>
                  <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p class="text-xs uppercase tracking-[0.2em] text-slate-400">线程编号</p>
                    <p class="mt-2 break-all text-sm font-medium leading-6 text-slate-900">{{ threadId || '等待创建' }}</p>
                  </div>
                </div>
              </div>

              <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Metrics</p>
                    <h3 class="mt-2 text-xl font-semibold tracking-tight text-slate-950">关键指标</h3>
                  </div>
                </div>

                <div class="mt-5 grid grid-cols-2 gap-3">
                  <div v-for="item in workspaceStats" :key="item.label" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p class="text-xs uppercase tracking-[0.18em] text-slate-400">{{ item.label }}</p>
                    <p class="mt-3 text-2xl font-semibold tracking-tight text-slate-950">{{ item.value }}</p>
                    <p class="mt-2 text-xs leading-5 text-slate-500">{{ item.hint }}</p>
                  </div>
                </div>
              </div>

              <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Cost</p>
                    <h3 class="mt-2 text-xl font-semibold tracking-tight text-slate-950">模型与成本</h3>
                  </div>
                </div>

                <div class="mt-5 grid grid-cols-2 gap-3">
                  <div v-for="item in modelStats" :key="item.label" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p class="text-xs uppercase tracking-[0.18em] text-slate-400">{{ item.label }}</p>
                    <p class="mt-3 break-words text-sm font-semibold leading-5 text-slate-950">{{ item.value }}</p>
                    <p class="mt-2 text-xs leading-5 text-slate-500">{{ item.hint }}</p>
                  </div>
                </div>
              </div>

              <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Checkpoint</p>
                    <h3 class="mt-2 text-xl font-semibold tracking-tight text-slate-950">状态存档</h3>
                  </div>
                  <button
                    type="button"
                    :disabled="!threadId || loadingCheckpointHistory"
                    class="rounded-lg px-2 py-1 text-sm font-medium text-slate-500 transition hover:text-slate-950 disabled:cursor-not-allowed disabled:text-slate-300"
                    @click="fetchCheckpointHistory()"
                  >
                    刷新
                  </button>
                </div>

                <div v-if="checkpointTimeline.length" class="mt-5 space-y-3">
                  <div v-for="item in checkpointTimeline" :key="`${item.index}-${item.time}-${item.status}`" class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div class="flex items-center justify-between gap-3">
                      <span class="text-xs font-semibold text-slate-400">#{{ item.index }}</span>
                      <span class="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600">{{ item.status }}</span>
                    </div>
                    <p class="mt-3 line-clamp-2 text-sm font-medium leading-6 text-slate-900">{{ item.title }}</p>
                    <div class="mt-3 space-y-1 text-xs leading-5 text-slate-500">
                      <p>Next: {{ item.next }}</p>
                      <p>Metrics: {{ item.nodeCount }}</p>
                      <p>{{ item.time }}</p>
                    </div>
                  </div>
                </div>
                <div
                  v-else
                  class="mt-5 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500"
                >
                  当前还没有 checkpoint 记录。
                </div>
              </div>

              <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">Activity</p>
                    <h3 class="mt-2 text-xl font-semibold tracking-tight text-slate-950">运行日志</h3>
                  </div>
                  <button
                    type="button"
                    class="rounded-lg px-2 py-1 text-sm font-medium text-slate-500 transition hover:text-slate-950"
                    @click="clearStreamLogs"
                  >
                    清空
                  </button>
                </div>

                <div v-if="recentLogs.length" class="mt-5 min-w-0 space-y-3">
                  <div v-for="(log, index) in recentLogs" :key="`${log.time}-${log.type}-${index}`" class="min-w-0 max-w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div class="flex items-center justify-between gap-3">
                      <span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="getLogBadgeClass(log.type)">
                        {{ getLogBadgeLabel(log.type) }}
                      </span>
                      <span class="text-xs text-slate-400">{{ log.time }}</span>
                    </div>
                    <p class="mt-3 whitespace-normal break-words text-sm leading-6 text-slate-600 [overflow-wrap:anywhere]">
                      {{ log.message }}
                    </p>
                  </div>
                </div>

                <div
                  v-else
                  class="mt-5 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-12 text-center text-sm text-slate-500"
                >
                  当前还没有运行日志。
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  deleteThread,
  downloadPublishPackage,
  getAllThreads,
  getCurrentUser,
  getWorkflowHistory,
  getWorkflowState,
  isLoggedIn as checkLoggedIn,
  login,
  logout,
  register,
  streamApproveArticle,
  streamApproveImages,
  streamGenerateMissingImages,
  streamRegenerateImage,
  streamRejectArticle,
  streamSelectTopic,
  streamStartWorkflow,
} from './api.js'

const steps = ['输入方向', '选择选题', '审核草稿', '生成配图', '任务完成']
const stepDescriptions = ['定义内容范围', '挑选继续写的题目', '确认文章质量', '输出视觉素材', '查看最终结果']
const imageRoleLabels = ['封面主视觉', '方法 / 流程图', '成果 / 细节图']
const CUSTOM_MODE_LABEL = '自定义'
const contentModes = ['小红书爆款', '技术干货', '职场方法', CUSTOM_MODE_LABEL]
const quickPrompts = ['AI Agent 入门实战', 'AI 工具如何提升内容效率', 'Python 自动化办公案例', '求职新人如何搭建个人知识体系']

const isLoggedIn = ref(false)
const isLoginMode = ref(true)
const authLoading = ref(false)
const authError = ref('')
const currentUsername = ref('')
const authForm = ref({ username: '', password: '' })

const sidebarOpen = ref(true)
const loadingThreads = ref(false)
const threadList = ref([])
const streamLogs = ref([])
const checkpointHistory = ref([])
const loadingCheckpointHistory = ref(false)

const currentStep = ref(0)
const loading = ref(false)
const exportingPackage = ref(false)
const message = ref('')
const messageType = ref('info')
const activeMode = ref(contentModes[0])
const customContentMode = ref('')

const threadId = ref('')
const workflowStatus = ref('')
const interruptInfo = ref(null)

const topicDirection = ref('')
const generatedTopics = ref([])
const selectedTopic = ref('')
const customTopic = ref('')
const articleContent = ref('')
const feedback = ref('')
const imageUrls = ref([])
const visualPoints = ref([])
const nodeMetrics = ref([])
const imageModel = ref('')
const imageReviewStatus = ref('pending')
const imageHistory = ref([])
const imageFeedbacks = ref({})
const regeneratingImageIndex = ref(null)
const imageProgress = ref({
  active: false,
  event: 'idle',
  index: null,
  total: 0,
  completed: 0,
  visualPoint: '',
  url: '',
  message: '',
})

let messageTimer = null
let taskAbortController = null
let taskAbortTimer = null
let taskAbortReason = ''

const TASK_TIMEOUT_MS = 6 * 60 * 1000
const ESTIMATED_LLM_COST_PER_1K = Number(import.meta.env.VITE_ESTIMATED_LLM_COST_PER_1K || 0.02)
const ESTIMATED_IMAGE_COST_PER_IMAGE = Number(import.meta.env.VITE_ESTIMATED_IMAGE_COST_PER_IMAGE || 0.6)

const userInitial = computed(() => (currentUsername.value?.charAt(0) || 'A').toUpperCase())
const resolvedContentMode = computed(() => (
  activeMode.value === CUSTOM_MODE_LABEL ? customContentMode.value.trim() : activeMode.value
))
const isCustomTopicSelected = computed(() => (
  Boolean(customTopic.value.trim()) && selectedTopic.value === customTopic.value.trim()
))
const currentStepLabel = computed(() => steps[currentStep.value] || steps[0])
const latestLLMModel = computed(() => {
  const item = [...nodeMetrics.value].reverse().find((metric) => metric.model && metric.node_name !== 'generate_images')
  return item?.model || 'qwen-plus'
})

const runStatusLabel = computed(() => {
  if (loading.value) return '运行中'
  if (currentStep.value === 4) return '已完成'
  if (workflowStatus.value) return workflowStatus.value
  return currentStep.value === 0 ? '待开始' : '待处理'
})

const totalDuration = computed(() => {
  const total = nodeMetrics.value.reduce((sum, item) => sum + Number(item.duration_ms || 0), 0)
  return formatDuration(total)
})

const totalTokens = computed(() => {
  return nodeMetrics.value.reduce((sum, item) => sum + Number(item.total_tokens || 0), 0)
})

const estimatedCost = computed(() => {
  const tokenCost = (totalTokens.value / 1000) * ESTIMATED_LLM_COST_PER_1K
  const imageCost = imageUrls.value.length * ESTIMATED_IMAGE_COST_PER_IMAGE
  return formatCurrency(tokenCost + imageCost)
})

const needsImageReview = computed(() => {
  if (!imageUrls.value.length) return false
  if (imageReviewStatus.value === 'approved') return false
  return interruptInfo.value?.action_required === 'image_review' || currentStep.value === 3
})

const imageReviewReady = computed(() => {
  return needsImageReview.value && !loading.value && interruptInfo.value?.action_required === 'image_review'
})

const canFillMissingImages = computed(() => {
  return imageReviewReady.value && visualPoints.value.length > imageUrls.value.length
})

const imageProgressPercent = computed(() => {
  const total = Number(imageProgress.value.total || 0)
  if (!total) return imageProgress.value.active ? 8 : 0
  const completed = Number(imageProgress.value.completed || 0)
  if (imageProgress.value.event === 'image_start') {
    return Math.max(8, Math.round((completed / total) * 100))
  }
  return Math.min(100, Math.round((completed / total) * 100))
})

const imageProgressMessage = computed(() => {
  const progress = imageProgress.value
  const total = progress.total || 1
  const index = progress.index === null || progress.index === undefined ? 1 : Number(progress.index) + 1

  if (progress.event === 'image_start') return `正在生成第 ${index}/${total} 张配图`
  if (progress.event === 'image_done') return `第 ${index}/${total} 张已生成`
  if (progress.event === 'image_failed') return `第 ${index}/${total} 张生成失败，继续处理`
  if (progress.event === 'image_batch_done') return `配图生成完成：${progress.completed || 0}/${total}`
  if (progress.event === 'image_skipped') return progress.message || '已跳过配图生成'
  return '已进入图片生成队列，等待模型响应'
})

const workspaceStats = computed(() => [
  {
    label: '阶段',
    value: currentStepLabel.value,
    hint: loading.value ? '正在执行中' : '等待下一步操作',
  },
  {
    label: '线程',
    value: threadList.value.length,
    hint: '当前账号下的历史任务数',
  },
  {
    label: '选题',
    value: generatedTopics.value.length,
    hint: '本次工作流生成的候选数',
  },
  {
    label: '图片',
    value: imageUrls.value.length,
    hint: '完成后可在结果区查看',
  },
])

const modelStats = computed(() => [
  {
    label: 'LLM模型',
    value: latestLLMModel.value,
    hint: '选题与写稿阶段',
  },
  {
    label: '图片模型',
    value: imageModel.value || 'doubao-seedream-4-5-251128',
    hint: '配图阶段',
  },
  {
    label: '估算成本',
    value: estimatedCost.value,
    hint: '按前端估算单价',
  },
  {
    label: 'Checkpoint',
    value: checkpointHistory.value.length,
    hint: '最近存档数',
  },
])

const checkpointTimeline = computed(() => checkpointHistory.value.slice(0, 5).map((item, index) => ({
  index: index + 1,
  title: item.values?.selected_topic || item.values?.topic_direction || item.values?.status || `快照 ${index + 1}`,
  status: item.values?.status || 'unknown',
  next: item.next?.length ? item.next.join(' → ') : 'END',
  time: formatTimestamp(item.created_at),
  nodeCount: item.values?.node_metrics?.length || 0,
})))

const recentLogs = computed(() => streamLogs.value.slice(-8).reverse())

const messageToneClass = computed(() => {
  if (messageType.value === 'success') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (messageType.value === 'error') return 'border-rose-200 bg-rose-50 text-rose-700'
  return 'border-slate-200 bg-slate-50 text-slate-700'
})

async function checkAuth() {
  if (!checkLoggedIn()) return
  try {
    const user = await getCurrentUser()
    currentUsername.value = user.username
    isLoggedIn.value = true
  } catch {
    isLoggedIn.value = false
  }
}

async function handleAuth() {
  authError.value = ''

  if (!authForm.value.username || authForm.value.username.length < 3) {
    authError.value = '用户名至少需要 3 个字符'
    return
  }

  if (!authForm.value.password || authForm.value.password.length < 6) {
    authError.value = '密码至少需要 6 个字符'
    return
  }

  authLoading.value = true

  try {
    if (isLoginMode.value) {
      await login(authForm.value.username, authForm.value.password)
    } else {
      await register(authForm.value.username, authForm.value.password)
      await login(authForm.value.username, authForm.value.password)
    }

    const user = await getCurrentUser()
    currentUsername.value = user.username
    isLoggedIn.value = true
    authForm.value = { username: '', password: '' }
  } catch (error) {
    const detail = error.response?.data?.detail
    authError.value = Array.isArray(detail) ? detail.map((item) => item.msg).join('；') : (detail || error.message || '操作失败')
  } finally {
    authLoading.value = false
  }
}

function onAuthLogout() {
  handleLogout()
}

function handleLogout() {
  logout()
  isLoggedIn.value = false
  currentUsername.value = ''
  threadList.value = []
  resetWorkflowState()
}

watch(isLoggedIn, (value) => {
  if (value) {
    fetchThreadList()
  }
})

onMounted(() => {
  checkAuth()
  window.addEventListener('auth:logout', onAuthLogout)
})

onUnmounted(() => {
  window.removeEventListener('auth:logout', onAuthLogout)
  if (messageTimer) clearTimeout(messageTimer)
  clearTaskGuard()
})

function showMessage(text, type = 'info') {
  message.value = text
  messageType.value = type

  if (messageTimer) clearTimeout(messageTimer)
  messageTimer = setTimeout(() => {
    message.value = ''
  }, 4000)
}

function resetWorkflowState() {
  currentStep.value = 0
  loading.value = false
  threadId.value = ''
  workflowStatus.value = ''
  interruptInfo.value = null
  activeMode.value = contentModes[0]
  customContentMode.value = ''
  topicDirection.value = ''
  generatedTopics.value = []
  selectedTopic.value = ''
  customTopic.value = ''
  articleContent.value = ''
  feedback.value = ''
  imageUrls.value = []
  visualPoints.value = []
  nodeMetrics.value = []
  imageModel.value = ''
  imageReviewStatus.value = 'pending'
  imageHistory.value = []
  imageFeedbacks.value = {}
  regeneratingImageIndex.value = null
  resetImageProgress()
  checkpointHistory.value = []
  streamLogs.value = []
  message.value = ''
}

function handleReset() {
  resetWorkflowState()
}

function handleNewWorkflow() {
  resetWorkflowState()
  fetchThreadList()
}

function clearTaskGuard() {
  if (taskAbortTimer) {
    clearTimeout(taskAbortTimer)
    taskAbortTimer = null
  }
  taskAbortController = null
  taskAbortReason = ''
}

function beginTaskGuard() {
  clearTaskGuard()
  taskAbortController = new AbortController()
  taskAbortTimer = setTimeout(() => {
    if (taskAbortController) {
      taskAbortReason = 'timeout'
      taskAbortController.abort()
    }
  }, TASK_TIMEOUT_MS)
  return taskAbortController
}

function cancelCurrentTask() {
  if (!taskAbortController) return
  taskAbortReason = 'manual'
  taskAbortController.abort()
}

function formatTaskError(errorText) {
  if (errorText === '__ABORTED__') {
    return taskAbortReason === 'timeout' ? '任务超时，已自动取消。' : '任务已取消。'
  }
  return errorText
}

function formatTimestamp(value) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleString('zh-CN', {
      hour12: false,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return String(value)
  }
}

function formatCurrency(value) {
  if (!Number.isFinite(value)) return '¥0.00'
  return `¥${value.toFixed(2)}`
}

async function fetchCheckpointHistory(targetThreadId = threadId.value) {
  if (!targetThreadId) {
    checkpointHistory.value = []
    return
  }

  loadingCheckpointHistory.value = true
  try {
    const result = await getWorkflowHistory(targetThreadId)
    checkpointHistory.value = result.history || []
  } catch (error) {
    showMessage(`获取 checkpoint 失败: ${error.response?.data?.detail || error.message}`, 'error')
  } finally {
    loadingCheckpointHistory.value = false
  }
}

function buildTopicRequest() {
  const topic = topicDirection.value.trim()
  return resolvedContentMode.value ? `${topic}｜内容模式：${resolvedContentMode.value}` : topic
}

function applyTemplate(prompt) {
  topicDirection.value = prompt
}

function selectCustomTopic(event) {
  if (typeof event?.target?.value === 'string') {
    customTopic.value = event.target.value
  }
  selectedTopic.value = customTopic.value.trim()
}

function addStreamLog(type, data, source = '') {
  // Token 流属于内部传输数据，用户日志只展示阶段性文字。
  if (type === 'llm_token') return

  const now = new Date()
  const time = now.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  const message = getLogMessage(type, data)
  const lastLog = streamLogs.value[streamLogs.value.length - 1]
  if (lastLog?.type === type && lastLog?.message === message && lastLog?.source === source) return

  streamLogs.value.push({
    type,
    source,
    time,
    message,
  })

  if (streamLogs.value.length > 500) {
    streamLogs.value = streamLogs.value.slice(-400)
  }
}

function clearStreamLogs() {
  streamLogs.value = []
}

function getLogMessage(type, data) {
  const nodeLabel = getNodeLabel(data?.node)
  const index = Number(data?.index ?? 0) + 1
  const total = Number(data?.total || 0)

  if (type === 'image_progress') {
    const imageMessages = {
      image_start: data?.message || `正在生成第 ${index}${total ? `/${total}` : ''} 张配图`,
      image_done: `第 ${index} 张配图生成完成`,
      image_failed: `第 ${index} 张配图生成失败，已保留其他图片`,
      image_batch_done: `配图处理完成，共生成 ${Number(data?.completed || 0)}${total ? `/${total}` : ''} 张`,
      image_skipped: data?.message || '没有需要生成的配图',
    }
    return imageMessages[data?.event] || '配图生成进度已更新'
  }

  const map = {
    init: '新任务已创建',
    start: '任务开始处理',
    resume: getResumeMessage(data?.action),
    update: nodeLabel ? `${nodeLabel}进度已更新` : '任务进度已更新',
    node_start: nodeLabel ? `正在${nodeLabel}` : '正在处理当前步骤',
    node_end: nodeLabel ? `${nodeLabel}已完成` : '当前步骤已完成',
    llm_start: '开始生成内容',
    llm_end: '内容生成完成',
    done: '当前阶段处理完成',
    error: '操作出现异常，请根据页面提示重试',
  }

  return map[type] || '任务状态已更新'
}

function getNodeLabel(node) {
  const labels = {
    topic_selection: '准备选题',
    plan_topics: '生成候选选题',
    human_select_topic: '等待选择选题',
    write_draft: '生成文章草稿',
    human_review: '等待审核文章',
    extract_visuals: '提取配图要点',
    generate_images: '生成配图',
    human_image_review: '等待审核配图',
  }
  return labels[node] || ''
}

function getResumeMessage(action) {
  const messages = {
    select_topic: '已选择选题，开始生成文章',
    approve: '文章审核通过，开始生成配图',
    reject: '已提交修改意见，开始重写文章',
    approve_images: '配图审核通过',
    regenerate_image: '已提交单张配图修改要求',
    generate_missing_images: '开始补齐缺失配图',
  }
  return messages[action] || '继续处理任务'
}

function getLogBadgeLabel(type) {
  const labels = {
    init: '任务创建',
    start: '开始处理',
    resume: '继续执行',
    update: '进度更新',
    node_start: '正在处理',
    node_end: '步骤完成',
    llm_start: '内容生成',
    llm_end: '内容完成',
    image_progress: '配图进度',
    done: '阶段完成',
    error: '处理异常',
  }
  return labels[type] || '状态更新'
}

function getLogBadgeClass(type) {
  const map = {
    init: 'bg-emerald-100 text-emerald-700',
    start: 'bg-blue-100 text-blue-700',
    resume: 'bg-violet-100 text-violet-700',
    update: 'bg-amber-100 text-amber-700',
    node_start: 'bg-sky-100 text-sky-700',
    node_end: 'bg-cyan-100 text-cyan-700',
    llm_start: 'bg-slate-900 text-white',
    llm_end: 'bg-slate-100 text-slate-700',
    image_progress: 'bg-cyan-100 text-cyan-700',
    done: 'bg-emerald-100 text-emerald-700',
    error: 'bg-rose-100 text-rose-700',
  }

  return map[type] || 'bg-slate-100 text-slate-700'
}

function formatDuration(ms) {
  if (!ms) return '0ms'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function getStepCircleClass(index) {
  if (currentStep.value > index) return 'border-slate-900 bg-slate-900 text-white'
  if (currentStep.value === index) return 'border-slate-900 bg-white text-slate-950'
  return 'border-slate-200 bg-white text-slate-400'
}

function getThreadTitle(thread) {
  return thread.selected_topic || thread.topic_direction || '未命名任务'
}

function getThreadSubtitle(thread) {
  return thread.topic_direction || thread.status || (thread.is_completed ? '已完成' : '进行中')
}

async function fetchThreadList() {
  loadingThreads.value = true
  try {
    const result = await getAllThreads()
    threadList.value = result.threads || []
  } catch (error) {
    showMessage(`获取任务列表失败: ${error.response?.data?.detail || error.message}`, 'error')
  } finally {
    loadingThreads.value = false
  }
}

async function handleStart() {
  if (!topicDirection.value.trim()) return
  if (activeMode.value === CUSTOM_MODE_LABEL && !customContentMode.value.trim()) {
    showMessage('请先填写自定义内容模式。', 'error')
    return
  }

  const controller = beginTaskGuard()
  loading.value = true
  currentStep.value = 1
  workflowStatus.value = ''
  interruptInfo.value = null
  generatedTopics.value = []
  selectedTopic.value = ''
  customTopic.value = ''
  articleContent.value = ''
  feedback.value = ''
  imageUrls.value = []
  visualPoints.value = []
  nodeMetrics.value = []
  imageModel.value = ''
  imageReviewStatus.value = 'pending'
  imageHistory.value = []
  imageFeedbacks.value = {}
  regeneratingImageIndex.value = null
  resetImageProgress()
  checkpointHistory.value = []
  streamLogs.value = []
  message.value = ''

  try {
    await streamStartWorkflow(buildTopicRequest(), {
      onInit: (data) => {
        threadId.value = data.thread_id
        addStreamLog('init', data, 'start')
      },
      onStart: (data) => addStreamLog('start', data, 'start'),
      onNodeStart: (data) => addStreamLog('node_start', data, 'start'),
      onNodeEnd: (data) => {
        addStreamLog('node_end', data, 'start')
        if (data.output?.generated_topics?.length) generatedTopics.value = data.output.generated_topics
        if (data.output?.node_metrics) nodeMetrics.value = data.output.node_metrics
      },
      onUpdate: (node, output) => {
        addStreamLog('update', { node, output }, 'start')
        if (output.generated_topics?.length) generatedTopics.value = output.generated_topics
        if (output.node_metrics) nodeMetrics.value = output.node_metrics
      },
      onDone: (data) => {
        addStreamLog('done', data, 'start')
        workflowStatus.value = data.status
        interruptInfo.value = data.interrupt_info
        if (data.values?.image_model) imageModel.value = data.values.image_model

        if (data.interrupt_info?.options?.length && generatedTopics.value.length === 0) {
          generatedTopics.value = data.interrupt_info.options
        }

        if (data.values?.generated_topics?.length) generatedTopics.value = data.values.generated_topics
        if (data.values?.node_metrics) nodeMetrics.value = data.values.node_metrics
        void fetchCheckpointHistory(threadId.value)

        loading.value = false
        showMessage('选题已生成，接下来选择一个继续写稿。', 'success')
        fetchThreadList()
      },
      onError: (errorText) => {
        const messageText = formatTaskError(errorText)
        addStreamLog('error', { message: messageText }, 'start')
        loading.value = false
        currentStep.value = 0
        showMessage(`启动失败: ${messageText}`, 'error')
      },
    }, 'updates', { signal: controller.signal })
  } catch (error) {
    loading.value = false
    currentStep.value = 0
    showMessage(`启动失败: ${error.message}`, 'error')
  } finally {
    clearTaskGuard()
  }
}

async function handleSelectTopic() {
  const topic = selectedTopic.value.trim()
  if (!topic) return

  const controller = beginTaskGuard()
  loading.value = true
  currentStep.value = 2
  articleContent.value = ''

  try {
    await streamSelectTopic(threadId.value, topic, {
      onResume: (data) => addStreamLog('resume', data, 'select_topic'),
      onStart: (data) => addStreamLog('start', data, 'select_topic'),
      onNodeStart: (data) => addStreamLog('node_start', data, 'select_topic'),
      onNodeEnd: (data) => {
        addStreamLog('node_end', data, 'select_topic')
        if (data.output?.article_content) articleContent.value = data.output.article_content
        if (data.output?.node_metrics) nodeMetrics.value = data.output.node_metrics
      },
      onLlmToken: (content) => {
        articleContent.value += content
        addStreamLog('llm_token', content, 'select_topic')
      },
      onUpdate: (node, output) => {
        addStreamLog('update', { node, output }, 'select_topic')
        if (node === 'write_draft' && output.article_content) articleContent.value = output.article_content
        if (output.node_metrics) nodeMetrics.value = output.node_metrics
      },
      onDone: (data) => {
        addStreamLog('done', data, 'select_topic')
        workflowStatus.value = data.status
        interruptInfo.value = data.interrupt_info
        if (data.values?.article_content) articleContent.value = data.values.article_content
        if (data.values?.node_metrics) nodeMetrics.value = data.values.node_metrics
        void fetchCheckpointHistory(threadId.value)
        loading.value = false
        showMessage('草稿已生成，可以开始审核。', 'success')
      },
      onError: (errorText) => {
        const messageText = formatTaskError(errorText)
        addStreamLog('error', { message: messageText }, 'select_topic')
        loading.value = false
        currentStep.value = 1
        showMessage(`生成草稿失败: ${messageText}`, 'error')
      },
    }, 'events', { signal: controller.signal })
  } catch (error) {
    loading.value = false
    currentStep.value = 1
    showMessage(`生成草稿失败: ${error.message}`, 'error')
  } finally {
    clearTaskGuard()
  }
}

async function handleApprove() {
  const controller = beginTaskGuard()
  loading.value = true
  currentStep.value = 3
  resetImageProgress()

  try {
    await streamApproveArticle(threadId.value, {
      onResume: (data) => addStreamLog('resume', data, 'approve'),
      onStart: (data) => addStreamLog('start', data, 'approve'),
      onNodeStart: (data) => addStreamLog('node_start', data, 'approve'),
      onNodeEnd: (data) => {
        addStreamLog('node_end', data, 'approve')
        if (data.output?.visual_points) visualPoints.value = data.output.visual_points
        if (data.output?.image_urls) imageUrls.value = data.output.image_urls
        if (data.output?.image_model) imageModel.value = data.output.image_model
        if (data.output?.node_metrics) nodeMetrics.value = data.output.node_metrics
      },
      onUpdate: (node, output) => {
        addStreamLog('update', { node, output }, 'approve')
        if (output.visual_points) visualPoints.value = output.visual_points
        if (output.image_urls) imageUrls.value = output.image_urls
        if (output.node_metrics) nodeMetrics.value = output.node_metrics
      },
      onImageProgress: (data) => {
        addStreamLog('image_progress', data, 'approve')
        updateImageProgress(data)
      },
      onDone: (data) => {
        addStreamLog('done', data, 'approve')
        workflowStatus.value = data.status
        interruptInfo.value = data.interrupt_info
        imageReviewStatus.value = data.values?.image_review_status || imageReviewStatus.value
        if (data.is_completed) {
          articleContent.value = data.values?.article_content || articleContent.value
          visualPoints.value = data.values?.visual_points || visualPoints.value
          imageUrls.value = data.values?.image_urls || imageUrls.value
          imageModel.value = data.values?.image_model || imageModel.value
          imageHistory.value = data.values?.image_history || imageHistory.value
          if (data.values?.node_metrics) nodeMetrics.value = data.values.node_metrics
          void fetchCheckpointHistory(threadId.value)
          currentStep.value = 4
          showMessage('任务完成，结果已经整理好了。', 'success')
        } else if (data.interrupt_info?.action_required === 'image_review') {
          articleContent.value = data.values?.article_content || articleContent.value
          visualPoints.value = data.values?.visual_points || visualPoints.value
          imageUrls.value = data.values?.image_urls || imageUrls.value
          imageModel.value = data.values?.image_model || imageModel.value
          imageHistory.value = data.values?.image_history || imageHistory.value
          if (data.values?.node_metrics) nodeMetrics.value = data.values.node_metrics
          void fetchCheckpointHistory(threadId.value)
          currentStep.value = 3
          showMessage('配图已生成，请审核。', 'success')
        }
        imageProgress.value.active = false
        loading.value = false
        fetchThreadList()
      },
      onError: (errorText) => {
        const messageText = formatTaskError(errorText)
        addStreamLog('error', { message: messageText }, 'approve')
        loading.value = false
        imageProgress.value.active = false
        currentStep.value = 2
        showMessage(`生成配图失败: ${messageText}`, 'error')
      },
    }, 'updates', { signal: controller.signal })
  } catch (error) {
    loading.value = false
    imageProgress.value.active = false
    currentStep.value = 2
    showMessage(`生成配图失败: ${error.message}`, 'error')
  } finally {
    clearTaskGuard()
  }
}

async function handleReject() {
  const controller = beginTaskGuard()
  loading.value = true
  articleContent.value = ''
  const currentFeedback = feedback.value
  feedback.value = ''

  try {
    await streamRejectArticle(threadId.value, currentFeedback, {
      onResume: (data) => addStreamLog('resume', data, 'reject'),
      onStart: (data) => addStreamLog('start', data, 'reject'),
      onNodeStart: (data) => addStreamLog('node_start', data, 'reject'),
      onNodeEnd: (data) => {
        addStreamLog('node_end', data, 'reject')
        if (data.output?.article_content) articleContent.value = data.output.article_content
        if (data.output?.node_metrics) nodeMetrics.value = data.output.node_metrics
      },
      onLlmToken: (content) => {
        articleContent.value += content
        addStreamLog('llm_token', content, 'reject')
      },
      onUpdate: (node, output) => {
        addStreamLog('update', { node, output }, 'reject')
        if (node === 'write_draft' && output.article_content) articleContent.value = output.article_content
        if (output.node_metrics) nodeMetrics.value = output.node_metrics
      },
      onDone: (data) => {
        addStreamLog('done', data, 'reject')
        workflowStatus.value = data.status
        interruptInfo.value = data.interrupt_info
        if (data.values?.article_content) articleContent.value = data.values.article_content
        if (data.values?.node_metrics) nodeMetrics.value = data.values.node_metrics
        void fetchCheckpointHistory(threadId.value)
        loading.value = false
        currentStep.value = 2
        showMessage('草稿已重写，请重新审核。', 'success')
      },
      onError: (errorText) => {
        const messageText = formatTaskError(errorText)
        addStreamLog('error', { message: messageText }, 'reject')
        loading.value = false
        currentStep.value = 2
        showMessage(`重写失败: ${messageText}`, 'error')
      },
    }, 'events', { signal: controller.signal })
  } catch (error) {
    loading.value = false
    currentStep.value = 2
    showMessage(`重写失败: ${error.message}`, 'error')
  } finally {
    clearTaskGuard()
  }
}

function applyWorkflowValues(values = {}) {
  if (values.article_content) articleContent.value = values.article_content
  if (values.visual_points) visualPoints.value = values.visual_points
  if (values.image_urls) imageUrls.value = values.image_urls
  if (values.image_model) imageModel.value = values.image_model
  if (values.image_review_status) imageReviewStatus.value = values.image_review_status
  if (values.image_history) imageHistory.value = values.image_history
  if (values.node_metrics) nodeMetrics.value = values.node_metrics
}

function resetImageProgress() {
  imageProgress.value = {
    active: false,
    event: 'idle',
    index: null,
    total: 0,
    completed: 0,
    visualPoint: '',
    url: '',
    message: '',
  }
}

function updateImageProgress(data = {}) {
  const event = data.event || 'image_progress'
  const total = Number(data.total || imageProgress.value.total || 0)
  const index = data.index ?? imageProgress.value.index
  const completed = data.completed ?? (
    event === 'image_done'
      ? Number(index ?? imageProgress.value.completed ?? 0) + 1
      : imageProgress.value.completed
  )
  imageProgress.value = {
    active: event !== 'image_batch_done' && event !== 'image_skipped',
    event,
    index,
    total,
    completed,
    visualPoint: data.visual_point || imageProgress.value.visualPoint || '',
    url: data.url || imageProgress.value.url || '',
    message: data.message || '',
  }

  if (event === 'image_done' && data.url != null && index !== null && index !== undefined) {
    const nextUrls = [...imageUrls.value]
    while (nextUrls.length <= Number(index)) nextUrls.push('')
    nextUrls[Number(index)] = data.url
    imageUrls.value = nextUrls
  }
}

async function handleApproveImages() {
  const controller = beginTaskGuard()
  loading.value = true
  currentStep.value = 3
  resetImageProgress()

  try {
    await streamApproveImages(threadId.value, {
      onResume: (data) => addStreamLog('resume', data, 'approve_images'),
      onStart: (data) => addStreamLog('start', data, 'approve_images'),
      onNodeStart: (data) => addStreamLog('node_start', data, 'approve_images'),
      onNodeEnd: (data) => {
        addStreamLog('node_end', data, 'approve_images')
        applyWorkflowValues(data.output || {})
      },
      onImageProgress: (data) => {
        addStreamLog('image_progress', data, 'approve_images')
        updateImageProgress(data)
      },
      onDone: (data) => {
        addStreamLog('done', data, 'approve_images')
        workflowStatus.value = data.status
        interruptInfo.value = data.interrupt_info
        applyWorkflowValues(data.values || {})
        void fetchCheckpointHistory(threadId.value)

        if (data.is_completed) {
          currentStep.value = 4
          showMessage('配图已确认，任务完成。', 'success')
          fetchThreadList()
        } else {
          currentStep.value = determineCurrentStep(data)
          showMessage('配图状态已更新。', 'success')
        }
        imageProgress.value.active = false
        loading.value = false
      },
      onError: (errorText) => {
        const messageText = formatTaskError(errorText)
        addStreamLog('error', { message: messageText }, 'approve_images')
        loading.value = false
        imageProgress.value.active = false
        showMessage(`确认配图失败: ${messageText}`, 'error')
      },
    }, 'updates', { signal: controller.signal })
  } catch (error) {
    loading.value = false
    imageProgress.value.active = false
    showMessage(`确认配图失败: ${error.message}`, 'error')
  } finally {
    clearTaskGuard()
  }
}

async function handleFillMissingImages() {
  const controller = beginTaskGuard()
  loading.value = true
  currentStep.value = 3
  resetImageProgress()

  try {
    await streamGenerateMissingImages(threadId.value, {
      onResume: (data) => addStreamLog('resume', data, 'generate_missing_images'),
      onStart: (data) => addStreamLog('start', data, 'generate_missing_images'),
      onNodeStart: (data) => addStreamLog('node_start', data, 'generate_missing_images'),
      onNodeEnd: (data) => {
        addStreamLog('node_end', data, 'generate_missing_images')
        applyWorkflowValues(data.output || {})
      },
      onImageProgress: (data) => {
        addStreamLog('image_progress', data, 'generate_missing_images')
        updateImageProgress(data)
      },
      onDone: (data) => {
        addStreamLog('done', data, 'generate_missing_images')
        workflowStatus.value = data.status
        interruptInfo.value = data.interrupt_info
        applyWorkflowValues(data.values || {})
        void fetchCheckpointHistory(threadId.value)
        currentStep.value = 3
        imageProgress.value.active = false
        loading.value = false
        showMessage('剩余配图已补齐，请继续审核。', 'success')
      },
      onError: (errorText) => {
        const messageText = formatTaskError(errorText)
        addStreamLog('error', { message: messageText }, 'generate_missing_images')
        loading.value = false
        imageProgress.value.active = false
        showMessage(`补齐配图失败: ${messageText}`, 'error')
      },
    }, 'updates', { signal: controller.signal })
  } catch (error) {
    loading.value = false
    imageProgress.value.active = false
    showMessage(`补齐配图失败: ${error.message}`, 'error')
  } finally {
    clearTaskGuard()
  }
}

async function handleRegenerateImage(index) {
  const controller = beginTaskGuard()
  const currentFeedback = imageFeedbacks.value[index] || ''
  const preservedImageUrls = [...imageUrls.value]
  let regeneratedUrl = ''

  const applyRegenerationUpdate = (values = {}) => {
    const returnedUrls = Array.isArray(values.image_urls) ? values.image_urls : []
    if (returnedUrls[index]) regeneratedUrl = returnedUrls[index]

    const valuesWithoutImages = { ...values }
    delete valuesWithoutImages.image_urls
    applyWorkflowValues(valuesWithoutImages)

    if (regeneratedUrl) {
      const nextUrls = [...preservedImageUrls]
      while (nextUrls.length <= index) nextUrls.push('')
      nextUrls[index] = regeneratedUrl
      imageUrls.value = nextUrls
    }
  }

  loading.value = true
  currentStep.value = 3
  regeneratingImageIndex.value = index
  resetImageProgress()

  try {
    await streamRegenerateImage(threadId.value, index, currentFeedback, {
      onResume: (data) => addStreamLog('resume', data, 'regenerate_image'),
      onStart: (data) => addStreamLog('start', data, 'regenerate_image'),
      onNodeStart: (data) => addStreamLog('node_start', data, 'regenerate_image'),
      onNodeEnd: (data) => {
        addStreamLog('node_end', data, 'regenerate_image')
        applyRegenerationUpdate(data.output || {})
      },
      onImageProgress: (data) => {
        addStreamLog('image_progress', data, 'regenerate_image')
        updateImageProgress(data)
        if (Number(data.index) === index && data.url) {
          regeneratedUrl = data.url
          applyRegenerationUpdate()
        }
      },
      onDone: (data) => {
        addStreamLog('done', data, 'regenerate_image')
        workflowStatus.value = data.status
        interruptInfo.value = data.interrupt_info
        applyRegenerationUpdate(data.values || {})
        imageFeedbacks.value[index] = ''
        void fetchCheckpointHistory(threadId.value)
        currentStep.value = data.is_completed ? 4 : 3
        loading.value = false
        regeneratingImageIndex.value = null
        imageProgress.value.active = false
        showMessage(`第 ${index + 1} 张配图已重生成，请再次审核。`, 'success')
      },
      onError: (errorText) => {
        const messageText = formatTaskError(errorText)
        addStreamLog('error', { message: messageText }, 'regenerate_image')
        loading.value = false
        regeneratingImageIndex.value = null
        imageProgress.value.active = false
        showMessage(`重生成配图失败: ${messageText}`, 'error')
      },
    }, { signal: controller.signal })
  } catch (error) {
    loading.value = false
    regeneratingImageIndex.value = null
    imageProgress.value.active = false
    showMessage(`重生成配图失败: ${error.message}`, 'error')
  } finally {
    clearTaskGuard()
  }
}

async function handleSwitchThread(targetThreadId) {
  if (targetThreadId === threadId.value) return

  loading.value = true
  message.value = ''

  try {
    const state = await getWorkflowState(targetThreadId)
    const values = state.values || {}

    threadId.value = targetThreadId
    workflowStatus.value = state.status
    interruptInfo.value = state.interrupt_info
    topicDirection.value = values.topic_direction || ''
    generatedTopics.value = values.generated_topics || []
    selectedTopic.value = values.selected_topic || ''
    customTopic.value = selectedTopic.value && !generatedTopics.value.includes(selectedTopic.value)
      ? selectedTopic.value
      : ''
    articleContent.value = values.article_content || ''
    imageUrls.value = values.image_urls || []
    visualPoints.value = values.visual_points || []
    imageModel.value = values.image_model || ''
    imageReviewStatus.value = values.image_review_status || 'pending'
    imageHistory.value = values.image_history || []
    imageFeedbacks.value = {}
    regeneratingImageIndex.value = null
    resetImageProgress()
    feedback.value = ''
    streamLogs.value = []
    checkpointHistory.value = []
    nodeMetrics.value = (state.node_metrics || values.node_metrics || []).map((item) => ({
      node_name: item.node_name || '',
      duration_ms: item.duration_ms || 0,
      input_tokens: item.input_tokens || 0,
      output_tokens: item.output_tokens || 0,
      total_tokens: item.total_tokens || 0,
      model: item.model || '',
    }))

    currentStep.value = determineCurrentStep(state)
    void fetchCheckpointHistory(targetThreadId)
    showMessage('已切换到历史任务。', 'success')
  } catch (error) {
    showMessage(`切换失败: ${error.response?.data?.detail || error.message}`, 'error')
  } finally {
    loading.value = false
  }
}

function determineCurrentStep(state) {
  const values = state.values || {}
  const actionRequired = state.interrupt_info?.action_required

  if (state.is_completed) return 4
  if (actionRequired === 'select_topic') return 1
  if (actionRequired === 'review') return 2
  if (actionRequired === 'image_review') return 3
  if (values.image_review_status === 'pending' && values.image_urls?.length) return 3
  if (values.image_urls?.length) return 4
  if (values.visual_points?.length) return 3
  if (values.article_content || values.selected_topic) return 2
  if (values.generated_topics?.length) return 1
  return 0
}

async function handleDeleteThread(targetThreadId) {
  const confirmed = window.confirm('确定要删除这条历史任务吗？')
  if (!confirmed) return

  try {
    await deleteThread(targetThreadId)

    if (targetThreadId === threadId.value) {
      resetWorkflowState()
    }

    await fetchThreadList()
    showMessage('任务已删除。', 'success')
  } catch (error) {
    showMessage(`删除失败: ${error.response?.data?.detail || error.message}`, 'error')
  }
}

function copyArticle() {
  navigator.clipboard.writeText(articleContent.value || '').then(() => {
    showMessage('文章已复制到剪贴板。', 'success')
  }).catch(() => {
    showMessage('复制失败，请稍后再试。', 'error')
  })
}

function exportArticle() {
  const blob = new Blob([articleContent.value || ''], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `article-${Date.now()}.md`
  link.click()
  URL.revokeObjectURL(url)
  showMessage('Markdown 已导出。', 'success')
}

async function handleExportPublishPackage() {
  if (!threadId.value || exportingPackage.value) return
  exportingPackage.value = true
  try {
    const { blob, filename } = await downloadPublishPackage(threadId.value)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    showMessage('发布包已导出，包含标题、文案、标签和配图。', 'success')
  } catch (error) {
    showMessage('发布包导出失败，请确认文章和配图均已生成。', 'error')
  } finally {
    exportingPackage.value = false
  }
}

function handleRegenerate() {
  handleReject()
}

function handleCancelTask() {
  cancelCurrentTask()
  loading.value = false
  showMessage('当前任务已取消。', 'error')
}
</script>
