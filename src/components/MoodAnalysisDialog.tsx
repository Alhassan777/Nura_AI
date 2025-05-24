import React, { useEffect, useRef, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Button } from "@/components/ui/button";
import { Line, Bar } from "react-chartjs-2";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Reflection } from "@/components/DailyReflection";
import { MOOD_OPTIONS } from "@/constant";
import { StreakCounter } from "@/components/StreakCounter";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface MoodAnalysisDialogProps {
  dailyReflection: Reflection[];
}

export function MoodAnalysisDialog({
  dailyReflection,
}: MoodAnalysisDialogProps) {
  const moodValues = {
    great: 5,
    good: 4,
    neutral: 3,
    bad: 2,
    awful: 1,
  };

  // Calculate streak
  const getStreak = () => {
    console.log(dailyReflection);
    if (!dailyReflection.length) return 0;
    const dates = dailyReflection
      .map((r) => r.date)
      .map((d) => new Date(d))
      .sort((a, b) => b.getTime() - a.getTime());
    let streak = 0;
    let current = new Date();
    current.setHours(0, 0, 0, 0);
    for (let i = 0; i < dates.length; i++) {
      if (dates[i].toDateString() === current.toDateString()) {
        streak++;
        current.setDate(current.getDate() - 1);
      } else {
        break;
      }
    }
    return streak;
  };
  const streak = getStreak();

  // Animation state
  const [animate, setAnimate] = useState(false);
  const prevStreak = useRef(streak);

  useEffect(() => {
    // Only animate if streak increases to 3, 7, or 30
    if (
      (streak === 3 || streak === 7 || streak === 30) &&
      prevStreak.current < streak
    ) {
      setAnimate(true);
      const timeout = setTimeout(() => setAnimate(false), 2000);
      return () => clearTimeout(timeout);
    }
    prevStreak.current = streak;
  }, [streak]);

  // Calculate average mood
  const averageMood =
    dailyReflection.length > 0
      ? dailyReflection.reduce((acc, ref) => acc + moodValues[ref.mood], 0) /
        dailyReflection.length
      : 0;

  // Calculate mood distribution
  const moodDistribution = MOOD_OPTIONS.map((mood) => ({
    label: mood.label,
    value: dailyReflection.filter((ref) => ref.mood === mood.value).length,
    emoji: mood.emoji,
  }));

  const lineChartData = {
    labels: dailyReflection.map((ref) =>
      new Date(ref.date).toLocaleDateString()
    ),
    datasets: [
      {
        label: "Mood Trend",
        data: dailyReflection.map((ref) => moodValues[ref.mood]),
        borderColor: "rgb(75, 192, 192)",
        backgroundColor: "rgba(75, 192, 192, 0.5)",
        tension: 0.4,
        fill: true,
      },
      {
        label: "Average Mood",
        data: dailyReflection.map(() => averageMood),
        borderColor: "rgb(255, 99, 132)",
        borderDash: [5, 5],
        borderWidth: 2,
        pointRadius: 0,
      },
    ],
  };

  const barChartData = {
    labels: moodDistribution.map((m) => m.emoji),
    datasets: [
      {
        label: "Mood Distribution",
        data: moodDistribution.map((m) => m.value),
        backgroundColor: [
          "rgba(75, 192, 192, 0.6)",
          "rgba(54, 162, 235, 0.6)",
          "rgba(255, 206, 86, 0.6)",
          "rgba(255, 99, 132, 0.6)",
          "rgba(153, 102, 255, 0.6)",
        ],
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    scales: {
      y: {
        min: 0,
        max: 6,
        ticks: {
          stepSize: 1,
          callback: function (tickValue: number | string) {
            if (typeof tickValue === "number") {
              return (
                Object.entries(moodValues).find(
                  ([_, v]) => v === tickValue
                )?.[0] || tickValue
              );
            }
            return tickValue;
          },
        },
      },
    },
    plugins: {
      legend: {
        position: "top" as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const reflection = dailyReflection[context.dataIndex];
            const labels = [`Mood: ${context.dataset.label}`];
            if (reflection?.notes) {
              labels.push(`Notes: ${reflection.notes}`);
            }
            return labels;
          },
        },
      },
    },
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Mood Analysis Dashboard</CardTitle>
      </CardHeader>
      <CardContent>
        <StreakCounter reflections={dailyReflection} />
        <div className="grid gap-4 mt-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex flex-col items-center">
              <span className="text-sm font-medium">Total Entries</span>
              <span className="text-2xl font-bold">
                {dailyReflection.length}
              </span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-sm font-medium">Average Mood</span>
              <span className="text-2xl font-bold">
                {Object.entries(moodValues).find(
                  ([_, v]) => Math.round(v) === Math.round(averageMood)
                )?.[0] || "N/A"}
              </span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-sm font-medium">Most Common Mood</span>
              <span className="text-2xl font-bold">
                {
                  moodDistribution.reduce((a, b) => (a.value > b.value ? a : b))
                    .emoji
                }
              </span>
            </div>
          </div>

          <Tabs defaultValue="trend" className="w-full mt-4">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="trend">Mood Trend</TabsTrigger>
              <TabsTrigger value="distribution">Mood Distribution</TabsTrigger>
            </TabsList>
            <TabsContent value="trend" className="h-[400px]">
              <Line data={lineChartData} options={chartOptions} />
            </TabsContent>
            <TabsContent value="distribution" className="h-[400px]">
              <Bar data={barChartData} options={chartOptions} />
            </TabsContent>
          </Tabs>
        </div>
      </CardContent>
    </Card>
  );
}
