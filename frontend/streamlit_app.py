import datetime
import os
import uuid
from typing import Any, Dict

import requests
import streamlit as st

API_BASE = os.getenv("VCAT_BOND_BUNDLE_API_BASE", "https://vcat-bond-bundle-mvp.onrender.com")


def safe_json(resp: requests.Response) -> Dict[str, Any]:
    """Try to parse JSON; return a readable fallback when response isn't JSON."""
    try:
        data = resp.json()
        if isinstance(data, dict):
            return data
        return {"data": data}
    except Exception:
        text = (resp.text or "").strip()
        return {
            "detail": f"Server did not return JSON (HTTP {resp.status_code}).",
            "content_type": resp.headers.get("content-type", ""),
            "body_preview": text[:1000],
        }


def error_message(resp: requests.Response, fallback: str) -> str:
    payload = safe_json(resp)
    detail = payload.get("detail")
    if detail:
        return str(detail)
    return f"{fallback} (HTTP {resp.status_code})"


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
        try:
            resp = requests.post(f"{API_BASE}/case", json=payload, timeout=30)
        except requests.RequestException as exc:
            st.error(f"Could not reach backend: {exc}")
            st.stop()

        if resp.status_code == 200:
            st.session_state["case"] = safe_json(resp)
            st.success("Saved.")
        else:
            st.error(error_message(resp, "Could not save case"))

    case = st.session_state.get("case")
    if not case:
        st.stop()

    case_id = case.get("id")
    if not case_id:
        st.error("Case data is missing an id. Please save your case again.")
        st.stop()

    st.header("Upload evidence")
    uploaded_files = st.file_uploader(
        "Upload PDFs or images",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        for f in uploaded_files:
            files = {"file": (f.name, f.getvalue(), f.type)}
            try:
                r = requests.post(f"{API_BASE}/upload", params={"case_id": case_id}, files=files, timeout=60)
            except requests.RequestException as exc:
                st.error(f"Upload failed for {f.name}: {exc}")
                continue

            if r.status_code == 200:
                st.success(f"Uploaded {f.name}")
            else:
                st.error(f"Upload failed for {f.name}: {error_message(r, 'Upload failed')}")

    if st.button("Generate preview"):
        try:
            r = requests.post(f"{API_BASE}/case/{case_id}/generate-preview", timeout=60)
        except requests.RequestException as exc:
            st.error(f"Preview request failed: {exc}")
            r = None

        if r is not None:
            if r.status_code == 200:
                st.session_state["preview"] = safe_json(r)
                st.success("Preview ready.")
            else:
                st.error(error_message(r, "Preview failed"))

    preview = st.session_state.get("preview")
    if not preview:
        st.stop()

    st.header("Preview downloads (watermarked)")
    for doc_type in preview.get("documents", {}).keys():
        try:
            r = requests.get(f"{API_BASE}/case/{case_id}/documents/{doc_type}", params={"preview": True}, timeout=60)
        except requests.RequestException as exc:
            st.error(f"Could not fetch {doc_type}: {exc}")
            continue

        content_type = r.headers.get("content-type", "").lower()
        if r.status_code == 200 and "application/pdf" in content_type:
            st.download_button(
                f"Download {doc_type} (preview)",
                data=r.content,
                file_name=f"{doc_type}_preview.pdf",
                mime="application/pdf",
            )
        else:
            st.error(f"Could not fetch {doc_type}: {error_message(r, 'Unexpected response')}.")

    if st.button("Unlock final documents ($39)"):
        try:
            r = requests.post(f"{API_BASE}/case/{case_id}/create-checkout-session", timeout=30)
        except requests.RequestException as exc:
            st.error(f"Could not start payment: {exc}")
            r = None

        if r is not None:
            if r.status_code == 200:
                checkout = safe_json(r)
                st.success("Payment link created (stub in this MVP if Stripe keys not set).")
                st.write(checkout.get("checkout_url", "No checkout URL returned."))
                case["status"] = "paid"
                st.session_state["case"] = case
            else:
                st.error(error_message(r, "Could not start payment"))

    if st.session_state.get("case", {}).get("status") == "paid":
        st.header("Final downloads (no watermark)")
        for doc_type in preview.get("documents", {}).keys():
            try:
                r = requests.get(
                    f"{API_BASE}/case/{case_id}/documents/{doc_type}",
                    params={"preview": False},
                    timeout=60,
                )
            except requests.RequestException as exc:
                st.error(f"Could not fetch final {doc_type}: {exc}")
                continue

            content_type = r.headers.get("content-type", "").lower()
            if r.status_code == 200 and "application/pdf" in content_type:
                st.download_button(
                    f"Download {doc_type} (final)",
                    data=r.content,
                    file_name=f"{doc_type}.pdf",
                    mime="application/pdf",
                )
            else:
                st.error(f"Could not fetch final {doc_type}: {error_message(r, 'Unexpected response')}.")


if __name__ == "__main__":
    main()
