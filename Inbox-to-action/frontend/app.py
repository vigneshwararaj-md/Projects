import os, requests, streamlit as st

API = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Inbox → Action", page_icon="📥")
st.title("📥 Inbox → Action")

if "token" not in st.session_state:
    st.session_state.token = None

def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

if not st.session_state.token:
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])
    with tab_login:
        e = st.text_input("Email", key="le")
        p = st.text_input("Password", type="password", key="lp")
        if st.button("Log in"):
            r = requests.post(f"{API}/auth/login", json={"email": e, "password": p})
            if r.ok:
                st.session_state.token = r.json()["access_token"]
                st.rerun()
            else:
                st.error(r.text)
    with tab_signup:
        e2 = st.text_input("Email", key="se")
        p2 = st.text_input("Password", type="password", key="sp")
        if st.button("Sign up"):
            r = requests.post(f"{API}/auth/signup", json={"email": e2, "password": p2})
            if r.ok and r.json().get("access_token"):
                st.session_state.token = r.json()["access_token"]
                st.rerun()
            elif r.ok:
                st.success("Check your email to confirm, then log in.")
            else:
                st.error(r.text)
else:
    st.success("Logged in")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔗 Connect Gmail"):
            st.markdown(f"[Authorize Gmail]({API}/auth/gmail/start)")
        with c2:
            if st.button("🔄 Process inbox now"):
                r = requests.post(f"{API}/api/process-inbox", headers=auth_headers())
                if r.status_code == 200:
                    st.json(r.json())
                else:
                    st.error(f"Backend Error ({r.status_code}): {r.text}")
    st.divider()
    st.subheader("Your tasks")
    r = requests.get(f"{API}/api/actions", headers=auth_headers())
    if r.ok:
        for a in r.json():
            due = a.get("due_date") or ""
            # Clean up the date string to only show YYYY-MM-DD
            display_date = due.split("T")[0] if due else "No due date"
            st.checkbox(f"[{a['priority']}] {a['title']} — {display_date}")
    else:
        st.error("Could not load tasks")