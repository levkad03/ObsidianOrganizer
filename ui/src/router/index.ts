import ChatView from '@/views/ChatView.vue';
import SetupView from '@/views/SetupView.vue';
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'setup',
      component: SetupView,
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
      beforeEnter: (to, from, next) => {
        const vaultPath = localStorage.getItem('vaultPath');
        if (!vaultPath) {
          next('/');
        } else {
          next();
        }
      },
    },
  ],
});

export default router;
