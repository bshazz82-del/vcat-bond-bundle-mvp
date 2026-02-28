import os
import uuid
import datetime
from typing import Optional

import streamlit as st
import requests

API_BASE = os.getenv("VCAT_BOND_BUNDLE_API_BASE", "http://localhost:8000")

def main() -> None:
    st.set_page_config(page_title="VCAT Bond Bundle", layout="centered")
    st.title("VCAT Bond Bundle – Bond Recovery Assistant")
    st.markdown(
        """
        This tool helps Victorian renters prepare documents for a bond return application.
        It does **not** give legal advice.
        """
    )

    if "session_uuid" not in st.session_state:
        st.session_state["session_uuid"] = str(uuid.uuid4())
    session_uuid = st.session_state["session_uuid"]

    st.header("Check if this tool is right for you")
    with st.form("scope_form"):
        is_tenant = st.checkbox("I am the renter and I want the bond back")
        no_fv = st.checkbox("This does not involve family violence or criminal issues")
        no_commercial = st.checkbox("This is not a commercial lease (shop/warehouse/business)")
        only_bond = st.checkbox("This is only about the bond (no other claims like repairs/compensation)")
        go = st.form_submit_button("Continue")

    if go:
        if not (is_tenant and no_fv and no_commercial and only_bond):
            st.error("Sorry — this tool only handles simple renter-initiated bond return matters.")
            st.stop()
        st.session_state["scope_ok"] = True

    if not st.session_state.get("scope_ok"):
        st.stop()

    st.header("Your case details")
    with st.form("case_form"):
        property_address = st.text_input("Property address")
        tenancy_end_date = st.date_input("Date tenancy ended", value=datetime.date.today())
        bond_amount = st.text_input("Bond amount ($)")
        narrative = st.text_area("What happened? (short, factual)")
        orders_sought = st.text_area("What do you want VCAT to order?", value="Return the bond in full.")
        save_case = st.form_submit_button("Save")

    if save_case:
        payload = {
            "session_uuid": session_uuid,
            "property_address": property_address,
            "tenancy_end_date": tenancy_end_date.isoformat() + "T00:00:00",
            "bond_amount": bond_amount,
            "narrative": narrative,
            "orders_sought": orders_sought,
        }
        resp = requests.post(f"{API_BASE}/case", json=payload)
        if resp.status_code == 200:
            st.session_state["case"] = resp.json()
            st.success("Saved.")
        else:
            st.error(resp.json().get("detail", "Could not save."))

    case = st.session_state.get("case")
    if not case:
        st.stop()

    case_id = case["id"]

    st.header("Upload evidence")
    uploaded_files = st.file_uploader("Upload PDFs or images", type=["pdf","jpg","jpeg","png"], accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            files = {"file": (f.name, f.getvalue(), f.type)}
            r = requests.post(f"{API_BASE}/upload", params={"case_id": case_id}, files=files)
            if r.status_code == 200:
                st.success(f"Uploaded {f.name}")
            else:
                st.error(f"Upload failed: {r.json().get('detail')}")

    if st.button("Generate preview"):
        r = requests.post(f"{API_BASE}/case/{case_id}/generate-preview")
        if r.status_code == 200:
            st.session_state["preview"] = r.json()
            st.success("Preview ready.")
        else:
            st.error(r.json().get("detail", "Preview failed."))

    preview = st.session_state.get("preview")
    if not preview:
        st.stop()

    st.header("Preview downloads (watermarked)")
    for doc_type in preview.get("documents", {}).keys():
        r = requests.get(f"{API_BASE}/case/{case_id}/documents/{doc_type}", params={"preview": True})
        if r.status_code == 200:
            st.download_button(f"Download {doc_type} (preview)", data=r.content, file_name=f"{doc_type}_preview.pdf")
        else:
            st.write(f"Could not fetch {doc_type}")

    if st.button("Unlock final documents ($39)"):
        r = requests.post(f"{API_BASE}/case/{case_id}/create-checkout-session")
        if r.status_code == 200:
            st.success("Payment link created (stub in this MVP if Stripe keys not set).")
            st.write(r.json().get("checkout_url"))
            # In stub mode, backend marks paid immediately
            case["status"] = "paid"
            st.session_state["case"] = case
        else:
            st.error(r.json().get("detail", "Could not start payment."))

    if st.session_state["case"].get("status") == "paid":
        st.header("Final downloads (no watermark)")
        for doc_type in preview.get("documents", {}).keys():
            r = requests.get(f"{API_BASE}/case/{case_id}/documents/{doc_type}", params={"preview": False})
            if r.status_code == 200:
                st.download_button(f"Download {doc_type} (final)", data=r.content, file_name=f"{doc_type}.pdf")
            else:
                st.write(f"Could not fetch final {doc_type}")

if __name__ == "__main__":
    main()
