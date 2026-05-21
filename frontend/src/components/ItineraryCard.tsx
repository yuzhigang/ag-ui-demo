import type { Itinerary } from "../types";

interface ItineraryCardProps {
  itinerary: Itinerary;
}

export default function ItineraryCard({ itinerary }: ItineraryCardProps) {
  const hasData = itinerary.city || itinerary.weather || itinerary.hotels || itinerary.attractions || itinerary.flight;

  if (!hasData) {
    return (
      <div className="border rounded-xl bg-white p-5 shadow-sm"
      >
        <div className="flex items-center gap-2 mb-3"
        >
          <div className="w-6 h-6 rounded-md bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center"
          >
            <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h2 className="text-sm font-bold text-gray-800"
          >行程信息</h2
          >
        </div>
        <div className="flex flex-col items-center justify-center py-6 text-center"
        >
          <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-2"
          >
            <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <p className="text-gray-400 text-sm"
          >暂无行程数据</p
          >
          <p className="text-gray-300 text-xs mt-1"
          >与助手对话开始规划</p
          >
        </div>
      </div>
    );
  }

  return (
    <div className="border rounded-xl bg-white p-4 shadow-sm overflow-y-auto"
    >
      <div className="flex items-center gap-2 mb-4"
      >
        <div className="w-6 h-6 rounded-md bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center"
        >
          <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <h2 className="text-sm font-bold text-gray-800"
        >行程信息</h2
        >
      </div>

      {itinerary.city && (
        <div className="mb-4"
        >
          <span className="text-xs text-gray-500 font-medium uppercase tracking-wide"
          >目的地</span
          >
          <p className="font-semibold text-gray-800 mt-0.5 text-base"
          >{itinerary.city}</p
          >
        </div>
      )}

      {itinerary.flight && (
        <div className="mb-4 p-3 bg-gradient-to-r from-sky-50 to-blue-50 rounded-lg border border-sky-100"
        >
          <div className="flex items-center gap-1.5 mb-2"
          >
            <svg className="w-3.5 h-3.5 text-sky-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            <span className="text-xs text-sky-700 font-semibold"
            >航班信息</span
            >
          </div>
          <div className="space-y-1.5"
          >
            <div className="flex justify-between"
            >
              <span className="text-xs text-gray-500"
              >航班号</span
              >
              <span className="text-xs font-medium text-gray-800"
              >{itinerary.flight.flight_number}</span
              >
            </div>
            <div className="flex justify-between"
            >
              <span className="text-xs text-gray-500"
              >航线</span
              >
              <span className="text-xs font-medium text-gray-800"
              >{itinerary.flight.departure} → {itinerary.flight.arrival}</span
              >
            </div>
            <div className="flex justify-between"
            >
              <span className="text-xs text-gray-500"
              >日期</span
              >
              <span className="text-xs font-medium text-gray-800"
              >{itinerary.flight.date}</span
              >
            </div>
            <div className="flex justify-between"
            >
              <span className="text-xs text-gray-500"
              >座位</span
              >
              <span className="text-xs font-medium text-gray-800"
              >{itinerary.flight.seat}</span
              >
            </div>
            <div className="flex justify-between"
            >
              <span className="text-xs text-gray-500"
              >状态</span
              >
              <span className="text-xs font-medium text-emerald-600"
              >{itinerary.flight.status}</span
              >
            </div>
          </div>
        </div>
      )}

      {itinerary.weather && (
        <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100"
        >
          <div className="flex items-center gap-1.5 mb-2"
          >
            <svg className="w-3.5 h-3.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
            <span className="text-xs text-blue-700 font-semibold"
            >天气</span
            >
          </div>
          <div className="space-y-1"
          >
            <p className="text-sm font-medium text-gray-800"
            >
              {itinerary.weather.date} {itinerary.weather.weather}
            </p>
            <p className="text-xs text-gray-600"
            >气温: {itinerary.weather.temperature}</p
            >
            <p className="text-xs text-gray-600"
            >湿度: {itinerary.weather.humidity}</p
            >
          </div>
        </div>
      )}

      {itinerary.hotels && itinerary.hotels.length > 0 && (
        <div className="mb-4"
        >
          <div className="flex items-center gap-1.5 mb-2"
          >
            <svg className="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span className="text-xs text-gray-500 font-semibold uppercase tracking-wide"
            >推荐酒店</span
            >
          </div>
          <div className="space-y-2"
          >
            {itinerary.hotels.map((hotel, idx) => (
              <div key={idx} className="p-2.5 bg-gray-50 rounded-lg border border-gray-100 hover:shadow-sm transition-shadow"
              >
                <p className="font-semibold text-sm text-gray-800"
                >{hotel.name}</p
                >
                <p className="text-xs text-gray-500 mt-0.5"
                >{hotel.location}</p
                >
                <div className="flex justify-between mt-1.5"
                >
                  <span className="text-xs font-medium text-emerald-600"
                  >{hotel.price}</span
                  >
                  <span className="text-xs font-medium text-amber-600"
                  >★ {hotel.rating}</span
                  >
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {itinerary.attractions && itinerary.attractions.length > 0 && (
        <div
        >
          <div className="flex items-center gap-1.5 mb-2"
          >
            <svg className="w-3.5 h-3.5 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-xs text-gray-500 font-semibold uppercase tracking-wide"
            >推荐景点</span
            >
          </div>
          <div className="space-y-2"
          >
            {itinerary.attractions.map((attr, idx) => (
              <div key={idx} className="p-2.5 bg-gray-50 rounded-lg border border-gray-100 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center justify-between"
                >
                  <p className="font-semibold text-sm text-gray-800"
                  >{attr.name}</p
                  >
                  <span className="text-xs px-1.5 py-0.5 rounded-full bg-rose-100 text-rose-700"
                  >{attr.type}</span
                  >
                </div>
                <p className="text-xs text-gray-500 mt-0.5"
                >{attr.description}</p
                >
                <div className="flex justify-between mt-1.5"
                >
                  <span className="text-xs text-gray-500"
                  >⏱ {attr.duration}</span
                  >
                  <span className="text-xs font-medium text-amber-600"
                  >★ {attr.rating}</span
                  >
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
