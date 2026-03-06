"use client";

/**
 * 消息气泡组件 — 展示单条用户或 AI 消息
 */
import ReactMarkdown from "react-markdown";
import { Bot, User } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { ChatMessage } from "@/lib/store";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""} mb-6`}>
      {/* 头像 */}
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback
          className={
            isUser
              ? "bg-blue-500 text-white"
              : "bg-gradient-to-br from-emerald-400 to-teal-500 text-white"
          }
        >
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* 消息内容 */}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-500 text-white rounded-tr-sm"
            : "bg-gray-100 dark:bg-gray-800 rounded-tl-sm"
        }`}
      >
        {/* 图片展示 */}
        {message.image_urls && message.image_urls.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {message.image_urls.map((url, i) => (
              <img
                key={i}
                src={url}
                alt={`上传的图片 ${i + 1}`}
                className="max-w-[200px] max-h-[200px] rounded-lg object-cover"
              />
            ))}
          </div>
        )}

        {/* 文本内容（Markdown 渲染） */}
        <div
          className={`prose prose-sm max-w-none ${
            isUser
              ? "prose-invert"
              : "dark:prose-invert"
          }`}
        >
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
