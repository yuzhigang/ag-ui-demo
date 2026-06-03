export default function ProgressBar({ step, total }: { step: number; total: number }) {
  return (
    <div data-testid="rendered-ProgressBar" className="p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500">进度</span>
        <span className="text-xs font-medium text-gray-700">{step} / {total}</span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-300"
          style={{ width: `${(step / total) * 100}%` }}
        />
      </div>
    </div>
  );
}
