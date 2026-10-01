import { createContext } from "react";

export type NotificationType =
  | "success"
  | "error"
  | "warning"
  | "info";

export interface Notification {
  id: number;
  type: NotificationType;
  title: string;
  message?: string;
}

export interface NotificationContextValue {
  notify: {
    success: (title: string, message?: string) => void;
    error: (title: string, message?: string) => void;
    warning: (title: string, message?: string) => void;
    info: (title: string, message?: string) => void;
  };
}

export const NotificationContext =
  createContext<NotificationContextValue | null>(null);