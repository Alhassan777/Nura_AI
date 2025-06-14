"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Empty, Spin, Tag, Avatar, Divider, App, Modal } from "antd";
import {
  UserAddOutlined,
  CheckOutlined,
  CloseOutlined,
  MailOutlined,
  UserOutlined,
  SettingOutlined,
  HeartOutlined,
  SafetyOutlined,
} from "@ant-design/icons";
import {
  usePendingInvitations,
  useAcceptInvitation,
  useRejectInvitation,
  useWhoAmIHelping,
} from "@/services/hooks/use-safety-invitations";
import { useInvitationNotifications } from "@/contexts/InvitationNotificationContext";
import { PermissionBuilder } from "./PermissionBuilder";

interface Invitation {
  id: string;
  status: "pending" | "accepted" | "declined";
  relationship_type: string;
  invitation_message?: string;
  requested_permissions: Record<string, any>;
  permission_summary?: {
    data_access: Array<{ name: string; description: string }>;
    alert_types: Array<{ name: string; description: string }>;
    privacy_level: string;
    total_permissions: number;
  };
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

interface HelpingRelationship {
  id: string;
  helping_user: {
    id: string;
    full_name?: string;
    display_name?: string;
    email: string;
    avatar_url?: string;
  };
  relationship_type: string;
  permissions_granted: Record<string, any>;
  communication_methods: string[];
  preferred_method: string;
  is_emergency_contact: boolean;
  priority_order: number;
  notes?: string;
  created_at: string;
  last_contacted_at?: string;
  last_contact_successful?: boolean;
  preferred_contact_time?: string;
  timezone: string;
}

export const InvitationsSection = () => {
  const { data: invitations, isLoading } = usePendingInvitations();
  const { data: helpingData, isLoading: helpingLoading } = useWhoAmIHelping();
  const acceptInvitationMutation = useAcceptInvitation();
  const rejectInvitationMutation = useRejectInvitation();
  const { checkForNewInvitations } = useInvitationNotifications();
  const { message } = App.useApp();

  // State for permission customization modal
  const [customizeModalVisible, setCustomizeModalVisible] = useState(false);
  const [selectedInvitation, setSelectedInvitation] =
    useState<Invitation | null>(null);
  const [customPermissions, setCustomPermissions] = useState<
    Record<string, any>
  >({});

  const handleAcceptInvitation = (
    invitation: Invitation,
    useCustomPermissions = false
  ) => {
    const permissionsToGrant = useCustomPermissions
      ? customPermissions
      : invitation.requested_permissions; // Accept exactly what was requested

    acceptInvitationMutation.mutate(
      {
        invitationId: invitation.id,
        data: {
          granted_permissions: permissionsToGrant,
        },
      },
      {
        onSuccess: () => {
          message.success("Invitation accepted successfully! 🎉");
          checkForNewInvitations(); // Refresh the invitation count
          setCustomizeModalVisible(false);
          setSelectedInvitation(null);
          setCustomPermissions({});
        },
        onError: (error: any) => {
          message.error("Failed to accept invitation. Please try again.");
          console.error("Error accepting invitation:", error);
        },
      }
    );
  };

  const handleCustomizePermissions = (invitation: Invitation) => {
    setSelectedInvitation(invitation);
    setCustomPermissions(invitation.requested_permissions || {});
    setCustomizeModalVisible(true);
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

  const renderPermissionSummary = (invitation: Invitation) => {
    const summary = invitation.permission_summary;
    if (!summary || summary.total_permissions === 0) {
      return (
        <div className="text-sm text-gray-500 italic">
          No specific permissions requested - basic profile access only
        </div>
      );
    }

    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Privacy Level: {summary.privacy_level}
          </span>
          <Tag
            color={
              summary.privacy_level === "minimal"
                ? "green"
                : summary.privacy_level === "moderate"
                ? "orange"
                : "red"
            }
          >
            {summary.total_permissions} permission(s)
          </Tag>
        </div>

        {summary.data_access && summary.data_access.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              Data Access:
            </p>
            <div className="flex flex-wrap gap-1">
              {summary.data_access.map((access, index) => (
                <Tag key={index} color="blue" className="text-xs">
                  {access.name}
                </Tag>
              ))}
            </div>
          </div>
        )}

        {summary.alert_types && summary.alert_types.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
              Alert Types:
            </p>
            <div className="flex flex-wrap gap-1">
              {summary.alert_types.map((alert, index) => (
                <Tag key={index} color="red" className="text-xs">
                  {alert.name}
                </Tag>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderHelpingPermissions = (permissions: Record<string, any>) => {
    if (!permissions || Object.keys(permissions).length === 0) {
      return (
        <div className="text-sm text-gray-500 italic">
          Basic permissions only
        </div>
      );
    }

    const permissionsList: string[] = [];

    if (permissions.can_see_location) permissionsList.push("Location Access");
    if (permissions.can_see_activities) permissionsList.push("Activity Access");
    if (permissions.alert_preferences?.crisis_alerts)
      permissionsList.push("Crisis Alerts");
    if (permissions.alert_preferences?.goal_reminders)
      permissionsList.push("Goal Reminders");

    return (
      <div className="flex flex-wrap gap-1">
        {permissionsList.map((permission, index) => (
          <Tag key={index} color="blue" className="text-xs">
            {permission}
          </Tag>
        ))}
        {permissionsList.length === 0 && (
          <span className="text-sm text-gray-500 italic">
            Custom permissions
          </span>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center py-8">
          <Spin size="large" />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <UserAddOutlined />
            <span>Safety Network Invitations</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Received Invitations */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <MailOutlined />
              <span>Received ({invitations?.received?.length || 0})</span>
            </h3>

            {!invitations?.received || invitations.received.length === 0 ? (
              <Empty
                description="No pending invitations"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              <div className="space-y-4">
                {invitations.received.map((invitation: Invitation) => (
                  <div
                    key={invitation.id}
                    className="p-6 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 shadow-sm hover:shadow-md transition-all duration-200"
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

                          {/* Permission Summary */}
                          <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            {renderPermissionSummary(invitation)}
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

                      <div className="flex flex-col space-y-2 ml-4">
                        <Button
                          type="primary"
                          icon={<CheckOutlined />}
                          onClick={() => handleAcceptInvitation(invitation)}
                          className="bg-green-600 hover:bg-green-700 border-green-600 hover:border-green-700 text-white font-medium px-4 py-2 rounded-lg"
                        >
                          Accept as Requested
                        </Button>
                        <Button
                          icon={<SettingOutlined />}
                          onClick={() => handleCustomizePermissions(invitation)}
                          className="border-blue-600 text-blue-600 hover:bg-blue-50 font-medium px-4 py-2 rounded-lg"
                        >
                          Customize & Accept
                        </Button>
                        <Button
                          danger
                          icon={<CloseOutlined />}
                          onClick={() => handleRejectInvitation(invitation.id)}
                          className="bg-red-600 hover:bg-red-700 border-red-600 hover:border-red-700 text-white font-medium px-4 py-2 rounded-lg"
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
                {invitations.sent.map((invitation: Invitation) => (
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

          <Divider />

          {/* Who Am I Helping Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <HeartOutlined className="text-pink-500" />
              <span>
                Who Am I Helping ({helpingData?.helping?.length || 0})
              </span>
            </h3>

            {helpingLoading ? (
              <div className="flex items-center justify-center py-4">
                <Spin />
              </div>
            ) : !helpingData?.helping || helpingData.helping.length === 0 ? (
              <Empty
                description="You are not currently helping anyone in their safety network"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              <div className="space-y-4">
                {helpingData.helping.map(
                  (relationship: HelpingRelationship) => (
                    <div
                      key={relationship.id}
                      className="p-6 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 shadow-sm hover:shadow-md transition-all duration-200"
                    >
                      <div className="flex items-start space-x-4">
                        <Avatar
                          size={56}
                          icon={<UserOutlined />}
                          src={relationship.helping_user.avatar_url}
                          className="bg-gradient-to-br from-pink-500 to-pink-600 text-white border-2 border-pink-100 dark:border-pink-800"
                        />
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                              {relationship.helping_user.full_name ||
                                relationship.helping_user.display_name ||
                                relationship.helping_user.email}
                            </h4>
                            {relationship.is_emergency_contact && (
                              <Tag color="red" className="text-xs font-medium">
                                <SafetyOutlined /> Emergency Contact
                              </Tag>
                            )}
                          </div>

                          <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                            {relationship.helping_user.email}
                          </p>

                          <div className="flex items-center space-x-2 mb-3">
                            <Tag color="purple" className="text-xs font-medium">
                              {relationship.relationship_type}
                            </Tag>
                            <Tag color="gray" className="text-xs font-medium">
                              Priority #{relationship.priority_order}
                            </Tag>
                          </div>

                          {/* Permissions Granted */}
                          <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Permissions You've Granted:
                            </p>
                            {renderHelpingPermissions(
                              relationship.permissions_granted
                            )}
                          </div>

                          {/* Communication Methods */}
                          <div className="mb-3">
                            <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                              Contact Methods:
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {relationship.communication_methods.map(
                                (method, index) => (
                                  <Tag
                                    key={index}
                                    color={
                                      method === relationship.preferred_method
                                        ? "green"
                                        : "default"
                                    }
                                    className="text-xs"
                                  >
                                    {method}
                                    {method === relationship.preferred_method &&
                                      " (Preferred)"}
                                  </Tag>
                                )
                              )}
                            </div>
                          </div>

                          {relationship.notes && (
                            <div className="p-3 bg-blue-50 dark:bg-blue-900 rounded-lg border-l-4 border-blue-500">
                              <p className="text-sm text-blue-700 dark:text-blue-200">
                                <strong>Notes:</strong> {relationship.notes}
                              </p>
                            </div>
                          )}

                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-3">
                            <div>
                              Added:{" "}
                              {new Date(
                                relationship.created_at
                              ).toLocaleDateString()}
                            </div>
                            {relationship.last_contacted_at && (
                              <div>
                                Last contact:{" "}
                                {new Date(
                                  relationship.last_contacted_at
                                ).toLocaleDateString()}
                                {relationship.last_contact_successful !==
                                  null && (
                                  <span
                                    className={
                                      relationship.last_contact_successful
                                        ? "text-green-600"
                                        : "text-red-600"
                                    }
                                  >
                                    {" "}
                                    (
                                    {relationship.last_contact_successful
                                      ? "Successful"
                                      : "Failed"}
                                    )
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Permission Customization Modal */}
      <Modal
        title="Customize Permissions"
        open={customizeModalVisible}
        onCancel={() => {
          setCustomizeModalVisible(false);
          setSelectedInvitation(null);
          setCustomPermissions({});
        }}
        footer={[
          <Button
            key="cancel"
            onClick={() => {
              setCustomizeModalVisible(false);
              setSelectedInvitation(null);
              setCustomPermissions({});
            }}
          >
            Cancel
          </Button>,
          <Button
            key="accept"
            type="primary"
            onClick={() =>
              selectedInvitation &&
              handleAcceptInvitation(selectedInvitation, true)
            }
            loading={acceptInvitationMutation.isPending}
          >
            Accept with Custom Permissions
          </Button>,
        ]}
        width={800}
        className="permission-modal"
      >
        {selectedInvitation && (
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">
                Invitation from{" "}
                {selectedInvitation.other_user?.full_name ||
                  selectedInvitation.other_user?.email}
              </h4>
              <p className="text-sm text-blue-700">
                You can modify what permissions to grant when accepting this
                invitation. You have complete control over what this person can
                access.
              </p>
            </div>

            <PermissionBuilder
              selectedPermissions={customPermissions}
              onPermissionsChange={setCustomPermissions}
              relationshipType={selectedInvitation.relationship_type}
            />
          </div>
        )}
      </Modal>
    </>
  );
};
