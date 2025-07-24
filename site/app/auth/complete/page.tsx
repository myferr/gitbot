"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function AuthComplete() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [discordId, setDiscordId] = useState("");

  useEffect(() => {
    const discord = searchParams.get("discord");
    if (typeof discord === "string") {
      setDiscordId(discord);
    }
  }, [searchParams]);

  return (
    <main className="flex flex-1 flex-col justify-center text-center">
      <div className="container max-w-xl text-center space-y-4 p-8 rounded-lg">
        <h1 className="text-4xl font-semibold">
          You're linked,&nbsp;
          <span className="bg-gradient-to-r from-pink-500 via-yellow-500 to-blue-500 bg-clip-text text-transparent font-bold">
            {discordId}
          </span>
          !
        </h1>
        <p className="text-gray-400">You can now return to Discord.</p>
      </div>
    </main>
  );
}
