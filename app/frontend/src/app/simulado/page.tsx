import { serverApi, QuestionMeta } from "@/lib/server-api";
import { SimuladoClient } from "./SimuladoClient";

export const dynamic = "force-dynamic";

export default async function SimuladoPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  let meta: QuestionMeta | undefined;
  try {
    meta = await serverApi.questions.getMeta();
  } catch (err: any) {
    if (err.message?.includes('DYNAMIC_SERVER_USAGE') || err.digest?.includes('DYNAMIC_SERVER_USAGE')) {
      throw err;
    }
    console.warn("SSR getMeta fallback to client fetch:", err);
  }
  const rawParams = await searchParams;
  const initialFilters: Record<string, string | string[]> = {};
  
  for (const key in rawParams) {
    const val = rawParams[key];
    if (val !== undefined) {
      initialFilters[key] = val;
    }
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      <SimuladoClient initialFilters={initialFilters} meta={meta} />
    </div>
  );
}
