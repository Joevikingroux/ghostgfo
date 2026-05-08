import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface UploadDropzoneProps {
  label: string;
  description: string;
  file: File | null;
  required?: boolean;
  onFile: (file: File) => void;
}

const ACCEPTED = {
  "text/csv": [".csv"],
  "application/vnd.ms-excel": [".xls"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "text/plain": [".txt"],
};

export default function UploadDropzone({
  label,
  description,
  file,
  required,
  onFile,
}: UploadDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) onFile(accepted[0]);
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
    multiple: false,
  });

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1.5">
        <span className="text-xs font-medium text-zinc-300">{label}</span>
        {required && <span className="text-brand-teal text-xs">*</span>}
      </div>
      <p className="text-xs text-zinc-500 mb-2">{description}</p>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg px-4 py-5 text-center cursor-pointer transition-colors ${
          isDragActive
            ? "border-brand-teal bg-brand-teal/5"
            : file
            ? "border-emerald-700 bg-emerald-950/30"
            : "border-surface-border hover:border-zinc-600"
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <span className="text-sm text-emerald-400">✓ {file.name}</span>
        ) : isDragActive ? (
          <span className="text-sm text-brand-teal">Drop file here…</span>
        ) : (
          <span className="text-sm text-zinc-500">
            Drag & drop or <span className="text-brand-teal underline">browse</span>
          </span>
        )}
      </div>
    </div>
  );
}
