export function formatDuration(seconds) {
  if (!seconds) return "0m";

  const total = Math.round(Number(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);

  if (hours) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function formatDate(dateString) {
  if (!dateString) return "No date";

  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return dateString;

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function inferTaskStatus(deadline) {
  if (!deadline || deadline === "TBD") return "Needs owner";

  const parsed = new Date(deadline);
  if (Number.isNaN(parsed.getTime())) return "In progress";

  const now = new Date();
  const diffDays = (parsed.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);

  if (diffDays < 0) return "At risk";
  if (diffDays < 3) return "Due soon";
  return "On track";
}

export function safeJsonParse(value, fallback = []) {
  if (!value) return fallback;

  if (Array.isArray(value) || typeof value === "object") return value;

  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

export function sentenceCase(value) {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
}
