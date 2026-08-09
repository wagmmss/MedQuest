import { serverApi } from "@/lib/server-api";
import { QuizClient } from "./QuizClient";

export default async function EstudarPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  const meta = await serverApi.questions.getMeta();
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
