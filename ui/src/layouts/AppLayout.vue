<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { Hexagon, LayoutDashboard, MessageSquare } from 'lucide-vue-next';
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
        class="h-10 w-10 bg-primary/20 rounded-xl flex items-center justify-center text-primary mb-4 shadow-sm shadow-primary/10 shrink-0"
      >
        <Hexagon class="h-6 w-6 fill-primary/20" />
      </div>

      <Button
        variant="ghost"
        size="icon"
        class="rounded-xl h-10 w-10 p-0 flex items-center justify-center transition-all duration-200"
        :class="
          isActive('/dashboard')
            ? 'bg-primary/15 text-primary shadow-[0_0_15px_rgba(var(--primary),0.3)]'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        "
        title="Dashboard"
        @click="navigate('/dashboard')"
      >
        <LayoutDashboard class="h-5 w-5" />
      </Button>

      <Button
        variant="ghost"
        size="icon"
        class="rounded-xl h-10 w-10 p-0 flex items-center justify-center transition-all duration-200"
        :class="
          isActive('/chat')
            ? 'bg-primary/15 text-primary shadow-[0_0_15px_rgba(var(--primary),0.3)]'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        "
        title="Chat"
        @click="navigate('/chat')"
      >
        <MessageSquare class="h-5 w-5" />
      </Button>
    </aside>

    <main class="flex-1 overflow-auto">
      <router-view></router-view>
    </main>
  </div>
</template>
