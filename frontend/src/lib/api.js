const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

export const api = {
  getHealth: () => request("/health"),
  listMeetings: () => request("/meetings?limit=100"),
  getMeeting: (meetingId) => request(`/meetings/${meetingId}`),
  getStatus: (meetingId) => request(`/status/${meetingId}`),
  uploadMeeting: async (file, summaryStyle) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("summary_style", summaryStyle);

    return request("/upload", {
      method: "POST",
      body: formData,
    });
  },
};
