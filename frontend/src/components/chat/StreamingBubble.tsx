"use client";

/**
 * 流式消息气泡 — AI 正在回复时的实时展示
 */
import ReactMarkdown from "react-markdown";
import { Bot } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface Props {
  text: string;
}

export default function StreamingBubble({ text }: Props) {
  return (
    <div className="flex gap-3 mb-6">
      {/* AI 头像 */}
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className="bg-gradient-to-br from-emerald-400 to-teal-500 text-white">
          <Bot className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>

      {/* 流式内容 */}
      <div className="max-w-[80%] rounded-2xl rounded-tl-sm bg-gray-100 dark:bg-gray-800 px-4 py-3">
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown>{text}</ReactMarkdown>
          {/* 打字光标 */}
          <span className="inline-block w-2 h-4 bg-emerald-500 animate-pulse ml-0.5" />
        </div>
      </div>
    </div>
  );
}
