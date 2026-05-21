export interface WeatherInfo {
  city: string;
  date: string;
  weather: string;
  temperature: string;
  humidity: string;
}

export interface HotelInfo {
  name: string;
  price: string;
  rating: number;
  location: string;
}

export interface AttractionInfo {
  name: string;
  type: string;
  rating: number;
  duration: string;
  description: string;
}

export interface FlightInfo {
  flight_number: string;
  departure: string;
  arrival: string;
  date: string;
  passenger: string;
  status: string;
  gate: string;
  seat: string;
}

export interface Itinerary {
  city?: string;
  checkIn?: string;
  checkOut?: string;
  weather?: WeatherInfo;
  hotels?: HotelInfo[];
  attractions?: AttractionInfo[];
  flight?: FlightInfo;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export type AgentStatus = "idle" | "thinking" | "tool_call" | "error" | "interrupt";

export interface AGUIEvent {
  id: string;
  timestamp: number;
  type: string;
  raw: Record<string, unknown>;
}

export interface ToolCallInfo {
  id: string;
  name: string;
  args: string;
  status: "pending" | "completed" | "error";
}

export interface InterruptFunctionCall {
  call_id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface InterruptRequest {
  id: string;
  value: {
    type: string;
    function_call: InterruptFunctionCall;
  };
}
