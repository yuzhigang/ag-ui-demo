import type { FlightInfo } from "../../../types";

export default function FlightCard(props: FlightInfo) {
  return (
    <div data-testid="rendered-FlightCard" className="mb-4 p-3 bg-linear-to-r from-sky-50 to-blue-50 rounded-lg border border-sky-100">
      <div className="flex items-center gap-1.5 mb-2">
        <svg className="w-3.5 h-3.5 text-sky-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
        <span className="text-xs text-sky-700 font-semibold">航班信息</span>
      </div>
      <div className="space-y-1.5">
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">航班号</span>
          <span className="text-xs font-medium text-gray-800">{props.flight_number}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">航线</span>
          <span className="text-xs font-medium text-gray-800">{props.departure} → {props.arrival}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">日期</span>
          <span className="text-xs font-medium text-gray-800">{props.date}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">座位</span>
          <span className="text-xs font-medium text-gray-800">{props.seat}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">状态</span>
          <span className="text-xs font-medium text-emerald-600">{props.status}</span>
        </div>
      </div>
    </div>
  );
}
