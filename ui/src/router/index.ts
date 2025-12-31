import AppLayout from '@/layouts/AppLayout.vue';
import ChatView from '@/views/ChatView.vue';
import DashboardView from '@/views/DashboardView.vue';
import SetupView from '@/views/SetupView.vue';
import {
  createRouter,
  createWebHistory,
  NavigationGuardNext,
  RouteLocationNormalized,
} from 'vue-router';

const requireVault = (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  const vaultPath = localStorage.getItem('vaultPath');
  if (!vaultPath) {
    next('/');
  } else {
    next();
  }
};

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 1. Landing Page (Vault Picker)
    {
      path: '/',
      name: 'setup',
      component: SetupView,
      beforeEnter: (to, from, next) => {
        // Optional: If user already has a vault, send them straight to dashboard
        if (localStorage.getItem('vaultPath')) {
          next('/dashboard');
        } else {
          next();
        }
      },
    },

    // 2. Authenticated App Routes (Wrapped in Layout)
    {
      path: '/',
      component: AppLayout,
      // Apply the guard here to protect ALL children (Dashboard & Chat)
      beforeEnter: requireVault,
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
        },
        {
          path: 'chat',
          name: 'chat',
          component: ChatView,
        },
      ],
    },
  ],
});

export default router;
