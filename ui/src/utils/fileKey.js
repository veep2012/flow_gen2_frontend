export const getFileKey = (file, fallback = "") => {
  if (file && typeof file === "object") {
    const fileId = file.fileId ?? file.id;
    if (fileId !== null && fileId !== undefined) {
      return `id:${fileId}`;
    }
    const fileName = file.name ?? "";
    const documentNumber = file.documentNumber ?? "";
    if (fileName) {
      return `name:${documentNumber ? `${documentNumber}-` : ""}${fileName}${
        fallback ? `:${fallback}` : ""
      }`;
    }
  }

  if (typeof file === "string") {
    return `name:${file}${fallback ? `:${fallback}` : ""}`;
  }

  return `unknown${fallback ? `:${fallback}` : ""}`;
};
