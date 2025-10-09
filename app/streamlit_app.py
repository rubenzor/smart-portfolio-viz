import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def login_ui():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            data = r.json()
            st.session_state["token"] = data["access_token"]
            st.success("Logged in!")
        else:
            st.error("Invalid credentials")

def me_ui():
    token = st.session_state.get("token")
    if not token:
        st.warning("Not logged in")
        return
    r = requests.get(f"{API_URL}/me", headers={"Authorization": f"Bearer {token}"})
    st.write(r.json())
    if st.button("Logout"):
        requests.post(f"{API_URL}/auth/logout", headers={"Authorization": f"Bearer {token}"})
        st.session_state.pop("token", None)
        st.success("Logged out")

def main():
    st.title("Smart Portfolio Viz")
    if "token" not in st.session_state:
        login_ui()
    else:
        st.sidebar.success("Authenticated")
        me_ui()
        st.write("---")
        st.subheader("Aquí irían tus páginas: Portfolio, Risk, Strategies, AltData, Recos...")

if __name__ == "__main__":
    main()
