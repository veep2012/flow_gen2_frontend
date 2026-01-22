/**
 * Utility functions for file type detection and icon assignment
 */

/**
 * Get the file extension from a filename
 * @param {string} filename - The filename to extract extension from
 * @returns {string} - The file extension (lowercase, without the dot)
 */
export const getFileExtension = (filename) => {
  if (!filename || typeof filename !== "string") return "";
  const parts = filename.split(".");
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : "";
};

/**
 * Get the appropriate icon for a file type
 * @param {string} filename - The filename
 * @returns {string} - The icon character/emoji for the file type
 */
export const getFileIcon = (filename) => {
  const ext = getFileExtension(filename);

  // PDF files
  if (ext === "pdf") return "📕";

  // Word documents
  if (["doc", "docx"].includes(ext)) return "📘";

  // Excel spreadsheets
  if (["xls", "xlsx"].includes(ext)) return "📗";

  // PowerPoint presentations
  if (["ppt", "pptx"].includes(ext)) return "📙";

  // Images
  if (["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp"].includes(ext)) return "🖼️";

  // Archives
  if (["zip", "rar", "7z", "tar", "gz"].includes(ext)) return "📦";

  // Text files
  if (["txt", "csv", "log"].includes(ext)) return "📄";

  // Code files
  if (
    ["js", "jsx", "ts", "tsx", "py", "java", "cpp", "c", "html", "css", "json", "xml"].includes(ext)
  )
    return "💻";

  // Default file icon
  return "📄";
};

/**
 * Get the file type label for display
 * @param {string} filename - The filename
 * @returns {string} - The file type label
 */
export const getFileTypeLabel = (filename) => {
  const ext = getFileExtension(filename);

  const typeMap = {
    pdf: "PDF Document",
    doc: "Word Document",
    docx: "Word Document",
    xls: "Excel Spreadsheet",
    xlsx: "Excel Spreadsheet",
    ppt: "PowerPoint Presentation",
    pptx: "PowerPoint Presentation",
    jpg: "Image",
    jpeg: "Image",
    png: "Image",
    gif: "Image",
    bmp: "Image",
    svg: "SVG Image",
    webp: "Image",
    zip: "ZIP Archive",
    rar: "RAR Archive",
    txt: "Text File",
    csv: "CSV File",
    json: "JSON File",
    xml: "XML File",
    js: "JavaScript File",
    jsx: "React Component",
    ts: "TypeScript File",
    tsx: "React TypeScript Component",
    py: "Python File",
  };

  return typeMap[ext] || "File";
};
