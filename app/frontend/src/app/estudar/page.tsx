import { serverApi, QuestionMeta } from "@/lib/server-api";
import { QuizClient } from "./QuizClient";

export const dynamic = "force-dynamic";

export default async function EstudarPage({
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

  // Convert searchParams to a simple record of strings
  const initialFilters: Record<string, string> = {};
  for (const key in rawParams) {
    const val = rawParams[key];
    if (typeof val === "string") {
      initialFilters[key] = val;
    }
  }

  return (
    <div className="animate-in fade-in duration-500 w-full h-full">
      <QuizClient 
        meta={meta} 
        initialFilters={initialFilters}
      />
    </div>
  );
}
