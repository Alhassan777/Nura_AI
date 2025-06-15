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
  contact_user_id?: string;
  relationship_type: string;
  is_emergency_contact: boolean;
  created_at: string;
  updated_at: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone_number?: string;
  priority_order: number;
  is_active: boolean;
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
                className="flex items-center justify-between p-6 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 bg-white dark:bg-gray-900 shadow-sm hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-center space-x-4">
                  <Avatar
                    size={56}
                    icon={<UserOutlined />}
                    className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-2 border-blue-100 dark:border-blue-800"
                  />
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                      {contact.full_name ||
                        `${contact.first_name || ""} ${
                          contact.last_name || ""
                        }`.trim() ||
                        contact.email ||
                        "Unknown User"}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                      {contact.email || "No email available"}
                    </p>
                    <div className="flex items-center space-x-2">
                      <Tag
                        color="blue"
                        className="text-xs font-medium px-2 py-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-0"
                      >
                        {contact.relationship_type}
                      </Tag>
                      {contact.is_emergency_contact && (
                        <Tag
                          color="red"
                          icon={<PhoneOutlined />}
                          className="text-xs font-medium px-2 py-1 rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-0"
                        >
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
                  className="flex items-center space-x-2 px-4 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  <span className="hidden sm:inline">Remove</span>
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
