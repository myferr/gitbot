"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function AuthComplete() {
  const searchParams = useSearchParams();
  const [discordId, setDiscordId] = useState("");

  useEffect(() => {
    const discord = searchParams.get("discord");
    if (discord) setDiscordId(discord);
  }, [searchParams]);

  return (
    <main className="flex flex-1 flex-col justify-center items-center min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-xl w-full text-center space-y-4 rounded-lg bg-gray-800 p-10 shadow-lg">
        <h1 className="text-4xl font-extrabold">
          You're linked,&nbsp;
          <span className="bg-gradient-to-r from-pink-500 via-yellow-500 to-blue-500 bg-clip-text text-transparent">
            {discordId || "Unknown User"}
          </span>
          !
        </h1>
        <p className="text-gray-400 text-lg">You can now return to Discord.</p>
      </div>
    </main>
  );
}

