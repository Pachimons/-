"use client";

/**
 * 输入栏组件 — 文字输入 + 图片上传 + 发送按钮
 */
import { useState, useRef, KeyboardEvent } from "react";
import { Send, ImagePlus, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChatStore } from "@/lib/store";
import { uploadImage } from "@/lib/api";

export default function InputBar() {
  const [text, setText] = useState("");
  const [images, setImages] = useState<Array<{ url: string; file: File }>>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { isStreaming, sendUserMessage, stopStreaming } = useChatStore();

  /** 发送消息 */
  const handleSend = async () => {
    const trimmed = text.trim();
    if (!trimmed && images.length === 0) return;
    if (isStreaming) return;

    const imageUrls = images.map((img) => img.url);
    setText("");
    setImages([]);

    await sendUserMessage(trimmed, imageUrls);
  };

  /** 键盘快捷键：Enter 发送，Shift+Enter 换行 */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  /** 处理图片上传 */
  const handleImageUpload = async (files: FileList | null) => {
    if (!files) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        if (!file.type.startsWith("image/")) continue;
        const result = await uploadImage(file);
        setImages((prev) => [...prev, { url: result.url, file }]);
      }
    } catch (err) {
      console.error("图片上传失败:", err);
    } finally {
      setUploading(false);
    }
  };

  /** 移除已选择的图片 */
  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t bg-white dark:bg-gray-950 p-4">
      {/* 已选择的图片预览 */}
      {images.length > 0 && (
        <div className="flex gap-2 mb-3 flex-wrap">
          {images.map((img, i) => (
            <div key={i} className="relative group">
              <img
                src={URL.createObjectURL(img.file)}
                alt="预览"
                className="h-16 w-16 rounded-lg object-cover border"
              />
              <button
                onClick={() => removeImage(i)}
                className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 输入区域 */}
      <div className="flex items-end gap-2">
        {/* 图片上传按钮 */}
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 text-gray-500 hover:text-emerald-500"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <ImagePlus className="h-5 w-5" />
          )}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e) => handleImageUpload(e.target.files)}
        />

        {/* 文本输入框 */}
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="描述您的建房需求..."
          className="min-h-[44px] max-h-[120px] resize-none rounded-xl border-gray-200"
          rows={1}
        />

        {/* 发送/停止按钮 */}
        {isStreaming ? (
          <Button
            onClick={stopStreaming}
            variant="destructive"
            size="icon"
            className="shrink-0 rounded-xl"
          >
            <X className="h-5 w-5" />
          </Button>
        ) : (
          <Button
            onClick={handleSend}
            disabled={!text.trim() && images.length === 0}
            size="icon"
            className="shrink-0 rounded-xl bg-emerald-500 hover:bg-emerald-600"
          >
            <Send className="h-5 w-5" />
          </Button>
        )}
      </div>

      <p className="text-xs text-gray-400 mt-2 text-center">
        按 Enter 发送，Shift + Enter 换行
      </p>
    </div>
  );
}
