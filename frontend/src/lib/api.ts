/**
 * 后端 API 请求封装
 * 所有与后端的通信都通过这个文件
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

/** 通用请求函数 */
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "请求失败");
  }

  return res.json();
}

// ==================== 会话相关 ====================

/** 创建新会话 */
export async function createConversation(sessionId: string) {
  return request<{
    id: string;
    title: string;
    status: string;
    created_at: string;
    message_count: number;
  }>("/api/conversations", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

/** 获取会话列表 */
export async function getConversations(sessionId: string) {
  return request<
    Array<{
      id: string;
      title: string;
      status: string;
      created_at: string;
      updated_at: string;
      message_count: number;
    }>
  >(`/api/conversations?session_id=${sessionId}`);
}

/** 获取会话详情（含消息） */
export async function getConversation(conversationId: string) {
  return request<{
    id: string;
    title: string;
    status: string;
    messages: Array<{
      id: string;
      role: string;
      content: string;
      image_urls: string[];
      created_at: string;
    }>;
  }>(`/api/conversations/${conversationId}`);
}

/** 删除会话 */
export async function deleteConversation(conversationId: string) {
  return request(`/api/conversations/${conversationId}`, { method: "DELETE" });
}

/** 发送消息（SSE 流式） */
export function sendMessageStream(
  conversationId: string,
  content: string,
  imageUrls: string[] = [],
  onText: (text: string) => void,
  onRequirement: (data: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (error: string) => void
) {
  const url = `${API_BASE}/api/conversations/${conversationId}/messages?stream=true`;

  const controller = new AbortController();

  let finished = false;

  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, image_urls: imageUrls }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error("请求失败");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("无法读取响应流");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "text") {
                onText(data.content);
              } else if (data.type === "requirement") {
                onRequirement(data.data);
              } else if (data.type === "done") {
                if (!finished) {
                  finished = true;
                  onDone();
                  // 主动关闭连接，避免 Safari "Load failed" 误报
                  controller.abort();
                  return;
                }
              } else if (data.error) {
                onError(data.error);
              }
            } catch {
              // 忽略解析错误
            }
          }
        }
      }

      if (!finished) {
        finished = true;
        onDone();
      }
    })
    .catch((err) => {
      // 忽略主动中止和流已完成后的网络错误（Safari "Load failed"）
      if (err.name !== "AbortError" && !finished) {
        onError(err.message);
      }
    });

  // 返回取消函数
  return () => controller.abort();
}

/** 发送消息（非流式） */
export async function sendMessage(
  conversationId: string,
  content: string,
  imageUrls: string[] = []
) {
  return request<{
    message: {
      id: string;
      role: string;
      content: string;
      image_urls: string[];
      created_at: string;
    };
    requirement: Record<string, unknown> | null;
  }>(`/api/conversations/${conversationId}/messages?stream=false`, {
    method: "POST",
    body: JSON.stringify({ content, image_urls: imageUrls }),
  });
}

// ==================== 需求相关 ====================

/** 获取结构化需求 */
export async function getRequirement(conversationId: string) {
  return request<Record<string, unknown>>(
    `/api/conversations/${conversationId}/requirement`
  );
}

// ==================== 图像生成相关 ====================

/** 获取会话的所有效果图 */
export async function getConversationPlans(conversationId: string) {
  return request<
    Array<{
      id: string;
      rendering_urls: string[];
      description: string;
      status: string;
      created_at: string;
    }>
  >(`/api/conversations/${conversationId}/plans`);
}

/** 生成效果图 */
export async function generateImage(
  conversationId: string,
  prompt?: string,
  imageSize: string = "1K"
) {
  return request<{
    id: string;
    rendering_urls: string[];
    description: string;
    status: string;
  }>(`/api/conversations/${conversationId}/generate-image`, {
    method: "POST",
    body: JSON.stringify({ prompt, image_size: imageSize }),
  });
}

// ==================== 文件上传 ====================

/** 上传图片 */
export async function uploadImage(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_BASE}/api/upload/image`;
  const res = await fetch(url, { method: "POST", body: formData });

  if (!res.ok) {
    throw new Error("上传失败");
  }

  const data = await res.json();
  // 返回完整 URL
  return {
    url: `${API_BASE}${data.url}`,
    filename: data.filename as string,
  };
}

// ==================== 健康检查 ====================

/** 健康检查 */
export async function healthCheck() {
  return request<{
    status: string;
    ai_available: boolean;
    image_available: boolean;
  }>("/api/health");
}
