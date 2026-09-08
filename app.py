# --- TAB 3: DETAILANSICHT ---
with tab_detail:
    st.header("Gegenstand-Details & Verwaltung")
    
    if df_items.empty:
        st.info("Derzeit gibt es keine eingetragenen Fundstücke.")
    else:
        all_ids = df_items["id"].tolist()
        
        default_index = 0
        if st.session_state.selected_item_id in all_ids:
            default_index = all_ids.index(st.session_state.selected_item_id)
            
        selected_id = st.selectbox(
            "Fundstück auswählen", 
            options=all_ids,
            index=default_index,
            format_func=lambda x: f"ID {x}: {df_items.loc[df_items['id'] == x, 'titel'].values[0]} ({df_items.loc[df_items['id'] == x, 'status'].values[0]})"
        )
        
        item_data = df_items[df_items["id"] == selected_id].iloc[0]
        
        col_img, col_info = st.columns([1, 1])
        with col_img:
            if pd.notna(item_data["bild_base64"]) and str(item_data["bild_base64"]).startswith("data:image"):
                st.image(item_data["bild_base64"], use_container_width=True)
        
        with col_info:
            st.title(item_data["titel"])
            st.write(f"**Status:** {item_data['status']}")
            st.write(f"**Kategorie:** {item_data['kategorie']}")
            st.write(f"**Fundort:** {item_data['fundort']} (Raum: {item_data['raum']})")
            st.write(f"**Gefunden am:** {item_data['datum']}")
            st.write(f"**Kontakt / Abgabeort:** {item_data['kontakt']}")
            
            st.divider()
            
            col_action1, col_action2 = st.columns(2)
            
            # Status auf Abgeholt setzen
            with col_action1:
                if item_data["status"] == "Offen":
                    if st.button("Das gehört mir! (Abgeholt)", use_container_width=True):
                        df_items.loc[df_items["id"] == selected_id, "status"] = "Abgeholt"
                        save_data(df_items)
                        st.success("Als 'Abgeholt' markiert!")
                        st.rerun()
                else:
                    st.warning("Bereits abgeholt.")

            # Eintrag komplett aus der Datenbank löschen
            with col_action2:
                if st.button("🗑️ Eintrag löschen", type="primary", use_container_width=True):
                    df_items = df_items[df_items["id"] != selected_id]
                    save_data(df_items)
                    st.session_state.selected_item_id = None
                    st.success("Eintrag erfolgreich gelöscht!")
                    st.rerun()
