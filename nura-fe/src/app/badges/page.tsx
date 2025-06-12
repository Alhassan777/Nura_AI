"use client";
import { useBadges } from "@/services/hooks/use-badge";
import Image from "next/image";
import React, { useRef, useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge, Typography, Progress, Carousel, Button } from "antd";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";
import { cn } from "@/lib/utils";

const { Title, Text } = Typography;

function getTierBorderShadow(tier: string) {
  switch (tier) {
    case "wood":
      return {
        border: "border-yellow-800",
        shadow: "shadow-yellow-800",
        background: "bg-yellow-50",
        text: "text-yellow-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI3MCIgaGVpZ2h0PSI3MCIgdmlld0JveD0iMCAwIDcwIDcwIj48cGF0aCBkPSJNMCAwaDcwdjcwSDBWMHptNyA3aDU2djU2SDdWN3oiIGZpbGw9IiNjNDkyMzAiIGZpbGwtb3BhY2l0eT0iMC4xIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiLz48L3N2Zz4=')]",
      };
    case "iron":
      return {
        border: "border-gray-500",
        shadow: "shadow-gray-500",
        background: "bg-gray-50",
        text: "text-gray-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDQwIDQwIj48ZyBmaWxsPSIjNmI3MjgwIiBmaWxsLW9wYWNpdHk9IjAuMSIgZmlsbC1ydWxlPSJldmVub2RkIj48cGF0aCBkPSJNMCAwaDQwdjQwSDBWMHptMjAgMjBjMTEuMDQ2IDAgMjAtOC45NTQgMjAtMjBIMHYyMGgyMHoiLz48L2c+PC9zdmc+')]",
      };
    case "bronze":
      return {
        border: "border-amber-700",
        shadow: "shadow-amber-700",
        background: "bg-amber-50",
        text: "text-amber-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj48ZyBmaWxsPSIjYjQ1MzA5IiBmaWxsLW9wYWNpdHk9IjAuMSIgZmlsbC1ydWxlPSJldmVub2RkIj48cGF0aCBkPSJNMzYgMzRjMCAxLjEtLjkgMi0yIDItMS4xIDAtMi0uOS0yLTIgMC0xLjEuOS0yIDItMiAxLjEgMCAyIC45IDIgMnptLTE4LTJjLTEuMSAwLTIgLjktMiAyIDAgMS4xLjkgMiAyIDJzMi0uOSAyLTJjMC0xLjEtLjktMi0yLTJ6bTE4LTE0YzEuMSAwIDIgLjkgMiAycy0uOSAyLTIgMi0yLS45LTItMiAuOS0yIDItMnpNMTggMThjMS4xIDAgMi0uOSAyLTJzLS45LTItMi0yLTIgLjktMiAyIC45IDIgMiAyeiIvPjwvZz48L3N2Zz4=')]",
      };
    case "silver":
      return {
        border: "border-gray-300",
        shadow: "shadow-gray-300",
        background: "bg-gray-50",
        text: "text-gray-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI1MiIgaGVpZ2h0PSI1MiIgdmlld0JveD0iMCAwIDUyIDUyIj48cGF0aCBmaWxsPSIjOWNhM2FmIiBmaWxsLW9wYWNpdHk9IjAuMSIgZD0iTTAgMGg1MnY1MkgwVjB6bTI2IDI2YzAgMS4xLS45IDItMiAycy0yLS45LTItMiAuOS0yIDItMiAyIC45IDIgMnptMjQgMGMwIDEuMS0uOSAyLTIgMnMtMi0uOS0yLTIgLjktMiAyLTIgMiAuOSAyIDJ6bS0yNi0yNGMwIDEuMS0uOSAyLTIgMnMtMi0uOS0yLTIgLjktMiAyLTIgMiAuOSAyIDJ6bTI2IDBjMCAxLjEtLjkgMi0yIDJzLTItLjktMi0yIC45LTIgMi0yIDIgLjkgMiAyeiIvPjwvc3ZnPg==')]",
      };
    case "gold":
      return {
        border: "border-amber-400",
        shadow: "shadow-amber-400",
        background: "bg-amber-50",
        text: "text-amber-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MCIgaGVpZ2h0PSI4MCIgdmlld0JveD0iMCAwIDgwIDgwIj48cGF0aCBkPSJNMTQuMTQyIDIxLjIxM0E4IDggMCAwIDEgMjAgMjBoMjBhOCA4IDAgMCAxIDUuODU4IDEuMjEzbC0xMC4zMDMgMTAuMzA0YTggOCAwIDAgMS0xMS4zMTQgMGwtMTAuMzAzLTEwLjMwNHpNOC4yMzYgMzIuNWwtNS44NTcgNS44NThhOCA4IDAgMCAwIDAgMTEuMzE0bDExLjMxNCAxMS4zMTRhOCA4IDAgMCAwIDExLjMxNCAwbDExLjMxNC0xMS4zMTRhOCA4IDAgMCAwIDAtMTEuMzE0TDMwLjUgMzIuNWwtOC4xMiA4LjEyYTEyIDEyIDAgMCAxLTE2Ljk3IDAtLjE3NS0uMTc0TDguMjM1IDMyLjV6bS0xLjQxNCAxLjQxNEw1LjcwNyAzNS4wM2ExMiAxMiAwIDAgMSAwLTE2Ljk3TC0uMDEgMTIuNDQzYTggOCAwIDAgMC0uMzYzIDIuMzY0TDAgMTZ2MTZhOCA4IDAgMCAwIDIuMzQzIDUuNjU3bDQuNDc5LTQuNDc4em03MC4zNTYgOS4xNzJhOCA4IDAgMCAwIDAtMTEuMzE0TDY2Ljg2NCAxMS4zQTggOCAwIDAgMCA1NS41NiAxMS4zbC0zLjE0OCAzLjE0OWMtLjQ0NS4zMTMtLjY0LjU1NC0uODUxLjc2NkwzOCA2LjIzNmEyOC4zMDkgMjguMzA5IDAgMCAwLTIuMi0uOTMzQTggOCAwIDAgMCAzMiA0SDE2YTggOCAwIDAgMC01LjY1NyAyLjM0M0wyMS42MzcgMTcuNjM2YTEyIDEyIDAgMCAxIDE2Ljk3IDBsLjE3NC4xNzUgMzguMzk3IDM4LjM5NnoiIGZpbGw9IiNmNTkyMWUiIGZpbGwtb3BhY2l0eT0iMC4xIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiLz48L3N2Zz4=')]",
      };
    case "platinum":
      return {
        border: "border-teal-200",
        shadow: "shadow-teal-200",
        background: "bg-teal-50",
        text: "text-teal-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI3MCIgaGVpZ2h0PSI3MCIgdmlld0JveD0iMCAwIDcwIDcwIj48ZyBmaWxsPSIjMTE0ZTRlIiBmaWxsLW9wYWNpdHk9IjAuMSIgZmlsbC1ydWxlPSJldmVub2RkIj48cGF0aCBkPSJNMzAgMTBhNyA3IDAgMSAxIDE0IDAgNyA3IDAgMCAxLTE0IDB6bTE0IDI0YTcgNyAwIDEgMS0xNCAwIDcgNyAwIDAgMSAxNCAwek0xMCAzMGE3IDcgMCAxIDEgMC0xNCA3IDcgMCAwIDEgMCAxNHptMCAxNGE3IDcgMCAxIDEgMCAxNCA3IDcgMCAwIDEgMC0xNHpNMzAgNjBhNyA3IDAgMSAxIDE0IDAgNyA3IDAgMCAxLTE0IDB6TTYwIDQ0YTcgNyAwIDEgMS0xNCAwIDcgNyAwIDAgMSAxNCAwem0wLTE0YTcgNyAwIDEgMSAwIDE0IDcgNyAwIDAgMSAwLTE0em0wLTMwYTcgNyAwIDEgMSAwIDE0IDcgNyAwIDAgMSAwLTE0eiIvPjwvZz48L3N2Zz4=')]",
      };
    case "diamond":
      return {
        border: "border-blue-400",
        shadow: "shadow-blue-400",
        background: "bg-blue-50",
        text: "text-blue-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI1MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDUwIDQwIj48ZyBmaWxsPSIjMzg4MmY2IiBmaWxsLW9wYWNpdHk9IjAuMSI+PHBhdGggZD0iTTUwIDBIMFY0MEg1MFYwWk0zMSAxNkMyOC43OSAxNiAyNyAxNy43OSAyNyAyMFYyMkgxOFYxMkMxOCA5Ljc5IDE2LjIxIDggMTQgOEMxMS43OSA4IDEwIDkuNzkgMTAgMTJWMjJIMFYxMkMwIDUuMzcgNS4zNyAwIDEyIDBDMTYuOTcgMCAyMS4xMiAzLjEyIDIzIDcuNzRDMjQuODggMy4xMiAyOS4wMyAwIDM0IDBDNDAuNjMgMCA0NiA1LjM3IDQ2IDEyVjIySDE5VjIwQzE5IDE5LjQ1IDE5LjQ1IDE5IDIwIDE5SDMxQzM2LjUyIDE5IDQxIDE0LjUyIDQxIDlDNDEgNS4xNCAzOC4zNSAyIDM1IDJDMzEuNjUgMiAyOSA1LjE0IDI5IDlDMjkgMTAuMTggMjkuMjUgMTEuMjkgMjkuNjggMTIuMjlDMjYuNDIgMTMuMTcgMjQgMTUuOTcgMjQgMTlIMjBDMTcuMjQgMTkgMTUgMjEuMjQgMTUgMjRWMzBDMTUgMzMuMzEgMTcuNjkgMzYgMjEgMzZIMjlDMzIuMzEgMzYgMzUgMzMuMzEgMzUgMzBWMjRDMzUgMTkuNTggMzEuNDIgMTYgMjcgMTZIMjVDMjUgMTQuOSAyNS45IDE0IDI3IDE0SDM5VjIwSDQxVjEyQzQxIDYuNDggMzYuNTIgMiAzMSAyWiIvPjwvZz48L3N2Zz4=')]",
      };
    case "legendary":
      return {
        border: "border-purple-500",
        shadow: "shadow-purple-500",
        background: "bg-purple-50",
        text: "text-purple-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj48ZyBmaWxsPSIjODgzMGU3IiBmaWxsLW9wYWNpdHk9IjAuMTUiPjxwYXRoIGQ9Ik0yNS40NiAyMS44YTEgMSAwIDAgMSAxLjA4IDBsMTUgOUExIDEgMCAwIDEgNDIgMzEuOVYzNmExIDEgMCAwIDEtLjUuODdsMi42MyAxLjU1IDMuMzctMnYtOS4wMmExIDEgMCAwIDAtLjUtLjg3bC0xNS05YTEgMSAwIDAgMC0xIDBsLTggNC44IDMgMS43NnptNS4wNCAzLjFsLTggNC43djkuMDFhMSAxIDAgMCAwIC41Ljg3bDggNC43NWExIDEgMCAwIDAgMSAwbDgtNC43NWExIDEgMCAwIDAgLjUtLjg3VjI5LjZsLTggNC43NWExIDEgMCAwIDEtMS4wMSAwbC04LTQuNzUgNy0zLjkzek0xNyAzMy4zNmwzIjwvcGF0aD48L2c+PC9zdmc+')]",
      };
    default:
      return {
        border: "border-gray-200",
        shadow: "shadow-gray-200",
        background: "bg-gray-50",
        text: "text-gray-800",
        texture:
          "bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDQwIDQwIj48ZyBmaWxsPSIjZDFkNWRiIiBmaWxsLW9wYWNpdHk9IjAuMSIgZmlsbC1ydWxlPSJldmVub2RkIj48cGF0aCBkPSJNMCAwaDQwdjQwSDBWMHptMjAgMjBjMTEuMDQ2IDAgMjAtOC45NTQgMjAtMjBIMHYyMGgyMHoiLz48L2c+PC9zdmc+')]",
      };
  }
}

interface BadgeItem {
  id: string;
  name: string;
  description: string;
  icon?: string;
  unlocked?: boolean;
  progress?: {
    current: number;
    total: number;
  };
  isNext?: boolean;
  tier?:
    | "bronze"
    | "silver"
    | "gold"
    | "platinum"
    | "diamond"
    | "legendary"
    | "wood"
    | "iron";
}

export default function BadgesPage() {
  const { data: badges, isLoading } = useBadges();

  // Create refs for each carousel
  const carouselRefs = useRef<Record<string, any>>({});
  // Track scroll position for each carousel
  const [scrollPositions, setScrollPositions] = useState<
    Record<string, { atStart: boolean; atEnd: boolean }>
  >({});

  // Initialize scroll positions
  useEffect(() => {
    if (badges) {
      const initialPositions: Record<
        string,
        { atStart: boolean; atEnd: boolean }
      > = {};
      Object.keys(badges).forEach((category) => {
        initialPositions[category] = { atStart: true, atEnd: false };
      });
      setScrollPositions(initialPositions);
    }
  }, [badges]);

  // Handle after-change event to update scroll position
  const handleAfterChange = (
    currentSlide: number,
    category: string,
    totalSlides: number,
    slidesToShow: number
  ) => {
    setScrollPositions((prev) => ({
      ...prev,
      [category]: {
        atStart: currentSlide === 0,
        atEnd: currentSlide >= totalSlides - slidesToShow,
      },
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl font-medium text-gray-600">
          Loading badges...
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-10">
        <Title level={2} className="!text-3xl !mb-2">
          Your Badges
        </Title>
        <Text className="text-gray-600">
          Collect badges as you complete achievements
        </Text>
      </div>

      <div className="space-y-16">
        {Object.entries(badges || {}).map(([category, badgeList]) => {
          // Create a ref for this specific carousel
          if (!carouselRefs.current[category]) {
            carouselRefs.current[category] = React.createRef();
          }

          const totalBadges = (badgeList as BadgeItem[]).length;
          const slidesToShow =
            window?.innerWidth >= 1280
              ? 4
              : window?.innerWidth >= 1024
              ? 3
              : window?.innerWidth >= 640
              ? 2
              : 1;

          return (
            <div key={category} className="space-y-6">
              <div className="border-b border-gray-200 pb-2 flex justify-between items-center">
                <Title level={4} className="!mb-0">
                  <span className="inline-block border-l-4 border-purple-600 pl-3">
                    {category}
                  </span>
                </Title>

                <div className="flex gap-2">
                  <Button
                    icon={<LeftOutlined />}
                    onClick={() =>
                      carouselRefs.current[category].current?.prev()
                    }
                    shape="circle"
                    disabled={scrollPositions[category]?.atStart}
                  />
                  <Button
                    icon={<RightOutlined />}
                    onClick={() =>
                      carouselRefs.current[category].current?.next()
                    }
                    shape="circle"
                    disabled={scrollPositions[category]?.atEnd}
                  />
                </div>
              </div>

              <div className="relative">
                {/* Left gradient shadow indicator */}
                {!scrollPositions[category]?.atStart && (
                  <div
                    className="absolute left-0 top-0 bottom-0 w-16 z-10 pointer-events-none"
                    style={{
                      background:
                        "linear-gradient(to right, rgba(255,255,255,0.9), rgba(255,255,255,0))",
                    }}
                  />
                )}

                {/* Right gradient shadow indicator */}
                {!scrollPositions[category]?.atEnd &&
                  totalBadges > slidesToShow && (
                    <div
                      className="absolute right-0 top-0 bottom-0 w-16 z-10 pointer-events-none"
                      style={{
                        background:
                          "linear-gradient(to left, rgba(255,255,255,0.9), rgba(255,255,255,0))",
                      }}
                    />
                  )}

                <Carousel
                  ref={carouselRefs.current[category]}
                  slidesToShow={4}
                  slidesToScroll={1}
                  dots={false}
                  infinite={false}
                  swipeToSlide={true}
                  draggable={true}
                  afterChange={(current) =>
                    handleAfterChange(
                      current,
                      category,
                      totalBadges,
                      slidesToShow
                    )
                  }
                  responsive={[
                    {
                      breakpoint: 1280,
                      settings: {
                        slidesToShow: 3,
                      },
                    },
                    {
                      breakpoint: 1024,
                      settings: {
                        slidesToShow: 2,
                      },
                    },
                    {
                      breakpoint: 640,
                      settings: {
                        slidesToShow: 1,
                      },
                    },
                  ]}
                >
                  {(badgeList as BadgeItem[]).map((badge) => (
                    <div key={badge.id} className="px-2 py-6">
                      <div
                        className={cn(
                          "p-4 h-full flex items-center rounded-lg border shadow-lg transition-all duration-200 hover:-translate-y-1",
                          getTierBorderShadow(badge.tier || "").border,
                          "shadow-sm hover:shadow-md",
                          getTierBorderShadow(badge.tier || "").background,
                          getTierBorderShadow(badge.tier || "").texture,
                          getTierBorderShadow(badge.tier || "").text,
                          badge.isNext
                            ? "ring-2 ring-purple-500 ring-opacity-50"
                            : "",
                          !badge.unlocked ? "opacity-80" : ""
                        )}
                      >
                        <div className="flex items-center gap-4 h-full">
                          <div
                            className={`
                              relative w-16 h-16 rounded-full overflow-hidden flex items-center justify-center
                              ${!badge.unlocked ? "opacity-40 grayscale" : ""}
                              
                              
                            `}
                          >
                            {badge.icon ? (
                              <Image
                                src={badge.icon}
                                alt={badge.name}
                                fill
                                className="object-cover"
                              />
                            ) : (
                              <span className="text-white text-lg font-bold">
                                {badge.name.substring(0, 2).toUpperCase()}
                              </span>
                            )}

                            {badge.isNext && (
                              <div className="absolute -top-1 -right-1 bg-purple-600 text-white text-[10px] px-1.5 py-0.5 rounded-sm rotate-12 shadow-sm">
                                Next
                              </div>
                            )}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Title
                                level={5}
                                className="!m-0 !text-base truncate"
                              >
                                {badge.name}
                              </Title>
                              {badge.unlocked && (
                                <Badge
                                  status="success"
                                  className="relative top-px"
                                />
                              )}
                            </div>

                            <Text className="text-gray-600 text-sm line-clamp-2 w-full">
                              {badge.description}
                            </Text>

                            {badge.progress && !badge.unlocked && (
                              <div className="mt-2">
                                <div className="flex justify-between text-xs text-gray-500 mb-1">
                                  <span className="italic">Progress</span>
                                  <span>
                                    {badge.progress.current}/
                                    {badge.progress.total}
                                  </span>
                                </div>
                                <Progress
                                  percent={Math.round(
                                    (badge.progress.current /
                                      badge.progress.total) *
                                      100
                                  )}
                                  showInfo={false}
                                  size="small"
                                  strokeColor="#9810fa"
                                />
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </Carousel>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
