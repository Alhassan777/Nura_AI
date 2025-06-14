"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Empty, Spin, Tag, Avatar, Divider, App } from "antd";
import {
  UserAddOutlined,
  CheckOutlined,
  CloseOutlined,
  MailOutlined,
  UserOutlined,
} from "@ant-design/icons";
import {
  usePendingInvitations,
  useAcceptInvitation,
  useRejectInvitation,
} from "@/services/hooks/use-safety-invitations";
import { useInvitationNotifications } from "@/contexts/InvitationNotificationContext";

interface Invitation {
  id: string;
  status: "pending" | "accepted" | "declined";
  relationship_type: string;
  invitation_message?: string;
  requested_permissions: object;
  created_at: string;
  expires_at?: string;
  other_user?: {
    id: string;
    full_name?: string;
    display_name?: string;
    avatar_url?: string;
    verification_status: string;
    email?: string;
  };
  // For backward compatibility
  sender_id?: string;
  recipient_email?: string;
  sender_profile?: {
    email: string;
    full_name?: string;
  };
}

export const InvitationsSection = () => {
  const { data: invitations, isLoading } = usePendingInvitations();
  const acceptInvitationMutation = useAcceptInvitation();
  const rejectInvitationMutation = useRejectInvitation();
  const { checkForNewInvitations } = useInvitationNotifications();
  const { message } = App.useApp();

  const handleAcceptInvitation = (invitationId: string) => {
    acceptInvitationMutation.mutate(
      {
        invitationId,
        data: {
          granted_permissions: {
            can_view_mood: true,
            can_receive_alerts: true,
          },
        },
      },
      {
        onSuccess: () => {
          message.success("Invitation accepted successfully! 🎉");
          checkForNewInvitations(); // Refresh the invitation count
        },
        onError: (error: any) => {
          message.error("Failed to accept invitation. Please try again.");
          console.error("Error accepting invitation:", error);
        },
      }
    );
  };

  const handleRejectInvitation = (invitationId: string) => {
    rejectInvitationMutation.mutate(invitationId, {
      onSuccess: () => {
        message.info("Invitation declined.");
        checkForNewInvitations(); // Refresh the invitation count
      },
      onError: (error: any) => {
        message.error("Failed to decline invitation. Please try again.");
        console.error("Error rejecting invitation:", error);
      },
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MailOutlined />
            <span>Invitations</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex justify-center py-8">
          <Spin size="large" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <MailOutlined />
          <span>Invitations</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Received Invitations */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <UserAddOutlined />
            <span>Received ({invitations?.received?.length || 0})</span>
          </h3>

          {!invitations?.received || invitations.received.length === 0 ? (
            <Empty
              description="No pending invitations"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <div className="space-y-4">
              {invitations.received.map((invitation) => (
                <div
                  key={invitation.id}
                  className="p-6 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <Avatar
                        size={56}
                        icon={<UserOutlined />}
                        className="bg-gradient-to-br from-green-500 to-green-600 text-white border-2 border-green-100 dark:border-green-800"
                      />
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                          {invitation.other_user?.full_name ||
                            invitation.other_user?.display_name ||
                            invitation.sender_profile?.full_name ||
                            invitation.sender_profile?.email ||
                            "Unknown User"}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                          {invitation.other_user?.email ||
                            invitation.sender_profile?.email ||
                            "No email available"}
                        </p>
                        <div className="flex items-center space-x-2 mb-3">
                          <Tag
                            color="blue"
                            className="text-xs font-medium px-3 py-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-0"
                          >
                            {invitation.relationship_type}
                          </Tag>
                        </div>
                        {invitation.invitation_message && (
                          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-blue-500">
                            <p className="text-sm text-gray-700 dark:text-gray-200 italic">
                              "{invitation.invitation_message}"
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3 ml-4">
                      <Button
                        type="primary"
                        icon={<CheckOutlined />}
                        onClick={() => handleAcceptInvitation(invitation.id)}
                        className="bg-green-600 hover:bg-green-700 border-green-600 hover:border-green-700 text-white font-medium px-4 py-2 rounded-lg"
                        // loading={acceptInvitationMutation.isPending}
                      >
                        Accept
                      </Button>
                      <Button
                        danger
                        icon={<CloseOutlined />}
                        onClick={() => handleRejectInvitation(invitation.id)}
                        className="bg-red-600 hover:bg-red-700 border-red-600 hover:border-red-700 text-white font-medium px-4 py-2 rounded-lg"
                        // loading={rejectInvitationMutation.isPending}
                      >
                        Decline
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <Divider />

        {/* Sent Invitations */}
        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <MailOutlined />
            <span>Sent ({invitations?.sent?.length || 0})</span>
          </h3>

          {!invitations?.sent || invitations.sent.length === 0 ? (
            <Empty
              description="No sent invitations"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <div className="space-y-4">
              {invitations.sent.map((invitation) => (
                <div
                  key={invitation.id}
                  className="p-6 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <Avatar
                        size={48}
                        icon={<UserOutlined />}
                        className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-2 border-orange-100 dark:border-orange-800"
                      />
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                          {invitation.recipient_email}
                        </h4>
                        <div className="flex items-center space-x-2 mb-2">
                          <Tag
                            color="blue"
                            className="text-xs font-medium px-3 py-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-0"
                          >
                            {invitation.relationship_type}
                          </Tag>
                          <Tag
                            color="orange"
                            className="text-xs font-medium px-3 py-1 rounded-full bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 border-0"
                          >
                            Pending Response
                          </Tag>
                        </div>
                      </div>
                    </div>

                    <div className="text-sm text-gray-500 dark:text-gray-400 text-right">
                      <div className="font-medium">Sent</div>
                      <div>
                        {new Date(invitation.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
