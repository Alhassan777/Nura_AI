"use client";

import { redirect } from "next/navigation";
import { SignupFormData } from "@/components/auth/types";
import { LoginFormData } from "@/components/auth/LoginForm";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function login(formData: LoginFormData) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: formData.email,
        password: formData.password,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Login failed");
    }

    if (!data.success) {
      throw new Error(data.message || "Login failed");
    }

    // Store the JWT token for subsequent requests
    if (typeof window !== "undefined" && data.session?.access_token) {
      localStorage.setItem("auth_token", data.session.access_token);
      if (data.session.refresh_token) {
        localStorage.setItem("refresh_token", data.session.refresh_token);
      }
    }

    console.log("DATA", data);

    return {
      user: data.user,
      session: data.session,
      token: data.session.access_token,
    };
  } catch (error) {
    console.error("Login error:", error);
    throw error;
  }
}

export async function signup(signupFormData: SignupFormData) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: signupFormData.email,
        password: signupFormData.password,
        full_name: signupFormData.fullName,
        phone_number: signupFormData.phoneNumber,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Signup failed");
    }

    if (!data.success) {
      throw new Error(data.message || "Signup failed");
    }

    console.log("Signup successful:", data);

    return {
      user: data.user,
      email_verification_sent: data.email_verification_sent,
      message: data.message,
    };
  } catch (error) {
    console.error("Signup error:", error);
    throw error;
  }
}

export async function resendVerification(email: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to resend verification");
    }

    if (!data.success) {
      throw new Error(data.message || "Failed to resend verification");
    }

    return true;
  } catch (error) {
    console.error("Resend verification error:", error);
    throw error;
  }
}

export async function logout() {
  try {
    // Call backend logout endpoint if needed
    const token =
      typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

    if (token) {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
    }

    // Clear local storage
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
    }

    return true;
  } catch (error) {
    console.error("Logout error:", error);
    // Still clear local storage even if backend call fails
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
    }
    throw error;
  }
}

export async function getCurrentUser() {
  try {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

    if (!token) {
      return null;
    }

    const response = await fetch(`${API_BASE_URL}/users/profile`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      // Token might be expired, clear it
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
      }
      return null;
    }

    const data = await response.json();
    return data; // This should return the user profile data
  } catch (error) {
    console.error("Get current user error:", error);
    return null;
  }
}
