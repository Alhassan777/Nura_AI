import { Smile, Frown, Meh, Angry, Laugh } from "lucide-react";
import { ReactNode } from "react";

export const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export const MOOD_OPTIONS: {
  key: string;
  icon: ReactNode;
  label: string;
  color: string;
  colorToken: string;
}[] = [
  {
    key: "great",
    icon: <Laugh color="#52c41a" size={22} strokeWidth={2} />,
    color: "#52c41a",
    label: "Great",
    colorToken: "green",
  },
  {
    key: "good",
    icon: <Smile color="#9810fa" size={22} strokeWidth={2} />,
    color: "#9810fa",
    label: "Good",
    colorToken: "purple",
  },
  {
    key: "natural",
    icon: <Meh color="#8c8c8c" size={22} strokeWidth={2} />,
    color: "#8c8c8c",
    label: "Natural",
    colorToken: "gray",
  },
  {
    key: "bad",
    icon: <Frown color="#fa541c" size={22} strokeWidth={2} />,
    color: "#fa541c",
    label: "Bad",
    colorToken: "red",
  },
  {
    key: "very sad",
    icon: <Angry color="#f5222d" size={22} strokeWidth={2} />,
    color: "#f5222d",
    label: "Very Sad",
    colorToken: "red",
  },
];

export const MOOD_ICONS: Record<string, ReactNode> = {
  great: <Laugh color="#52c41a" size={22} strokeWidth={2} />,
  good: <Smile color="#9810fa" size={22} strokeWidth={2} />,
  natural: <Meh color="#8c8c8c" size={22} strokeWidth={2} />,
  bad: <Frown color="#fa541c" size={22} strokeWidth={2} />,
  very_sad: <Angry color="#f5222d" size={22} strokeWidth={2} />,
};
