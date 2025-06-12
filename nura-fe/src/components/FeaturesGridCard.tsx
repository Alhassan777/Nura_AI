import {
  Lightbulb,
  CalendarDays,
  MessageCircle,
  Users,
  Book,
  Lock,
  Heart,
  Settings,
} from "lucide-react";

const features = [
  {
    icon: Lightbulb,
    title: "Thought Map",
    desc: "Visualize your thoughts",
  },
  {
    icon: CalendarDays,
    title: "Memory Replay",
    desc: "Revisit past reflections",
  },
  {
    icon: MessageCircle,
    title: "Voice Call",
    desc: "Talk with Nura",
  },
  {
    icon: Users,
    title: "Social Network",
    desc: "Connect with others",
  },
  {
    icon: Book,
    title: "Sources",
    desc: "Manage your inspiration",
  },
  {
    icon: Lock,
    title: "Confessional Mode",
    desc: "Private thoughts",
  },
  {
    icon: Heart,
    title: "Tell Me About Them",
    desc: "Remember loved ones",
  },
  {
    icon: Settings,
    title: "Settings",
    desc: "Customize your experience",
  },
];

export default function FeaturesGridCard() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {features.map((f) => (
        <div
          key={f.title}
          className="flex flex-col items-center justify-center p-4 sm:p-6 bg-white rounded-md border border-gray-200 shadow-xs hover:shadow-sm transition-shadow text-center cursor-pointer hover:bg-gray-50 duration-300"
        >
          <f.icon
            size={28}
            strokeWidth={2}
            color="#9810fa"
            className="mb-2 sm:mb-3"
          />
          <div className="font-semibold text-gray-900 text-base sm:text-lg mb-1">
            {f.title}
          </div>
          <div className="text-gray-500 text-xs sm:text-sm">{f.desc}</div>
        </div>
      ))}
    </div>
  );
}
