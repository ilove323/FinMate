import { create } from 'zustand';
import type { ChatMessage, ModuleContext } from '../types';

// ─── Period Store ─────────────────────────────────────────────────────────────

interface PeriodState {
  period: string;
  setPeriod: (p: string) => void;
}

export const usePeriodStore = create<PeriodState>((set) => ({
  period: '2024-03',
  setPeriod: (period) => set({ period }),
}));

// ─── Chat Store ───────────────────────────────────────────────────────────────

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  moduleContext: ModuleContext;
  setModuleContext: (ctx: ModuleContext) => void;
  addMessage: (msg: ChatMessage) => void;
  appendToLastAssistant: (text: string) => void;
  setStreaming: (v: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  moduleContext: null,
  setModuleContext: (moduleContext) => set({ moduleContext }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  appendToLastAssistant: (text) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, content: last.content + text };
      }
      return { messages: msgs };
    }),
  setStreaming: (isStreaming) => set({ isStreaming }),
  clearMessages: () => set({ messages: [] }),
}));
