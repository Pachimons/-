"use client";

/**
 * 需求面板组件 — 展示 AI 提取的结构化建房需求
 */
import { useState } from "react";
import {
  ChevronRight,
  ChevronLeft,
  MapPin,
  Layers,
  Palette,
  BedDouble,
  Bath,
  Car,
  Trees,
  Accessibility,
  DollarSign,
  ImagePlus,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useChatStore } from "@/lib/store";
import { generateImage } from "@/lib/api";

export default function RequirementPanel() {
  const { requirement, activeConversationId, generatedImages, addGeneratedImages } = useChatStore();
  const [collapsed, setCollapsed] = useState(false);
  const [generatingImage, setGeneratingImage] = useState(false);

  if (!activeConversationId) return null;

  // 计算已收集的参数数量
  const fields = requirement
    ? [
        requirement.land_area,
        requirement.land_location,
        requirement.floors,
        requirement.style,
        requirement.bedrooms,
        requirement.bathrooms,
      ].filter((v) => v != null).length
    : 0;

  const completeness = requirement?.completeness ?? 0;

  /** 生成效果图 */
  const handleGenerateImage = async () => {
    if (!activeConversationId) return;
    setGeneratingImage(true);
    try {
      const result = await generateImage(activeConversationId);
      addGeneratedImages(result.rendering_urls);
    } catch (err) {
      console.error("生成效果图失败:", err);
    } finally {
      setGeneratingImage(false);
    }
  };

  if (collapsed) {
    return (
      <div className="border-l flex items-start pt-4">
        <button
          onClick={() => setCollapsed(false)}
          className="p-2 text-gray-400 hover:text-emerald-500 transition-colors"
          title="展开需求面板"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="w-80 shrink-0 h-screen border-l bg-gray-50 dark:bg-gray-900 overflow-y-auto">
      {/* 面板头部 */}
      <div className="p-4 flex items-center justify-between border-b">
        <h3 className="font-semibold text-sm">设计需求</h3>
        <button
          onClick={() => setCollapsed(true)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* 完整度进度条 */}
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>需求收集进度</span>
            <span>{Math.round(completeness * 100)}%</span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full transition-all duration-500"
              style={{ width: `${completeness * 100}%` }}
            />
          </div>
        </div>

        {/* 需求参数卡片 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">已收集参数 ({fields}/6)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ParamRow
              icon={<MapPin className="h-4 w-4" />}
              label="土地面积"
              value={
                requirement?.land_area
                  ? `${requirement.land_area} ㎡`
                  : undefined
              }
            />
            <ParamRow
              icon={<MapPin className="h-4 w-4" />}
              label="所在位置"
              value={requirement?.land_location ?? undefined}
            />
            <ParamRow
              icon={<Layers className="h-4 w-4" />}
              label="楼层数"
              value={
                requirement?.floors
                  ? `${requirement.floors} 层`
                  : undefined
              }
            />
            <ParamRow
              icon={<Palette className="h-4 w-4" />}
              label="建筑风格"
              value={requirement?.style ?? undefined}
            />
            <ParamRow
              icon={<BedDouble className="h-4 w-4" />}
              label="卧室数"
              value={
                requirement?.bedrooms
                  ? `${requirement.bedrooms} 间`
                  : undefined
              }
            />
            <ParamRow
              icon={<Bath className="h-4 w-4" />}
              label="卫生间"
              value={
                requirement?.bathrooms
                  ? `${requirement.bathrooms} 个`
                  : undefined
              }
            />
            <ParamRow
              icon={<Accessibility className="h-4 w-4" />}
              label="老人房"
              value={
                requirement?.has_elderly_room != null
                  ? requirement.has_elderly_room
                    ? "需要"
                    : "不需要"
                  : undefined
              }
            />
            <ParamRow
              icon={<Car className="h-4 w-4" />}
              label="车库"
              value={
                requirement?.has_garage != null
                  ? requirement.has_garage
                    ? "需要"
                    : "不需要"
                  : undefined
              }
            />
            <ParamRow
              icon={<Trees className="h-4 w-4" />}
              label="花园"
              value={
                requirement?.has_garden != null
                  ? requirement.has_garden
                    ? "需要"
                    : "不需要"
                  : undefined
              }
            />
            <ParamRow
              icon={<DollarSign className="h-4 w-4" />}
              label="预算"
              value={
                requirement?.budget
                  ? `${(requirement.budget / 10000).toFixed(0)} 万元`
                  : undefined
              }
            />
          </CardContent>
        </Card>

        {/* 生成效果图按钮 */}
        {completeness >= 0.4 && (
          <Button
            className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-xl"
            onClick={handleGenerateImage}
            disabled={generatingImage}
          >
            {generatingImage ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                正在生成效果图...
              </>
            ) : (
              <>
                <ImagePlus className="h-4 w-4 mr-2" />
                生成效果图
              </>
            )}
          </Button>
        )}

        {/* 生成的效果图展示 */}
        {generatedImages.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">效果图</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {generatedImages.map((url, i) => (
                  <a key={i} href={url} target="_blank" rel="noopener noreferrer">
                    <img
                      src={url}
                      alt={`效果图 ${i + 1}`}
                      className="w-full rounded-lg border hover:opacity-90 transition-opacity cursor-pointer"
                    />
                  </a>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

/** 单行参数展示 */
function ParamRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value?: string;
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-400">{icon}</span>
      <span className="text-gray-500 w-16 shrink-0">{label}</span>
      {value ? (
        <span className="font-medium text-emerald-600 dark:text-emerald-400">
          {value}
        </span>
      ) : (
        <span className="text-gray-300 dark:text-gray-600">待收集</span>
      )}
    </div>
  );
}
