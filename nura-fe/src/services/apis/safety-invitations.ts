import { axiosInstance } from "./index";

export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
}

export interface Invitation {
  id: string;
  sender_id: string;
  recipient_id: string;
  recipient_email: string;
  relationship_type: string;
  requested_permissions: object;
  granted_permissions?: object;
  invitation_message?: string;
  status: "pending" | "accepted" | "rejected";
  created_at: string;
  updated_at: string;
  sender_profile?: User;
}

export interface SearchUsersPayload {
  query: string;
  limit?: number;
}

export interface SendInvitationPayload {
  recipient_email: string;
  relationship_type: string;
  requested_permissions: object;
  invitation_message?: string;
}

export interface AcceptInvitationPayload {
  granted_permissions: object;
}

// Safety Invitations API functions
export const safetyInvitationsApi = {
  // Search users for invitations
  searchUsers: (data: SearchUsersPayload) =>
    axiosInstance
      .post("/safety-invitations/search/users", data)
      .then((res) => res.data),

  // Send safety network invitation
  sendInvitation: (data: SendInvitationPayload) =>
    axiosInstance
      .post("/safety-invitations/invite", data)
      .then((res) => res.data),

  // Get pending invitations (sent and received)
  getPendingInvitations: () =>
    axiosInstance.get("/safety-invitations/pending").then((res) => res.data),

  // Accept invitation
  acceptInvitation: (invitationId: string, data: AcceptInvitationPayload) =>
    axiosInstance
      .post(`/safety-invitations/${invitationId}/accept`, data)
      .then((res) => res.data),

  // Reject invitation
  rejectInvitation: (invitationId: string) =>
    axiosInstance
      .post(`/safety-invitations/${invitationId}/reject`)
      .then((res) => res.data),
};
