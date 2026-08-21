import { headers, cookies } from "next/headers";

/**
 * Retorna o ID de visitante confiável para a requisição corrente.
 * Prioriza o header interno injetado pelo proxy (válido inclusive no 1º request).
 */
export async function getGuestSession(): Promise<string | undefined> {
  try {
    const headerList = await headers();
    const internalGuestId = headerList.get("x-internal-guest-id");
    if (internalGuestId) {
      return internalGuestId;
    }
  } catch {
    // Caso invocado em contexto onde headers() não está disponível
  }

  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("medquest_guest_session");
    if (sessionCookie?.value) {
      return sessionCookie.value;
    }
  } catch {
    // Caso invocado em contexto onde cookies() não está disponível
  }

  // Fallback seguro gerando UUID v4 válido se ainda não existir sessão gravada
  return crypto.randomUUID();
}
