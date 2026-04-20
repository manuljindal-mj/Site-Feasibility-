# --------------------------------------------
# Additional utilisation check alert for nearby QIS
# --------------------------------------------

nearby_qis_check = (
    qis_table[qis_table["Distance_km"] <= 1.5]
    if not qis_table.empty
    else pd.DataFrame()
)

qis_names = ", ".join(
    nearby_qis_check["QIS"].astype(str).tolist()
) if not nearby_qis_check.empty else ""

if qis_names:
    st.info(
        f"""QIS exists within 1.5 km radius.
Please check the current utilisation levels before proceeding.

Nearby QIS: {qis_names}"""
    )

# --------------------------------------------
# TABLES
# --------------------------------------------

colA, colB = st.columns(2)

with colA:
    st.subheader("P0 within 1.5km")
    st.dataframe(pd.DataFrame(p0_results))

    st.subheader("Nearest QIS")
    st.dataframe(qis_table)

with colB:
    st.subheader("Nearby Deals")

    if deal_table.empty:
        st.write("No deals nearby")
    else:
        st.dataframe(deal_table)

    if nearest_dark is not None:
        st.write(
            f"Nearest Darkstore: {nearest_dark_name} | {round(nearest_dark, 2)} km"
        )
