export const normalizeFile = (input = {}, overrides = {}) => {
  const raw = input && typeof input === "object" ? input : {};
  const id = raw.fileId ?? raw.id ?? null;
  const name = raw.name ?? raw.filename ?? "";

  return {
    fileId: id,
    id,
    name,
    documentNumber: raw.documentNumber ?? overrides.documentNumber ?? null,
    uploadedAt: raw.uploadedAt ?? overrides.uploadedAt ?? null,
    s3_uid: raw.s3_uid ?? raw.s3Uid ?? null,
    mimetype: raw.mimetype ?? raw.mimeType ?? null,
    revId: raw.revId ?? raw.rev_id ?? null,
    isFromApi: raw.isFromApi ?? overrides.isFromApi ?? false,
  };
};
