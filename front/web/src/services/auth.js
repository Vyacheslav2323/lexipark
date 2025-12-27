export function getToken() {
    return localStorage.getItem("access_token");
}
  
export function isLoggedIn() {
    return !!getToken();
}

export function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("chat_id");
}