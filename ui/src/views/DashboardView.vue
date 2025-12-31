<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api, DashboardSummary } from '@/services/api';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const loading = ref(true);
const summary = ref<DashboardSummary | null>(null);

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

onMounted(async () => {
  const threadId = localStorage.getItem('threadId');
  if (!threadId) {
    router.push('/');
    return;
  }

  try {
    summary.value = await api.getDashboardSummary(threadId);
  } catch (error) {
    console.error('Failed to load dashboard', error);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div
    class="min-h-screen bg-background text-foreground p-6 space-y-8 animate-in fade-in duration-500"
  >
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Vault Overview</h1>
        <p v-if="summary" class="text-muted-foreground mt-1">
          {{ summary.vault.path }}
        </p>
      </div>
      <div v-if="loading" class="flex gap-2 items-center text-sm text-muted-foreground">
        <div
          class="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent"
        ></div>
        Syncing...
      </div>
    </div>

    <div v-if="summary" class="space-y-8">
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card class="bg-card/50 backdrop-blur-sm border-primary/20">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Total Notes</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-muted-foreground"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold">{{ summary.stats.total_notes }}</div>
          </CardContent>
        </Card>

        <Card
          v-if="summary.stats.broken_links > 0"
          class="bg-card/50 backdrop-blur-sm border-destructive/20"
        >
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium text-destructive">Broken Links</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-destructive"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
            </svg>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-destructive">{{ summary.stats.broken_links }}</div>
            <p class="text-xs text-muted-foreground">Across all notes</p>
          </CardContent>
        </Card>
        <Card v-else class="bg-card/50 backdrop-blur-sm border-yellow-500/20">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium text-yellow-500">Orphaned</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-yellow-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-yellow-500">{{ summary.stats.orphaned_notes }}</div>
          </CardContent>
        </Card>

        <Card class="bg-card/50 backdrop-blur-sm border-primary/20">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Untagged</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-muted-foreground"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"
              />
              <line x1="7" y1="7" x2="7.01" y2="7" />
            </svg>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold">{{ summary.stats.untagged_notes }}</div>
          </CardContent>
        </Card>

        <Card class="bg-card/50 backdrop-blur-sm border-primary/20">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Active This Week</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4 text-muted-foreground"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold">{{ summary.stats.recent_notes }}</div>
          </CardContent>
        </Card>
      </div>

      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card class="col-span-4 bg-card/30 border-border/50">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div
                v-for="note in summary.recent_notes.slice(0, 5)"
                :key="note.path"
                class="flex items-center justify-between group cursor-pointer hover:bg-muted/50 p-2 rounded-lg transition-colors"
              >
                <div class="flex items-center gap-4">
                  <div
                    class="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="h-4 w-4"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path
                        d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"
                      />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm font-medium leading-none">{{ note.name }}</p>
                    <p class="text-xs text-muted-foreground mt-1">{{ note.path }}</p>
                  </div>
                </div>
                <div class="text-sm text-muted-foreground">{{ formatDate(note.modified_at) }}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="col-span-3 bg-card/30 border-border/50">
          <CardHeader>
            <CardTitle>Top Connections</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div v-for="(hub, i) in summary.top_hubs" :key="hub.note" class="flex items-center">
                <div class="w-8 font-mono text-muted-foreground text-sm">0{{ i + 1 }}</div>
                <div class="flex-1 text-sm font-medium truncate pr-4">{{ hub.note }}</div>
                <div class="text-xs bg-primary/20 text-primary px-2 py-1 rounded-full font-bold">
                  {{ hub.backlinks }} links
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>
