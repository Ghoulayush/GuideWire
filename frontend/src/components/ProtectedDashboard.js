"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import DashboardClient from "@/components/DashboardClient";
import { getStoredUser } from "@/lib/auth";

export default function ProtectedDashboard({ storyHtml }) {
  const router = useRouter();
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    const user = getStoredUser();
    if (!user) {
      router.replace("/auth");
      const redirectFrame = window.requestAnimationFrame(() => {
        setStatus("redirecting");
      });

      return () => {
        window.cancelAnimationFrame(redirectFrame);
      };
    }

    const allowFrame = window.requestAnimationFrame(() => {
      setStatus("allowed");
    });

    return () => {
      window.cancelAnimationFrame(allowFrame);
    };
  }, [router]);

  if (status === "checking") {
    return (
      <main className="page-shell">
        <p>Checking session...</p>
      </main>
    );
  }

  if (status !== "allowed") {
    return (
      <main className="page-shell">
        <p>Redirecting to login...</p>
      </main>
    );
  }

  return <DashboardClient storyHtml={storyHtml} />;
}
