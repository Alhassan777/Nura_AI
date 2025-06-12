"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Empty, Spin, Tag, Avatar, Switch } from "antd";
import { PhoneOutlined, UserOutlined } from "@ant-design/icons";
import {
  useEmergencyContacts,
  useUpdateEmergencyContact,
} from "@/services/hooks/use-safety-network";

interface EmergencyContact {
  id: string;
  contact_id: string;
  relationship_type: string;
  is_emergency_contact: boolean;
  user_profile?: {
    email: string;
    full_name?: string;
  };
}

export const EmergencyContactsSection = () => {
  const { data: emergencyContacts, isLoading } = useEmergencyContacts();
  const updateEmergencyContactMutation = useUpdateEmergencyContact();

  const handleToggleEmergencyStatus = (
    contactId: string,
    isEmergency: boolean
  ) => {
    updateEmergencyContactMutation.mutate({
      contactId,
      data: { is_emergency_contact: isEmergency },
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PhoneOutlined className="text-red-500" />
            <span>Emergency Contacts</span>
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
          <PhoneOutlined className="text-red-500" />
          <span>Emergency Contacts</span>
          <Tag color="red" className="ml-2">
            Quick Access
          </Tag>
        </CardTitle>
        <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
          These contacts can be quickly reached during crisis situations
        </p>
      </CardHeader>
      <CardContent>
        {!emergencyContacts || emergencyContacts.length === 0 ? (
          <Empty
            description="No emergency contacts set"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <div className="space-y-4">
            {emergencyContacts.map((contact) => (
              <div
                key={contact.id}
                className="flex items-center justify-between p-4 border rounded-lg bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
              >
                <div className="flex items-center space-x-4">
                  <Avatar
                    size={48}
                    icon={<UserOutlined />}
                    className="bg-red-500"
                  />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {contact.user_profile?.full_name ||
                        contact.user_profile?.email ||
                        "Unknown User"}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {contact.user_profile?.email}
                    </p>
                    <Tag color="red" className="mt-1">
                      {contact.relationship_type}
                    </Tag>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <Button
                    type="primary"
                    danger
                    icon={<PhoneOutlined />}
                    size="large"
                  >
                    Call Now
                  </Button>

                  <Switch
                    checked={contact.is_emergency_contact}
                    onChange={(checked) =>
                      handleToggleEmergencyStatus(contact.id, checked)
                    }
                    checkedChildren="Emergency"
                    unCheckedChildren="Regular"
                    loading={updateEmergencyContactMutation.isPending}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
