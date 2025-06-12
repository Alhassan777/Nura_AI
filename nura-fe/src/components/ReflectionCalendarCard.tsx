"use client";
import { Calendar } from "antd";
import { useState } from "react";
import dayjs, { Dayjs } from "dayjs";

const months = [
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

export default function ReflectionCalendarCard() {
  const [value, setValue] = useState<Dayjs>(dayjs());
  const [mode, setMode] = useState<"month" | "year">("month");

  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0 w-full">
      <div className="p-6">
        <Calendar
          value={value}
          mode={mode}
          fullscreen={false}
          onPanelChange={(val, m) => {
            setValue(val);
            setMode(m);
          }}
          onSelect={setValue}
          headerRender={({ value: current, onChange, onTypeChange }) => {
            const year = current.year();
            const month = current.month();
            const years = Array.from({ length: 10 }, (_, i) => year - 5 + i);
            return (
              <div className="flex items-center gap-2 justify-end  pb-4 mb-4">
                <select
                  className="border rounded px-2 py-1 text-gray-700"
                  value={year}
                  onChange={(e) => {
                    const newYear = parseInt(e.target.value, 10);
                    onChange(current.clone().year(newYear));
                  }}
                >
                  {years.map((y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  ))}
                </select>
                <select
                  className="border rounded px-2 py-1 text-gray-700"
                  value={month}
                  onChange={(e) => {
                    const newMonth = parseInt(e.target.value, 10);
                    onChange(current.clone().month(newMonth));
                  }}
                >
                  {months.map((m: string, i: number) => (
                    <option key={m} value={i}>
                      {m}
                    </option>
                  ))}
                </select>
                <button
                  className={`border rounded px-3 py-1 text-sm font-medium ${
                    mode === "month"
                      ? "bg-purple-50 text-purple-600 border-purple-500"
                      : "bg-white text-gray-700"
                  }`}
                  onClick={() => onTypeChange("month")}
                >
                  Month
                </button>
                <button
                  className={`border rounded px-3 py-1 text-sm font-medium ${
                    mode === "year"
                      ? "bg-purple-50 text-purple-600 border-purple-500"
                      : "bg-white text-gray-700"
                  }`}
                  onClick={() => onTypeChange("year")}
                >
                  Year
                </button>
              </div>
            );
          }}
          fullCellRender={(date) => {
            const isSelected = date.isSame(value, "date");
            return (
              <div
                className={`w-8 h-8 flex items-center justify-center rounded-lg ${
                  isSelected
                    ? "bg-purple-500 text-white font-semibold border-2 border-purple-600"
                    : ""
                }`}
              >
                {date.date().toString().padStart(2, "0")}
              </div>
            );
          }}
        />
      </div>
    </div>
  );
}
