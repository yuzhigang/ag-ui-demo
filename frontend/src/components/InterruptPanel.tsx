import type { InterruptRequest } from "../types";

interface InterruptPanelProps {
  interrupts: InterruptRequest[];
  onConfirm: (interrupt: InterruptRequest) => void;
  onReject: (interrupt: InterruptRequest) => void;
}

export default function InterruptPanel({
  interrupts,
  onConfirm,
  onReject,
}: InterruptPanelProps) {
  if (interrupts.length === 0) return null;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-amber-500 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <h3 className="text-white font-bold text-lg">需要您的确认</h3>
              <p className="text-orange-100 text-sm">以下操作需要人工审核</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {interrupts.map((interrupt) => {
            const fn = interrupt.value?.function_call;
            if (!fn) return null;

            const isBooking = fn.name === "book_flight";
            const args = fn.arguments || {};

            return (
              <div
                key={interrupt.id}
                className="border rounded-xl p-4 bg-gray-50 space-y-3"
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isBooking ? "bg-sky-500" : "bg-gray-400"}`} />
                  <span className="font-semibold text-gray-800">
                    {isBooking ? "航班预订" : fn.name}
                  </span>
                </div>

                {/* 参数展示 */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(args).map(([key, value]) => (
                    <div key={key} className="flex flex-col">
                      <span className="text-xs text-gray-400 uppercase tracking-wide">{key}</span>
                      <span className="font-medium text-gray-700">{String(value)}</span>
                    </div>
                  ))}
                </div>

                {/* 操作按钮 */}
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={() => onReject(interrupt)}
                    className="flex-1 px-4 py-2.5 rounded-lg border border-gray-200 text-gray-600 font-medium hover:bg-gray-100 transition-colors"
                  >
                    拒绝
                  </button>
                  <button
                    onClick={() => onConfirm(interrupt)}
                    className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium hover:from-blue-600 hover:to-blue-700 transition-all shadow-sm"
                  >
                    确认执行
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
