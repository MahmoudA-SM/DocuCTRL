import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "",
});

console.log("API BASE:", process.env.REACT_APP_API_BASE_URL);

export const getMe = async () => {
  const response = await api.get("/me");
  return response.data;
};

export const getMyProjects = async () => {
  const response = await api.get("/me/projects");
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

export const verifySerial = async (serial) => {
  const response = await api.get(`/verify/${serial}`);
  return response.data;
};

export const buildDownloadUrl = (documentId) =>
  `${api.defaults.baseURL || ""}/documents/${documentId}/download`;

export const buildVerifyUrl = (serial) =>
  `${api.defaults.baseURL || ""}/verify/${serial}`;

export default api;
