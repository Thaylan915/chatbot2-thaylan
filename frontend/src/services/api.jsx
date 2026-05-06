import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// Injeta o token JWT em todas as requisições automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redireciona para login se o token expirar
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const failedUrl = error.config?.url || "";

      // Redireciona apenas quando falha a autenticação em si.
      // Requests protegidos como chat/histórico devem exibir erro local,
      // sem derrubar a tela inteira de forma brusca.
      if (failedUrl.includes("/api/token/")) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/";
      }
    }
    return Promise.reject(error);
  }
);

export default api;