"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentSession, onAuthStateChange } from "@/lib/supabase";

export default function ProtectedRoute({ children }) {
  const router = useRouter();
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let isMounted = true;
    let frame = null;

    async function validateSession() {
      const session = await getCurrentSession();
      if (!isMounted) return;

      if (!session) {
        router.replace("/auth");
        frame = window.requestAnimationFrame(() => {
          setStatus("redirecting");
        });
        return;
      }

      frame = window.requestAnimationFrame(() => {
        setStatus("allowed");
      });
    }

    validateSession();

    const { data } = onAuthStateChange((_event, session) => {
      if (!isMounted) return;

      if (!session) {
        router.replace("/auth");
        setStatus("redirecting");
      } else {
        setStatus("allowed");
      }
    });

    return () => {
      isMounted = false;
      if (frame) {
        window.cancelAnimationFrame(frame);
      }
      data?.subscription?.unsubscribe?.();
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

  return children;
}
