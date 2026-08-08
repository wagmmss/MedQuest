import { BuscarClient } from "./BuscarClient";

export default async function BuscarPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  const rawParams = await searchParams;
  const q = typeof rawParams.q === "string" ? rawParams.q : "";

  return (
    <div className="animate-in fade-in duration-500 w-full h-full">
      <BuscarClient initialQuery={q} />
    </div>
  );
}
