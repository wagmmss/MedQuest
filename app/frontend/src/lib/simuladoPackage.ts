/**
 * Gerenciador de Pacotes Offline de Simulado (MedQuest)
 * Orquestra download determinístico, integridade, expiração e gestão de pacotes no IndexedDB (Dexie).
 */

import { localDb, getLocalOwnerId, SimuladoPackage, isPackageValid } from "./db";
import { api } from "./api";
import { QuestionDetail, QuestionListItem } from "@/types/api";

export const SIMULADO_PACKAGE_VERSION = 1;
export const SIMULADO_PACKAGE_VALIDITY_DAYS = 30;
const OFFLINE_STUDY_SHELL_CACHE = "medquest-study-shell";
const OFFLINE_IMAGE_CACHE = "medquest-image-cache";
const IMAGE_DOWNLOAD_CONCURRENCY = 4;
const IMAGE_DOWNLOAD_ATTEMPTS = 3;

export interface SimuladoDownloadProgress {
  step: "list" | "details" | "images" | "complete" | "error";
  progress: number; // 0 a 100
  message: string;
  loadedQuestions: number;
  totalQuestions: number;
}

export interface SimuladoConfigParams {
  institutions?: string[];
  years?: string[];
  questions_per_area?: number;
  duration_minutes?: number;
  force_4_options?: boolean;
  name?: string;
  [key: string]: unknown;
}

/**
 * Pré-carrega imagens médicas associadas às questões baixadas no Cache Storage / HTTP Cache.
 * Retorna contagem de imagens em cache e lista de URLs que falharam.
 */
async function prefetchImages(imageUrls: string[]): Promise<{ cachedCount: number; failedUrls: string[] }> {
  const uniqueUrls = Array.from(new Set(imageUrls.filter(Boolean)));
  let cachedCount = 0;
  const failedUrls: string[] = [];

  // A large simulado may reference hundreds of images. Starting every request
  // at once makes mobile browsers abort otherwise valid downloads, so keep a
  // small worker pool and retry transient network failures.
  let nextIndex = 0;
  const fetchOne = async (url: string): Promise<boolean> => {
    const fullUrl = url.startsWith("http") ? url : `${url.startsWith("/") ? "" : "/"}${url}`;
    for (let attempt = 1; attempt <= IMAGE_DOWNLOAD_ATTEMPTS; attempt++) {
      try {
        const res = await fetch(fullUrl, { cache: "force-cache" });
        if (res.ok) {
          // Fetching alone only reaches Workbox after the service worker has
          // taken control. Persist the image here too, so a newly opened app
          // can immediately use the completed package offline.
          if (typeof caches !== "undefined") {
            const imageCache = await caches.open(OFFLINE_IMAGE_CACHE);
            await imageCache.put(fullUrl, res.clone());
          }
          return true;
        }

        // A missing/invalid image is permanent; retries only help temporary
        // server and connection failures.
        if (res.status >= 400 && res.status < 500) return false;
      } catch {
        // Retry network failures below.
      }

      if (attempt < IMAGE_DOWNLOAD_ATTEMPTS) {
        await new Promise<void>((resolve) => setTimeout(resolve, attempt * 250));
      }
    }
    return false;
  };

  const workers = Array.from({ length: Math.min(IMAGE_DOWNLOAD_CONCURRENCY, uniqueUrls.length) }, async () => {
    while (nextIndex < uniqueUrls.length) {
      const url = uniqueUrls[nextIndex++];
      if (await fetchOne(url)) cachedCount++;
      else failedUrls.push(url);
    }
  });

  await Promise.all(workers);
  return { cachedCount, failedUrls };
}

async function requestPersistentStorage(): Promise<void> {
  try {
    await navigator.storage?.persist?.();
  } catch {
    // This is a best-effort request. IndexedDB remains usable if the browser
    // declines it, but is less likely to evict a completed offline package.
  }
}

/**
 * Stores the study screen that Workbox uses as the navigation fallback. The
 * downloaded questions live in IndexedDB, but without this shell a cold
 * offline navigation to /estudar cannot render those questions.
 */
async function primeOfflineStudyShell(): Promise<void> {
  try {
    const response = await fetch("/estudar", { cache: "reload" });
    if (!response.ok || typeof caches === "undefined") return;

    const studyCache = await caches.open(OFFLINE_STUDY_SHELL_CACHE);
    await studyCache.put("/estudar", response.clone());
  } catch (error) {
    // The question package is still complete and may be used from an already
    // open study page. Do not discard it because refreshing the shell failed.
    console.warn("Não foi possível preparar a tela de estudo offline:", error);
  }
}

/**
 * Realiza o download atômico e determinístico de um pacote offline completo de simulado.
 */
export async function downloadSimuladoPackage(
  config: SimuladoConfigParams,
  onProgress?: (p: SimuladoDownloadProgress) => void
): Promise<SimuladoPackage> {
  if (typeof window === "undefined" || !localDb) {
    throw new Error("Armazenamento local (IndexedDB) indisponível neste ambiente.");
  }

  await requestPersistentStorage();

  const uid = getLocalOwnerId();
  const packageId = crypto.randomUUID();
  const now = Date.now();
  const expiresAt = now + SIMULADO_PACKAGE_VALIDITY_DAYS * 24 * 60 * 60 * 1000;
  const packageName = config.name || `Simulado Offline (${config.questions_per_area || 20} Qs/área)`;

  // 1. Criar registro inicial com status "downloading"
  const initialPackage: SimuladoPackage = {
    id: packageId,
    owner_id: uid,
    name: packageName,
    config,
    question_ids: [],
    questions_count: 0,
    details_count: 0,
    images_count: 0,
    estimated_size_bytes: 0,
    status: "downloading",
    download_progress: 5,
    created_at: now,
    updated_at: now,
    expires_at: expiresAt,
    version: SIMULADO_PACKAGE_VERSION,
  };

  await localDb.simuladoPackages.put(initialPackage);

  onProgress?.({
    step: "list",
    progress: 10,
    message: "Gerando fila de questões do simulado...",
    loadedQuestions: 0,
    totalQuestions: 0,
  });

  try {
    // 2. Buscar lista determinística de questões
    let questionsList: QuestionListItem[] = [];
    if (config.institutions?.length || config.years?.length || config.questions_per_area) {
      questionsList = await api.questions.getCustomSimulado({
        institutions: config.institutions,
        years: config.years,
        questions_per_area: config.questions_per_area,
        duration_minutes: config.duration_minutes,
        force_4_options: config.force_4_options,
      });
    } else {
      questionsList = await api.questions.getSimuladoUSP();
    }

    if (!questionsList || questionsList.length === 0) {
      throw new Error("Nenhuma questão retornada para a configuração selecionada.");
    }

    const totalQuestions = questionsList.length;
    const questionIds = questionsList.map((q) => q.id);

    onProgress?.({
      step: "details",
      progress: 25,
      message: `Baixando detalhes de ${totalQuestions} questões...`,
      loadedQuestions: 0,
      totalQuestions,
    });

    // 3. Baixar detalhes e explicações em lotes de 10
    const chunkSize = 10;
    const allImageUrls: string[] = [];
    let loadedCount = 0;
    let totalBytesEstimated = 0;

    for (let i = 0; i < questionIds.length; i += chunkSize) {
      const chunkIds = questionIds.slice(i, i + chunkSize);
      const batchRes = await api.questions.getBatch(chunkIds, config.force_4_options);
      
      if (!batchRes || !batchRes.questions) {
        throw new Error(`Falha ao obter detalhes das questões ${chunkIds.join(", ")}.`);
      }

      const details = Array.isArray(batchRes.questions)
        ? batchRes.questions
        : (Object.values(batchRes.questions) as QuestionDetail[]);

      if (details.length < chunkIds.length) {
        throw new Error(`Lote parcial de detalhes retornado: recebidas ${details.length} de ${chunkIds.length} questões esperadas.`);
      }
      
      // Salvar questões no Dexie associadas ao dono atual
      await localDb.questions.bulkPut(
        details.map((d) => ({
          ...d,
          _owner_id: uid,
        }))
      );

      for (const d of details) {
        totalBytesEstimated += JSON.stringify(d).length;
        if (d.images && Array.isArray(d.images)) {
          allImageUrls.push(...d.images.map(normalizeImageForCache));
        }
        if (d.clinical_case?.images && Array.isArray(d.clinical_case.images)) {
          allImageUrls.push(...d.clinical_case.images.map(normalizeImageForCache));
        }
      }
      loadedCount += details.length;

      const progressVal = 25 + Math.round((loadedCount / totalQuestions) * 55);
      onProgress?.({
        step: "details",
        progress: progressVal,
        message: `Baixando questões (${loadedCount}/${totalQuestions})...`,
        loadedQuestions: loadedCount,
        totalQuestions,
      });

      // Atualizar progresso no pacote do banco
      await localDb.simuladoPackages.update(packageId, {
        question_ids: questionIds.slice(0, loadedCount),
        questions_count: totalQuestions,
        details_count: loadedCount,
        download_progress: progressVal,
        updated_at: Date.now(),
      });
    }

    if (loadedCount < totalQuestions) {
      throw new Error(`Inconsistência de integridade: baixadas ${loadedCount} de ${totalQuestions} questões esperadas.`);
    }

    // 4. Pré-carregar imagens médicas obrigatórias
    let cachedImages = 0;
    if (allImageUrls.length > 0) {
      onProgress?.({
        step: "images",
        progress: 85,
        message: `Armazenando ${allImageUrls.length} imagens médicas em cache...`,
        loadedQuestions: loadedCount,
        totalQuestions,
      });
      const { cachedCount, failedUrls } = await prefetchImages(allImageUrls);
      if (failedUrls.length > 0) {
        throw new Error(`Falha no download de ${failedUrls.length} imagem(ns) obrigatória(s) do simulado.`);
      }
      cachedImages = cachedCount;
      totalBytesEstimated += cachedImages * 50 * 1024; // Estimativa média ~50KB por imagem
    }

    await primeOfflineStudyShell();

    // 5. Finalizar e marcar como "ready"
    const readyPackage: SimuladoPackage = {
      id: packageId,
      owner_id: uid,
      name: packageName,
      config,
      question_ids: questionIds,
      questions_count: totalQuestions,
      details_count: loadedCount,
      images_count: cachedImages,
      estimated_size_bytes: totalBytesEstimated,
      status: "ready",
      download_progress: 100,
      created_at: now,
      updated_at: Date.now(),
      expires_at: expiresAt,
      version: SIMULADO_PACKAGE_VERSION,
    };

    await localDb.simuladoPackages.put(readyPackage);

    onProgress?.({
      step: "complete",
      progress: 100,
      message: "Pacote de simulado offline pronto para uso!",
      loadedQuestions: loadedCount,
      totalQuestions,
    });

    window.dispatchEvent(new CustomEvent("simulado-package-updated", { detail: readyPackage }));
    return readyPackage;
  } catch (error) {
    const isQuota =
      error instanceof DOMException &&
      (error.name === "QuotaExceededError" || error.code === 22);

    const failStatus = isQuota ? "quota_exceeded" : "incomplete";
    const errorMsg = error instanceof Error ? error.message : String(error);

    await localDb.simuladoPackages.update(packageId, {
      status: failStatus,
      last_error: errorMsg,
      updated_at: Date.now(),
    });

    onProgress?.({
      step: "error",
      progress: 0,
      message: isQuota ? "Espaço em disco insuficiente." : `Falha no download: ${errorMsg}`,
      loadedQuestions: 0,
      totalQuestions: 0,
    });

    window.dispatchEvent(new CustomEvent("simulado-package-failed", { detail: { packageId, error: errorMsg } }));
    throw error;
  }
}


function normalizeImageForCache(img: string): string {
  // Keep this normalization aligned with the question renderer. Previously
  // `images/foo.png` became `/api/images/images/foo.png` here while the screen
  // correctly rendered `/api/images/foo.png`, making otherwise valid downloads
  // fail during image prefetch.
  const trimmed = (img || "")
    .trim()
    .replace(/^\/api\/images\/images\//, "/api/images/")
    .replace(/MedQuest-assets\.s3\.sa-east-1\.amazonaws\.com/gi, "medcof-assets.s3.sa-east-1.amazonaws.com")
    .replace(/MedQuest-assets\.s3\.amazonaws\.com/gi, "medcof-assets.s3.amazonaws.com")
    .replace(/cdn\.MedQuest\.com\.br/gi, "cdn.medway.com.br")
    .replace(/www\.MedQuest\.com\.br/gi, "www.medway.com.br");
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://") || trimmed.startsWith("/api/")) {
    return trimmed;
  }
  return `/api/images/${trimmed}`;
}

/**
 * Retorna o pacote pronto e válido mais recente para o usuário atual.
 */
export async function getReadySimuladoPackage(ownerId?: string): Promise<SimuladoPackage | null> {
  if (typeof window === "undefined" || !localDb) return null;
  try {
    const uid = ownerId || getLocalOwnerId();
    const packages = await localDb.simuladoPackages
      .where('owner_id')
      .equals(uid)
      .toArray();

    const validPackages = packages
      .filter((pkg) => isPackageValid(pkg).valid)
      .sort((a, b) => b.updated_at - a.updated_at);

    return validPackages[0] || null;
  } catch (err) {
    console.warn("Erro ao buscar pacote de simulado pronto:", err);
    return null;
  }
}

/**
 * Lista todos os pacotes offline pertencentes ao usuário.
 */
export async function listSimuladoPackages(ownerId?: string): Promise<SimuladoPackage[]> {
  if (typeof window === "undefined" || !localDb) return [];
  try {
    const uid = ownerId || getLocalOwnerId();
    return await localDb.simuladoPackages
      .where('owner_id')
      .equals(uid)
      .reverse()
      .sortBy("updated_at");
  } catch (err) {
    console.warn("Erro ao listar pacotes offline:", err);
    return [];
  }
}

/**
 * Remove um pacote específico do IndexedDB.
 */
export async function deleteSimuladoPackage(packageId: string, ownerId?: string): Promise<void> {
  if (typeof window === "undefined" || !localDb) return;
  const uid = ownerId || getLocalOwnerId();
  const pkg = await localDb.simuladoPackages.get(packageId);
  if (!pkg || pkg.owner_id !== uid) return;

  await localDb.simuladoPackages.delete(packageId);
  window.dispatchEvent(new CustomEvent("simulado-package-updated", { detail: { deletedId: packageId } }));
}

/**
 * Limpa todos os pacotes e questões do usuário atual.
 */
export async function clearAllSimuladoPackages(ownerId?: string): Promise<void> {
  if (typeof window === "undefined" || !localDb) return;
  const uid = ownerId || getLocalOwnerId();
  await localDb.simuladoPackages.where('owner_id').equals(uid).delete();
  window.dispatchEvent(new CustomEvent("simulado-package-updated", { detail: { cleared: true } }));
}
