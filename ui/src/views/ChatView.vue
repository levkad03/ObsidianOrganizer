<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { api, ChatRequest } from '@/services/api';
import { nextTick, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const router = useRouter();
const vaultPath = ref('');
const threadId = ref('');
const messages = ref<Message[]>([]);
const inputMessage = ref('');
const isLoading = ref(false);
const chatContainer = ref<HTMLElement | null>(null);

onMounted(() => {
  const savedPath = localStorage.getItem('vaultPath');
  const savedThreadId = localStorage.getItem('threadId');

  if (!savedPath || !savedThreadId) {
    router.push('/');
    return;
  }
  vaultPath.value = savedPath;
  threadId.value = savedThreadId;
});

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  const userMessage: Message = {
    role: 'user',
    content: inputMessage.value,
  };

  messages.value.push(userMessage);
  const messageToSend = inputMessage.value;
  inputMessage.value = '';
  isLoading.value = true;

  await scrollToBottom();

  try {
    const assistantMessage: Message = {
      role: 'assistant',
      content: '',
    };

    const request: ChatRequest = {
      message: messageToSend,
      thread_id: threadId.value,
    };

    for await (const token of api.chatStream(request)) {
      assistantMessage.content += token;
      await scrollToBottom();
    }
  } catch (error) {
    const errorMessage: Message = {
      role: 'assistant',
      content: `Error: ${error instanceof Error ? error.message : 'Unknown error.'}`,
    };

    if (messages.value[messages.value.length - 1].content === '') {
      messages.value[messages.value.length - 1] = errorMessage;
    } else {
      messages.value.push(errorMessage);
    }
  } finally {
    isLoading.value = false;
    await scrollToBottom();
  }
};

const changeVault = () => {
  localStorage.removeItem('vaultPath');
  localStorage.removeItem('threadId');
  router.push('/');
};
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <header class="border-b px-6 py-4">
      <div class="container mx-auto flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">Obsidian Organizer</h1>
          <p class="text-sm text-muted-foreground">{{ vaultPath }}</p>
        </div>
        <Button variant="outline" @click="changeVault">Change Vault</Button>
      </div>
    </header>

    <div class="flex-1 container mx-auto max-w-4xl p-6 flex flex-col">
      <div ref="chatContainer" class="flex-1 space-y-4 overflow-y-auto mb-4">
        <Card
          v-for="(message, index) in messages"
          :key="index"
          :class="message.role === 'user' ? 'ml-auto max-w-[80%]' : 'mr-auto max-w-[80%]'"
        >
          <CardHeader>
            <CardTitle class="text-sm">{{
              message.role === 'user' ? 'You' : 'Assistant'
            }}</CardTitle>
          </CardHeader>
          <CardContent>
            <p class="whitespace-pre-wrap">{{ message.content }}</p>
          </CardContent>
        </Card>

        <div
          v-if="isLoading && messages[messages.length - 1]?.content === ''"
          class="mr-auto max-w-[80%]"
        >
          <Card>
            <CardContent class="pt-6">
              <p class="text-muted-foreground">Assistant is thinking...</p>
            </CardContent>
          </Card>
        </div>
      </div>
      <div class="flex-gap-2">
        <Input
          v-model="inputMessage"
          placeholder="Ask me anything about your vault..."
          :disabled="isLoading"
          class="flex-1"
          @keyup.enter="sendMessage"
        />
        <Button :disabled="isLoading || !inputMessage.trim()" @click="sendMessage">Send</Button>
      </div>
    </div>
  </div>
</template>
