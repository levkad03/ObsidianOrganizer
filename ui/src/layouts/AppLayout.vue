<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';

const router = useRouter();
const route = useRoute();

const navigate = (path: string) => router.push(path);
const isActive = (path: string) => route.path === path;
</script>

<template>
  <div class="flex h-screen bg-background text-foreground font-sans">
    <aside class="w-16 border-r border-border/40 bg-muted/10 flex flex-col items-center py-6 gap-4">
      <div
        class="h-10 w-10 bg-primary/20 rounded-xl flex items-center justify-center text-primary mb-4"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
          />
        </svg>
      </div>

      <Button
        variant="ghost"
        size="icon"
        class="rounded-xl h-10 w-10 transition-all"
        :class="
          isActive('/dashboard')
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:bg-muted'
        "
        title="Dashboard"
        @click="navigate('/dashboard')"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <rect width="7" height="9" x="3" y="3" rx="1" />
          <rect width="7" height="5" x="14" y="3" rx="1" />
          <rect width="7" height="9" x="14" y="12" rx="1" />
          <rect width="7" height="5" x="3" y="16" rx="1" />
        </svg>
      </Button>

      <Button
        variant="ghost"
        size="icon"
        class="rounded-xl h-10 w-10 transition-all"
        :class="
          isActive('/chat')
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:bg-muted'
        "
        title="Chat"
        @click="navigate('/chat')"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2v5Z" />
          <path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1" />
        </svg>
      </Button>
    </aside>

    <main class="flex-1 overflow-auto">
      <router-view></router-view>
    </main>
  </div>
</template>
