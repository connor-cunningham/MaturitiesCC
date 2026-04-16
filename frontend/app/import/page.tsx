"use client";
import { useState, useCallback } from "react";
import useSWR, { mutate } from "swr";
import { useDropzone } from "react-dropzone";
import { api, fmt } from "@/lib/api";
import { Upload, FileSpreadsheet, Check, AlertCircle } from "lucide-react";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function ImportPage() {
  const [step, setStep] = useState<"upload" | "preview" | "mapping" | "complete">("upload");
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [selectedSheet, setSelectedSheet] = useState("");
  const [sourceType, setSourceType] = useState("internal");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [error, setError] = useState("");

  const { data: imports } = useSWR("/uploads/imports", fetcher);

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setError("");
    const fd = new FormData();
    fd.append("file", file);
    fd.append("source_type", sourceType);
    try {
      const { data } = await api.post("/uploads", fd);
      setUploadResult(data);
      setSelectedSheet(data.default_sheet || data.sheets?.[0] || "");
      setStep("preview");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Upload failed");
    }
  }, [sourceType]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { "application/vnd.ms-excel": [".xls"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"], "text/csv": [".csv"] },
    multiple: false,
  });

  const runImport = async () => {
    setImporting(true);
    setError("");
    const fd = new FormData();
    fd.append("source_file_id", uploadResult.source_file_id);
    fd.append("sheet_name", selectedSheet);
    if (Object.keys(mapping).length > 0) {
      fd.append("mapping_config", JSON.stringify(mapping));
    }
    try {
      const { data } = await api.post("/uploads/import", fd);
      setImportResult(data);
      setStep("complete");
      mutate("/uploads/imports");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Import failed");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="max-w-4xl space-y-5">
      <h1 className="text-xl font-bold text-gray-900">Import Center</h1>

      {/* Step 1: Upload */}
      {step === "upload" && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-3">Upload File</h2>
            <div className="mb-3 flex gap-3">
              <label className="text-xs text-gray-600">Source Type</label>
              {["costar", "msci", "internal", "other"].map(s => (
                <button key={s} onClick={() => setSourceType(s)}
                  className={`text-xs px-2 py-1 rounded border ${sourceType === s ? "bg-blue-600 text-white border-blue-600" : "border-gray-200 text-gray-600"}`}>
                  {s}
                </button>
              ))}
            </div>
            <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${isDragActive ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-gray-400"}`}>
              <input {...getInputProps()} />
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600 font-medium">Drop your Excel or CSV file here</p>
              <p className="text-xs text-gray-400 mt-1">Supports .xlsx, .xls, .csv</p>
            </div>
            {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
          </div>
        </div>
      )}

      {/* Step 2: Preview + mapping */}
      {(step === "preview" || step === "mapping") && uploadResult && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">File Preview</h2>
            <button onClick={() => setStep("upload")} className="text-xs text-gray-400 hover:text-gray-700">Start over</button>
          </div>
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="w-5 h-5 text-green-600" />
            <span className="text-sm text-gray-700 font-medium">{uploadResult.filename}</span>
            <span className="text-xs text-gray-400">{(uploadResult.file_size / 1024).toFixed(1)} KB</span>
          </div>

          {uploadResult.sheets?.length > 1 && (
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500">Sheet:</label>
              <select value={selectedSheet} onChange={e => setSelectedSheet(e.target.value)}
                className="text-xs border border-gray-200 rounded px-2 py-1">
                {uploadResult.sheets.map((s: string) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          )}

          {/* Detected columns */}
          <div>
            <p className="text-xs text-gray-500 mb-2">Detected columns ({uploadResult.columns?.length}):</p>
            <div className="flex flex-wrap gap-1.5">
              {uploadResult.columns?.map((col: string) => (
                <span key={col} className="text-xs bg-gray-100 rounded px-2 py-0.5 text-gray-700">{col}</span>
              ))}
            </div>
          </div>

          {/* Sample rows */}
          {uploadResult.sample_rows?.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2">Sample rows:</p>
              <div className="overflow-x-auto border border-gray-200 rounded">
                <table className="text-xs w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      {uploadResult.columns?.map((c: string) => (
                        <th key={c} className="px-2 py-1.5 text-left text-gray-600 font-medium whitespace-nowrap">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {uploadResult.sample_rows.map((row: any, i: number) => (
                      <tr key={i}>
                        {uploadResult.columns?.map((c: string) => (
                          <td key={c} className="px-2 py-1 text-gray-700 whitespace-nowrap max-w-[150px] truncate">
                            {row[c] != null ? String(row[c]) : ""}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="pt-2 flex items-center gap-3">
            <button onClick={runImport} disabled={importing}
              className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
              {importing ? "Importing…" : "Run Import"}
            </button>
            <p className="text-xs text-gray-500">
              Auto-detects columns for {uploadResult.source_type} format. Override via column mapping if needed.
            </p>
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
        </div>
      )}

      {/* Step 3: Complete */}
      {step === "complete" && importResult && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <div className="flex items-center gap-2 text-green-700">
            <Check className="w-5 h-5" />
            <h2 className="font-semibold">Import Complete</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              ["Rows Processed", importResult.stats?.inserted + importResult.stats?.merged + importResult.stats?.skipped + importResult.stats?.queued],
              ["New Records", importResult.stats?.inserted],
              ["Merged", importResult.stats?.merged],
              ["Queued for Review", importResult.stats?.queued],
            ].map(([label, val]) => (
              <div key={label as string} className="bg-gray-50 rounded p-3">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-xl font-bold text-gray-900">{val}</p>
              </div>
            ))}
          </div>
          {importResult.stats?.errors?.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <p className="text-xs font-medium text-red-700 mb-1">{importResult.stats.errors.length} errors:</p>
              {importResult.stats.errors.slice(0, 5).map((e: any, i: number) => (
                <p key={i} className="text-xs text-red-600">Row {e.row}: {e.error}</p>
              ))}
            </div>
          )}
          <button onClick={() => { setStep("upload"); setUploadResult(null); setImportResult(null); }}
            className="text-sm text-blue-600 hover:underline">
            Import another file
          </button>
        </div>
      )}

      {/* Import history */}
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-800 mb-3">Import History</h2>
        {!imports || imports.length === 0 ? (
          <p className="text-gray-400 text-sm">No imports yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-500 border-b border-gray-100">
              <tr>
                {["Date", "Status", "Processed", "New", "Merged", "Errors"].map(h => (
                  <th key={h} className="text-left px-2 py-2 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {imports.map((run: any) => (
                <tr key={run.id}>
                  <td className="px-2 py-2 text-gray-600">{fmt.date(run.created_at)}</td>
                  <td className="px-2 py-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${run.status === "complete" ? "bg-green-100 text-green-700" : run.status === "failed" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-center">{run.rows_processed}</td>
                  <td className="px-2 py-2 text-center">{run.rows_inserted}</td>
                  <td className="px-2 py-2 text-center">{run.rows_merged}</td>
                  <td className="px-2 py-2 text-center">
                    {run.errors?.length > 0 ? (
                      <span className="text-red-500">{run.errors.length}</span>
                    ) : "0"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
