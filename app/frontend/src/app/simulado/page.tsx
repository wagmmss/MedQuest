import { serverApi } from "@/lib/server-api";
import { SimuladoClient } from "./SimuladoClient";

export default async function SimuladoPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  const meta = await serverApi.questions.getMeta();
  const rawParams = await searchParams;
  const initialFilters: Record<string, string | string[]> = {};
  
  for (const key in rawParams) {
    const val = rawParams[key];
    if (val !== undefined) {
      initialFilters[key] = val;
    }
  }

  return (
    <div className="animate-in fade-in duration-500 w-full h-full">
      <SimuladoClient initialFilters={initialFilters} meta={meta} />
    </div>
  );
}
