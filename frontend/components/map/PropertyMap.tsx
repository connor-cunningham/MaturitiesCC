"use client";
import { useState, useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import Link from "next/link";
import { api, fmt, scoreColor } from "@/lib/api";
import { MapPin } from "@/lib/types";
import "leaflet/dist/leaflet.css";

export default function PropertyMap() {
  const [pins, setPins] = useState<MapPin[]>([]);
  const [filters, setFilters] = useState({ state: "", building_class: "", min_units: "" });
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
    const { data } = await api.get(`/properties/map-pins?${params}`);
    setPins(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, [filters.state, filters.building_class, filters.min_units]);

  const setFilter = (k: string, v: string) => setFilters(f => ({ ...f, [k]: v }));

  const pinColor = (score: number | null | undefined) => {
    if (score == null) return "#9ca3af";
    if (score >= 75) return "#dc2626";
    if (score >= 55) return "#ea580c";
    if (score >= 35) return "#ca8a04";
    return "#16a34a";
  };

  const center: [number, number] = [37.0902, -95.7129];

  return (
    <div className="space-y-3">
      {/* Map filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-3 flex flex-wrap gap-3">
        {[
          ["State", "state", "TX"],
          ["Class", "building_class", "A"],
          ["Min Units", "min_units", "100"],
        ].map(([label, key, ph]) => (
          <div key={key} className="flex items-center gap-1.5">
            <label className="text-xs text-gray-500">{label}</label>
            <input value={(filters as any)[key]} onChange={e => setFilter(key, e.target.value)}
              placeholder={ph}
              className="text-xs border border-gray-200 rounded px-2 py-1 w-20 outline-none focus:border-blue-400" />
          </div>
        ))}
        <div className="flex items-center gap-3 ml-auto text-xs text-gray-500">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-600 inline-block" /> High Priority</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-orange-500 inline-block" /> Medium</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-yellow-500 inline-block" /> Low</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-600 inline-block" /> Minimal</span>
        </div>
        <div className="text-xs text-gray-400">{pins.length} properties shown</div>
      </div>

      <MapContainer
        center={center}
        zoom={5}
        style={{ height: "calc(100vh - 200px)", width: "100%", borderRadius: "0.5rem" }}
        className="border border-gray-200"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {pins.map(pin => (
          <CircleMarker
            key={pin.id}
            center={[pin.lat, pin.lng]}
            radius={pin.units ? Math.max(6, Math.min(18, pin.units / 40)) : 7}
            pathOptions={{
              fillColor: pinColor(pin.priority_score),
              fillOpacity: 0.8,
              color: "white",
              weight: 1.5,
            }}
          >
            <Popup>
              <div className="min-w-[200px]">
                <p className="font-semibold text-gray-900 mb-1">{pin.name}</p>
                <p className="text-xs text-gray-500 mb-2">{pin.city}, {pin.state}</p>
                <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs mb-2">
                  <span className="text-gray-500">Units</span>
                  <span className="font-medium">{fmt.number(pin.units)}</span>
                  <span className="text-gray-500">Class</span>
                  <span className="font-medium">{pin.building_class || "—"}</span>
                  <span className="text-gray-500">Score</span>
                  <span className="font-medium">{pin.priority_score?.toFixed(0) ?? "—"}</span>
                </div>
                <div className="flex gap-2">
                  <Link href={`/properties/${pin.id}`}
                    className="text-xs text-blue-600 hover:underline">Property →</Link>
                  {pin.owner_id && (
                    <Link href={`/owners/${pin.owner_id}`}
                      className="text-xs text-blue-600 hover:underline">Owner →</Link>
                  )}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
