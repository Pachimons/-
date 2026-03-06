/**
 * Zustand 全局状态管理
 * 管理会话列表、当前对话消息、流式状态、结构化需求
 */
import { create } from "zustand";
import {
  createConversation,
  getConversations,
  getConversation,
  deleteConversation,
  sendMessageStream,
  getRequirement,
  getConversationPlans,
} from "./api";

// ==================== 类型定义 ====================

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  image_urls: string[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Requirement {
  land_area?: number | null;
  land_location?: string | null;
  floors?: number | null;
  style?: string | null;
  total_rooms?: number | null;
  bedrooms?: number | null;
  bathrooms?: number | null;
  has_elderly_room?: boolean | null;
  has_garage?: boolean | null;
  has_garden?: boolean | null;
  budget?: number | null;
  special_notes?: string | null;
  completeness: number;
}

interface ChatState {
  // 匿名用户 ID（保存在 localStorage）
  sessionId: string;
  // 会话列表
  conversations: Conversation[];
  // 当前活跃的会话 ID
  activeConversationId: string | null;
  // 当前对话的消息列表
  messages: ChatMessage[];
  // AI 是否正在回复
  isStreaming: boolean;
  // 当前正在流式生成的 AI 回复文本
  streamingText: string;
  // 当前提取的结构化需求
  requirement: Requirement | null;
  // 当前会话的效果图 URL 列表
  generatedImages: string[];
  // 侧边栏是否展开
  sidebarOpen: boolean;
  // 取消流式请求的函数
  cancelStream: (() => void) | null;

  // Actions
  initSession: () => void;
  loadConversations: () => Promise<void>;
  createNewChat: () => Promise<string>;
  selectConversation: (id: string) => Promise<void>;
  removeConversation: (id: string) => Promise<void>;
  sendUserMessage: (content: string, imageUrls?: string[]) => Promise<void>;
  addGeneratedImages: (urls: string[]) => void;
  stopStreaming: () => void;
  toggleSidebar: () => void;
}

// ==================== Store 实现 ====================

export const useChatStore = create<ChatState>((set, get) => ({
  sessionId: "",
  conversations: [],
  activeConversationId: null,
  messages: [],
  isStreaming: false,
  streamingText: "",
  requirement: null,
  generatedImages: [],
  sidebarOpen: true,
  cancelStream: null,

  /** 初始化会话 ID（从 localStorage 读取或新建），并加载历史会话 */
  initSession: () => {
    if (typeof window === "undefined") return;
    let sid = localStorage.getItem("villa_session_id");
    if (!sid) {
      sid = crypto.randomUUID();
      localStorage.setItem("villa_session_id", sid);
    }
    set({ sessionId: sid });
    // 初始化后立即加载历史会话列表
    get().loadConversations();
  },

  /** 加载会话列表 */
  loadConversations: async () => {
    const { sessionId } = get();
    if (!sessionId) return;
    try {
      const convs = await getConversations(sessionId);
      set({ conversations: convs });
    } catch (err) {
      console.error("加载会话列表失败:", err);
    }
  },

  /** 创建新对话 */
  createNewChat: async () => {
    const { sessionId } = get();
    const conv = await createConversation(sessionId);

    // 加载完整会话（含欢迎消息）
    const detail = await getConversation(conv.id);

    set((state) => ({
      conversations: [
        {
          id: conv.id,
          title: conv.title,
          status: conv.status,
          created_at: conv.created_at,
          updated_at: conv.created_at,
          message_count: detail.messages.length,
        },
        ...state.conversations,
      ],
      activeConversationId: conv.id,
      messages: detail.messages.map((m) => ({
        id: m.id,
        role: m.role as ChatMessage["role"],
        content: m.content,
        image_urls: m.image_urls || [],
        created_at: m.created_at,
      })),
      requirement: null,
      streamingText: "",
    }));

    return conv.id;
  },

  /** 选择并加载某个会话 */
  selectConversation: async (id: string) => {
    try {
      const detail = await getConversation(id);
      set({
        activeConversationId: id,
        messages: detail.messages.map((m) => ({
          id: m.id,
          role: m.role as ChatMessage["role"],
          content: m.content,
          image_urls: m.image_urls || [],
          created_at: m.created_at,
        })),
        streamingText: "",
        requirement: null,
      });
      // 并行加载该会话的结构化需求和效果图
      const [reqResult, plansResult] = await Promise.allSettled([
        getRequirement(id),
        getConversationPlans(id),
      ]);
      if (reqResult.status === "fulfilled") {
        set({ requirement: reqResult.value as unknown as Requirement });
      }
      if (plansResult.status === "fulfilled") {
        const allUrls = plansResult.value.flatMap((p) => p.rendering_urls);
        set({ generatedImages: allUrls });
      }
    } catch (err) {
      console.error("加载会话失败:", err);
    }
  },

  /** 删除会话 */
  removeConversation: async (id: string) => {
    try {
      await deleteConversation(id);
      set((state) => {
        const newConvs = state.conversations.filter((c) => c.id !== id);
        const isActive = state.activeConversationId === id;
        return {
          conversations: newConvs,
          activeConversationId: isActive ? null : state.activeConversationId,
          messages: isActive ? [] : state.messages,
        };
      });
    } catch (err) {
      console.error("删除会话失败:", err);
    }
  },

  /** 发送用户消息 */
  sendUserMessage: async (content: string, imageUrls: string[] = []) => {
    const { activeConversationId } = get();
    let convId = activeConversationId;

    // 如果没有活跃会话，先创建一个
    if (!convId) {
      convId = await get().createNewChat();
    }

    // 添加用户消息到列表（乐观更新）
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content,
      image_urls: imageUrls,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
      isStreaming: true,
      streamingText: "",
    }));

    // 发起 SSE 流式请求
    const cancel = sendMessageStream(
      convId!,
      content,
      imageUrls,
      // onText: 收到一小段文字
      (text) => {
        set((state) => ({
          streamingText: state.streamingText + text,
        }));
      },
      // onRequirement: 收到结构化需求更新
      (data) => {
        set({ requirement: data as unknown as Requirement });
      },
      // onDone: 流结束
      () => {
        const { streamingText, messages } = get();
        if (streamingText) {
          // 把流式文本添加为完整的 AI 消息
          const aiMsg: ChatMessage = {
            id: `ai-${Date.now()}`,
            role: "assistant",
            content: streamingText,
            image_urls: [],
            created_at: new Date().toISOString(),
          };
          set({
            messages: [...messages, aiMsg],
            isStreaming: false,
            streamingText: "",
            cancelStream: null,
          });
        } else {
          set({ isStreaming: false, cancelStream: null });
        }

        // 刷新会话列表（标题可能更新了）
        get().loadConversations();
      },
      // onError: 出错了
      (error) => {
        console.error("消息发送失败:", error);
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `抱歉，出现了错误：${error}`,
          image_urls: [],
          created_at: new Date().toISOString(),
        };
        set((state) => ({
          messages: [...state.messages, errorMsg],
          isStreaming: false,
          streamingText: "",
          cancelStream: null,
        }));
      }
    );

    set({ cancelStream: cancel });
  },

  /** 添加生成的效果图（追加到列表） */
  addGeneratedImages: (urls: string[]) => {
    set((state) => ({
      generatedImages: [...state.generatedImages, ...urls],
    }));
  },

  /** 停止流式生成 */
  stopStreaming: () => {
    const { cancelStream } = get();
    if (cancelStream) cancelStream();
    set({ isStreaming: false, cancelStream: null });
  },

  /** 切换侧边栏 */
  toggleSidebar: () => {
    set((state) => ({ sidebarOpen: !state.sidebarOpen }));
  },
}));
