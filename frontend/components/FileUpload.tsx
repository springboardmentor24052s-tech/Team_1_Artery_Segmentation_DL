import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, X } from 'lucide-react';

interface FileUploadProps {
  onFileSelected?: (file: File | null) => void;
  acceptedFormats?: string;
  maxSizeMB?: number;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelected,
  acceptedFormats = '.dcm, .nii, .nii.gz, .raw, .zip',
  maxSizeMB = 500
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      if (onFileSelected) onFileSelected(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (onFileSelected) onFileSelected(file);
    }
  };

  const handleRemove = () => {
    setSelectedFile(null);
    if (onFileSelected) onFileSelected(null);
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? 'border-[#A91121] bg-[#A91121]/5'
            : selectedFile
            ? 'border-emerald-300 bg-emerald-50/30'
            : 'border-[#A91121]/30 hover:border-[#A91121] bg-[#F5F5F5]/60'
        }`}
      >
        <input
          type="file"
          onChange={handleFileChange}
          accept={acceptedFormats}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        {selectedFile ? (
          <div className="flex flex-col items-center space-y-2 pointer-events-none">
            <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <p className="text-sm font-semibold text-[#252525]">{selectedFile.name}</p>
            <p className="text-xs font-mono text-slate-500">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Ready for processing
            </p>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleRemove();
              }}
              className="pointer-events-auto mt-2 inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-[#A91121] bg-[#A91121]/10 hover:bg-[#A91121]/20 rounded-md transition-colors"
            >
              <X className="w-3.5 h-3.5" /> Remove file
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-3 pointer-events-none">
            <div className="w-12 h-12 bg-[#A91121]/10 text-[#A91121] rounded-full flex items-center justify-center">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-[#252525]">
                Drag and drop medical scan here, or <span className="text-[#A91121] underline font-semibold">browse</span>
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Supports DICOM (.dcm), NIfTI (.nii, .nii.gz), RAW, or ZIP archives (Max {maxSizeMB}MB)
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
