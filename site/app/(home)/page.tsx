import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col justify-center text-center">
      <h1 className="mb-4 text-2xl font-bold">GitBot</h1>
      <p className="text-fd-muted-foreground text-center">
        A Discord bot that allows you to view GitHub information,<br/>merge and close PRs, open and close issues, etc. all from Discord.
      </p>
      <div className="mt-8 flex gap-2 w-full justify-center items-center">
        <Link href="/docs">
          <button className="py-2 px-8 bg-fd-muted/50 rounded-xl border-fd-muted-foreground/10 hover:border-fd-muted-foreground/20 hover:bg-fd-muted border transition-all duration-300">View documentation</button>
        </Link>
        
        <Link href="https://discord.com/oauth2/authorize?client_id=1397762688507052142" target="_blank">
          <button className="py-2 px-8 bg-blue-500/50 rounded-xl border-fd-muted-foreground/10 hover:border-fd-muted-foreground/20 hover:bg-blue-500 border transition-all duration-300">Invite to Discord</button>
        </Link>
      </div>
    </main>
  );
}
