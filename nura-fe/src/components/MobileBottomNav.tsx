import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Home,
  Book,
  Library,
  User,
  Calendar,
  Trophy,
  Shield,
  MessageCircle,
  CheckSquare,
  Database,
  UserCheck,
  FileText,
  MessageSquare,
  ChevronUp,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useInvitationNotifications } from "@/contexts/InvitationNotificationContext";

const navItems = [
  { label: "Home", href: "/", icon: Home },
  { label: "Calendar", href: "/calendar", icon: Calendar },
  { label: "Badges", href: "/badges", icon: Trophy },
  { label: "Safety", href: "/safety-network", icon: Shield },
];

// Additional navigation items that will be in the dropdown
const dropdownItems = [
  { label: "Quests", href: "/quests", icon: CheckSquare },
  { label: "Chat", href: "/chat", icon: MessageCircle },
  { label: "Memory Vault", href: "/memories", icon: Database },
  { label: "Privacy", href: "/privacy", icon: Shield },
  { label: "Soul Gallery", href: "/soul-gallery", icon: UserCheck },
  { label: "Chat History", href: "/chat-history", icon: MessageSquare },
  { label: "Action Plans", href: "/action-plans", icon: FileText },
];

export default function MobileBottomNav() {
  const pathname = usePathname();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const { hasNewInvitations, newInvitationsCount, markNotificationsAsRead } =
    useInvitationNotifications();

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const closeDropdown = () => {
    setIsDropdownOpen(false);
  };

  // Check if any dropdown item is active
  const isDropdownItemActive = dropdownItems.some(
    (item) => pathname === item.href
  );

  return (
    <>
      {/* Backdrop */}
      <AnimatePresence>
        {isDropdownOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 md:hidden"
            onClick={closeDropdown}
          />
        )}
      </AnimatePresence>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isDropdownOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="fixed bottom-20 left-4 right-4 bg-white rounded-2xl shadow-2xl border border-gray-200 z-50 md:hidden overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">More Options</h3>
              <button
                onClick={closeDropdown}
                className="p-1 rounded-full hover:bg-gray-100 transition-colors"
              >
                <X size={20} className="text-gray-500" />
              </button>
            </div>

            {/* Dropdown Items */}
            <div className="grid grid-cols-2 gap-1 p-2">
              {dropdownItems.map((item, index) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.05 }}
                  >
                    <Link
                      href={item.href}
                      onClick={closeDropdown}
                      className={`flex flex-col items-center justify-center p-4 rounded-xl transition-all duration-200 ${
                        isActive
                          ? "bg-purple-50 text-purple-600"
                          : "hover:bg-gray-50 text-gray-600"
                      }`}
                    >
                      <Icon
                        size={24}
                        className={`mb-2 ${
                          isActive ? "text-purple-600" : "text-gray-500"
                        }`}
                      />
                      <span
                        className={`text-xs font-medium text-center ${
                          isActive ? "text-purple-600" : "text-gray-600"
                        }`}
                      >
                        {item.label}
                      </span>
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 flex justify-around items-center h-16 md:hidden">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          const showBadge =
            item.href === "/safety-network" && hasNewInvitations;

          const handleClick = () => {
            if (item.href === "/safety-network" && hasNewInvitations) {
              markNotificationsAsRead();
            }
          };

          return (
            <Link
              key={item.label}
              href={item.href}
              className="flex flex-col items-center justify-center flex-1 relative"
              onClick={handleClick}
            >
              <div className="relative">
                <Icon
                  size={28}
                  color={isActive ? "#7c3aed" : "#6b7280"}
                  strokeWidth={2.2}
                />
                {showBadge && (
                  <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold">
                    {newInvitationsCount > 9 ? "9+" : newInvitationsCount}
                  </span>
                )}
              </div>
              <span
                className={`text-xs mt-1 font-medium ${
                  isActive ? "text-purple-600" : "text-gray-500"
                }`}
              >
                {item.label}
              </span>
              {isActive && (
                <span className="block w-8 h-1 rounded-full bg-purple-600 mt-1" />
              )}
            </Link>
          );
        })}

        {/* More/Dropdown Button */}
        <button
          onClick={toggleDropdown}
          className="flex flex-col items-center justify-center flex-1"
        >
          <motion.div
            animate={{ rotate: isDropdownOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronUp
              size={28}
              color={
                isDropdownItemActive || isDropdownOpen ? "#7c3aed" : "#6b7280"
              }
              strokeWidth={2.2}
            />
          </motion.div>
          <span
            className={`text-xs mt-1 font-medium ${
              isDropdownItemActive || isDropdownOpen
                ? "text-purple-600"
                : "text-gray-500"
            }`}
          >
            More
          </span>
          {(isDropdownItemActive || isDropdownOpen) && (
            <span className="block w-8 h-1 rounded-full bg-purple-600 mt-1" />
          )}
        </button>
      </nav>
    </>
  );
}
