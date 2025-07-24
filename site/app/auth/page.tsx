"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";

export default function Auth() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const discord = searchParams.get("discord") || "";
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;
    const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_BASE_URL; // e.g. your tunnel URL

    if (!clientId || !backendBaseUrl) {
      console.error("Missing environment variables");
      return;
    }

    // Prepare scopes separated by spaces
    const scopes = "repo admin:repo_hook notifications read:user";

    // URL encode scopes and redirect URI
    const encodedScopes = encodeURIComponent(scopes);
    const redirectUri = `${backendBaseUrl}/callback?discord=${discord}`;
    const encodedRedirectUri = encodeURIComponent(redirectUri);

    // Build GitHub OAuth URL
    const oauthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodedRedirectUri}&scope=${encodedScopes}`;

    // Redirect to GitHub OAuth page
    window.location.href = oauthUrl;
  }, [searchParams]);

  return null;
}

