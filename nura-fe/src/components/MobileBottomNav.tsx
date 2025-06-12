import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Book,
  Library,
  User,
  Calendar,
  Trophy,
  Shield,
} from "lucide-react";

const navItems = [
  { label: "Home", href: "/", icon: Home },
  { label: "Calendar", href: "/calendar", icon: Calendar },
  { label: "Badges", href: "/badges", icon: Trophy },
  { label: "Safety", href: "/safety-network", icon: Shield },
  { label: "Profile", href: "/profile", icon: User },
];

export default function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <>
      <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 flex justify-around items-center h-16 md:hidden">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className="flex flex-col items-center justify-center flex-1"
            >
              <Icon
                size={28}
                color={isActive ? "#7c3aed" : "#6b7280"}
                strokeWidth={2.2}
              />
              <span
                className={`text-xs mt-1 font-medium ${
                  isActive ? "text-purple-600" : "text-gray-500"
                }`}
              >
                {item.label}
              </span>
              {isActive && (
                <span className="block w-8 h-1 rounded-full bg-black mt-1" />
              )}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
