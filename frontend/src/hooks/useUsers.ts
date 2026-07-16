import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  activateUser,
  adminResetPassword,
  changeUserRole,
  deactivateUser,
  listUsers,
} from '../api/endpoints/users';

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  });
}

export function useSetUserActive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, active }: { userId: number; active: boolean }) =>
      active ? activateUser(userId) : deactivateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

export function useChangeUserRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: string }) =>
      changeUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}

export function useAdminResetPassword() {
  return useMutation({
    mutationFn: ({ userId, newPassword }: { userId: number; newPassword: string }) =>
      adminResetPassword(userId, newPassword),
  });
}
