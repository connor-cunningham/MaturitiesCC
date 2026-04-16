"use client";
import dynamic from "next/dynamic";

// Leaflet must be dynamically imported (no SSR) because it needs window
const PropertyMap = dynamic(() => import("@/components/map/PropertyMap"), {
  ssr: false,
  loading: () => (
    <div className="h-[calc(100vh-120px)] bg-gray-100 flex items-center justify-center text-gray-400 rounded-lg">
      Loading map…
    </div>
  ),
});

export default function MapPage() {
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-bold text-gray-900">Property Map</h1>
      <PropertyMap />
    </div>
  );
}
