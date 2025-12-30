<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { api, ChatRequest } from '@/services/api';
import DOMPurify from 'dompurify';
import MarkdownIt from 'markdown-it';
import { nextTick, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const md = new MarkdownIt({
  html: false, // Disable HTML tags in source for security
  linkify: true, // Autoconvert URL-like text to links
  breaks: true, // Convert '\n' in paragraphs into <br>
});

const renderMarkdown = (content: string) => {
  const rawHtml = md.render(content);
  return DOMPurify.sanitize(rawHtml);
};

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
    // 1. Push an empty assistant message to the array immediately
    messages.value.push({
      role: 'assistant',
      content: '',
    });

    const request: ChatRequest = {
      message: messageToSend,
      thread_id: threadId.value,
    };

    for await (const token of api.chatStream(request)) {
      // 2. Access the LAST message in the array (which is now a Reactive Proxy)
      const lastMessage = messages.value[messages.value.length - 1];

      // 3. Update the reactive property to trigger the UI re-render
      lastMessage.content += token;

      await scrollToBottom();
    }
  } catch (error) {
    const errorMessage: Message = {
      role: 'assistant',
      content: `Error: ${error instanceof Error ? error.message : 'Unknown error.'}`,
    };

    // If the last message is empty (the failed streaming one), replace it
    if (messages.value[messages.value.length - 1]?.content === '') {
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
  <div class="flex flex-col h-screen bg-background text-foreground font-sans">
    <header class="sticky top-0 z-10 border-b border-border/40 bg-background/80 backdrop-blur-md">
      <div class="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div
            class="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <div>
            <h1 class="text-sm font-semibold leading-none">Obsidian Assistant</h1>
            <p class="text-xs text-muted-foreground truncate max-w-50" :title="vaultPath">
              {{ vaultPath }}
            </p>
          </div>
        </div>
        <Button variant="ghost" size="sm" class="text-xs h-8" @click="changeVault">
          Switch Vault
        </Button>
      </div>
    </header>

    <div class="flex-1 overflow-hidden relative">
      <div ref="chatContainer" class="h-full overflow-y-auto px-4 py-6 scroll-smooth">
        <div class="max-w-3xl mx-auto space-y-8 pb-4">
          <div
            v-if="messages.length === 0"
            class="h-[60vh] flex flex-col items-center justify-center text-center text-muted-foreground"
          >
            <div class="h-12 w-12 rounded-xl bg-muted flex items-center justify-center mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </div>
            <p class="text-lg font-medium text-foreground">Ready to explore your vault</p>
            <p class="text-sm">Ask about your notes, summaries, or connections.</p>
          </div>

          <div
            v-for="(message, index) in messages"
            :key="index"
            class="group flex gap-4 w-full"
            :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div v-if="message.role === 'assistant'" class="shrink-0 mt-1">
              <div
                class="h-8 w-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-xs font-bold"
              >
                AI
              </div>
            </div>

            <div
              class="relative max-w-[85%] rounded-2xl px-5 py-3 text-sm shadow-sm"
              :class="[
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-br-sm'
                  : 'bg-muted/30 border border-border/50 text-foreground rounded-bl-sm',
              ]"
            >
              <div
                v-if="message.role === 'assistant'"
                class="prose prose-sm prose-invert max-w-none prose-pre:bg-[#1e1e2e] prose-pre:border prose-pre:border-white/10 prose-headings:text-foreground prose-p:text-foreground/90 prose-strong:text-foreground"
                v-html="renderMarkdown(message.content)"
              ></div>
              <p v-else class="whitespace-pre-wrap leading-relaxed">{{ message.content }}</p>
            </div>
          </div>

          <div v-if="isLoading && messages[messages.length - 1]?.content === ''" class="flex gap-4">
            <div
              class="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-bold animate-pulse"
            >
              AI
            </div>
            <div class="flex items-center gap-1 h-8">
              <span class="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce"></span>
              <span
                class="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.2s]"
              ></span>
              <span
                class="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.4s]"
              ></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="p-4 bg-background/80 backdrop-blur-lg border-t border-border/40">
      <div class="max-w-3xl mx-auto">
        <form class="relative flex items-center" @submit.prevent="sendMessage">
          <input
            v-model="inputMessage"
            placeholder="Ask me anything..."
            :disabled="isLoading"
            class="flex w-full pl-6 pr-14 h-14 rounded-full bg-muted/40 border border-transparent focus:outline-none focus:border-primary/50 focus:bg-background transition-all shadow-sm text-base file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
          />

          <Button
            type="submit"
            size="icon"
            class="absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full shrink-0 transition-opacity"
            :class="{ 'opacity-50 cursor-not-allowed': isLoading || !inputMessage.trim() }"
          >
            <div
              v-if="isLoading"
              class="animate-spin rounded-full h-4 w-4 border-b-2 border-current"
            ></div>

            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="m5 12 7-7 7 7" />
              <path d="M12 19V5" />
            </svg>
            <span class="sr-only">Send</span>
          </Button>
        </form>
      </div>

      <div class="text-center mt-2">
        <p class="text-[10px] text-muted-foreground/50">
          AI can make mistakes. Verify important info.
        </p>
      </div>
    </div>
  </div>
</template>
