import type { AttractionInfo } from "../../types";

export default function AttractionList({ attractions }: { attractions: AttractionInfo[] }) {
  return (
    <div data-testid="rendered-AttractionList">
      <div className="flex items-center gap-1.5 mb-2">
        <svg className="w-3.5 h-3.5 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span className="text-xs text-gray-500 font-semibold uppercase tracking-wide">推荐景点</span>
      </div>
      <div className="space-y-2">
        {attractions.map((attr, idx) => (
          <div key={idx} className="p-2.5 bg-gray-50 rounded-lg border border-gray-100">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-sm text-gray-800">{attr.name}</p>
              <span className="text-xs px-1.5 py-0.5 rounded-full bg-rose-100 text-rose-700">{attr.type}</span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{attr.description}</p>
            <div className="flex justify-between mt-1.5">
              <span className="text-xs text-gray-500">⏱ {attr.duration}</span>
              <span className="text-xs font-medium text-amber-600">★ {attr.rating}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
