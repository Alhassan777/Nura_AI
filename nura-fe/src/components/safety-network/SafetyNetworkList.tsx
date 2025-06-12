"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, Empty, Spin, Tag, Avatar } from "antd";
import { DeleteOutlined, UserOutlined, PhoneOutlined } from "@ant-design/icons";
import {
  useSafetyNetwork,
  useRemoveContact,
} from "@/services/hooks/use-safety-network";

interface Contact {
  id: string;
  contact_id: string;
  relationship_type: string;
  is_emergency_contact: boolean;
  user_profile?: {
    email: string;
    full_name?: string;
  };
}

export const SafetyNetworkList = () => {
  const { data: contacts, isLoading } = useSafetyNetwork();
  const removeContactMutation = useRemoveContact();

  const handleRemoveContact = (contactId: string) => {
    removeContactMutation.mutate(contactId);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Your Safety Network</CardTitle>
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
        <CardTitle>Your Safety Network</CardTitle>
      </CardHeader>
      <CardContent>
        {!contacts || contacts.length === 0 ? (
          <Empty
            description="No contacts in your safety network yet"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <div className="space-y-4">
            {contacts.map((contact) => (
              <div
                key={contact.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <div className="flex items-center space-x-4">
                  <Avatar
                    size={48}
                    icon={<UserOutlined />}
                    className="bg-blue-500"
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
                    <div className="flex items-center space-x-2 mt-1">
                      <Tag color="blue">{contact.relationship_type}</Tag>
                      {contact.is_emergency_contact && (
                        <Tag color="red" icon={<PhoneOutlined />}>
                          Emergency Contact
                        </Tag>
                      )}
                    </div>
                  </div>
                </div>

                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleRemoveContact(contact.id)}
                  loading={removeContactMutation.isPending}
                >
                  Remove
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
