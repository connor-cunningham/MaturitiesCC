"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, X } from "lucide-react";
import { api } from "@/lib/api";

export function TopBar() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [results, setResults] = useState<any>(null);
  const [open, setOpen] = useState(false);

  const handleSearch = async (value: string) => {
    setQ(value);
    if (value.length < 2) { setResults(null); setOpen(false); return; }
    try {
      const { data } = await api.get(`/search?q=${encodeURIComponent(value)}`);
      setResults(data);
      setOpen(true);
    } catch { /* ignore */ }
  };

  const navigate = (type: string, id: string) => {
    setOpen(false);
    setQ("");
    const map: Record<string, string> = { loan: "/loans", property: "/properties", owner: "/owners" };
    router.push(`${map[type]}/${id}`);
  };

  const total = results
    ? (results.loans?.length || 0) + (results.properties?.length || 0) + (results.owners?.length || 0)
    : 0;

  return (
    <header className="h-12 bg-white border-b border-gray-200 flex items-center px-6 gap-4 flex-shrink-0">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={q}
          onChange={e => handleSearch(e.target.value)}
          placeholder="Search loans, properties, owners…"
          className="w-full pl-9 pr-8 py-1.5 text-sm bg-gray-50 border border-gray-200 rounded-md outline-none focus:border-blue-400 focus:bg-white"
        />
        {q && (
          <button onClick={() => { setQ(""); setResults(null); setOpen(false); }}
            className="absolute right-2 top-1/2 -translate-y-1/2">
            <X className="w-3.5 h-3.5 text-gray-400" />
          </button>
        )}

        {open && total > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
            {results.loans?.length > 0 && (
              <div>
                <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 bg-gray-50 border-b">Loans</div>
                {results.loans.map((r: any) => (
                  <button key={r.id} onClick={() => navigate("loan", r.id)}
                    className="w-full text-left px-3 py-2 hover:bg-blue-50 text-sm flex justify-between">
                    <span className="truncate">{r.label}</span>
                    {r.maturity_date && <span className="text-gray-400 text-xs ml-2">{r.maturity_date}</span>}
                  </button>
                ))}
              </div>
            )}
            {results.properties?.length > 0 && (
              <div>
                <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 bg-gray-50 border-b">Properties</div>
                {results.properties.map((r: any) => (
                  <button key={r.id} onClick={() => navigate("property", r.id)}
                    className="w-full text-left px-3 py-2 hover:bg-blue-50 text-sm flex justify-between">
                    <span className="truncate">{r.label}</span>
                    <span className="text-gray-400 text-xs ml-2">{r.city}, {r.state}</span>
                  </button>
                ))}
              </div>
            )}
            {results.owners?.length > 0 && (
              <div>
                <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 bg-gray-50 border-b">Owners</div>
                {results.owners.map((r: any) => (
                  <button key={r.id} onClick={() => navigate("owner", r.id)}
                    className="w-full text-left px-3 py-2 hover:bg-blue-50 text-sm">{r.label}</button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="ml-auto flex items-center gap-2 text-xs text-gray-400">
        <span className="w-2 h-2 rounded-full bg-green-400 inline-block" />
        Connected
      </div>
    </header>
  );
}
