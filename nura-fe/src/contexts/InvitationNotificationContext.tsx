"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useRef,
} from "react";
import { message } from "antd";
import { safetyInvitationsApi } from "@/services/apis/safety-invitations";
import { useAuth } from "./AuthContext";
import { triggerFullNotification } from "@/utils/notification-utils";

interface Invitation {
  id: string;
  status: "pending" | "accepted" | "declined";
  relationship_type: string;
  invitation_message?: string;
  created_at: string;
  other_user?: {
    id: string;
    full_name?: string;
    display_name?: string;
    email?: string;
  };
}

interface InvitationNotificationContextType {
  hasNewInvitations: boolean;
  newInvitationsCount: number;
  markNotificationsAsRead: () => void;
  checkForNewInvitations: () => Promise<void>;
}

const InvitationNotificationContext = createContext<
  InvitationNotificationContextType | undefined
>(undefined);

export const useInvitationNotifications = () => {
  const context = useContext(InvitationNotificationContext);
  if (!context) {
    throw new Error(
      "useInvitationNotifications must be used within InvitationNotificationProvider"
    );
  }
  return context;
};

interface InvitationNotificationProviderProps {
  children: React.ReactNode;
}

export const InvitationNotificationProvider: React.FC<
  InvitationNotificationProviderProps
> = ({ children }) => {
  const { user } = useAuth();
  const [hasNewInvitations, setHasNewInvitations] = useState(false);
  const [newInvitationsCount, setNewInvitationsCount] = useState(0);
  const [lastCheckedInvitations, setLastCheckedInvitations] = useState<
    Set<string>
  >(new Set());
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const [messageApi, contextHolder] = message.useMessage();

  const showInvitationToast = (invitation: Invitation) => {
    const senderName =
      invitation.other_user?.full_name ||
      invitation.other_user?.display_name ||
      invitation.other_user?.email ||
      "Someone";

    messageApi.open({
      type: "info",
      content: (
        <div className="flex flex-col">
          <div className="font-semibold text-blue-800">
            New Safety Network Invitation! 🤝
          </div>
          <div className="text-sm text-gray-600 mt-1">
            <strong>{senderName}</strong> wants to join your safety network as a{" "}
            <strong>{invitation.relationship_type}</strong>
          </div>
          {invitation.invitation_message && (
            <div className="text-xs text-gray-500 mt-2 italic">
              "{invitation.invitation_message}"
            </div>
          )}
          <div className="text-xs text-blue-600 mt-2">
            Check your Safety Network page to respond
          </div>
        </div>
      ),
      duration: 8, // Show for 8 seconds
      style: {
        marginTop: "20vh",
      },
    });
  };

  const checkForNewInvitations = async () => {
    if (!user) return;

    try {
      const response = await safetyInvitationsApi.getPendingInvitations(
        "incoming",
        "pending"
      );
      const currentInvitations = response.invitations || [];

      // Find new invitations by comparing with last checked set
      const newInvitations = currentInvitations.filter(
        (invitation: Invitation) => !lastCheckedInvitations.has(invitation.id)
      );

      // Update state
      setNewInvitationsCount(currentInvitations.length);
      setHasNewInvitations(currentInvitations.length > 0);

      // Show toast notifications for new invitations
      if (newInvitations.length > 0 && lastCheckedInvitations.size > 0) {
        // Only show toasts if we had previous data (prevents showing on first load)
        newInvitations.forEach((invitation: Invitation) => {
          const senderName =
            invitation.other_user?.full_name ||
            invitation.other_user?.display_name ||
            invitation.other_user?.email ||
            "Someone";

          showInvitationToast(invitation);

          // Trigger full notification (sound, vibration, browser notification)
          triggerFullNotification(
            "New Safety Network Invitation! 🤝",
            `${senderName} wants to join your safety network as a ${invitation.relationship_type}`,
            {
              playSound: true,
              vibrate: true,
              browserNotification: true,
              vibrationPattern: [200, 100, 200, 100, 200],
            }
          );
        });
      }

      // Update the set of known invitation IDs
      const currentInvitationIds = new Set<string>(
        currentInvitations.map((inv: Invitation) => inv.id)
      );
      setLastCheckedInvitations(currentInvitationIds);
    } catch (error) {
      console.error("Error checking for new invitations:", error);
    }
  };

  const markNotificationsAsRead = () => {
    setHasNewInvitations(false);
    // Keep the count but mark as read
  };

  // Set up periodic checking when user is logged in
  useEffect(() => {
    if (!user) {
      // Clear interval and reset state when user logs out
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setHasNewInvitations(false);
      setNewInvitationsCount(0);
      setLastCheckedInvitations(new Set());
      return;
    }

    // Initial check
    checkForNewInvitations();

    // Set up interval to check every 30 seconds
    intervalRef.current = setInterval(checkForNewInvitations, 30000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [user]);

  // Enhanced check when user becomes active (page focus)
  useEffect(() => {
    const handleFocus = () => {
      if (user) {
        checkForNewInvitations();
      }
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [user]);

  const contextValue: InvitationNotificationContextType = {
    hasNewInvitations,
    newInvitationsCount,
    markNotificationsAsRead,
    checkForNewInvitations,
  };

  return (
    <InvitationNotificationContext.Provider value={contextValue}>
      {contextHolder}
      {children}
    </InvitationNotificationContext.Provider>
  );
};
