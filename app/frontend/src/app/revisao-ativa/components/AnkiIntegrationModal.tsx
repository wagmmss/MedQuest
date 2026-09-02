"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { FlashcardDeck } from "@/types/api";
import { api } from "@/lib/api";
import { checkAnkiConnect, getAnkiDecks, fetchDeckCards } from "@/lib/ankiConnect";
import {
  X,
  UploadCloud,
  FileArchive,
  Radio,
  Download,
  FolderMinus,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  FolderOpen,
  Info,
} from "lucide-react";
import toast from "react-hot-toast";

interface AnkiIntegrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  decks: FlashcardDeck[];
}

type TabType = "file" | "connect" | "export" | "manage";

export function AnkiIntegrationModal({
  isOpen,
  onClose,
  onSuccess,
  decks,
}: AnkiIntegrationModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>("file");

  // State: File Upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [customDeckName, setCustomDeckName] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State: AnkiConnect
  const [ankiConnectStatus, setAnkiConnectStatus] = useState<"idle" | "checking" | "connected" | "disconnected">("idle");
  const [ankiVersion, setAnkiVersion] = useState<number | null>(null);
  const [localDecks, setLocalDecks] = useState<string[]>([]);
  const [selectedLocalDeck, setSelectedLocalDeck] = useState<string>("");
  const [isSyncingAnkiConnect, setIsSyncingAnkiConnect] = useState(false);

  // State: Export
  const [isExporting, setIsExporting] = useState(false);

  // State: Manage
  const [deletingDeck, setDeletingDeck] = useState<string | null>(null);

  const testConnection = useCallback(async () => {
    setAnkiConnectStatus("checking");
    const result = await checkAnkiConnect();
    if (result.connected) {
      setAnkiConnectStatus("connected");
      setAnkiVersion(result.version || null);
      try {
        const dNames = await getAnkiDecks();
        setLocalDecks(dNames);
        if (dNames.length > 0 && !selectedLocalDeck) {
          setSelectedLocalDeck(dNames[0]);
        }
      } catch {
        // ignore deck list fetch failure
      }
    } else {
      setAnkiConnectStatus("disconnected");
    }
  }, [selectedLocalDeck]);

  useEffect(() => {
    if (isOpen && activeTab === "connect") {
      const timer = setTimeout(() => {
        void testConnection();
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [isOpen, activeTab, testConnection]);

  if (!isOpen) return null;

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      toast.error("Selecione um arquivo .apkg ou .txt para enviar.");
      return;
    }

    setIsUploading(true);
    try {
      const result = await api.flashcards.importFile(selectedFile, customDeckName.trim() || undefined);
      toast.success(`Importação concluída! ${result.total_imported} flashcards processados.`);
      setSelectedFile(null);
      setCustomDeckName("");
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao importar arquivo do Anki.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleAnkiConnectSync = async () => {
    if (!selectedLocalDeck) {
      toast.error("Selecione um baralho do Anki para sincronizar.");
      return;
    }

    setIsSyncingAnkiConnect(true);
    try {
      const cards = await fetchDeckCards(selectedLocalDeck, 500);
      if (cards.length === 0) {
        toast.error("Nenhuma nota encontrada no baralho selecionado.");
        return;
      }

      const result = await api.flashcards.importBatch(cards, selectedLocalDeck);
      toast.success(`Sincronização concluída! ${result.total_imported} flashcards importados com sucesso.`);
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao sincronizar com o AnkiConnect.");
    } finally {
      setIsSyncingAnkiConnect(false);
    }
  };

  const handleExportAnki = async () => {
    setIsExporting(true);
    try {
      await api.flashcards.exportAnki(false);
      toast.success("Arquivo Anki (.txt) baixado com sucesso!");
    } catch {
      toast.error("Erro ao exportar flashcards para o Anki.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteDeck = async (deckName: string) => {
    if (!window.confirm(`Tem certeza que deseja excluir o baralho "${deckName}" e todos os seus flashcards?`)) {
      return;
    }

    setDeletingDeck(deckName);
    try {
      const res = await api.flashcards.deleteDeck(deckName);
      toast.success(`Baralho "${deckName}" excluído (${res.deleted_count} cartões removidos).`);
      onSuccess();
    } catch {
      toast.error("Erro ao excluir baralho.");
    } finally {
      setDeletingDeck(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-card border border-border shadow-2xl rounded-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center font-black text-lg">
              ⚡
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                Integração com o Anki
              </h2>
              <p className="text-xs text-muted-foreground">
                Estude seus flashcards do Anki diretamente na plataforma do MedQuest
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
            aria-label="Fechar modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border bg-muted/20 px-6 gap-2 pt-2">
          <button
            onClick={() => setActiveTab("file")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition-all ${
              activeTab === "file"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileArchive size={14} /> Pacote / Arquivo (.apkg, .txt)
          </button>
          <button
            onClick={() => setActiveTab("connect")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition-all ${
              activeTab === "connect"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Radio size={14} /> AnkiConnect (Ao Vivo)
          </button>
          <button
            onClick={() => setActiveTab("manage")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition-all ${
              activeTab === "manage"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FolderOpen size={14} /> Baralhos ({decks.length})
          </button>
          <button
            onClick={() => setActiveTab("export")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition-all ${
              activeTab === "export"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Download size={14} /> Exportar
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* TAB 1: File Upload */}
          {activeTab === "file" && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 ${
                  isDragging
                    ? "border-primary bg-primary/5"
                    : selectedFile
                    ? "border-success/50 bg-success/5"
                    : "border-border hover:border-primary/50 hover:bg-muted/30"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".apkg,.colpkg,.txt,.tsv,.csv"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      setSelectedFile(e.target.files[0]);
                    }
                  }}
                />

                {selectedFile ? (
                  <>
                    <div className="w-12 h-12 rounded-full bg-success/20 text-success flex items-center justify-center">
                      <CheckCircle2 size={24} />
                    </div>
                    <div>
                      <p className="font-bold text-foreground text-sm">{selectedFile.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {(selectedFile.size / 1024).toFixed(1)} KB — Clique para trocar de arquivo
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                      <UploadCloud size={24} />
                    </div>
                    <div>
                      <p className="font-bold text-foreground text-sm">
                        Arraste seu arquivo do Anki (.apkg ou .txt) aqui
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        ou clique para navegar no seu computador
                      </p>
                    </div>
                  </>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-foreground block">
                  Nome do Baralho no MedQuest (opcional)
                </label>
                <input
                  type="text"
                  placeholder="Ex: Anki::Cardiologia ou deixe vazio para usar o nome original"
                  value={customDeckName}
                  onChange={(e) => setCustomDeckName(e.target.value)}
                  className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4 flex gap-3 text-xs text-muted-foreground leading-relaxed">
                <Info size={16} className="text-blue-500 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-foreground mb-1">Como exportar do seu Anki Desktop:</p>
                  <p>1. No Anki, clique no menu <strong>Arquivo &gt; Exportar</strong>.</p>
                  <p>2. Selecione o formato <strong>Pacote de Baralho do Anki (.apkg)</strong> ou <strong>Notas em Texto (.txt)</strong>.</p>
                  <p>3. Envie o arquivo aqui para estudar com nosso sistema de repetição espaçada FSRS.</p>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 rounded-xl border border-border text-sm font-semibold text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleFileUpload}
                  disabled={!selectedFile || isUploading}
                  className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-bold shadow-lg hover:bg-primary/90 transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {isUploading ? <Loader2 size={16} className="animate-spin" /> : <UploadCloud size={16} />}
                  Importar Flashcards
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: AnkiConnect Live */}
          {activeTab === "connect" && (
            <div className="space-y-5 animate-in fade-in duration-200">
              <div className="flex items-center justify-between p-4 rounded-xl border border-border bg-muted/20">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-3.5 h-3.5 rounded-full ${
                      ankiConnectStatus === "connected"
                        ? "bg-success animate-pulse"
                        : ankiConnectStatus === "checking"
                        ? "bg-warning animate-spin"
                        : "bg-destructive"
                    }`}
                  />
                  <div>
                    <p className="text-sm font-bold text-foreground">
                      {ankiConnectStatus === "connected"
                        ? `AnkiConnect Conectado (v${ankiVersion || 6})`
                        : ankiConnectStatus === "checking"
                        ? "Detectando Anki Desktop..."
                        : "AnkiConnect Desconectado"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Endpoint: http://127.0.0.1:8765
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => void testConnection()}
                  disabled={ankiConnectStatus === "checking"}
                  className="px-3 py-1.5 rounded-lg border border-border text-xs font-semibold text-foreground hover:bg-muted/50 transition-colors flex items-center gap-1.5"
                >
                  <RefreshCw size={12} className={ankiConnectStatus === "checking" ? "animate-spin" : ""} />
                  Testar Conexão
                </button>
              </div>

              {ankiConnectStatus === "connected" ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-bold text-foreground block mb-2">
                      Selecione o Baralho do Anki para sincronizar:
                    </label>
                    <select
                      value={selectedLocalDeck}
                      onChange={(e) => setSelectedLocalDeck(e.target.value)}
                      className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      {localDecks.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    type="button"
                    onClick={handleAnkiConnectSync}
                    disabled={isSyncingAnkiConnect || !selectedLocalDeck}
                    className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-bold text-sm shadow-lg hover:bg-primary/90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isSyncingAnkiConnect ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Radio size={16} />
                    )}
                    Sincronizar Baralho &quot;{selectedLocalDeck}&quot; com MedQuest
                  </button>
                </div>
              ) : (
                <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-4 space-y-3">
                  <div className="flex items-center gap-2 text-destructive font-bold text-xs">
                    <AlertCircle size={16} /> Não foi possível comunicar com o Anki local
                  </div>
                  <div className="text-xs text-muted-foreground space-y-2 leading-relaxed">
                    <p>Para usar a sincronização direta ao vivo:</p>
                    <ol className="list-decimal list-inside space-y-1 pl-1">
                      <li>Abra o aplicativo <strong>Anki</strong> no seu computador.</li>
                      <li>Instale a extensão <strong>AnkiConnect</strong> (Código: <code className="bg-muted px-1.5 py-0.5 rounded font-mono text-foreground">2055492159</code> no menu Ferramentas &gt; Complementos &gt; Baixar Complementos).</li>
                      <li>Reinicie o Anki e clique em <strong>Testar Conexão</strong> acima.</li>
                    </ol>
                    <p className="pt-1 text-foreground font-semibold">
                      💡 Alternativa: Você também pode usar a aba <strong>Pacote / Arquivo</strong> para importar arquivos sem precisar da extensão!
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Manage Decks */}
          {activeTab === "manage" && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <p className="text-xs text-muted-foreground">
                Estes são os baralhos disponíveis na sua conta. Você pode filtrar por qualquer um deles na tela de revisão ou remover baralhos importados.
              </p>

              {decks.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  Nenhum baralho cadastrado ainda.
                </div>
              ) : (
                <div className="divide-y divide-border border border-border rounded-xl overflow-hidden bg-background">
                  {decks.map((d) => (
                    <div
                      key={d.name}
                      className="p-4 flex items-center justify-between gap-3 hover:bg-muted/20 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
                          📁
                        </div>
                        <div>
                          <p className="font-bold text-sm text-foreground">{d.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {d.total_cards} cartões ·{" "}
                            <span className={d.due_cards > 0 ? "text-warning font-semibold" : "text-muted-foreground"}>
                              {d.due_cards} para revisar hoje
                            </span>
                          </p>
                        </div>
                      </div>

                      {d.name !== "Geral" && (
                        <button
                          type="button"
                          onClick={() => handleDeleteDeck(d.name)}
                          disabled={deletingDeck === d.name}
                          className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
                          title="Excluir baralho"
                        >
                          {deletingDeck === d.name ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <FolderMinus size={16} />
                          )}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: Export to Anki */}
          {activeTab === "export" && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="rounded-xl border border-border bg-muted/20 p-5 space-y-3">
                <div className="flex items-center gap-2 text-foreground font-bold text-sm">
                  <Download size={18} className="text-primary" /> Exportar Erros do MedQuest para o Anki
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Gere um arquivo de texto formatado com todas as questões que você errou ou marcou no MedQuest, incluindo contexto clínico e omissões de palavras (Cloze).
                </p>
                <button
                  type="button"
                  onClick={handleExportAnki}
                  disabled={isExporting}
                  className="px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-bold text-xs shadow-md hover:bg-primary/90 transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {isExporting ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                  Baixar Arquivo Anki (.txt)
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
