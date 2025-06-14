"use client";

import React from "react";
import { Select } from "antd";

const { Option } = Select;

export interface PriorityLevel {
  value: number;
  label: string;
  emoji: string;
  description: string;
  color: string;
}

export const PRIORITY_LEVELS: PriorityLevel[] = [
  {
    value: 1,
    label: "Priority 1 - Critical",
    emoji: "🚨",
    description: "First person contacted in any emergency",
    color: "text-red-600",
  },
  {
    value: 2,
    label: "Priority 2 - High",
    emoji: "⚡",
    description: "Second person contacted if first unavailable",
    color: "text-orange-600",
  },
  {
    value: 3,
    label: "Priority 3 - Medium",
    emoji: "📞",
    description: "Regular contact for support and check-ins",
    color: "text-yellow-600",
  },
  {
    value: 4,
    label: "Priority 4 - Low",
    emoji: "💬",
    description: "Occasional contact for updates and sharing",
    color: "text-blue-600",
  },
  {
    value: 5,
    label: "Priority 5 - Minimal",
    emoji: "📱",
    description: "Basic safety network member with limited contact",
    color: "text-gray-600",
  },
];

export const getPriorityLevel = (value: number): PriorityLevel | undefined => {
  return PRIORITY_LEVELS.find((level) => level.value === value);
};

export const formatPriorityLabel = (value: number): string => {
  const level = getPriorityLevel(value);
  return level ? `${level.emoji} ${level.label}` : `Priority ${value}`;
};

interface PrioritySelectorProps {
  value?: number;
  onChange?: (value: number) => void;
  placeholder?: string;
  size?: "small" | "middle" | "large";
  disabled?: boolean;
  required?: boolean;
  showDescription?: boolean;
}

export const PrioritySelector: React.FC<PrioritySelectorProps> = ({
  value,
  onChange,
  placeholder = "Select priority level",
  size = "large",
  disabled = false,
  required = false,
  showDescription = true,
}) => {
  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      size={size}
      disabled={disabled}
      className="w-full"
    >
      {PRIORITY_LEVELS.map((level) => (
        <Option key={level.value} value={level.value}>
          <div>
            <div className={`font-medium ${level.color}`}>
              {level.emoji} {level.label}
            </div>
            {showDescription && (
              <div className="text-xs text-gray-500">{level.description}</div>
            )}
          </div>
        </Option>
      ))}
    </Select>
  );
};

export default PrioritySelector;
