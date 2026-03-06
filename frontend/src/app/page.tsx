"use client";

import { useEffect } from "react";
import { useChatStore } from "@/lib/store";
import Sidebar from "@/components/chat/Sidebar";
import ChatArea from "@/components/chat/ChatArea";
import RequirementPanel from "@/components/chat/RequirementPanel";

export default function Home() {
  const { initSession } = useChatStore();

  // 应用启动时初始化匿名会话 ID
  useEffect(() => {
    initSession();
  }, [initSession]);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* 左栏：历史会话列表 */}
      <Sidebar />
      {/* 中栏：对话区域（自适应宽度，内部可滚动） */}
      <ChatArea />
      {/* 右栏：需求进度面板（固定宽度，不随聊天滚动） */}
      <RequirementPanel />
    </div>
  );
}
