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

export const getVisibleUsers = async (projectId) => {
  const response = await api.get("/users/visible", {
    params: { project_id: projectId },
  });
  return response.data;
};

export const getPermissions = async (projectId) => {
  const response = await api.get("/permissions", {
    params: { project_id: projectId },
  });
  return response.data;
};

export const getRolePresets = async (projectId) => {
  const response = await api.get("/roles/presets", {
    params: { project_id: projectId },
  });
  return response.data;
};

export const getUserPermissionsForProject = async ({ projectId, userId }) => {
  const response = await api.get(`/projects/${projectId}/users/${userId}/permissions`);
  return response.data;
};

export const setUserPermissionsForProject = async ({ projectId, userId, permissions }) => {
  const response = await api.put(`/projects/${projectId}/users/${userId}/permissions`, {
    permissions,
  });
  return response.data;
};

export const getAdminUsers = async () => {
  const response = await api.get("/admin/users");
  return response.data;
};

export const assignUserToProject = async ({ projectId, userId }) => {
  const response = await api.post(`/projects/${projectId}/users/${userId}/assign`);
  return response.data;
};

export const removeUserFromProject = async ({ projectId, userId }) => {
  const response = await api.delete(`/projects/${projectId}/users/${userId}/assign`);
  return response.data;
};

export const assignUserRoleToProject = async ({ projectId, userId, roleName }) => {
  const response = await api.post(`/projects/${projectId}/users/${userId}/roles`, {
    role_name: roleName,
  });
  return response.data;
};

export const removeUserRoleFromProject = async ({ projectId, userId, roleName }) => {
  const response = await api.delete(`/projects/${projectId}/users/${userId}/roles/${roleName}`);
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

export const exportDocuments = async (projectId) => {
  const response = await api.get("/documents/export", {
    params: projectId ? { project_id: projectId } : {},
    responseType: "blob",
  });
  return response.data;
};

export const buildVerifyPageUrl = (serial) => `/verify?serial=${encodeURIComponent(serial)}`;

export default api;
