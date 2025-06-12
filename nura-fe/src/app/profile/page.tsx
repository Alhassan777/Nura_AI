"use client";

import { useAuth } from "@/contexts/AuthContext";
import { Card } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { Button, Spin, Badge, Alert, App, Tooltip, Divider } from "antd";
import { useState } from "react";
import {
  UserIcon,
  MailIcon,
  CheckCircleIcon,
  XCircleIcon,
  CalendarIcon,
  ShieldCheckIcon,
  KeyIcon,
  LogOutIcon,
  EditIcon,
  CopyIcon,
} from "lucide-react";
import { useUser } from "@/services/hooks/user";
import EditProfileModal from "@/components/EditProfileModal";

export default function ProfilePage() {
  const { user: authUser, logout } = useAuth();
  const { data: user, isLoading, error, refetch } = useUser();
  const [resendingEmail, setResendingEmail] = useState(false);
  const [copiedUserId, setCopiedUserId] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const { message } = App.useApp();

  // Use auth user if available, fallback to user hook data
  const currentUser = authUser || user;

  const handleResendVerificationEmail = async () => {
    if (!currentUser?.email) return;

    try {
      setResendingEmail(true);
      // TODO: Implement email verification resend with backend
      message.info(
        "Email verification will be implemented with backend integration"
      );
    } catch (error: any) {
      console.error("Error sending verification email:", error);
      message.error(error.message || "Failed to send verification email");
    } finally {
      setResendingEmail(false);
    }
  };

  const copyUserId = () => {
    if (currentUser?.id) {
      navigator.clipboard.writeText(currentUser.id);
      setCopiedUserId(true);
      message.success("User ID copied to clipboard!");
      setTimeout(() => setCopiedUserId(false), 2000);
    }
  };

  const handleEditProfile = () => {
    setEditModalVisible(true);
  };

  const handleEditSuccess = () => {
    // Refresh user data
    refetch();
    message.success("Profile updated successfully!");
  };

  const handleLogout = async () => {
    try {
      await logout();
      message.info("You have been signed out");
    } catch (error) {
      console.error("Logout error:", error);
      message.error("Error signing out");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spin size="large" tip="Loading user information..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Alert
          message="Error Loading Profile"
          description={
            error.message || "Something went wrong while loading your profile."
          }
          type="error"
          showIcon
        />
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <div className="text-center space-y-4">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <XCircleIcon className="h-12 w-12 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Not Logged In</h2>
          <p className="text-gray-600 max-w-md">
            You need to be logged in to view your profile. Please log in to
            continue.
          </p>
          <Button type="primary" size="large" href="/login" className="mt-6">
            Log in to Your Account
          </Button>
        </div>
      </div>
    );
  }

  const isVerified = currentUser.is_verified;

  return (
    <div className="h-full w-full bg-white">
      <div className="mx-auto md:p-6 p-0">
        <div className="grid grid-cols-1 lg:grid-cols-3 md:gap-6 gap-0">
          {/* Left column - User info */}
          <div className="lg:col-span-1">
            <div className="md:p-6 p-0 flex flex-col items-center text-center md:bg-gray-50 md:rounded-lg md:border md:border-gray-200 md:shadow-xs">
              <Avatar className="h-24 w-24 bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center mb-4">
                {currentUser.avatar_url ? (
                  <img
                    src={currentUser.avatar_url}
                    alt={
                      currentUser.display_name ||
                      currentUser.full_name ||
                      currentUser.email ||
                      "User"
                    }
                    className="h-full w-full object-cover rounded-full"
                  />
                ) : (
                  <UserIcon className="h-12 w-12 text-white" />
                )}
              </Avatar>

              <h2 className="text-xl font-bold text-gray-900 mt-2">
                {currentUser.display_name ||
                  currentUser.full_name ||
                  currentUser.email?.split("@")[0] ||
                  "User"}
              </h2>

              <div className="mt-4 flex items-center justify-center">
                {isVerified ? (
                  <Badge
                    status="success"
                    text={
                      <div className="flex items-center gap-1 text-green-600 font-medium">
                        <ShieldCheckIcon className="h-4 w-4 animate-pulse" />
                        <span>Verified Account</span>
                      </div>
                    }
                  />
                ) : (
                  <Badge
                    status="warning"
                    text={
                      <div className="flex items-center gap-1 text-orange-600 font-medium">
                        <XCircleIcon className="h-4 w-4" />
                        <span>Unverified</span>
                      </div>
                    }
                  />
                )}
              </div>

              {!isVerified && (
                <Button
                  type="primary"
                  size="middle"
                  onClick={handleResendVerificationEmail}
                  loading={resendingEmail}
                  className="bg-blue-600 hover:bg-blue-700 border-blue-600 mt-4"
                  icon={<MailIcon className="h-4 w-4" />}
                >
                  Verify Email
                </Button>
              )}

              <div className="mt-6 space-y-4 w-full">
                <Button
                  type="default"
                  size="large"
                  icon={<EditIcon className="h-4 w-4" />}
                  className="w-full"
                  onClick={handleEditProfile}
                >
                  Edit Profile
                </Button>

                <Button
                  type="default"
                  danger
                  size="large"
                  onClick={handleLogout}
                  icon={<LogOutIcon className="h-4 w-4" />}
                  className="w-full"
                >
                  Sign Out
                </Button>
              </div>
            </div>

            <Divider className="!block md:!hidden  my-6" />
          </div>

          {/* Right column - User details */}
          <div className="lg:col-span-2">
            <div className="md:p-6 p-0 md:bg-gray-50 md:rounded-lg md:border md:border-gray-200 md:shadow-xs">
              <h3 className="text-xl font-semibold mb-6 text-gray-800">
                Account Information
              </h3>

              <div className="space-y-6">
                {/* Email */}
                <div className="flex items-start md:p-4 p-0 lg:bg-white lg:rounded-lg lg:border lg:border-gray-200 lg:shadow-xs">
                  <div className="p-2 bg-blue-100 rounded-lg mr-4">
                    <MailIcon className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-500">Email Address</p>
                    <p className="font-medium text-gray-900">
                      {currentUser.email}
                    </p>
                  </div>
                </div>

                <Divider className="block my-0" />

                {/* User ID */}
                <div className="flex items-start md:p-4 p-0 lg:bg-white lg:rounded-lg lg:border lg:border-gray-200 lg:shadow-xs">
                  <div className="p-2 bg-purple-100 rounded-lg mr-4">
                    <KeyIcon className="h-5 w-5 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-500">User ID</p>
                    <div className="flex items-center">
                      <code className="font-bold bg-gray-100 px-2 py-1 rounded-md text-sm text-gray-900 mr-2">
                        {currentUser.id.substring(0, 8)}...
                        {currentUser.id.substring(currentUser.id.length - 4)}
                      </code>
                      <Tooltip
                        title={copiedUserId ? "Copied!" : "Copy User ID"}
                      >
                        <Button
                          type="text"
                          icon={<CopyIcon className="h-4 w-4" />}
                          onClick={copyUserId}
                          className="text-gray-500 hover:text-gray-700"
                        />
                      </Tooltip>
                    </div>
                  </div>
                </div>

                <Divider className="block my-0" />

                {/* Display Name */}
                {currentUser.display_name && (
                  <>
                    <div className="flex items-start md:p-4 p-0 lg:bg-white lg:rounded-lg lg:border lg:border-gray-200 lg:shadow-xs">
                      <div className="p-2 bg-green-100 rounded-lg mr-4">
                        <UserIcon className="h-5 w-5 text-green-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-500">Display Name</p>
                        <p className="font-medium text-gray-900">
                          {currentUser.display_name}
                        </p>
                      </div>
                    </div>
                    <Divider className="block my-0" />
                  </>
                )}

                {/* Bio */}
                {currentUser.bio && (
                  <>
                    <div className="flex items-start md:p-4 p-0 lg:bg-white lg:rounded-lg lg:border lg:border-gray-200 lg:shadow-xs">
                      <div className="p-2 bg-indigo-100 rounded-lg mr-4">
                        <EditIcon className="h-5 w-5 text-indigo-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-500">Bio</p>
                        <p className="text-gray-900">{currentUser.bio}</p>
                      </div>
                    </div>
                    <Divider className="block my-0" />
                  </>
                )}

                {/* Member Since */}
                {currentUser.created_at && (
                  <div className="flex items-start md:p-4 p-0 lg:bg-white lg:rounded-lg lg:border lg:border-gray-200 lg:shadow-xs">
                    <div className="p-2 bg-yellow-100 rounded-lg mr-4">
                      <CalendarIcon className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-500">Member Since</p>
                      <p className="font-medium text-gray-900">
                        {new Date(currentUser.created_at).toLocaleDateString(
                          "en-US",
                          {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          }
                        )}
                      </p>
                    </div>
                  </div>
                )}

                <Divider className="block my-0" />

                {/* Stats Section */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="md:p-4 p-0 lg:bg-white lg:rounded-lg lg:border lg:border-gray-200 lg:shadow-xs text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {currentUser.xp || 0}
                    </p>
                    <p className="text-sm text-gray-500">Experience Points</p>
                  </div>
                  <div className="md:p-4 p-0 lg:bg-white lg:rounded-lg lg:border lg:border-gray-200 lg:shadow-xs text-center">
                    <p className="text-2xl font-bold text-green-600">
                      {currentUser.current_streak || 0}
                    </p>
                    <p className="text-sm text-gray-500">Day Streak</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Email Verification Alert - Only show if not verified */}
        {!isVerified && (
          <div className="mt-6">
            <Alert
              message={
                <span className="font-semibold text-orange-900">
                  Email Verification Required
                </span>
              }
              description={
                <div className="mt-2">
                  <p className="text-orange-800 mb-3">
                    Please verify your email address to unlock all features and
                    ensure account security.
                  </p>
                  <Button
                    type="primary"
                    size="middle"
                    onClick={handleResendVerificationEmail}
                    loading={resendingEmail}
                    className="bg-orange-600 hover:bg-orange-700 border-orange-600"
                    icon={<MailIcon className="h-4 w-4" />}
                  >
                    Resend Verification Email
                  </Button>
                </div>
              }
              type="warning"
              showIcon
              icon={<XCircleIcon className="h-5 w-5 text-orange-600" />}
              className="border-orange-200 bg-orange-50"
            />
          </div>
        )}
      </div>

      {/* Edit Profile Modal */}
      <EditProfileModal
        visible={editModalVisible}
        onClose={() => setEditModalVisible(false)}
        onSuccess={handleEditSuccess}
      />
    </div>
  );
}
