"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useTheme } from "next-themes";
import { Button } from "./ui/button";
import { useUser } from "@/app/providers";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { AuthDialog } from "./AuthDialog";
export default function Header() {
  const [isAuthDialogOpen, setIsAuthDialogOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [currentTheme, setCurrentTheme] = useState("dark");
  const { isAuthenticated, isLoading, name, picture, email } = useUser();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Navigation links
  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/dashboard", label: "Dashboard" },
    { href: "/dashboard/connections", label: "Connections" },
    { href: "/daily", label: "Daily" },
  ];

  // Helper function to check if a link is active
  const isLinkActive = (href: string): boolean => {
    if (href === "/") {
      return pathname === "/";
    }

    if (href === "/dashboard") {
      // Only consider the exact match or direct child routes like /dashboard/call/[id]
      // but not /dashboard/connections
      return (
        pathname === "/dashboard" ||
        (pathname.startsWith("/dashboard/") &&
          !pathname.startsWith("/dashboard/connections"))
      );
    }

    // For other routes, check if the pathname starts with the href
    return pathname.startsWith(href);
  };

  // Handle logout
  const handleLogout = () => {
    // Clear authentication data
    document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    localStorage.removeItem("user");
    router.push("/auth");
  };

  useEffect(() => {
    setCurrentTheme(theme || "dark");
  }, [theme]);

  return (
    <motion.header
      className="backdrop-blur-md bg-background/80 dark:bg-transparent border-b border-neutral-200/20 dark:border-neutral-800/50 sticky top-0 z-50"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
          <Link href="/" className="font-bold text-xl">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/80 dark:from-primary dark:to-primary/80">
              Nura
            </span>
          </Link>
        </motion.div>

        <div className="flex items-center gap-6">
          <nav>
            <ul className="flex space-x-6">
              {navLinks.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="relative group">
                    <motion.span
                      className={`${
                        isLinkActive(link.href)
                          ? "text-primary font-medium"
                          : "text-foreground/80 hover:text-primary"
                      }`}
                      whileHover={{ y: -1 }}
                      transition={{ type: "spring", stiffness: 300 }}
                    >
                      {link.label}
                    </motion.span>
                    {isLinkActive(link.href) && (
                      <motion.div
                        className="absolute -bottom-1.5 left-0 right-0 h-0.5 bg-gradient-to-r from-primary to-primary/80 dark:from-primary dark:to-primary/80"
                        layoutId="activeNavIndicator"
                        transition={{
                          type: "spring",
                          stiffness: 300,
                          damping: 30,
                        }}
                      />
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="icon"
              className="rounded-full w-9 h-9 border-neutral-200/30 dark:border-neutral-800/50"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              <motion.div
                animate={{ rotate: theme === "dark" ? 180 : 0 }}
                transition={{ duration: 0.5 }}
              >
                {currentTheme === "dark" ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="12" cy="12" r="5" />
                    <line x1="12" y1="1" x2="12" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="23" />
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                    <line x1="1" y1="12" x2="3" y2="12" />
                    <line x1="21" y1="12" x2="23" y2="12" />
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                  </svg>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                  </svg>
                )}
              </motion.div>
            </Button>

            {isAuthenticated && !isLoading && (
              <DropdownMenu
                open={isDropdownOpen}
                onOpenChange={setIsDropdownOpen}
              >
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="rounded-full h-9 w-9 p-0 overflow-hidden border-2 border-transparent hover:border-primary/20 transition-all"
                  >
                    <Avatar>
                      <AvatarImage src={picture} alt={name || "User avatar"} />
                      <AvatarFallback className="bg-primary/10 text-primary">
                        {name ? name.charAt(0).toUpperCase() : "U"}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="flex flex-col space-y-1 p-2 border-b border-neutral-200/20 dark:border-neutral-800/50">
                    <p className="text-sm font-medium">{name || "User"}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {email || ""}
                    </p>
                  </div>
                  <DropdownMenuItem asChild>
                    <Link href="/dashboard">Dashboard</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/dashboard/connections">Connections</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-red-500 hover:text-red-600 focus:text-red-600 cursor-pointer"
                    onClick={handleLogout}
                  >
                    Log Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {!isAuthenticated && !isLoading && pathname !== "/auth" && (
              <Button
                variant="default"
                size="sm"
                onClick={() => router.push("/auth")}
              >
                Sign In
              </Button>
            )}
          </div>
        </div>
      </div>
    </motion.header>
  );
}
