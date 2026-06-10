import { create } from 'zustand';
import axios from 'axios';

// --- Interfaces ---
export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface SessionInfo {
  id?: string;
  timestamp: string;
  filename: string;
  cwd?: string;
  model_id?: string;
  source?: string;
  title?: string;
}

export type ViewMode = 'direct_chat' | 'pidev_sessions' | 'pidev_session_detail' | 'models' | 's3_facade' | 'data_explorer';

export interface ModelConfig {
  model_id: string;
  model_name: string;
  active: boolean;
  log_path?: string;
  custom?: Record<string, any>;
}

export interface SessionDetailItem {
  prompt?: string;
  response?: string;
  type?: string;
  message?: {
    role: 'user' | 'assistant' | 'toolResult';
    content: Array<{ type: 'text'; text: string } | { type: 'toolCall'; name: string; arguments: any }>;
    toolName?: string;
  };
  session_id?: string;
}

interface AppState {
  viewMode: ViewMode;
  isSidebarOpen: boolean;
  configuredModel: string;
  modelsList: ModelConfig[];
  piDevSessions: SessionInfo[];
  directChatSessions: SessionInfo[];
  activePiDevSessionDetail: SessionDetailItem[] | null;
  currentDirectChatMessages: Message[];
  currentDirectChatSessionId: string;
  alertMessage: string | null;
}

interface AppActions {
  setAlertMessage: (message: string | null) => void;
  // UI / Navigation Actions
  toggleSidebar: () => void;
  setViewMode: (mode: ViewMode) => void;

  // Global Data Loading Actions
  loadInitialAppData: () => Promise<void>;
  refreshModelsConfig: () => Promise<void>;
  refreshAllSessions: () => Promise<void>;

  // DirectChat Specific Actions
  startNewDirectChat: () => void;
  loadDirectChatHistory: (filename: string) => Promise<void>;
  addDirectChatMessage: (role: 'user' | 'assistant', content: string) => void;
  addDirectChatSessionToList: (sessionInfo: SessionInfo) => void;
  updateCurrentDirectChatMessages: (messages: Message[]) => void;

  // PiDev Sessions Specific Actions
  navigateToPiDevSessions: () => Promise<void>;
  loadPiDevSessionDetail: (filename: string) => Promise<void>;
  clearPiDevSessionDetail: () => void;

  // Model Management Actions
  addModel: (model_id: string, model_name: string) => Promise<void>;
  updateModel: (model_id: string, updatedConfig: Partial<ModelConfig>) => Promise<void>;
  deleteModel: (model_id: string) => Promise<void>;
  selectModel: (model_id: string) => Promise<void>;
}

export const useAppStore = create<AppState & AppActions>((set, get) => ({
  // --- Initial State ---
  viewMode: 'direct_chat',
  isSidebarOpen: true,
  configuredModel: 'Loading...',
  modelsList: [],
  piDevSessions: [],
  directChatSessions: [],
  activePiDevSessionDetail: null,
  currentDirectChatMessages: [],
  currentDirectChatSessionId: crypto.randomUUID(),
  alertMessage: null,

  // --- Actions ---
  setAlertMessage: (message) => set({ alertMessage: message }),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setViewMode: (mode) => set({ viewMode: mode }),

  loadInitialAppData: async () => {
    await get().refreshModelsConfig();
    await get().refreshAllSessions();
  },

  refreshModelsConfig: async () => {
    try {
      const res = await axios.get('/api/models');
      set({
        configuredModel: res.data.configured_model,
        modelsList: res.data.models || [],
      });
    } catch (err) {
      console.error(err);
      set({ configuredModel: 'Error loading model' });
    }
  },

  refreshAllSessions: async () => {
    try {
      const res = await axios.get('/api/sessions');
      const all: SessionInfo[] = res.data;
      const piSessions = all.filter(s => s.source === 'pi' || !s.source);
      const customChatSessions = all.filter(s => s.source === 'chat');
      set({
        piDevSessions: piSessions,
        directChatSessions: customChatSessions,
      });
    } catch (e) {
      console.error(e);
    }
  },

  startNewDirectChat: () => set(() => ({
    currentDirectChatMessages: [],
    currentDirectChatSessionId: crypto.randomUUID(),
    viewMode: 'direct_chat',
  })),

  loadDirectChatHistory: async (filename) => {
    try {
      const res = await axios.get(`/api/sessions/${filename}`);
      const data = res.data.session;
      const mapped: Message[] = [];
      let foundSessionId: string | null = null;

      data.forEach((item: any) => {
        if (item.prompt) mapped.push({ role: 'user', content: item.prompt });
        if (item.response) mapped.push({ role: 'assistant', content: item.response });
        if (item.session_id && !foundSessionId) foundSessionId = item.session_id;
      });

      set({ currentDirectChatMessages: mapped });
      if (foundSessionId) set({ currentDirectChatSessionId: foundSessionId });
      set({ viewMode: 'direct_chat' });
    } catch (e) {
      console.error(e);
      get().setAlertMessage('Failed to load direct chat session.');
    }
  },

  addDirectChatMessage: (role, content) => set((state) => ({
    currentDirectChatMessages: [...state.currentDirectChatMessages, { role, content }],
  })),

  addDirectChatSessionToList: (sessionInfo) => set((state) => ({
    directChatSessions: [sessionInfo, ...state.directChatSessions],
  })),

  updateCurrentDirectChatMessages: (messages) => set({ currentDirectChatMessages: messages }),

  navigateToPiDevSessions: async () => {
    set({ viewMode: 'pidev_sessions' });
    await get().refreshAllSessions();
  },

  loadPiDevSessionDetail: async (filename) => {
    try {
      const res = await axios.get(`/api/sessions/${filename}`);
      set({ activePiDevSessionDetail: res.data.session });
      set({ viewMode: 'pidev_session_detail' });
    } catch (e) {
      console.error(e);
      get().setAlertMessage('Failed to load PiDev session detail.');
    }
  },

  clearPiDevSessionDetail: () => set({ viewMode: 'pidev_sessions', activePiDevSessionDetail: null }),

  addModel: async (model_id, model_name) => {
    try {
      await axios.post('/api/models', {
        model_id,
        model_name,
        log_path: 'backend/llm_logs.jsonl',
        custom: {},
      });
      await get().refreshModelsConfig();
    } catch (e) {
      console.error('Failed to add model', e);
      get().setAlertMessage('Failed to add model. Check if it already exists.');
    }
  },

  updateModel: async (model_id, updatedConfig) => {
    try {
      await axios.put(`/api/models/${model_id}`, {
        model_id,
        model_name: updatedConfig.model_name,
        log_path: updatedConfig.log_path,
        custom: updatedConfig.custom,
      });
      await get().refreshModelsConfig();
    } catch (e) {
      console.error('Failed to update model', e);
      get().setAlertMessage('Failed to update model.');
    }
  },

  deleteModel: async (model_id) => {
    try {
      await axios.delete(`/api/models/${model_id}`);
      await get().refreshModelsConfig();
    } catch (e) {
      console.error('Failed to delete model', e);
      get().setAlertMessage('Failed to delete model.');
    }
  },

  selectModel: async (model_id) => {
    try {
      await axios.post(`/api/models/select/${model_id}`);
      await get().refreshModelsConfig();
    } catch (e) {
      console.error('Failed to select model', e);
      get().setAlertMessage('Failed to select model.');
    }
  },
}));
