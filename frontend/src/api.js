const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL.replace(/\/$/, "")}${path}`, options);
  } catch {
    throw new Error("Cannot reach the API. Check that the backend is running and the API address is correct.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = Array.isArray(body.detail)
        ? body.detail.map((item) => item.msg).join("; ")
        : body.detail || detail;
    } catch {
      // response wasn't JSON, keep the default message
    }
    throw new Error(res.status >= 500 ? "The API is unavailable or encountered an error. Check the backend logs." : detail);
  }
  return res.status === 204 ? null : res.json();
}

export function uploadSheet(file, uploadDate) {
  const formData = new FormData();
  formData.append("file", file);
  if (uploadDate) {
    formData.append("upload_date", uploadDate);
  }
  return request("/api/uploads", { method: "POST", body: formData });
}

export function getSummary(uploadDate) {
  return request(`/api/dashboard/summary${uploadDate ? `?upload_date=${uploadDate}` : ""}`);
}

export function getByProduct(uploadDate) {
  const q = uploadDate ? `?upload_date=${uploadDate}` : "";
  return request(`/api/dashboard/by-product${q}`);
}

export function getByDays(uploadDate) {
  const q = uploadDate ? `?upload_date=${uploadDate}` : "";
  return request(`/api/dashboard/by-days${q}`);
}

export function getByCategory(uploadDate) {
  const q = uploadDate ? `?upload_date=${uploadDate}` : "";
  return request(`/api/dashboard/by-category${q}`);
}

export function getTrend(uploadDate) {
  return request(`/api/dashboard/trend${uploadDate ? `?upload_date=${uploadDate}` : ""}`);
}

export function getDisappeared(uploadDate) {
  return request(`/api/dashboard/disappeared${uploadDate ? `?upload_date=${uploadDate}` : ""}`);
}

export function getUploadDates() {
  return request("/api/dashboard/upload-dates");
}

export function getLoanHistory(loanId) {
  return request(`/api/loans/${encodeURIComponent(loanId)}/history`);
}
