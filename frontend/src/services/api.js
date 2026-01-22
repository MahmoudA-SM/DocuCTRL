import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "",
});

const getStoredToken = () => {
  try {
    return localStorage.getItem("access_token");
  } catch (err) {
    return null;
  }
};

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      try {
        localStorage.removeItem("access_token");
      } catch (err) {
        // ignore storage errors
      }
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const getMe = async () => {
  const response = await api.get("/me");
  return response.data;
};

export const getMyProjects = async () => {
  const response = await api.get("/me/projects");
  return response.data;
};

export const getOwnerCompanies = async () => {
  const response = await api.get("/owner-companies");
  return response.data;
};

export const createOwnerCompany = async (payload) => {
  const response = await api.post("/owner-companies", payload);
  return response.data;
};

export const createProject = async (payload) => {
  const response = await api.post("/projects", payload);
  return response.data;
};

export const createUser = async (payload) => {
  const response = await api.post("/users", payload);
  return response.data;
};

export const uploadDocument = async (formData) => {
  const response = await api.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const getProjectDocuments = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/documents`);
  return response.data;
};

export const getAllDocuments = async () => {
  const response = await api.get("/documents");
  return response.data;
};

export const verifySerial = async (serial) => {
  const response = await api.get(`/verify/${serial}`);
  return response.data;
};

export const downloadDocument = async (documentId) => {
  const response = await api.get(`/documents/${documentId}/download`, {
    responseType: "blob",
  });
  return response.data;
};

export const buildVerifyPageUrl = (serial) => `/verify?serial=${encodeURIComponent(serial)}`;

export default api;
