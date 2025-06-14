/**
 * Utility functions for notifications
 */

/**
 * Play a notification sound
 */
export const playNotificationSound = () => {
  if (typeof window !== "undefined" && "Audio" in window) {
    try {
      // Create a simple notification beep using Web Audio API
      const audioContext = new (window.AudioContext ||
        (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(
        0.01,
        audioContext.currentTime + 0.2
      );

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      console.warn("Could not play notification sound:", error);
    }
  }
};

/**
 * Trigger device vibration if supported
 */
export const vibrateDevice = (pattern: number | number[] = 200) => {
  if (
    typeof window !== "undefined" &&
    "navigator" in window &&
    "vibrate" in navigator
  ) {
    try {
      navigator.vibrate(pattern);
    } catch (error) {
      console.warn("Could not vibrate device:", error);
    }
  }
};

/**
 * Show browser notification if permission is granted
 */
export const showBrowserNotification = (
  title: string,
  options?: NotificationOptions
) => {
  if (typeof window !== "undefined" && "Notification" in window) {
    if (Notification.permission === "granted") {
      try {
        new Notification(title, {
          icon: "/favicon.ico",
          badge: "/favicon.ico",
          ...options,
        });
      } catch (error) {
        console.warn("Could not show browser notification:", error);
      }
    }
  }
};

/**
 * Request notification permission
 */
export const requestNotificationPermission =
  async (): Promise<NotificationPermission> => {
    if (typeof window !== "undefined" && "Notification" in window) {
      try {
        const permission = await Notification.requestPermission();
        return permission;
      } catch (error) {
        console.warn("Could not request notification permission:", error);
        return "denied";
      }
    }
    return "denied";
  };

/**
 * Check if notifications are supported and enabled
 */
export const areNotificationsSupported = (): boolean => {
  return typeof window !== "undefined" && "Notification" in window;
};

/**
 * Complete notification with sound, vibration, and browser notification
 */
export const triggerFullNotification = (
  title: string,
  message: string,
  options?: {
    playSound?: boolean;
    vibrate?: boolean;
    browserNotification?: boolean;
    vibrationPattern?: number | number[];
  }
) => {
  const {
    playSound = true,
    vibrate = true,
    browserNotification = true,
    vibrationPattern = [200, 100, 200],
  } = options || {};

  if (playSound) {
    playNotificationSound();
  }

  if (vibrate) {
    vibrateDevice(vibrationPattern);
  }

  if (browserNotification) {
    showBrowserNotification(title, {
      body: message,
      tag: "safety-invitation",
      requireInteraction: false,
    });
  }
};
