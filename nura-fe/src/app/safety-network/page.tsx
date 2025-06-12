"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "antd";
import {
  UserAddOutlined,
  TeamOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { SafetyNetworkList } from "@/components/safety-network/SafetyNetworkList";
import { AddContactModal } from "@/components/safety-network/AddContactModal";
import { EmergencyContactsSection } from "@/components/safety-network/EmergencyContactsSection";
import { InvitationsSection } from "@/components/safety-network/InvitationsSection";

export default function SafetyNetworkPage() {
  const [showAddContactModal, setShowAddContactModal] = useState(false);

  return (
    <div className="container mx-auto p-4 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Safety Network
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Build a support network of trusted contacts who can help during
            difficult times
          </p>
        </div>
        <Button
          type="primary"
          icon={<UserAddOutlined />}
          onClick={() => setShowAddContactModal(true)}
          size="large"
        >
          Add Contact
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Contacts
            </CardTitle>
            <TeamOutlined className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-</div>
            <p className="text-xs text-muted-foreground">
              People in your network
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Emergency Contacts
            </CardTitle>
            <WarningOutlined className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-</div>
            <p className="text-xs text-muted-foreground">
              Quick access contacts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Pending Invitations
            </CardTitle>
            <UserAddOutlined className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">-</div>
            <p className="text-xs text-muted-foreground">Awaiting responses</p>
          </CardContent>
        </Card>
      </div>

      {/* Emergency Contacts Section */}
      <EmergencyContactsSection />

      {/* Safety Network List */}
      <SafetyNetworkList />

      {/* Invitations Section */}
      <InvitationsSection />

      {/* Add Contact Modal */}
      <AddContactModal
        isOpen={showAddContactModal}
        onClose={() => setShowAddContactModal(false)}
      />
    </div>
  );
}
