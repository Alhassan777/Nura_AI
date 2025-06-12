"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Empty, Spin, Tag, Avatar, Divider } from "antd";
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

interface Invitation {
  id: string;
  sender_id: string;
  recipient_email: string;
  relationship_type: string;
  invitation_message?: string;
  status: "pending" | "accepted" | "rejected";
  created_at: string;
  sender_profile?: {
    email: string;
    full_name?: string;
  };
}

export const InvitationsSection = () => {
  const { data: invitations, isLoading } = usePendingInvitations();
  const acceptInvitationMutation = useAcceptInvitation();
  const rejectInvitationMutation = useRejectInvitation();

  const handleAcceptInvitation = (invitationId: string) => {
    acceptInvitationMutation.mutate({
      invitationId,
      data: {
        granted_permissions: {
          can_view_mood: true,
          can_receive_alerts: true,
        },
      },
    });
  };

  const handleRejectInvitation = (invitationId: string) => {
    rejectInvitationMutation.mutate(invitationId);
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
                  className="p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      <Avatar
                        size={48}
                        icon={<UserOutlined />}
                        className="bg-blue-500"
                      />
                      <div>
                        <h4 className="font-semibold text-gray-900 dark:text-white">
                          {invitation.sender_profile?.full_name ||
                            invitation.sender_profile?.email ||
                            "Unknown User"}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300">
                          {invitation.sender_profile?.email}
                        </p>
                        <Tag color="blue" className="mt-1">
                          {invitation.relationship_type}
                        </Tag>
                        {invitation.invitation_message && (
                          <p className="text-sm text-gray-700 dark:text-gray-200 mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded">
                            "{invitation.invitation_message}"
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <Button
                        type="primary"
                        icon={<CheckOutlined />}
                        onClick={() => handleAcceptInvitation(invitation.id)}
                        // loading={acceptInvitationMutation.isPending}
                      >
                        Accept
                      </Button>
                      <Button
                        danger
                        icon={<CloseOutlined />}
                        onClick={() => handleRejectInvitation(invitation.id)}
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
                  className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-800"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">
                        {invitation.recipient_email}
                      </h4>
                      <div className="flex items-center space-x-2 mt-1">
                        <Tag color="blue">{invitation.relationship_type}</Tag>
                        <Tag color="orange">Pending Response</Tag>
                      </div>
                    </div>

                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      Sent{" "}
                      {new Date(invitation.created_at).toLocaleDateString()}
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
