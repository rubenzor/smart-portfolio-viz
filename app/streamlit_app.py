import streamlit as st
import requests
import time
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ────────────────────────────────
# AUTENTICACIÓN
# ────────────────────────────────

def login_ui():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            st.session_state["token"] = r.json()["access_token"]
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def register_ui():
    st.subheader("Create Account")
    name = st.text_input("Full name")
    email = st.text_input("Email (new user)")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if password != confirm:
            st.error("Passwords do not match")
            return
        r = requests.post(f"{API_URL}/auth/register", json={"name":name,"email": email, "password": password})
        if r.status_code == 200:
            st.success("User created successfully! You can now log in.")
            time.sleep(2)  # Espera 2 segundos antes de redirigir
            st.switch_page("pages/login.py") 
        else:
            st.error(f"Error: {r.text}")
def reset_password_ui():
    st.subheader("🔑 Reset Password")

    # Leer el token del enlace (compatibilidad universal)
    query_params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
    token_param = query_params.get("token")

    if isinstance(token_param, list):
        token = token_param[0] if token_param else None
    else:
        token = token_param

    if not token:
        st.error("Invalid or missing reset link.")
        return

    # Verificar token antes de mostrar formulario
    r = requests.get(f"{API_URL}/auth/verify_reset_token/{token}")
    if r.status_code != 200:
        st.error("Token invalid or expired.")
        return

    st.success("Token valid. You can set a new password.")
    new_pass = st.text_input("New password", type="password")
    confirm = st.text_input("Confirm password", type="password")

    if st.button("Reset password"):
        if new_pass != confirm:
            st.error("Passwords do not match.")
            return
        payload = {"token": token, "new_password": new_pass}
        resp = requests.post(f"{API_URL}/auth/reset_password", json=payload)
        if resp.status_code == 200:
            st.success("Password updated successfully! You can now log in.")
            time.sleep(2)
            st.session_state["auth_view"] = "Login"  # Redirige a login
            st.rerun()
        else:
            try:
                st.error(resp.json().get("detail", "Unknown error"))
            except Exception:
                st.error("Unknown error occurred.")

def forgot_password_ui():
    st.subheader("Forgot Password")
    email = st.text_input("Enter your registered email", key="forgot_email")
    if st.button("Reset Password"):
        r = requests.post(f"{API_URL}/auth/forgot_password", json={"email": email})
        if r.status_code == 200:
            st.success("Password reset link sent to your email.")
        else:
            st.error("Failed to send reset link")

def logout_ui():
    token = st.session_state.get("token")
    if token:
        requests.post(f"{API_URL}/auth/logout", headers={"Authorization": f"Bearer {token}"})
        st.session_state.pop("token", None)
        st.success("Logged out")
        st.rerun()

# ────────────────────────────────
# PÁGINAS
# ────────────────────────────────
def show_portfolios_page(token):
    st.title("📂 My Portfolios")

    # List portfolios
    r = requests.get(f"{API_URL}/portfolios/my", headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 200:
        portfolios = r.json()
        st.dataframe(portfolios)
    else:
        st.error("Failed to fetch portfolios")

    # Create portfolio
    st.subheader("➕ Create New Portfolio")
    name = st.text_input("Portfolio name")
    if st.button("Create Portfolio"):
        payload = {"name": name}
        r = requests.post(
            f"{API_URL}/portfolios/create",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        if r.status_code == 200:
            st.success("Portfolio created successfully!")
            st.rerun()
        else:
            st.error("Error creating portfolio")

def show_analytics_page(token):
    st.title("📊 Analytics Dashboard")

    pid = st.number_input("Portfolio ID", min_value=1, step=1)
    if st.button("Load Metrics"):
        headers = {"Authorization": f"Bearer {token}"}
        perf = requests.get(f"{API_URL}/analytics/{pid}/performance", headers=headers)
        risk = requests.get(f"{API_URL}/analytics/{pid}/risk", headers=headers)

        if perf.status_code == 200 and risk.status_code == 200:
            st.subheader("Performance Metrics")
            st.json(perf.json())
            st.subheader("Risk Metrics")
            st.json(risk.json())
        else:
            st.error("Could not retrieve analytics metrics")

def show_strategy_lab_page():
    st.title("🧠 Strategy Lab")
    st.info("Coming soon: backtesting & ML models!")

def show_altdata_page():
    st.title("🌐 Alternative Data")
    st.info("Coming soon: sentiment & trend analysis!")

def show_recommendations_page():
    st.title("💡 Recommendations")
    st.info("Coming soon: portfolio optimization!")

# ────────────────────────────────
# MAIN
# ────────────────────────────────
def main():
    st.title("Smart Portfolio Viz")

    #Inicialización del estado (crucial)
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "Login"
        
    # Si el enlace contiene ?token=..., mostrar pantalla de reset
    query_params = st.query_params
    if "token" in query_params:
        reset_password_ui()
        return

    # LOGIN / REGISTER / FORGOT PASSWORD
    if "token" not in st.session_state:
        if "auth_view" not in st.session_state:
            st.session_state["auth_view"] = "Login"  # Valor inicial

        view = st.session_state["auth_view"]

        menu = ["Login", "Register", "Forgot Password"]
        selected = st.radio("Select view", menu, horizontal=True, index=menu.index(view))

        # Si el usuario cambia manualmente de vista
        if selected != st.session_state["auth_view"]:
            st.session_state["auth_view"] = selected
            st.rerun()

        if view == "Login":
            login_ui()
        elif view == "Register":
            register_ui()
        elif view == "Forgot Password":
            forgot_password_ui()

    else:
        # Resto de la app (ya autenticado)
        token = st.session_state["token"]
        st.sidebar.title("Navigation")
        choice = st.sidebar.radio(
            "Go to",
            ["Portfolios", "Analytics", "Strategy Lab", "Alternative Data", "Recommendations"]
        )

        if st.sidebar.button("Logout"):
            logout_ui()

        st.write("---")

        if choice == "Portfolios":
            show_portfolios_page(token)
        elif choice == "Analytics":
            show_analytics_page(token)
        elif choice == "Strategy Lab":
            show_strategy_lab_page()
        elif choice == "Alternative Data":
            show_altdata_page()
        elif choice == "Recommendations":
            show_recommendations_page()


if __name__ == "__main__":
    main()
