"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";

function AuthRedirect() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const discord = searchParams.get("discord") || "";
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;
    const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_BASE_URL;

    if (!clientId || !backendBaseUrl) {
      console.error("Missing environment variables");
      return;
    }

    const scopes = "repo admin:repo_hook notifications read:user";
    const encodedScopes = encodeURIComponent(scopes);
    const redirectUri = `${backendBaseUrl}/callback?discord=${discord}`;
    const encodedRedirectUri = encodeURIComponent(redirectUri);

    const oauthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodedRedirectUri.replace("%2F%2Fcallback", "/callback")}&scope=${encodedScopes}`;
    window.location.href = oauthUrl;
  }, [searchParams]);

  return null;
}

export default function AuthPage() {
  return (
    <Suspense fallback={null}>
      <AuthRedirect />
    </Suspense>
  );
}
