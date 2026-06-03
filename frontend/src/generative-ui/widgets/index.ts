import { registerComponent } from "../ComponentRegistry";
import WeatherCard from "./WeatherCard";
import HotelList from "./HotelList";
import FlightCard from "./FlightCard";
import AttractionList from "./AttractionList";
import ProgressBar from "./ProgressBar";

export function registerGenerativeUIWidgets() {
  registerComponent("WeatherCard", WeatherCard);
  registerComponent("HotelList", HotelList);
  registerComponent("FlightCard", FlightCard);
  registerComponent("AttractionList", AttractionList);
  registerComponent("ProgressBar", ProgressBar);
}
