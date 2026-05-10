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

// ── Refresh automático em 401 ─────────────────────────────────────────────
// Ao receber 401, tenta renovar o access_token via /api/auth/refresh/ usando
// o refresh_token guardado, e refaz a request original. Se a renovação falhar,
// limpa os tokens e manda para o login.
let refreshing = null;

async function fazerRefresh() {
  if (refreshing) return refreshing;
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) throw new Error("sem refresh token");

  refreshing = axios
    .post("http://127.0.0.1:8000/api/auth/refresh/", { refresh: refreshToken })
    .then((res) => {
      const novoAccess = res.data?.access;
      if (!novoAccess) throw new Error("resposta de refresh sem access token");
      localStorage.setItem("access_token", novoAccess);
      return novoAccess;
    })
    .finally(() => {
      refreshing = null;
    });

  return refreshing;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const failedUrl = original?.url || "";

    // Só tenta refresh em 401, sem loop, e sem ser na rota de login/refresh
    if (
      status === 401 &&
      !original.__retry &&
      !failedUrl.includes("/api/auth/login/") &&
      !failedUrl.includes("/api/auth/refresh/") &&
      !failedUrl.includes("/api/token/")
    ) {
      original.__retry = true;
      try {
        const novoAccess = await fazerRefresh();
        original.headers.Authorization = `Bearer ${novoAccess}`;
        return api(original);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/";
        return Promise.reject(error);
      }
    }

    // 401 em login/refresh = sessão expirada de fato → logout
    if (
      status === 401 &&
      (failedUrl.includes("/api/token/") || failedUrl.includes("/api/auth/refresh/"))
    ) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/";
    }

    return Promise.reject(error);
  }
);

export default api;
