"use client";

import React from "react";
import { Sliders, Eye, Sparkles } from "lucide-react";

interface XAIControlsProps {
  heatmapOpacity: number;
  setHeatmapOpacity: (val: number) => void;
  selectedHead: "severity" | "binary";
  setSelectedHead: (head: "severity" | "binary") => void;
}

export const XAIControls: React.FC<XAIControlsProps> = ({
  heatmapOpacity,
  setHeatmapOpacity,
  selectedHead,
  setSelectedHead,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-4 bg-slate-900/60 p-3 rounded-lg border border-[#A91121]/20">
      {/* Opacity Slider */}
      <div className="flex items-center gap-2">
        <Sliders className="w-4 h-4 text-red-400" />
        <span className="text-xs font-semibold text-slate-300">Heatmap Opacity:</span>
        <input
          type="range"
          min="10"
          max="100"
          value={heatmapOpacity}
          onChange={(e) => setHeatmapOpacity(Number(e.target.value))}
          className="w-24 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-[#A91121]"
        />
        <span className="text-xs font-mono text-slate-400 w-8">{heatmapOpacity}%</span>
      </div>

      <div className="h-4 w-px bg-slate-700 hidden sm:block" />

      {/* Attribution Head Switcher */}
      <div className="flex items-center gap-2">
        <Eye className="w-4 h-4 text-red-400" />
        <span className="text-xs font-semibold text-slate-300">Attribution Head:</span>
        <div className="inline-flex rounded-md shadow-xs" role="group">
          <button
            type="button"
            onClick={() => setSelectedHead("severity")}
            className={`px-2.5 py-1 text-xs font-medium rounded-l-md border transition-colors ${
              selectedHead === "severity"
                ? "bg-[#A91121] text-white border-[#A91121]"
                : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
            }`}
          >
            Severity (ACC/AHA)
          </button>
          <button
            type="button"
            onClick={() => setSelectedHead("binary")}
            className={`px-2.5 py-1 text-xs font-medium rounded-r-md border transition-colors ${
              selectedHead === "binary"
                ? "bg-[#A91121] text-white border-[#A91121]"
                : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
            }`}
          >
            Binary Presence
          </button>
        </div>
      </div>

      <div className="ml-auto flex items-center gap-1.5 text-xs text-amber-400/90 font-mono">
        <Sparkles className="w-3.5 h-3.5" />
        <span>Grad-CAM Target: layer4.conv2</span>
      </div>
    </div>
  );
};

