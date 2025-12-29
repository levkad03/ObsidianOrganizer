<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/services/api';
import { open } from '@tauri-apps/api/dialog';
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const vaultPath = ref('');
const isValidating = ref(false);
const error = ref('');

onMounted(() => {
  const savedPath = localStorage.getItem('vaultPath');
  const savedThreadId = localStorage.getItem('threadId');

  if (savedPath && savedThreadId) {
    router.push('/chat');
  }
});

const selectFolder = async () => {
  try {
    const selected = await open({
      directory: true,
      multiple: false,
      title: 'Select Obsidian Vault',
    });

    if (selected && typeof selected === 'string') {
      vaultPath.value = selected;
      error.value = '';
    }
  } catch (err) {
    error.value = 'Failed to open folder selector';
    console.error(err);
  }
};

const validateAndContinue = async () => {
  if (!vaultPath.value) {
    error.value = 'Please select a vault path';
    return;
  }

  isValidating.value = true;
  error.value = '';

  try {
    const threadId = crypto.randomUUID();

    const result = await api.setVault({
      thread_id: threadId,
      vault_path: vaultPath.value,
    });

    if (result.status === 'ok') {
      localStorage.setItem('vaultPath', vaultPath.value);
      localStorage.setItem('threadId', threadId);
      router.push('/chat');
    } else {
      error.value = 'Failed to configure vault';
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to configure vault';
  } finally {
    isValidating.value = false;
  }
};
</script>

<template>
  <div class="min-h-screen bg-background flex items-center justify-center p-4">
    <Card class="w-full max-w-lg">
      <CardHeader>
        <CardTitle>Welcome to Obsidian Organizer</CardTitle>
        <CardDescription>Select your Obsidian vault to get started</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <Label for="vault-path">Vault Path</Label>
          <div class="flex gap-2">
            <Input
              id="vault-path"
              v-model="vaultPath"
              placeholder="/path/to/your/vault"
              readonly
              class="flex-1"
            />
            <Button variant="outline" @click="selectFolder">Browse</Button>
          </div>
        </div>

        <div v-if="error" class="text-sm text-destructive">
          {{ error }}
        </div>

        <Button :disabled="isValidating || !vaultPath" class="w-full" @click="validateAndContinue">
          {{ isValidating ? 'Configuring...' : 'Continue' }}
        </Button>
      </CardContent>
    </Card>
  </div>
</template>
