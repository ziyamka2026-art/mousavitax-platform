// =============================================================================
// Registry Document Form — Unified Component
// =============================================================================
// Features:
//   1. Dedicated Title field (required)
//   2. Source: choose "Drive picker" OR "URL paste"
//   3. Drive file browser with search + folder navigation
//   4. Auto-generated code preview (MKA-TYPE-001) based on inferred type
//   5. Inline error display (no silent failures)
//   6. RLS-safe via user JWT (requires migration 005_registry_documents.sql)
// =============================================================================

import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useMemo } from "react";
import { z } from "zod";
import {
  inferTypeFromFilename,
  TYPE_ABBREVIATIONS,
  TYPE_LABELS,
  generateCodePreview,
  type DocumentType,
} from "@mousavitax/registry";
import {
  registerDocument,
  listRegistryDocuments,
  updateRegistryDocument,
  deleteRegistryDocument,
} from "@/lib/registry.functions";
import {
  listDriveFiles,
  listDriveFolders,
  searchDriveFiles,
  getDriveFileMeta,
  checkDriveHealth,
} from "@/lib/drive-picker.functions";
import { AppHeader } from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { AlertCircle, FileText, Folder, Loader2, Search } from "lucide-react";

export const Route = createFileRoute("/registry")({
  head: () => ({
    meta: [
      { title: "Registry اسناد | MKA" },
      { name: "description", content: "ثبت، جست‌وجو و مدیریت اسناد حقوقی-مالیاتی." },
    ],
  }),
  component: RegistryPage,
});

// =============================================================================
// Main Registry Page
// =============================================================================

function RegistryPage() {
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(0);

  // Load documents with current filters
  const [docsData, setDocsData] = useState<{ documents: any[]; total: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    setLoading(true);
    setError(null);
    try {
      const result: any = await listRegistryDocuments({
        query: search,
        status: statusFilter,
        page,
        pageSize: 20,
      });
      setDocsData({ documents: result.documents ?? [], total: result.total ?? 0 });
    } catch (err) {
      setError((err as Error).message);
      setDocsData({ documents: [], total: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
  }, [search, statusFilter, page]);

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />
      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Registry اسناد</h1>
          <Button onClick={() => setShowForm(true)}>
            <FileText className="ml-2 size-4" />
            ثبت سند جدید
          </Button>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-wrap gap-3 mb-4">
          <div className="relative flex-1 min-w-64">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="جستجو در عنوان / کد / شماره / یادداشت"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              className="pr-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(0); }}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="همه وضعیت‌ها" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">همه وضعیت‌ها</SelectItem>
              <SelectItem value="unidentified">شناسایی‌نشده</SelectItem>
              <SelectItem value="identified">شناسایی‌شده</SelectItem>
              <SelectItem value="reviewed">بازبینی‌شده</SelectItem>
              <SelectItem value="approved">تأییدشده</SelectItem>
              <SelectItem value="rejected">رد‌شده</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-4 flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <AlertCircle className="size-5 text-destructive flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-destructive">خطا در بارگذاری اسناد</p>
              <p className="text-sm text-destructive/80 mt-1">{error}</p>
              <Button variant="outline" size="sm" className="mt-2" onClick={reload}>
                تلاش مجدد
              </Button>
            </div>
          </div>
        )}

        {/* Documents List */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : docsData?.documents.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <FileText className="mx-auto size-12 mb-3 opacity-50" />
            <p>موردی یافت نشد</p>
          </div>
        ) : (
          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-right">کد</th>
                  <th className="px-4 py-3 text-right">عنوان</th>
                  <th className="px-4 py-3 text-right">نوع</th>
                  <th className="px-4 py-3 text-right">وضعیت</th>
                  <th className="px-4 py-3 text-right">تاریخ ثبت</th>
                  <th className="px-4 py-3 text-left">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {docsData?.documents.map((doc) => (
                  <tr key={doc.id} className="border-t hover:bg-muted/30">
                    <td className="px-4 py-3 font-mono">{doc.code}</td>
                    <td className="px-4 py-3">{doc.title}</td>
                    <td className="px-4 py-3">
                      <span className="inline-block rounded px-2 py-0.5 bg-muted text-xs">
                        {TYPE_LABELS[doc.type_code] ?? doc.type_code}
                      </span>
                    </td>
                    <td className="px-4 py-3">{doc.status}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(doc.created_at).toLocaleDateString("fa-IR")}
                    </td>
                    <td className="px-4 py-3 text-left">
                      <Button variant="ghost" size="sm" asChild>
                        <a href={`/registry/${doc.id}`}>ویرایش</a>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* New Document Form */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>ثبت سند جدید</DialogTitle>
          </DialogHeader>
          <NewDocumentForm
            onClose={() => setShowForm(false)}
            onSaved={() => { setShowForm(false); reload(); }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

// =============================================================================
// New Document Form Component
// =============================================================================

type SourceMode = "drive" | "url" | "manual";

function NewDocumentForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  // ─── Form State ──────────────────────────────────────────────────────────
  const [title, setTitle] = useState("");
  const [sourceMode, setSourceMode] = useState<SourceMode>("drive");
  const [sourceUrl, setSourceUrl] = useState("");
  const [driveFile, setDriveFile] = useState<{ id: string; name: string; webViewLink?: string } | null>(null);
  const [typeHint, setTypeHint] = useState<DocumentType | "auto">("auto");
  const [expertNotes, setExpertNotes] = useState("");
  const [extractedText, setExtractedText] = useState("");

  // ─── Drive Picker State ──────────────────────────────────────────────────
  const [driveOpen, setDriveOpen] = useState(false);
  const [currentFolder, setCurrentFolder] = useState<string | undefined>(undefined);
  const [driveFiles, setDriveFiles] = useState<any[]>([]);
  const [driveFolders, setDriveFolders] = useState<any[]>([]);
  const [driveSearch, setDriveSearch] = useState("");
  const [driveLoading, setDriveLoading] = useState(false);
  const [driveError, setDriveError] = useState<string | null>(null);
  const [driveHealth, setDriveHealth] = useState<"ok" | "error" | "unknown">("unknown");

  // ─── Submission State ─────────────────────────────────────────────────────
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // ─── Drive Health Check on Mount ──────────────────────────────────────────
  useEffect(() => {
    checkDriveHealth().then((result: any) => {
      setDriveHealth(result.reachable ? "ok" : "error");
    }).catch(() => setDriveHealth("error"));
  }, []);

  // ─── Load Drive contents when picker opens ────────────────────────────────
  useEffect(() => {
    if (!driveOpen) return;
    loadDriveContents(currentFolder, driveSearch);
  }, [driveOpen, currentFolder, driveSearch]);

  const loadDriveContents = async (folderId: string | undefined, query: string) => {
    setDriveLoading(true);
    setDriveError(null);
    try {
      if (query.trim().length > 1) {
        // Search across all of Drive
        const r: any = await searchDriveFiles({ query });
        setDriveFiles(r.files ?? []);
        setDriveFolders([]);
      } else {
        // Browse folder
        const [filesR, foldersR]: any = await Promise.all([
          listDriveFiles({ folderId }),
          listDriveFolders({ folderId }),
        ]);
        setDriveFiles(filesR.files ?? []);
        setDriveFolders(foldersR.folders ?? []);
      }
    } catch (err) {
      setDriveError((err as Error).message);
      setDriveFiles([]);
      setDriveFolders([]);
    } finally {
      setDriveLoading(false);
    }
  };

  // ─── Infer type from current file/url ─────────────────────────────────────
  const inferredType: DocumentType = useMemo(() => {
    const hint = typeHint === "auto" ? null : typeHint;
    if (hint) return hint;
    const filename = driveFile?.name ?? sourceUrl ?? title;
    return inferTypeFromFilename(filename);
  }, [typeHint, driveFile, sourceUrl, title]);

  // Preview the code that will be generated by the DB trigger
  // (sequence number is unknown client-side; show placeholder)
  const codePreview = `MKA-${TYPE_ABBREVIATIONS[inferredType]}-???`;

  // ─── Handle Drive file selection ──────────────────────────────────────────
  const handleSelectDriveFile = (file: any) => {
    setDriveFile({
      id: file.id,
      name: file.name,
      webViewLink: file.webViewLink,
    });
    setSourceUrl(file.webViewLink ?? `https://drive.google.com/file/d/${file.id}/view`);
    setDriveOpen(false);
  };

  // ─── Submit form ──────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate
    if (!title.trim()) {
      setSubmitError("عنوان سند الزامی است.");
      return;
    }
    if (sourceMode === "drive" && !driveFile) {
      setSubmitError("یک فایل از Drive انتخاب کنید.");
      return;
    }
    if (sourceMode === "url" && !sourceUrl) {
      setSubmitError("لینک منبع الزامی است.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const payload = {
        title: title.trim(),
        source_type: sourceMode === "drive" ? "drive" : sourceMode === "url" ? "web" : "manual",
        source_url: sourceUrl || undefined,
        drive_file_id: driveFile?.id,
        source_ref: driveFile?.name,
        type_hint: inferredType,
        expert_notes: expertNotes || undefined,
        extracted_text: extractedText || undefined,
      };

      const result: any = await registerDocument(payload);
      // Show success — the actual code (with sequence number) comes from server
      alert(`سند با کد ${result.code} ثبت شد.`);
      onSaved();
    } catch (err) {
      setSubmitError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Drive health warning */}
      {driveHealth === "error" && sourceMode === "drive" && (
        <div className="flex items-center gap-2 rounded border border-amber-500/40 bg-amber-500/10 p-3 text-amber-700 text-sm">
          <AlertCircle className="size-4" />
          اتصال به Google Drive برقرار نیست. تنظیمات Lovable → Integrations را بررسی کنید یا از حالت «لینک دستی» استفاده کنید.
        </div>
      )}

      {/* Title field — REQUIRED */}
      <div className="space-y-2">
        <Label htmlFor="title">عنوان سند <span className="text-destructive">*</span></Label>
        <Input
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="مثلاً: بخشنامه ۲۰۰/۹۹/۵۲۲ نحوه حسابرسی"
          required
          maxLength={300}
        />
        <p className="text-xs text-muted-foreground">
          عنوان کوتاه و توصیفی. در جست‌وجوها نمایش داده می‌شود.
        </p>
      </div>

      {/* Source mode selector */}
      <div className="space-y-2">
        <Label>روش بارگذاری</Label>
        <div className="flex gap-2">
          <Button
            type="button"
            variant={sourceMode === "drive" ? "default" : "outline"}
            size="sm"
            onClick={() => setSourceMode("drive")}
          >
            <Folder className="ml-2 size-4" /> انتخاب از Drive
          </Button>
          <Button
            type="button"
            variant={sourceMode === "url" ? "default" : "outline"}
            size="sm"
            onClick={() => setSourceMode("url")}
          >
            لینک مستقیم
          </Button>
          <Button
            type="button"
            variant={sourceMode === "manual" ? "default" : "outline"}
            size="sm"
            onClick={() => setSourceMode("manual")}
          >
            متن دستی
          </Button>
        </div>
      </div>

      {/* Source input — varies by mode */}
      {sourceMode === "drive" && (
        <div className="space-y-2">
          <Label>فایل Google Drive</Label>
          {driveFile ? (
            <div className="flex items-center gap-2 rounded border bg-muted/30 p-3">
              <FileText className="size-5 text-blue-600" />
              <div className="flex-1">
                <p className="text-sm font-medium">{driveFile.name}</p>
                <p className="text-xs text-muted-foreground">{driveFile.id}</p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={() => setDriveOpen(true)}>
                تغییر
              </Button>
            </div>
          ) : (
            <Button type="button" variant="outline" onClick={() => setDriveOpen(true)}>
              <Folder className="ml-2 size-4" />
              انتخاب فایل از Drive
            </Button>
          )}
        </div>
      )}

      {sourceMode === "url" && (
        <div className="space-y-2">
          <Label htmlFor="sourceUrl">لینک منبع یا مسیر</Label>
          <Input
            id="sourceUrl"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            placeholder="https://drive.google.com/file/d/.../view"
          />
          <p className="text-xs text-muted-foreground">
            لینک کامل سند در گوگل درایو یا وب‌سایت رسمی.
          </p>
        </div>
      )}

      {/* Type hint (optional) */}
      <div className="space-y-2">
        <Label htmlFor="type">نوع سند</Label>
        <Select
          value={typeHint}
          onValueChange={(v) => setTypeHint(v as DocumentType | "auto")}
        >
          <SelectTrigger id="type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto">خودکار (بر اساس نام فایل)</SelectItem>
            <SelectItem value="law">قانون (LAW)</SelectItem>
            <SelectItem value="circular">بخشنامه (CIR)</SelectItem>
            <SelectItem value="judgment">رأی (JUD)</SelectItem>
            <SelectItem value="contract">قرارداد (CNT)</SelectItem>
            <SelectItem value="appeal">لایحه اعتراض (APL)</SelectItem>
            <SelectItem value="tax_case">پرونده مالیاتی (TAX)</SelectItem>
            <SelectItem value="general">عمومی (GEN)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Auto-generated code preview */}
      <div className="rounded-lg border bg-muted/20 p-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground mb-1">کد سند (خودکار)</p>
            <p className="font-mono text-base font-semibold">{codePreview}</p>
          </div>
          <div className="text-left">
            <p className="text-xs text-muted-foreground">نوع شناسایی‌شده</p>
            <p className="text-sm font-medium">{TYPE_LABELS[TYPE_ABBREVIATIONS[inferredType]]}</p>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          شماره‌ی ترتیبی هنگام ثبت به‌صورت خودکار توسط پایگاه داده تخصیص می‌یابد.
        </p>
      </div>

      {/* Expert notes */}
      <div className="space-y-2">
        <Label htmlFor="expertNotes">یادداشت کارشناس</Label>
        <Textarea
          id="expertNotes"
          value={expertNotes}
          onChange={(e) => setExpertNotes(e.target.value)}
          placeholder="نکات مهم، حساسیت‌ها، ابهامات..."
          rows={3}
        />
      </div>

      {/* Extracted text */}
      <div className="space-y-2">
        <Label htmlFor="extractedText">متن استخراج‌شده (اختیاری)</Label>
        <Textarea
          id="extractedText"
          value={extractedText}
          onChange={(e) => setExtractedText(e.target.value)}
          placeholder="اگر متن سند را جداگانه استخراج کرده‌اید، اینجا paste کنید..."
          rows={5}
        />
      </div>

      {/* Submit error */}
      {submitError && (
        <div className="flex items-start gap-2 rounded border border-destructive/50 bg-destructive/10 p-3">
          <AlertCircle className="size-5 text-destructive flex-shrink-0 mt-0.5" />
          <p className="text-sm text-destructive">{submitError}</p>
        </div>
      )}

      {/* Footer */}
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
          انصراف
        </Button>
        <Button type="submit" disabled={submitting || !title.trim()}>
          {submitting ? (
            <>
              <Loader2 className="ml-2 size-4 animate-spin" />
              در حال ثبت...
            </>
          ) : (
            "ثبت سند"
          )}
        </Button>
      </div>

      {/* Drive file picker dialog */}
      <DrivePickerDialog
        open={driveOpen}
        onClose={() => setDriveOpen(false)}
        onSelect={handleSelectDriveFile}
        folders={driveFolders}
        files={driveFiles}
        loading={driveLoading}
        error={driveError}
        search={driveSearch}
        onSearchChange={setDriveSearch}
        onFolderNavigate={setCurrentFolder}
      />
    </form>
  );
}

// =============================================================================
// Drive Picker Dialog — search + browse Drive files inline
// =============================================================================

function DrivePickerDialog({
  open,
  onClose,
  onSelect,
  folders,
  files,
  loading,
  error,
  search,
  onSearchChange,
  onFolderNavigate,
}: {
  open: boolean;
  onClose: () => void;
  onSelect: (file: any) => void;
  folders: any[];
  files: any[];
  loading: boolean;
  error: string | null;
  search: string;
  onSearchChange: (s: string) => void;
  onFolderNavigate: (folderId: string | undefined) => void;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-lg bg-background shadow-lg">
        <div className="border-b p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold">انتخاب فایل از Google Drive</h3>
            <Button variant="ghost" size="sm" onClick={onClose}>بستن</Button>
          </div>
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="جست‌وجوی نام فایل در Drive..."
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pr-9"
            />
          </div>
        </div>

        <div className="max-h-96 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="flex items-start gap-2 rounded border border-destructive/50 bg-destructive/10 p-3">
              <AlertCircle className="size-5 text-destructive flex-shrink-0" />
              <div>
                <p className="font-medium text-destructive">خطا</p>
                <p className="text-sm text-destructive/80 mt-1">{error}</p>
              </div>
            </div>
          ) : (
            <>
              {/* Folders */}
              {!search && folders.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-muted-foreground mb-2">پوشه‌ها</p>
                  <div className="grid grid-cols-2 gap-2">
                    {folders.map((f) => (
                      <button
                        key={f.id}
                        type="button"
                        onClick={() => onFolderNavigate(f.id)}
                        className="flex items-center gap-2 rounded border p-2 text-right hover:bg-muted/50"
                      >
                        <Folder className="size-4 text-amber-600" />
                        <span className="text-sm truncate">{f.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Files */}
              <p className="text-xs font-medium text-muted-foreground mb-2">فایل‌ها</p>
              {files.length === 0 ? (
                <p className="text-center py-8 text-sm text-muted-foreground">
                  فایلی یافت نشد.
                </p>
              ) : (
                <div className="space-y-1">
                  {files.map((f) => (
                    <button
                      key={f.id}
                      type="button"
                      onClick={() => onSelect(f)}
                      className="flex w-full items-center gap-3 rounded border p-2 text-right hover:bg-muted/50"
                    >
                      <FileText className="size-4 text-blue-600 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{f.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {f.mimeType} · {f.modifiedTime ? new Date(f.modifiedTime).toLocaleDateString("fa-IR") : ""}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Breadcrumb back to root */}
        {!search && (
          <div className="border-t p-3 text-xs">
            <button
              type="button"
              onClick={() => onFolderNavigate(undefined)}
              className="text-blue-600 hover:underline"
            >
              ← بازگشت به پوشه‌ی اصلی
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
