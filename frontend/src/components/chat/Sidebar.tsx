"use client";

/**
 * 侧边栏组件 — 历史会话列表 + 新建对话按钮
 */
import { useEffect } from "react";
import { Plus, MessageSquare, Trash2, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useChatStore } from "@/lib/store";

export default function Sidebar() {
  const {
    conversations,
    activeConversationId,
    sidebarOpen,
    loadConversations,
    createNewChat,
    selectConversation,
    removeConversation,
  } = useChatStore();

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  if (!sidebarOpen) return null;

  return (
    <div className="w-64 h-full bg-gray-50 dark:bg-gray-900 border-r flex flex-col">
      {/* 标题区域 */}
      <div className="p-4 flex items-center gap-2">
        <Home className="h-5 w-5 text-emerald-500" />
        <h1 className="font-bold text-lg">别墅设计助手</h1>
      </div>

      <Separator />

      {/* 新建对话按钮 */}
      <div className="p-3">
        <Button
          onClick={() => createNewChat()}
          className="w-full bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl"
        >
          <Plus className="h-4 w-4 mr-2" />
          新建设计咨询
        </Button>
      </div>

      {/* 会话列表 */}
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1 pb-4">
          {conversations.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">
              还没有会话记录
            </p>
          )}
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                activeConversationId === conv.id
                  ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                  : "hover:bg-gray-100 dark:hover:bg-gray-800"
              }`}
              onClick={() => selectConversation(conv.id)}
            >
              <MessageSquare className="h-4 w-4 shrink-0" />
              <span className="text-sm truncate flex-1">{conv.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeConversation(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-500"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* 底部信息 */}
      <div className="p-3 border-t">
        <p className="text-xs text-gray-400 text-center">
          AI 别墅设计助手 v0.1
        </p>
      </div>
    </div>
  );
}
