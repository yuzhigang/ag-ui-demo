import type { WeatherInfo } from "../../../types";

export default function WeatherCard(props: WeatherInfo) {
  return (
    <div data-testid="rendered-WeatherCard" className="mb-4 p-3 bg-linear-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
      <div className="flex items-center gap-1.5 mb-2">
        <svg className="w-3.5 h-3.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
        </svg>
        <span className="text-xs text-blue-700 font-semibold">天气</span>
      </div>
      <div className="space-y-1">
        {props.city && <p className="text-sm font-semibold text-gray-800">{props.city}</p>}
        <p className="text-sm font-medium text-gray-800">{props.date} {props.weather}</p>
        <p className="text-xs text-gray-600">气温: {props.temperature}</p>
        <p className="text-xs text-gray-600">湿度: {props.humidity}</p>
      </div>
    </div>
  );
}
