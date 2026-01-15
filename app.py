import streamlit as st
import db
import pandas as pd
import logging
import io

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Init DB (Run once)
if "db_initialized" not in st.session_state:
    db.init_db()
    st.session_state["db_initialized"] = True

st.set_page_config(page_title="Club de Basket - Échange de Vignettes", page_icon="🏀")

st.title("🏀 Club de Basket - Échange de Vignettes 🏀")

# Sidebar - User Login
st.sidebar.header("Qui es-tu ?")

# Get existing users
existing_users = db.get_users()

# Option to add new user
NEW_USER = "➕ Ajouter un nouveau..."
select_options = [NEW_USER] + existing_users

selected_user = st.sidebar.selectbox("Choisis ton prénom", select_options)

if selected_user == NEW_USER:
    user_name = st.sidebar.text_input("Ton prénom", key="new_user_input")
else:
    user_name = selected_user

if user_name:
    user_name = user_name.strip().title()
    if "current_user" not in st.session_state or st.session_state["current_user"] != user_name:
         logging.info(f"User logged in: {user_name}")
         st.session_state["current_user"] = user_name
    
    # Add user to DB silently to ensure existence
    db.add_user(user_name)

    # Tabs
    tab1, tab2 = st.tabs(["Ma Collection", "Rapport d'Échanges"])

    with tab1:
        st.header(f"Collection de {user_name}")
        
        # Load current data
        current_needs, current_duplicates = db.get_user_collection(user_name)
        
        # Prepare DataFrame for Editor
        # We want two independent columns, so we match lengths with None or Empty
        needs_list = sorted(current_needs)
        duplicates_list = sorted(current_duplicates)
        
        max_len = max(len(needs_list), len(duplicates_list))
        
        # Pad with None
        needs_padded = needs_list + [None] * (max_len - len(needs_list))
        duplicates_padded = duplicates_list + [None] * (max_len - len(duplicates_list))
        
        df = pd.DataFrame({
            "Manquantes (Ce que je cherche)": needs_padded,
            "Doubles (Ce que je donne)": duplicates_padded
        })
        
        st.info("💡 Tu peux copier-coller depuis Excel ou taper directement dans le tableau !")
        
        # Note: use_container_width is deprecated in recent Streamlit, using plain call or width if needed.
        # However, for now we stick to standard call.
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Enregistrer les modifications"):
                try:
                    # Extract clean lists
                    new_needs = []
                    new_duplicates = []
                    
                    # Process Needs
                    for val in edited_df["Manquantes (Ce que je cherche)"]:
                        if pd.notna(val) and str(val).strip() != "":
                            try:
                                new_needs.append(int(val))
                            except ValueError:
                                st.warning(f"Valeur ignorée (pas un nombre) : {val}")

                    # Process Duplicates
                    for val in edited_df["Doubles (Ce que je donne)"]:
                        if pd.notna(val) and str(val).strip() != "":
                            try:
                                new_duplicates.append(int(val))
                            except ValueError:
                                st.warning(f"Valeur ignorée (pas un nombre) : {val}")
                    
                    db.update_collection(user_name, new_needs, new_duplicates)
                    
                    logging.info(f"Update by {user_name}: Needs={len(new_needs)}, Duplicates={len(new_duplicates)}")
                    st.success(f"✅ Collection enregistrée ! ({len(new_needs)} manquantes, {len(new_duplicates)} doubles)")
                    st.rerun()
                except Exception as e:
                    logging.error(f"Error saving collection for {user_name}: {e}")
                    st.error(f"Erreur lors de la sauvegarde: {e}")

        with col2:
             # Excel Export
            try:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    edited_df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Exporter en Excel",
                    data=buffer.getvalue(),
                    file_name=f"collection_{user_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                 st.error(f"Erreur export: {e}")

    with tab2:
        st.header("Rapport d'Échanges")
        st.write("C'est ici que la magie opère ! Clique sur le bouton pour voir qui tu peux aider et qui peut t'aider.")
        
        if st.button("Générer le rapport"):
            logging.info(f"Generating report for {user_name}")
            all_needs, all_duplicates = db.get_all_data()
            
            # Logic
            my_needs = all_needs.get(user_name, set())
            my_duplicates = all_duplicates.get(user_name, set())
            
            found_exchange = False
            
            # 1. Perfect Matches (Two-way)
            st.subheader("🤝 Échanges Parfaits (Donnant-Donnant)")
            perfect_matches = []
            
            for other_user, other_needs in all_needs.items():
                if other_user == user_name:
                    continue
                
                other_duplicates = all_duplicates.get(other_user, set())
                
                # What I can give to them
                give = my_duplicates.intersection(other_needs)
                # What they can give to me
                receive = other_duplicates.intersection(my_needs)
                
                if give and receive:
                    perfect_matches.append({
                        "Participante": other_user,
                        "Je reçois": ', '.join(map(str, sorted(list(receive)))),
                        "Je donne": ', '.join(map(str, sorted(list(give))))
                    })
            
            if perfect_matches:
                found_exchange = True
                st.table(pd.DataFrame(perfect_matches))
            else:
                st.info("Aucun échange parfait trouvé pour le moment.")

            st.divider()

            # 2. One-way Matches (I receive)
            st.subheader("📥 Tu peux recevoir (Ils t'aident)")
            i_receive = []
            for other_user, other_duplicates in all_duplicates.items():
                if other_user == user_name:
                    continue
                
                receive = other_duplicates.intersection(my_needs)
                if receive:
                    i_receive.append({
                        "Participante": other_user,
                        "Je reçois": ', '.join(map(str, sorted(list(receive))))
                    })
            
            if i_receive:
                found_exchange = True
                st.table(pd.DataFrame(i_receive))
            else:
                st.write("Personne n'a tes manquants pour l'instant.")
                
            st.divider()

            # 3. One-way Matches (I give)
            st.subheader("📤 Tu peux aider (Tu donnes)")
            i_give = []
            for other_user, other_needs in all_needs.items():
                if other_user == user_name:
                    continue
                
                give = my_duplicates.intersection(other_needs)
                if give:
                    i_give.append({
                        "Participante": other_user,
                        "Je donne": ', '.join(map(str, sorted(list(give))))
                    })
                    
            if i_give:
                found_exchange = True
                st.table(pd.DataFrame(i_give))
            else:
                st.write("Tu n'as aucun sticker que les autres cherchent.")

else:
    st.info("👈 Entre ton nom dans la barre latérale pour commencer.")
