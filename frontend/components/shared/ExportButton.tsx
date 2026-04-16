"use client";
import { Download } from "lucide-react";

interface Props {
  href: string;
  label?: string;
}

export function ExportButton({ href, label = "Export Excel" }: Props) {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return (
    <a
      href={`${base}${href}`}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded hover:bg-gray-50 text-gray-700"
    >
      <Download className="w-4 h-4 text-green-600" />
      {label}
    </a>
  );
}
