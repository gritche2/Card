import streamlit as st
import db

# Init DB (Run once)
if "db_initialized" not in st.session_state:
    db.init_db()
    st.session_state["db_initialized"] = True

st.set_page_config(page_title="Club de Basket - Échange de Vignettes", page_icon="🏀")

st.title("🏀 Club de Basket - Échange de Vignettes 🏀")

# Sidebar - User Login
st.sidebar.header("Qui es-tu ?")
user_name = st.sidebar.text_input("Ton prénom", key="user_name_input")

if user_name:
    user_name = user_name.strip().title()
    # Add user to DB silently to ensure existence
    db.add_user(user_name)

    # Tabs
    tab1, tab2 = st.tabs(["Ma Collection", "Rapport d'Échanges"])

    with tab1:
        st.header(f"Collection de {user_name}")
        
        # Load current data
        current_needs, current_duplicates = db.get_user_collection(user_name)
        
        # Display current
        st.write(f"**Tu cherches ({len(current_needs)}):** {', '.join(map(str, sorted(current_needs)))}")
        st.write(f"**Tu as en double ({len(current_duplicates)}):** {', '.join(map(str, sorted(current_duplicates)))}")
        
        st.divider()
        
        st.subheader("Mettre à jour ma collection")
        st.info("Entre les numéros séparés par des virgules ou des espaces (ex: 4, 10, 55)")
        # Inputs
        needs_input = st.text_area("Numéros manquants (ceux que tu cherches)", 
                                   value=", ".join(map(str, sorted(current_needs))))
        duplicates_input = st.text_area("Numéros en double (ceux que tu peux donner)", 
                                        value=", ".join(map(str, sorted(current_duplicates))))
        
        if st.button("Enregistrer"):
            try:
                # Parse inputs
                def parse_numbers(text):
                    if not text:
                        return []
                    parts = text.replace(',', ' ').split()
                    return [int(p) for p in parts if p.isdigit()]

                new_needs = parse_numbers(needs_input)
                new_duplicates = parse_numbers(duplicates_input)
                
                db.update_collection(user_name, new_needs, new_duplicates)
                st.success("✅ Collection mise à jour !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde: {e}")

    with tab2:
        st.header("Rapport d'Échanges")
        st.write("C'est ici que la magie opère ! Clique sur le bouton pour voir qui tu peux aider et qui peut t'aider.")
        
        if st.button("Générer le rapport"):
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
                        "user": other_user,
                        "give": sorted(list(give)),
                        "receive": sorted(list(receive))
                    })
            
            if perfect_matches:
                found_exchange = True
                for match in perfect_matches:
                    st.success(f"**{match['user']}** peut te donner : {', '.join(map(str, match['receive']))} \n\n ET tu peux lui donner : {', '.join(map(str, match['give']))}")
            else:
                st.info("Aucun échange parfait trouvé pour le moment.")

            st.divider()

            # 2. One-way Matches (I receive)
            st.subheader("📥 Tu peux recevoir")
            i_receive = []
            for other_user, other_duplicates in all_duplicates.items():
                if other_user == user_name:
                    continue
                
                receive = other_duplicates.intersection(my_needs)
                if receive:
                    i_receive.append({
                        "user": other_user,
                        "receive": sorted(list(receive))
                    })
            
            if i_receive:
                found_exchange = True
                for match in i_receive:
                    st.write(f"**{match['user']}** a en double : {', '.join(map(str, match['receive']))}")
            else:
                st.write("Personne n'a tes manquants pour l'instant.")
                
            st.divider()

            # 3. One-way Matches (I give)
            st.subheader("📤 Tu peux aider")
            i_give = []
            for other_user, other_needs in all_needs.items():
                if other_user == user_name:
                    continue
                
                give = my_duplicates.intersection(other_needs)
                if give:
                    i_give.append({
                        "user": other_user,
                        "give": sorted(list(give))
                    })
                    
            if i_give:
                found_exchange = True
                for match in i_give:
                    st.write(f"**{match['user']}** cherche : {', '.join(map(str, match['give']))}")
            else:
                st.write("Tu n'as aucun sticker que les autres cherchent.")

else:
    st.info("👈 Entre ton nom dans la barre latérale pour commencer.")
