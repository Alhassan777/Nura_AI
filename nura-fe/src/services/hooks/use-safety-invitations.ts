import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  safetyInvitationsApi,
  SearchUsersPayload,
  SendInvitationPayload,
  AcceptInvitationPayload,
} from "../apis/safety-invitations";

// Search users for invitations
export const useSearchUsers = () => {
  return useMutation({
    mutationFn: (data: SearchUsersPayload) =>
      safetyInvitationsApi.searchUsers(data),
  });
};

// Get pending invitations
export const usePendingInvitations = () => {
  const incomingQuery = useQuery({
    queryKey: ["pending-invitations", "incoming"],
    queryFn: () =>
      safetyInvitationsApi.getPendingInvitations("incoming", "pending"),
  });

  const outgoingQuery = useQuery({
    queryKey: ["pending-invitations", "outgoing"],
    queryFn: () =>
      safetyInvitationsApi.getPendingInvitations("outgoing", "pending"),
  });

  return {
    data: {
      received: incomingQuery.data?.invitations || [],
      sent: outgoingQuery.data?.invitations || [],
    },
    isLoading: incomingQuery.isLoading || outgoingQuery.isLoading,
    error: incomingQuery.error || outgoingQuery.error,
  };
};

// Send invitation
export const useSendInvitation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SendInvitationPayload) =>
      safetyInvitationsApi.sendInvitation(data),
    onSuccess: () => {
      // Invalidate pending invitations to show the new sent invitation
      queryClient.invalidateQueries({ queryKey: ["pending-invitations"] });
    },
  });
};

// Accept invitation
export const useAcceptInvitation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      invitationId,
      data,
    }: {
      invitationId: string;
      data: AcceptInvitationPayload;
    }) => safetyInvitationsApi.acceptInvitation(invitationId, data),
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["pending-invitations"] });
      queryClient.invalidateQueries({ queryKey: ["safety-network"] });
      queryClient.invalidateQueries({ queryKey: ["emergency-contacts"] });
    },
  });
};

// Reject invitation
export const useRejectInvitation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationId: string) =>
      safetyInvitationsApi.rejectInvitation(invitationId),
    onSuccess: () => {
      // Invalidate pending invitations
      queryClient.invalidateQueries({ queryKey: ["pending-invitations"] });
    },
  });
};
