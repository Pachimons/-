"use client";

/**
 * 聊天区域组件 — 消息列表 + 输入栏（中间栏）
 */
import { useEffect, useRef } from "react";
import { Bot } from "lucide-react";
import { useChatStore } from "@/lib/store";
import MessageBubble from "./MessageBubble";
import StreamingBubble from "./StreamingBubble";
import InputBar from "./InputBar";

export default function ChatArea() {
  const { messages, isStreaming, streamingText, activeConversationId } =
    useChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  // 没有选中会话时显示欢迎页
  if (!activeConversationId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-white dark:bg-gray-950 p-8">
        <div className="max-w-md text-center space-y-6">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center">
            <Bot className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold">AI 别墅设计助手</h2>
          <p className="text-gray-500">
            告诉我您的土地信息和建房需求，我将帮您设计梦想中的别墅。
            支持文字描述、上传参考图片，AI 智能分析并生成效果图。
          </p>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3 text-left">
              <p className="font-medium mb-1">💬 智能对话</p>
              <p className="text-gray-400">通过对话收集您的建房需求</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3 text-left">
              <p className="font-medium mb-1">📐 结构化需求</p>
              <p className="text-gray-400">自动提取面积、楼层、风格等参数</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3 text-left">
              <p className="font-medium mb-1">🖼️ 效果图生成</p>
              <p className="text-gray-400">AI 生成别墅效果图</p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3 text-left">
              <p className="font-medium mb-1">📋 建筑规范</p>
              <p className="text-gray-400">自动检索相关建筑规范</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-gray-950">
      {/* 消息滚动区域 */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* 流式回复中 */}
          {isStreaming && streamingText && (
            <StreamingBubble text={streamingText} />
          )}

          {/* 正在思考提示 */}
          {isStreaming && !streamingText && (
            <div className="flex gap-3 mb-6">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}

          {/* 底部锚点，用于自动滚动 */}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* 输入栏（固定在底部） */}
      <InputBar />
    </div>
  );
}
