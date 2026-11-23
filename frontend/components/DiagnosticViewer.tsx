"use client";

import React, { useState } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Maximize2, Download } from "lucide-react";

interface DiagnosticViewerProps {
  quadViewUrl?: string;
  caliperViewUrl?: string;
  caseId: string;
}

export const DiagnosticViewer: React.FC<DiagnosticViewerProps> = ({
  quadViewUrl,
  caliperViewUrl,
  caseId,
}) => {
  const [activeTab, setActiveTab] = useState<"quad" | "caliper">("caliper");
  const [zoomLevel, setZoomLevel] = useState<number>(100);

  const activeUrl = activeTab === "quad" ? quadViewUrl : caliperViewUrl;

  return (
    <div className="bg-slate-900 border border-[#A91121]/20 rounded-xl overflow-hidden shadow-xl">
      {/* View Toggle Bar */}
      <div className="flex flex-wrap items-center justify-between p-3 border-b border-slate-800 bg-slate-950/70">
        <div className="inline-flex rounded-lg p-0.5 bg-slate-800 border border-slate-700">
          <button
            onClick={() => setActiveTab("quad")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === "quad"
                ? "bg-[#A91121] text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Clinical Diagnostic Quad-View
          </button>
          <button
            onClick={() => setActiveTab("caliper")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === "caliper"
                ? "bg-[#A91121] text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Quantitative QCA Caliper View
          </button>
        </div>

        {/* Zoom & Action Controls */}
        <div className="flex items-center gap-1.5 text-slate-300">
          <button
            onClick={() => setZoomLevel((z) => Math.max(50, z - 15))}
            className="p-1.5 hover:bg-slate-800 rounded-md transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono w-10 text-center">{zoomLevel}%</span>
          <button
            onClick={() => setZoomLevel((z) => Math.min(200, z + 15))}
            className="p-1.5 hover:bg-slate-800 rounded-md transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoomLevel(100)}
            className="p-1.5 hover:bg-slate-800 rounded-md transition-colors"
            title="Reset Zoom"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Image Canvas */}
      <div className="p-4 bg-black flex items-center justify-center overflow-auto min-h-[420px]">
        {activeUrl ? (
          <img
            src={activeUrl}
            alt={`Diagnostic Visualizer - ${activeTab}`}
            style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: "center" }}
            className="max-h-[500px] w-auto object-contain transition-transform duration-150"
          />
        ) : (
          <div className="text-center text-slate-500 py-16">
            <p className="text-sm">No diagnostic view generated for this case.</p>
          </div>
        )}
      </div>
    </div>
  );
};

