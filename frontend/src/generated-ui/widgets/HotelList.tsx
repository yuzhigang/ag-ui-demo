import type { HotelInfo } from "../../types";

export default function HotelList({ hotels }: { hotels: HotelInfo[] }) {
  return (
    <div data-testid="rendered-HotelList" className="mb-4">
      <div className="flex items-center gap-1.5 mb-2">
        <svg className="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span className="text-xs text-gray-500 font-semibold uppercase tracking-wide">推荐酒店</span>
      </div>
      <div className="space-y-2">
        {hotels.map((hotel, idx) => (
          <div key={idx} className="p-2.5 bg-gray-50 rounded-lg border border-gray-100">
            <p className="font-semibold text-sm text-gray-800">{hotel.name}</p>
            <p className="text-xs text-gray-500 mt-0.5">{hotel.location}</p>
            <div className="flex justify-between mt-1.5">
              <span className="text-xs font-medium text-emerald-600">{hotel.price}</span>
              <span className="text-xs font-medium text-amber-600">★ {hotel.rating}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
