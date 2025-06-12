"use client";

import { Button, Dropdown, Avatar, MenuProps, App } from "antd";
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  HomeOutlined,
  CheckSquareOutlined,
  CalendarOutlined,
  MessageOutlined,
  TrophyOutlined,
  SafetyCertificateOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import MobileBottomNav from "@/components/MobileBottomNav";
import StatsCards from "@/components/StatsCards";
import LevelProgress from "@/components/LevelProgress";
import { useAuth } from "@/contexts/AuthContext";

export default function Sidebar() {
  const { user, logout: authLogout, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { message } = App.useApp();

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false);
      }
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleLogout = async () => {
    try {
      await authLogout();
      message.success("Logged out successfully");
      router.push("/login");
    } catch (error) {
      message.error("Logout failed");
      console.error("Logout error:", error);
    }
  };

  const profileMenuItems: MenuProps["items"] = [
    {
      key: "user-info",
      label: (
        <div className="px-2 py-1">
          <div className="font-medium text-gray-900 truncate max-w-[200px]">
            {user?.full_name || user?.email}
          </div>
          <div className="text-sm text-gray-500 truncate max-w-[200px]">
            {user?.email}
          </div>
        </div>
      ),
      disabled: true,
    },
    {
      type: "divider",
    },
    {
      key: "profile",
      label: "Profile",
      icon: <UserOutlined />,
      onClick: () => router.push("/profile"),
    },
    {
      key: "settings",
      label: "Settings",
      icon: <SettingOutlined />,
      onClick: () => router.push("/settings"),
    },
    {
      type: "divider",
    },
    {
      key: "logout",
      label: "Logout",
      icon: <LogoutOutlined />,
      onClick: handleLogout,
    },
  ];

  const toggleSidebar = () => {
    if (isMobile) {
      setIsMobileMenuOpen(!isMobileMenuOpen);
    } else {
      setIsCollapsed(!isCollapsed);
    }
  };

  const sidebarClasses = `
    md:sticky fixed top-0 h-screen bg-white/80 backdrop-blur-md border-r border-gray-200 shadow-xs flex flex-col
    transition-all duration-300 ease-in-out
    ${
      isMobile
        ? "left-0 z-50 w-72 transform " +
          (isMobileMenuOpen ? "translate-x-0" : "-translate-x-full")
        : isCollapsed
        ? "left-0 w-[90px]"
        : "left-0 w-64"
    }
  `;

  const overlayClasses = `
    fixed inset-0 backdrop-blur-sm bg-white/30 z-40
    transition-opacity duration-300
    ${
      isMobile && isMobileMenuOpen
        ? "opacity-100"
        : "opacity-0 pointer-events-none"
    }
  `;

  const navigationItems = [
    {
      key: "home",
      label: "Home",
      icon: <HomeOutlined />,
      path: "/",
    },
    {
      key: "badges",
      label: "Badges",
      icon: <TrophyOutlined />,
      path: "/badges",
    },
    {
      key: "quests",
      label: "Quests",
      icon: <CheckSquareOutlined />,
      path: "/quests",
    },
    {
      key: "chat",
      label: "Chat",
      icon: <MessageOutlined />,
      path: "/chat",
    },
    {
      key: "safety-network",
      label: "Safety Network",
      icon: <SafetyCertificateOutlined />,
      path: "/safety-network",
    },
    {
      key: "memories",
      label: "Memory Vault",
      icon: <DatabaseOutlined />,
      path: "/memories",
    },
    {
      key: "privacy",
      label: "Privacy",
      icon: <SafetyCertificateOutlined />,
      path: "/privacy",
    },
    {
      key: "soul-gallery",
      label: "Soul Gallery",
      icon: <UserOutlined />,
      path: "/soul-gallery",
    },
    {
      key: "chat-history",
      label: "Chat History",
      icon: <UserOutlined />,
      path: "/chat-history",
    },
    {
      key: "action-plans",
      label: "Action Plans",
      icon: <UserOutlined />,
      path: "/action-plans",
    },

    {
      key: "daily",
      label: "Calendar",
      icon: <CalendarOutlined />,
      path: "/calendar",
    },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {isMobile && (
        <div
          className={overlayClasses}
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar only on md+ */}
      <aside className={sidebarClasses + " hidden md:flex"}>
        <div
          className={cn(
            "p-4 border-b border-gray-200 flex items-center justify-between",
            isCollapsed && "justify-center"
          )}
        >
          {!isCollapsed && (
            <Link href="/" className="text-xl font-bold text-gray-800 truncate">
              Nura
            </Link>
          )}
          {!isMobile && (
            <Button
              type="text"
              icon={isCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleSidebar}
            />
          )}
        </div>

        <div className="flex-1 p-2 overflow-y-auto">
          <nav
            className={cn(
              "space-y-3 mt-6",
              isCollapsed && "w-full flex flex-col items-center"
            )}
          >
            {navigationItems.map((item) => {
              const isActive = pathname === item.path;
              return (
                <Link key={item.key} href={item.path} className="block">
                  <Button
                    size="large"
                    icon={item.icon}
                    type={isActive ? "primary" : "default"}
                    className={cn(
                      "w-full flex items-center !shadow-xs",
                      isCollapsed ? "!justify-center" : "!justify-start"
                    )}
                  >
                    {(!isCollapsed || isMobile) && (
                      <span className={cn("ml-2", isActive && "font-medium")}>
                        {item.label}
                      </span>
                    )}
                  </Button>
                </Link>
              );
            })}
          </nav>

          {/* Stats Cards */}
          <StatsCards isCollapsed={isCollapsed} />
          <LevelProgress
            level={12}
            currentXP={2450}
            nextLevelXP={5000}
            isCollapsed={isCollapsed}
          />
        </div>

        <div className="border-t border-gray-200 p-2">
          {user ? (
            <Dropdown
              menu={{ items: profileMenuItems }}
              placement={isCollapsed ? "bottomRight" : "topRight"}
              arrow
            >
              <Button
                type="text"
                className={cn(
                  "w-full flex items-center !h-12 !px-2 ",
                  isCollapsed ? "!justify-center" : "!justify-start"
                )}
              >
                <Avatar
                  size={isCollapsed ? 24 : 32}
                  icon={<UserOutlined />}
                  className="bg-blue-500"
                />
                {(!isCollapsed || isMobile) && (
                  <div className="ml-3 text-left">
                    <div className="font-medium text-gray-900 truncate max-w-[150px]">
                      {user.full_name || user.email}
                    </div>
                    <div className="text-xs text-gray-500 truncate max-w-[150px]">
                      {user.email}
                    </div>
                  </div>
                )}
              </Button>
            </Dropdown>
          ) : (
            <div className={`space-y-2 ${isCollapsed ? "hidden" : ""}`}>
              <Link href="/login" className="block w-full">
                <Button className="w-full">Sign In</Button>
              </Link>
              <Link href="/signup" className="block w-full">
                <Button type="primary" className="w-full">
                  Sign Up
                </Button>
              </Link>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile Bottom Nav */}
      <MobileBottomNav />
    </>
  );
}
