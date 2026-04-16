"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAdminSession } from "@/lib/admin";

export default function ProtectedAdminRoute({ children }) {
  const router = useRouter();
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    const session = getAdminSession();
    if (!session) {
      router.replace("/admin/login");
      const frame = window.requestAnimationFrame(() => {
        setStatus("redirecting");
      });
      return () => window.cancelAnimationFrame(frame);
    }

    const frame = window.requestAnimationFrame(() => {
      setStatus("allowed");
    });
    return () => window.cancelAnimationFrame(frame);
  }, [router]);

  if (status === "checking") {
    return (
      <main className="page-shell">
        <p>Checking admin session...</p>
      </main>
    );
  }

  if (status !== "allowed") {
    return (
      <main className="page-shell">
        <p>Redirecting to admin login...</p>
      </main>
    );
  }

  return children;
}
