<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { api, DashboardSummary } from '@/services/api';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
// Using Lucide icons for a cleaner look consistent with the new cards
import { Activity, FileText, FileWarning, Link as LinkIcon, Tag } from 'lucide-vue-next';

const router = useRouter();
const loading = ref(true);
const summary = ref<DashboardSummary | null>(null);

// -- MODAL STATE --
const isDetailsOpen = ref(false);
const detailTitle = ref('');
const detailItems = ref<any[]>([]);
const loadingDetails = ref(false);

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// -- CLICK HANDLERS --
const showDetails = async (type: 'broken' | 'orphaned' | 'untagged') => {
  const threadId = localStorage.getItem('threadId');
  if (!threadId) return;

  isDetailsOpen.value = true;
  loadingDetails.value = true;
  detailItems.value = [];

  try {
    if (type === 'broken') {
      detailTitle.value = 'Broken Links';
      const data = await api.getBrokenLinks(threadId);
      detailItems.value = data;
    } else if (type === 'orphaned') {
      detailTitle.value = 'Orphaned Notes';
      const data = await api.getOrphanedNotes(threadId);
      detailItems.value = data.orphaned_notes;
    } else if (type === 'untagged') {
      detailTitle.value = 'Untagged Notes';
      const data = await api.getUntaggedNotes(threadId);
      detailItems.value = data.untagged_notes;
    }
  } catch (e) {
    console.error('Failed to fetch details', e);
  } finally {
    loadingDetails.value = false;
  }
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
            <FileText class="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold">{{ summary.stats.total_notes }}</div>
          </CardContent>
        </Card>

        <Card
          :class="[
            'bg-card/50 backdrop-blur-sm transition-all border-destructive/20 group',
            summary.stats.broken_links > 0 ? 'cursor-pointer hover:bg-destructive/10' : '',
          ]"
          @click="summary.stats.broken_links > 0 && showDetails('broken')"
        >
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium text-destructive">Broken Links</CardTitle>
            <LinkIcon class="h-4 w-4 text-destructive group-hover:scale-110 transition-transform" />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-destructive">{{ summary.stats.broken_links }}</div>
            <p v-if="summary.stats.broken_links > 0" class="text-xs text-muted-foreground">
              Click to view details
            </p>
            <p v-else class="text-xs text-muted-foreground">All clear</p>
          </CardContent>
        </Card>

        <Card
          :class="[
            'bg-card/50 backdrop-blur-sm transition-all border-yellow-500/20 group',
            summary.stats.orphaned_notes > 0 ? 'cursor-pointer hover:bg-yellow-500/10' : '',
          ]"
          @click="summary.stats.orphaned_notes > 0 && showDetails('orphaned')"
        >
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium text-yellow-500">Orphaned</CardTitle>
            <FileWarning
              class="h-4 w-4 text-yellow-500 group-hover:scale-110 transition-transform"
            />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-yellow-500">{{ summary.stats.orphaned_notes }}</div>
            <p v-if="summary.stats.orphaned_notes > 0" class="text-xs text-muted-foreground">
              Click to view details
            </p>
            <p v-else class="text-xs text-muted-foreground">All connected</p>
          </CardContent>
        </Card>

        <Card
          :class="[
            'bg-card/50 backdrop-blur-sm transition-all border-primary/20 group',
            summary.stats.untagged_notes > 0 ? 'cursor-pointer hover:bg-primary/10' : '',
          ]"
          @click="summary.stats.untagged_notes > 0 && showDetails('untagged')"
        >
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium">Untagged</CardTitle>
            <Tag class="h-4 w-4 text-muted-foreground group-hover:scale-110 transition-transform" />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold">{{ summary.stats.untagged_notes }}</div>
            <p v-if="summary.stats.untagged_notes > 0" class="text-xs text-muted-foreground">
              Click to view details
            </p>
            <p v-else class="text-xs text-muted-foreground">All tagged</p>
          </CardContent>
        </Card>
      </div>

      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card class="col-span-4 bg-card/30 border-border/50">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Activity class="h-5 w-5 text-primary" />
              Recent Activity
            </CardTitle>
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
                    <FileText class="h-4 w-4" />
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

    <Dialog v-model:open="isDetailsOpen">
      <DialogContent class="sm:max-w-125 max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{{ detailTitle }}</DialogTitle>
          <DialogDescription>
            Found {{ detailItems.length }} items that need attention.
          </DialogDescription>
        </DialogHeader>

        <div class="flex-1 overflow-y-auto pr-2 mt-4 space-y-2">
          <div v-if="loadingDetails" class="flex justify-center py-8">
            <div
              class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"
            ></div>
          </div>

          <div v-else-if="detailItems.length === 0" class="text-center text-muted-foreground py-4">
            No items found.
          </div>

          <div
            v-for="(item, idx) in detailItems"
            v-else
            :key="idx"
            class="p-3 rounded-md bg-muted/50 text-sm font-mono break-all border border-border/50 flex items-center gap-3"
          >
            <span v-if="typeof item === 'string'">{{ item }}</span>

            <div v-else class="flex flex-col gap-1">
              <span class="font-semibold text-destructive">{{ item.link || item }}</span>
              <span v-if="item.source" class="text-xs text-muted-foreground"
                >in {{ item.source }}</span
              >
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>
