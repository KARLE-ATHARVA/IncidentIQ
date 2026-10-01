import {
  useCallback,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  NotificationContext,
  type Notification,
  type NotificationType,
} from "./NotificationContext";

const AUTO_DISMISS_MS = 4500;

let notificationId = 0;

function NotificationIcon({
  type,
}: {
  type: NotificationType;
}) {
  switch (type) {
    case "success":
      return <span>✓</span>;

    case "error":
      return <span>!</span>;

    case "warning":
      return <span>!</span>;

    case "info":
      return <span>i</span>;
  }
}

function NotificationProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [notifications, setNotifications] = useState<
    Notification[]
  >([]);

  const dismiss = useCallback((id: number) => {
    setNotifications((current) =>
      current.filter(
        (notification) => notification.id !== id,
      ),
    );
  }, []);

  const push = useCallback(
    (
      type: NotificationType,
      title: string,
      message?: string,
    ) => {
      const id = ++notificationId;

      setNotifications((current) => [
        ...current,
        {
          id,
          type,
          title,
          message,
        },
      ]);

      window.setTimeout(() => {
        dismiss(id);
      }, AUTO_DISMISS_MS);
    },
    [dismiss],
  );

  const notify = useMemo(
    () => ({
      success: (
        title: string,
        message?: string,
      ) => {
        push("success", title, message);
      },

      error: (
        title: string,
        message?: string,
      ) => {
        push("error", title, message);
      },

      warning: (
        title: string,
        message?: string,
      ) => {
        push("warning", title, message);
      },

      info: (
        title: string,
        message?: string,
      ) => {
        push("info", title, message);
      },
    }),
    [push],
  );

  const contextValue = useMemo(
    () => ({
      notify,
    }),
    [notify],
  );

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}

      <div
        className="notification-container"
        aria-live="polite"
        aria-atomic="false"
      >
        {notifications.map((notification) => (
          <article
            key={notification.id}
            className={`notification notification-${notification.type}`}
          >
            <div className="notification-icon">
              <NotificationIcon
                type={notification.type}
              />
            </div>

            <div className="notification-content">
              <strong>
                {notification.title}
              </strong>

              {notification.message && (
                <p>{notification.message}</p>
              )}
            </div>

            <button
              type="button"
              className="notification-close"
              aria-label="Dismiss notification"
              onClick={() =>
                dismiss(notification.id)
              }
            >
              ×
            </button>
          </article>
        ))}
      </div>
    </NotificationContext.Provider>
  );
}

export default NotificationProvider;