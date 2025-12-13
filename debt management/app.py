import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
from datetime import datetime, timedelta
import copy

# Configuration de la page
st.set_page_config(
    page_title="Credit Manager",
    page_icon="💳",
    layout="wide"
)

# Dictionnaire des traductions
TRANSLATIONS = {
    "fr": {
        "title": "💳 Gestionnaire de Crédits et Simulations",
        "language": "Langue",
        "credit_management": "📊 Gestion des Crédits",
        "add_credit": "➕ Ajouter un Crédit",
        "credit_name": "Nom du crédit",
        "current_balance": "Solde actuel (€)",
        "annual_rate": "Taux annuel (%)",
        "remaining_duration": "Durée restante (mois)",
        "add_credit_btn": "Ajouter le crédit",
        "additional_budget": "💰 Budget Supplémentaire",
        "monthly_additional": "Budget mensuel supplémentaire (€)",
        "existing_credits": "📋 Crédits Existants",
        "balance": "Solde",
        "rate": "Taux",
        "monthly_payment": "Paiement mensuel",
        "remaining_term": "Durée restante",
        "remove": "Supprimer",
        "add_credits_info": "👈 Ajoutez des crédits dans la barre latérale pour commencer les simulations.",
        "overview": "📊 Vue d'ensemble",
        "avalanche_method": "🏔️ Méthode Avalanche",
        "snowball_method": "❄️ Méthode Snowball",
        "comparison": "⚖️ Comparaison",
        "credit_overview": "📊 Vue d'ensemble de vos crédits",
        "total_debt": "Dette totale",
        "monthly_payments": "Paiements mensuels",
        "total_interests": "Intérêts totaux",
        "weighted_avg_rate": "Taux moyen pondéré",
        "credit_details": "📋 Détail des crédits",
        "name": "Nom",
        "debt_distribution": "Répartition des dettes",
        "interest_rates": "Taux d'intérêt par crédit",
        "credit": "Crédit",
        "avalanche_info": "La méthode avalanche consiste à rembourser en priorité les crédits avec les taux d'intérêt les plus élevés.",
        "snowball_info": "La méthode snowball consiste à rembourser en priorité les crédits avec les soldes les plus petits.",
        "calculate_avalanche": "Calculer simulation Avalanche",
        "calculate_snowball": "Calculer simulation Snowball",
        "total_duration": "Durée totale",
        "total_paid": "Total payé",
        "interest_savings": "Économies d'intérêts",
        "balance_evolution": "Évolution des soldes",
        "month": "Mois",
        "balance_currency": "Solde (€)",
        "repayment_schedule": "📋 Calendrier de remboursement",
        "total_payment": "Paiement total",
        "free_budget": "Budget libre",
        "months_displayed": "Affichage des 12 premiers mois sur {0} mois total.",
        "compare_methods": "Comparer les méthodes",
        "comparison_title": "Comparaison des méthodes Avalanche vs Snowball",
        "total_debt_evolution": "Évolution du total des dettes",
        "monthly_payments_chart": "Paiements mensuels",
        "avalanche_debt": "Avalanche - Dette totale",
        "snowball_debt": "Snowball - Dette totale",
        "avalanche_payments": "Avalanche - Paiements",
        "snowball_payments": "Snowball - Paiements",
        "amount": "Montant (€)",
        "payment": "Paiement (€)",
        "comparison_summary": "📊 Résumé de la comparaison",
        "method": "Méthode",
        "duration_months": "Durée (mois)",
        "total_cost": "Coût total (€)",
        "interests_paid": "Intérêts payés (€)",
        "difference": "Différence",
        "avalanche_recommendation": "💡 **Recommandation**: La méthode Avalanche vous fera économiser plus d'argent en intérêts.",
        "snowball_recommendation": "💡 **Recommandation**: La méthode Snowball coûte un peu plus cher mais peut être plus motivante psychologiquement.",
        "similar_cost": "💡 Les deux méthodes ont un coût similaire, choisissez celle qui vous motive le plus.",
        "footer_tip": "💡 **Conseil**: Utilisez la méthode Avalanche pour minimiser les intérêts ou Snowball pour la motivation psychologique.",
        "principal_paid": "Principal payé",
        "remaining_debt": "Dette restante",
        "credit_added": "Crédit '{0}' ajouté avec succès!",
        "fill_all_fields": "Veuillez remplir tous les champs correctement.",
        "total_interests_label": "Intérêts totaux",
        "save_load": "💾 Sauvegarder/Charger",
        "save_scenario": "Sauvegarder le scénario",
        "scenario_name": "Nom du scénario",
        "save_btn": "Sauvegarder",
        "load_scenario": "Charger un scénario",
        "select_scenario": "Sélectionner un scénario",
        "load_btn": "Charger",
        "delete_btn": "Supprimer",
        "export_csv": "Exporter en CSV",
        "import_csv": "Importer depuis CSV",
        "download_csv": "Télécharger CSV",
        "upload_csv": "Uploader un fichier CSV",
        "scenario_saved": "Scénario '{0}' sauvegardé avec succès!",
        "scenario_loaded": "Scénario '{0}' chargé avec succès!",
        "scenario_deleted": "Scénario '{0}' supprimé!",
        "provide_scenario_name": "Veuillez fournir un nom de scénario.",
        "select_scenario_to_load": "Veuillez sélectionner un scénario à charger.",
        "no_scenarios": "Aucun scénario sauvegardé.",
        "csv_imported": "Données CSV importées avec succès!",
        "csv_error": "Erreur lors de l'import du fichier CSV.",
    },
    "en": {
        "title": "💳 Credit Manager and Simulations",
        "language": "Language",
        "credit_management": "📊 Credit Management",
        "add_credit": "➕ Add Credit",
        "credit_name": "Credit name",
        "current_balance": "Current balance (€)",
        "annual_rate": "Annual rate (%)",
        "remaining_duration": "Remaining duration (months)",
        "add_credit_btn": "Add credit",
        "additional_budget": "💰 Additional Budget",
        "monthly_additional": "Monthly additional budget (€)",
        "existing_credits": "📋 Existing Credits",
        "balance": "Balance",
        "rate": "Rate",
        "monthly_payment": "Monthly payment",
        "remaining_term": "Remaining term",
        "remove": "Remove",
        "add_credits_info": "👈 Add credits in the sidebar to start simulations.",
        "overview": "📊 Overview",
        "avalanche_method": "🏔️ Avalanche Method",
        "snowball_method": "❄️ Snowball Method",
        "comparison": "⚖️ Comparison",
        "credit_overview": "📊 Your credits overview",
        "total_debt": "Total debt",
        "monthly_payments": "Monthly payments",
        "total_interests": "Total interests",
        "weighted_avg_rate": "Weighted average rate",
        "credit_details": "📋 Credit details",
        "name": "Name",
        "debt_distribution": "Debt distribution",
        "interest_rates": "Interest rates by credit",
        "credit": "Credit",
        "avalanche_info": "The avalanche method consists of prioritizing repayment of credits with the highest interest rates.",
        "snowball_info": "The snowball method consists of prioritizing repayment of credits with the smallest balances.",
        "calculate_avalanche": "Calculate Avalanche simulation",
        "calculate_snowball": "Calculate Snowball simulation",
        "total_duration": "Total duration",
        "total_paid": "Total paid",
        "interest_savings": "Interest savings",
        "balance_evolution": "Balance evolution",
        "month": "Month",
        "balance_currency": "Balance (€)",
        "repayment_schedule": "📋 Repayment schedule",
        "total_payment": "Total payment",
        "free_budget": "Free budget",
        "months_displayed": "Showing first 12 months out of {0} total months.",
        "compare_methods": "Compare methods",
        "comparison_title": "Avalanche vs Snowball methods comparison",
        "total_debt_evolution": "Total debt evolution",
        "monthly_payments_chart": "Monthly payments",
        "avalanche_debt": "Avalanche - Total debt",
        "snowball_debt": "Snowball - Total debt",
        "avalanche_payments": "Avalanche - Payments",
        "snowball_payments": "Snowball - Payments",
        "amount": "Amount (€)",
        "payment": "Payment (€)",
        "comparison_summary": "📊 Comparison summary",
        "method": "Method",
        "duration_months": "Duration (months)",
        "total_cost": "Total cost (€)",
        "interests_paid": "Interests paid (€)",
        "difference": "Difference",
        "avalanche_recommendation": "💡 **Recommendation**: The Avalanche method will save you more money in interest.",
        "snowball_recommendation": "💡 **Recommendation**: The Snowball method costs a bit more but can be more psychologically motivating.",
        "similar_cost": "💡 Both methods have similar costs, choose the one that motivates you most.",
        "footer_tip": "💡 **Tip**: Use the Avalanche method to minimize interest or Snowball for psychological motivation.",
        "credit_added": "Credit '{0}' added successfully!",
        "fill_all_fields": "Please fill all fields correctly.",
        "total_interests_label": "Total interests",
        "principal_paid": "Principal paid",
        "remaining_debt": "Remaining debt",
        "save_load": "💾 Save/Load",
        "save_scenario": "Save scenario",
        "scenario_name": "Scenario name",
        "save_btn": "Save",
        "load_scenario": "Load scenario",
        "select_scenario": "Select scenario",
        "load_btn": "Load",
        "delete_btn": "Delete",
        "export_csv": "Export to CSV",
        "import_csv": "Import from CSV",
        "download_csv": "Download CSV",
        "upload_csv": "Upload CSV file",
        "scenario_saved": "Scenario '{0}' saved successfully!",
        "scenario_loaded": "Scenario '{0}' loaded successfully!",
        "scenario_deleted": "Scenario '{0}' deleted!",
        "provide_scenario_name": "Please provide a scenario name.",
        "select_scenario_to_load": "Please select a scenario to load.",
        "no_scenarios": "No saved scenarios.",
        "csv_imported": "CSV data imported successfully!",
        "csv_error": "Error importing CSV file.",
    }
}

# Initialisation de la langue
if 'language' not in st.session_state:
    st.session_state.language = 'fr'

# Fonction pour obtenir le texte traduit
def t(key):
    return TRANSLATIONS[st.session_state.language].get(key, key)

# Sélecteur de langue dans la barre latérale
st.sidebar.selectbox(
    t("language"),
    options=['fr', 'en'],
    format_func=lambda x: "Français" if x == 'fr' else "English",
    key='language'
)

# Titre principal
st.title(t("title"))

# Initialisation des données de session
if 'credits' not in st.session_state:
    st.session_state.credits = []

if 'budget_supplementaire' not in st.session_state:
    st.session_state.budget_supplementaire = 0

if 'saved_scenarios' not in st.session_state:
    st.session_state.saved_scenarios = {}

# Fonctions utilitaires
def calculer_paiement_mensuel(capital, taux_annuel, duree_mois):
    """Calcule le paiement mensuel d'un prêt"""
    if taux_annuel == 0:
        return capital / duree_mois
    
    taux_mensuel = taux_annuel / 100 / 12
    paiement = capital * (taux_mensuel * (1 + taux_mensuel)**duree_mois) / ((1 + taux_mensuel)**duree_mois - 1)
    return paiement

def calculer_interets_totaux(capital, taux_annuel, duree_mois):
    """Calcule les intérêts totaux d'un prêt"""
    paiement_mensuel = calculer_paiement_mensuel(capital, taux_annuel, duree_mois)
    return (paiement_mensuel * duree_mois) - capital

def simuler_remboursement(credits, budget_supplementaire, methode="avalanche"):
    """Simule le remboursement selon la méthode choisie"""
    credits_copy = copy.deepcopy(credits)
    
    # Tri selon la méthode
    if methode == "avalanche":
        credits_copy.sort(key=lambda x: x['taux'], reverse=True)
    else:  # snowball
        credits_copy.sort(key=lambda x: x['solde_actuel'])
    
    mois = 0
    historique = []
    budget_libre = budget_supplementaire
    
    while any(credit['solde_actuel'] > 0 for credit in credits_copy):
        mois += 1
        paiement_total_mois = 0
        
        # Paiements minimums
        for credit in credits_copy:
            if credit['solde_actuel'] > 0:
                paiement_minimum = credit['paiement_mensuel']
                interet = credit['solde_actuel'] * (credit['taux'] / 100 / 12)
                principal = min(paiement_minimum - interet, credit['solde_actuel'])
                
                if principal > 0:
                    credit['solde_actuel'] -= principal
                    paiement_total_mois += paiement_minimum
                
                if credit['solde_actuel'] <= 0:
                    credit['solde_actuel'] = 0
                    # Ajouter le paiement mensuel au budget libre
                    budget_libre += paiement_minimum
        
        # Paiements supplémentaires avec budget libre
        for credit in credits_copy:
            if credit['solde_actuel'] > 0 and budget_libre > 0:
                paiement_supplementaire = min(budget_libre, credit['solde_actuel'])
                credit['solde_actuel'] -= paiement_supplementaire
                budget_libre -= paiement_supplementaire
                paiement_total_mois += paiement_supplementaire
                
                if credit['solde_actuel'] <= 0:
                    credit['solde_actuel'] = 0
                    # Ajouter le paiement mensuel au budget libre
                    budget_libre += credit['paiement_mensuel']
        
        # Enregistrer l'historique
        historique.append({
            'mois': mois,
            'paiement_total': paiement_total_mois,
            'soldes': [credit['solde_actuel'] for credit in credits_copy],
            'budget_libre': budget_libre
        })
        
        # Sécurité pour éviter les boucles infinies
        if mois > 600:  # 50 ans max
            break
    
    return historique, mois

# Fonctions de sauvegarde et chargement
def save_scenario(name, credits, budget):
    """Sauvegarde un scénario de crédits"""
    st.session_state.saved_scenarios[name] = {
        'credits': copy.deepcopy(credits),
        'budget_supplementaire': budget,
        'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M")
    }

def load_scenario(name):
    """Charge un scénario de crédits"""
    if name in st.session_state.saved_scenarios:
        scenario = st.session_state.saved_scenarios[name]
        st.session_state.credits = copy.deepcopy(scenario['credits'])
        st.session_state.budget_supplementaire = scenario['budget_supplementaire']
        return True
    return False

def delete_scenario(name):
    """Supprime un scénario"""
    if name in st.session_state.saved_scenarios:
        del st.session_state.saved_scenarios[name]
        return True
    return False

def export_to_csv(credits, budget):
    """Exporte les crédits en CSV"""
    data = []
    for credit in credits:
        data.append({
            'Nom': credit['nom'],
            'Solde_actuel': credit['solde_actuel'],
            'Taux_annuel': credit['taux'],
            'Duree_mois': credit['duree_mois'],
            'Paiement_mensuel': credit['paiement_mensuel'],
            'Interets_totaux': credit['interets_totaux']
        })
    
    df = pd.DataFrame(data)
    
    # Ajouter le budget supplémentaire comme ligne séparée
    budget_row = pd.DataFrame([{
        'Nom': 'BUDGET_SUPPLEMENTAIRE',
        'Solde_actuel': budget,
        'Taux_annuel': 0,
        'Duree_mois': 0,
        'Paiement_mensuel': 0,
        'Interets_totaux': 0
    }])
    
    df = pd.concat([df, budget_row], ignore_index=True)
    return df.to_csv(index=False)

def import_from_csv(uploaded_file):
    """Importe les crédits depuis un fichier CSV"""
    try:
        df = pd.read_csv(uploaded_file)
        
        credits = []
        budget = 0
        
        for _, row in df.iterrows():
            if row['Nom'] == 'BUDGET_SUPPLEMENTAIRE':
                budget = float(row['Solde_actuel'])
            else:
                credit = {
                    'nom': str(row['Nom']),
                    'solde_actuel': float(row['Solde_actuel']),
                    'taux': float(row['Taux_annuel']),
                    'duree_mois': int(row['Duree_mois']),
                    'paiement_mensuel': float(row['Paiement_mensuel']),
                    'interets_totaux': float(row['Interets_totaux'])
                }
                credits.append(credit)
        
        st.session_state.credits = credits
        st.session_state.budget_supplementaire = budget
        return True
    except Exception as e:
        st.error(f"Erreur: {str(e)}")
        return False
    
# Sidebar pour la gestion des crédits
st.sidebar.header(t("credit_management"))

# Ajout d'un nouveau crédit
with st.sidebar.expander(t("add_credit")):
    nom_credit = st.text_input(t("credit_name"))
    solde_actuel = st.number_input(t("current_balance"), min_value=0.0, value=0.0, step=100.0)
    taux_annuel = st.number_input(t("annual_rate"), min_value=0.0, max_value=50.0, value=0.0, step=0.1)
    duree_mois = st.number_input(t("remaining_duration"), min_value=1, value=12, step=1)
    
    if st.button(t("add_credit_btn")):
        if nom_credit and solde_actuel > 0:
            paiement_mensuel = calculer_paiement_mensuel(solde_actuel, taux_annuel, duree_mois)
            nouveau_credit = {
                'nom': nom_credit,
                'solde_actuel': solde_actuel,
                'taux': taux_annuel,
                'duree_mois': duree_mois,
                'paiement_mensuel': paiement_mensuel,
                'interets_totaux': calculer_interets_totaux(solde_actuel, taux_annuel, duree_mois)
            }
            st.session_state.credits.append(nouveau_credit)
            st.success(t("credit_added").format(nom_credit))
        else:
            st.error(t("fill_all_fields"))

# Configuration du budget supplémentaire
st.sidebar.header(t("additional_budget"))
st.session_state.budget_supplementaire = st.sidebar.number_input(
    t("monthly_additional"), 
    min_value=0.0, 
    value=float(st.session_state.budget_supplementaire), 
    step=50.0
)

# Section Sauvegarde/Chargement
st.sidebar.header(t("save_load"))

# Sauvegarde de scénario
with st.sidebar.expander(t("save_scenario")):
    scenario_name = st.text_input(t("scenario_name"))
    if st.button(t("save_btn")):
        if scenario_name and st.session_state.credits:
            save_scenario(scenario_name, st.session_state.credits, st.session_state.budget_supplementaire)
            st.success(t("scenario_saved").format(scenario_name))
        elif not scenario_name:
            st.error(t("provide_scenario_name"))
        else:
            st.error(t("add_credits_info"))

# Chargement de scénario
with st.sidebar.expander(t("load_scenario")):
    if st.session_state.saved_scenarios:
        scenario_to_load = st.selectbox(
            t("select_scenario"),
            options=list(st.session_state.saved_scenarios.keys()),
            format_func=lambda x: f"{x} ({st.session_state.saved_scenarios[x]['date_creation']})"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("load_btn")):
                if load_scenario(scenario_to_load):
                    st.success(t("scenario_loaded").format(scenario_to_load))
                    st.rerun()
        
        with col2:
            if st.button(t("delete_btn")):
                if delete_scenario(scenario_to_load):
                    st.success(t("scenario_deleted").format(scenario_to_load))
                    st.rerun()
    else:
        st.info(t("no_scenarios"))

# Export/Import CSV
with st.sidebar.expander(t("export_csv")):
    if st.session_state.credits:
        csv_data = export_to_csv(st.session_state.credits, st.session_state.budget_supplementaire)
        st.download_button(
            label=t("download_csv"),
            data=csv_data,
            file_name=f"credits_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    else:
        st.info(t("add_credits_info"))

with st.sidebar.expander(t("import_csv")):
    uploaded_file = st.file_uploader(t("upload_csv"), type=['csv'])
    if uploaded_file is not None:
        if import_from_csv(uploaded_file):
            st.success(t("csv_imported"))
            st.rerun()
        else:
            st.error(t("csv_error"))

# Affichage des crédits existants
if st.session_state.credits:
    st.sidebar.header(t("existing_credits"))
    
    credits_to_remove = []
    for i, credit in enumerate(st.session_state.credits):
        with st.sidebar.expander(f"{credit['nom']} - {credit['solde_actuel']:.2f}€"):
            st.write(f"**{t('balance')}:** {credit['solde_actuel']:.2f}€")
            st.write(f"**{t('rate')}:** {credit['taux']:.2f}%")
            st.write(f"**{t('monthly_payment')}:** {credit['paiement_mensuel']:.2f}€")
            st.write(f"**{t('remaining_term')}:** {credit['duree_mois']} {t('month').lower()}")
            
            if st.button(t("remove"), key=f"remove_{i}"):
                credits_to_remove.append(i)
    
    # Supprimer les crédits marqués pour suppression
    for i in reversed(credits_to_remove):
        st.session_state.credits.pop(i)
        st.rerun()

# Corps principal de l'application
if not st.session_state.credits:
    st.info(t("add_credits_info"))
else:
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        t("overview"), 
        t("avalanche_method"), 
        t("snowball_method"), 
        t("comparison")
    ])
    with tab1:
        st.header(t("credit_overview"))
        
        # Statistiques générales
        col1, col2, col3, col4 = st.columns(4)
        
        total_dette = sum(credit['solde_actuel'] for credit in st.session_state.credits)
        total_paiements = sum(credit['paiement_mensuel'] for credit in st.session_state.credits)
        total_interets = sum(credit['interets_totaux'] for credit in st.session_state.credits)
        taux_moyen = sum(credit['taux'] * credit['solde_actuel'] for credit in st.session_state.credits) / total_dette if total_dette > 0 else 0
        
        col1.metric(t("total_debt"), f"{total_dette:.2f}€")
        col2.metric(t("monthly_payments"), f"{total_paiements:.2f}€")
        col3.metric(t("total_interests"), f"{total_interets:.2f}€")
        col4.metric(t("weighted_avg_rate"), f"{taux_moyen:.2f}%")
        
        # Tableau des crédits
        st.subheader(t("credit_details"))
        
        df_credits = pd.DataFrame([
            {
                t('name'): credit['nom'],
                t('current_balance'): f"{credit['solde_actuel']:.2f}€",
                t('rate') + ' (%)': f"{credit['taux']:.2f}%",
                t('monthly_payment'): f"{credit['paiement_mensuel']:.2f}€",
                t('remaining_term'): f"{credit['duree_mois']} {t('month').lower()}",
                t('total_interests_label'): f"{credit['interets_totaux']:.2f}€"
            } for credit in st.session_state.credits
        ])
        
        st.dataframe(df_credits, use_container_width=True)
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            # Graphique en secteurs - Répartition des dettes
            fig_pie = px.pie(
                values=[credit['solde_actuel'] for credit in st.session_state.credits],
                names=[credit['nom'] for credit in st.session_state.credits],
                title=t("debt_distribution")
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Graphique en barres - Taux d'intérêt
            fig_bar = px.bar(
                x=[credit['nom'] for credit in st.session_state.credits],
                y=[credit['taux'] for credit in st.session_state.credits],
                title=t("interest_rates"),
                labels={'x': t('credit'), 'y': t('rate') + ' (%)'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
            st.header(t("avalanche_method"))
            st.info(t("avalanche_info"))
            
            # Simulation automatique - pas besoin de bouton
            if st.session_state.credits:
                historique, duree_totale = simuler_remboursement(
                    st.session_state.credits, 
                    st.session_state.budget_supplementaire, 
                    "avalanche"
                )
                
                # Métriques de la simulation
                col1, col2, col3 = st.columns(3)
                
                total_paye = sum(h['paiement_total'] for h in historique)
                economies_interets = sum(credit['interets_totaux'] for credit in st.session_state.credits) - (total_paye - total_dette)
                
                col1.metric(t("total_duration"), f"{duree_totale} {t('month').lower()}")
                col2.metric(t("total_paid"), f"{total_paye:.2f}€")
                col3.metric(t("interest_savings"), f"{economies_interets:.2f}€")
                
                # Graphique d'évolution des soldes (Stacked Bar)
                fig = go.Figure()
                
                months = list(range(1, len(historique) + 1))
                
                for i, credit in enumerate(st.session_state.credits):
                    soldes = [h['soldes'][i] for h in historique]
                    fig.add_trace(go.Bar(
                        x=months,
                        y=soldes,
                        name=credit['nom'],
                        hovertemplate=f'<b>{credit["nom"]}</b><br>' +
                                    t("month") + ': %{x}<br>' +
                                    t("balance") + ': €%{y:,.2f}<br>' +
                                    '<extra></extra>'
                    ))
                
                fig.update_layout(
                    title=t("balance_evolution") + " - " + t("avalanche_method"),
                    xaxis_title=t("month"),
                    yaxis_title=t("balance_currency"),
                    barmode='stack',
                    hovermode='x unified',
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tableau de remboursement détaillé avec plus d'informations
                st.subheader(t("repayment_schedule"))
                
                # Slider pour contrôler le nombre de mois affichés
                max_months = min(len(historique), 60)  # Maximum 60 mois affichable
                months_to_show = st.slider(
                    f"{t('months_displayed').split(' ')[0]} {t('month').lower()}", 
                    min_value=6, 
                    max_value=max_months, 
                    value=min(24, max_months),
                    key="avalanche_months"
                )
                
                # Calculer des informations supplémentaires pour chaque mois
                detailed_data = []
                for h in historique[:months_to_show]:
                    mois_data = {
                        t('month'): h['mois'],
                        t('total_payment'): f"{h['paiement_total']:.2f}€",
                        t('free_budget'): f"{h['budget_libre']:.2f}€",
                    }
                    
                    # Ajouter les soldes de chaque crédit
                    for i, credit in enumerate(st.session_state.credits):
                        mois_data[f"{t('balance')} {credit['nom']}"] = f"{h['soldes'][i]:.2f}€"
                    
                    # Calculer les intérêts payés ce mois-ci
                    interets_mois = 0
                    for i, credit in enumerate(st.session_state.credits):
                        if h['soldes'][i] > 0:
                            # Solde du mois précédent
                            solde_precedent = historique[h['mois']-2]['soldes'][i] if h['mois'] > 1 else credit['solde_actuel']
                            interet_credit = solde_precedent * (credit['taux'] / 100 / 12)
                            interets_mois += interet_credit
                    
                    mois_data[t('interests_paid')] = f"{interets_mois:.2f}€"
                    
                    # Calculer le principal payé ce mois-ci
                    principal_mois = max(0, h['paiement_total'] - interets_mois)
                    mois_data[t('principal_paid')] = f"{principal_mois:.2f}€"
                    
                    # Dette totale restante
                    dette_totale_restante = sum(h['soldes'])
                    mois_data[t('remaining_debt')] = f"{dette_totale_restante:.2f}€"
                    
                    detailed_data.append(mois_data)
                
                df_historique = pd.DataFrame(detailed_data)
                st.dataframe(df_historique, use_container_width=True)
                
                if len(historique) > months_to_show:
                    st.info(f"Affichage de {months_to_show} mois sur {len(historique)} mois total.")
            else:
                st.warning(t("add_credits_info"))

    with tab3:
            st.header(t("snowball_method"))
            st.info(t("snowball_info"))
            
            # Simulation automatique - pas besoin de bouton
            if st.session_state.credits:
                historique, duree_totale = simuler_remboursement(
                    st.session_state.credits, 
                    st.session_state.budget_supplementaire, 
                    "snowball"
                )
                
                # Métriques de la simulation
                col1, col2, col3 = st.columns(3)
                
                total_paye = sum(h['paiement_total'] for h in historique)
                economies_interets = sum(credit['interets_totaux'] for credit in st.session_state.credits) - (total_paye - total_dette)
                
                col1.metric(t("total_duration"), f"{duree_totale} {t('month').lower()}")
                col2.metric(t("total_paid"), f"{total_paye:.2f}€")
                col3.metric(t("interest_savings"), f"{economies_interets:.2f}€")
                
                # Graphique d'évolution des soldes (Stacked Bar)
                fig = go.Figure()
                
                months = list(range(1, len(historique) + 1))
                
                for i, credit in enumerate(st.session_state.credits):
                    soldes = [h['soldes'][i] for h in historique]
                    fig.add_trace(go.Bar(
                        x=months,
                        y=soldes,
                        name=credit['nom'],
                        hovertemplate=f'<b>{credit["nom"]}</b><br>' +
                                    t("month") + ': %{x}<br>' +
                                    t("balance") + ': €%{y:,.2f}<br>' +
                                    '<extra></extra>'
                    ))
                
                fig.update_layout(
                    title=t("balance_evolution") + " - " + t("snowball_method"),
                    xaxis_title=t("month"),
                    yaxis_title=t("balance_currency"),
                    barmode='stack',
                    hovermode='x unified',
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tableau de remboursement détaillé avec plus d'informations
                st.subheader(t("repayment_schedule"))
                
                # Slider pour contrôler le nombre de mois affichés
                max_months = min(len(historique), 60)  # Maximum 60 mois affichable
                months_to_show = st.slider(
                    f"{t('months_displayed').split(' ')[0]} {t('month').lower()}", 
                    min_value=6, 
                    max_value=max_months, 
                    value=min(24, max_months),
                    key="snowball_months"
                )
                
                # Calculer des informations supplémentaires pour chaque mois
                detailed_data = []
                for h in historique[:months_to_show]:
                    mois_data = {
                        t('month'): h['mois'],
                        t('total_payment'): f"{h['paiement_total']:.2f}€",
                        t('free_budget'): f"{h['budget_libre']:.2f}€",
                    }
                    
                    # Ajouter les soldes de chaque crédit
                    for i, credit in enumerate(st.session_state.credits):
                        mois_data[f"{t('balance')} {credit['nom']}"] = f"{h['soldes'][i]:.2f}€"
                    
                    # Calculer les intérêts payés ce mois-ci
                    interets_mois = 0
                    for i, credit in enumerate(st.session_state.credits):
                        if h['soldes'][i] > 0:
                            # Solde du mois précédent
                            solde_precedent = historique[h['mois']-2]['soldes'][i] if h['mois'] > 1 else credit['solde_actuel']
                            interet_credit = solde_precedent * (credit['taux'] / 100 / 12)
                            interets_mois += interet_credit
                    
                    mois_data[t('interests_paid')] = f"{interets_mois:.2f}€"
                    
                    # Calculer le principal payé ce mois-ci
                    principal_mois = max(0, h['paiement_total'] - interets_mois)
                    mois_data[t('principal_paid')] = f"{principal_mois:.2f}€"
                    
                    # Dette totale restante
                    dette_totale_restante = sum(h['soldes'])
                    mois_data[t('remaining_debt')] = f"{dette_totale_restante:.2f}€"
                    
                    detailed_data.append(mois_data)
                
                df_historique = pd.DataFrame(detailed_data)
                st.dataframe(df_historique, use_container_width=True)
                
                if len(historique) > months_to_show:
                    st.info(f"Affichage de {months_to_show} mois sur {len(historique)} mois total.")
            else:
                st.warning(t("add_credits_info"))

    with tab4:
            st.header(t("comparison"))
            
            # Simulation automatique - pas besoin de bouton
            if st.session_state.credits:
                # Simulation Avalanche
                historique_avalanche, duree_avalanche = simuler_remboursement(
                    st.session_state.credits, 
                    st.session_state.budget_supplementaire, 
                    "avalanche"
                )
                
                # Simulation Snowball
                historique_snowball, duree_snowball = simuler_remboursement(
                    st.session_state.credits, 
                    st.session_state.budget_supplementaire, 
                    "snowball"
                )
                
                # Comparaison des métriques
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(t("avalanche_method"))
                    total_paye_avalanche = sum(h['paiement_total'] for h in historique_avalanche)
                    st.metric(t("total_duration"), f"{duree_avalanche} {t('month').lower()}")
                    st.metric(t("total_paid"), f"{total_paye_avalanche:.2f}€")
                    st.metric(t("interests_paid"), f"{total_paye_avalanche - total_dette:.2f}€")
                
                with col2:
                    st.subheader(t("snowball_method"))
                    total_paye_snowball = sum(h['paiement_total'] for h in historique_snowball)
                    st.metric(t("total_duration"), f"{duree_snowball} {t('month').lower()}")
                    st.metric(t("total_paid"), f"{total_paye_snowball:.2f}€")
                    st.metric(t("interests_paid"), f"{total_paye_snowball - total_dette:.2f}€")
                
                # Contrôle d'affichage des graphiques
                st.subheader("🎛️ Contrôles d'affichage")
                col1, col2 = st.columns(2)
                
                with col1:
                    show_stacked = st.checkbox("Graphiques empilés détaillés", value=True)
                with col2:
                    max_months_chart = max(duree_avalanche, duree_snowball, 12)  # Minimum 12
                    months_chart = st.slider(
                        "Mois à afficher sur les graphiques", 
                        min_value=12, 
                        max_value=max_months_chart, 
                        value=min(60, max_months_chart)
                    )

    if show_stacked:
                    # Graphiques de comparaison avec Stacked Bars
                    fig = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=(
                            t("total_debt_evolution") + " - " + t("avalanche_method").replace('🏔️ ', ''),
                            t("total_debt_evolution") + " - " + t("snowball_method").replace('❄️ ', ''),
                            t("monthly_payments_chart") + " - " + t("avalanche_method").replace('🏔️ ', ''),
                            t("monthly_payments_chart") + " - " + t("snowball_method").replace('❄️ ', '')
                        ),
                        specs=[[{"secondary_y": False}, {"secondary_y": False}],
                            [{"secondary_y": False}, {"secondary_y": False}]],
                        vertical_spacing=0.15,
                        horizontal_spacing=0.1
                    )
                    
                    # Avalanche - Evolution des dettes (Stacked Bar)
                    months_avalanche = list(range(1, min(len(historique_avalanche), months_chart) + 1))
                    for i, credit in enumerate(st.session_state.credits):
                        soldes_avalanche = [h['soldes'][i] for h in historique_avalanche[:months_chart]]
                        fig.add_trace(go.Bar(
                            x=months_avalanche,
                            y=soldes_avalanche,
                            name=f"Avalanche - {credit['nom']}",
                            legendgroup="avalanche",
                            showlegend=True if i == 0 else False,
                            hovertemplate=f'<b>{credit["nom"]}</b><br>Mois: %{{x}}<br>Solde: €%{{y:,.2f}}<extra></extra>'
                        ), row=1, col=1)
                    
                    # Snowball - Evolution des dettes (Stacked Bar)
                    months_snowball = list(range(1, min(len(historique_snowball), months_chart) + 1))
                    for i, credit in enumerate(st.session_state.credits):
                        soldes_snowball = [h['soldes'][i] for h in historique_snowball[:months_chart]]
                        fig.add_trace(go.Bar(
                            x=months_snowball,
                            y=soldes_snowball,
                            name=f"Snowball - {credit['nom']}",
                            legendgroup="snowball",
                            showlegend=True if i == 0 else False,
                            hovertemplate=f'<b>{credit["nom"]}</b><br>Mois: %{{x}}<br>Solde: €%{{y:,.2f}}<extra></extra>'
                        ), row=1, col=2)
                    
                    # Avalanche - Paiements mensuels
                    paiements_avalanche = [h['paiement_total'] for h in historique_avalanche[:months_chart]]
                    fig.add_trace(go.Bar(
                        x=months_avalanche,
                        y=paiements_avalanche,
                        name="Avalanche - Paiements",
                        marker_color='red',
                        legendgroup="avalanche_pay",
                        hovertemplate='Mois: %{x}<br>Paiement: €%{y:,.2f}<extra></extra>'
                    ), row=2, col=1)
                    
                    # Snowball - Paiements mensuels
                    paiements_snowball = [h['paiement_total'] for h in historique_snowball[:months_chart]]
                    fig.add_trace(go.Bar(
                        x=months_snowball,
                        y=paiements_snowball,
                        name="Snowball - Paiements",
                        marker_color='blue',
                        legendgroup="snowball_pay",
                        hovertemplate='Mois: %{x}<br>Paiement: €%{y:,.2f}<extra></extra>'
                    ), row=2, col=2)
                    
                    # Mise à jour du layout
                    fig.update_layout(
                        title=t("comparison_title"),
                        height=800,
                        barmode='stack'
                    )
                    
                    # Mise à jour des axes
                    for row in [1, 2]:
                        for col in [1, 2]:
                            fig.update_xaxes(title_text=t("month"), row=row, col=col)
                            if row == 1:
                                fig.update_yaxes(title_text=t("amount"), row=row, col=col)
                            else:
                                fig.update_yaxes(title_text=t("payment"), row=row, col=col)
                    
                    st.plotly_chart(fig, use_container_width=True)

    else:
                    # Graphique de comparaison simplifié (lignes)
                    fig = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=(t("total_debt_evolution"), t("monthly_payments_chart")),
                        vertical_spacing=0.1
                    )
                    
                    # Évolution des dettes totales
                    total_dette_avalanche = [sum(h['soldes']) for h in historique_avalanche[:months_chart]]
                    total_dette_snowball = [sum(h['soldes']) for h in historique_snowball[:months_chart]]
                    
                    fig.add_trace(go.Scatter(
                        x=list(range(1, len(total_dette_avalanche) + 1)),
                        y=total_dette_avalanche,
                        name=t("avalanche_debt"),
                        line=dict(color='red', width=3)
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=list(range(1, len(total_dette_snowball) + 1)),
                        y=total_dette_snowball,
                        name=t("snowball_debt"),
                        line=dict(color='blue', width=3)
                    ), row=1, col=1)
                    
                    # Paiements mensuels
                    paiements_avalanche = [h['paiement_total'] for h in historique_avalanche[:months_chart]]
                    paiements_snowball = [h['paiement_total'] for h in historique_snowball[:months_chart]]
                    
                    fig.add_trace(go.Scatter(
                        x=list(range(1, len(paiements_avalanche) + 1)),
                        y=paiements_avalanche,
                        name=t("avalanche_payments"),
                        line=dict(color='red', dash='dash', width=2)
                    ), row=2, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=list(range(1, len(paiements_snowball) + 1)),
                        y=paiements_snowball,
                        name=t("snowball_payments"),
                        line=dict(color='blue', dash='dash', width=2)
                    ), row=2, col=1)
                    
                    fig.update_layout(
                        title=t("comparison_title"),
                        height=600
                    )
                    
                    fig.update_xaxes(title_text=t("month"), row=2, col=1)
                    fig.update_yaxes(title_text=t("amount"), row=1, col=1)
                    fig.update_yaxes(title_text=t("payment"), row=2, col=1)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tableau de comparaison
                    st.subheader(t("comparison_summary"))
                    
                    difference_duree = duree_avalanche - duree_snowball
                    difference_cout = total_paye_avalanche - total_paye_snowball
                    
                    # Créer un tableau de comparaison détaillé
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            label="🏔️ " + t('avalanche_method').replace('🏔️ ', ''),
                            value=f"{duree_avalanche} mois",
                            delta=f"{difference_duree} mois" if difference_duree != 0 else None
                        )
                        st.write(f"**Coût total:** {total_paye_avalanche:.2f}€")
                        st.write(f"**Intérêts:** {total_paye_avalanche - total_dette:.2f}€")
                    
                    with col2:
                        st.metric(
                            label="❄️ " + t('snowball_method').replace('❄️ ', ''),
                            value=f"{duree_snowball} mois",
                            delta=f"{-difference_duree} mois" if difference_duree != 0 else None
                        )
                        st.write(f"**Coût total:** {total_paye_snowball:.2f}€")
                        st.write(f"**Intérêts:** {total_paye_snowball - total_dette:.2f}€")
                    
                    with col3:
                        st.metric(
                            label="💰 Économies (Avalanche vs Snowball)",
                            value=f"{-difference_cout:.2f}€",
                            delta=f"{abs(difference_duree)} mois {'plus rapide' if difference_duree < 0 else 'plus lent'}"
                        )
                        pourcentage_economie = (abs(difference_cout) / total_paye_snowball * 100) if total_paye_snowball > 0 else 0
                        st.write(f"**Économie:** {pourcentage_economie:.1f}%")

    # Tableau détaillé
                    df_comparaison = pd.DataFrame({
                        t('method'): [
                            t('avalanche_method').replace('🏔️ ', ''), 
                            t('snowball_method').replace('❄️ ', ''), 
                            t('difference')
                        ],
                        t('duration_months'): [duree_avalanche, duree_snowball, difference_duree],
                        t('total_cost'): [f"{total_paye_avalanche:.2f}€", f"{total_paye_snowball:.2f}€", f"{difference_cout:.2f}€"],
                        t('interests_paid'): [
                            f"{total_paye_avalanche - total_dette:.2f}€", 
                            f"{total_paye_snowball - total_dette:.2f}€",
                            f"{difference_cout:.2f}€"
                        ]
                    })
                    
                    st.dataframe(df_comparaison, use_container_width=True)
                
                    # Recommandation dynamique
                    if abs(difference_cout) > 100:  # Seuil de différence significative
                        if difference_cout < 0:
                            st.success(t("avalanche_recommendation"))
                        else:
                            st.info(t("snowball_recommendation"))
                    else:
                        st.info(t("similar_cost"))
                        
                    # Analyse détaillée
                    st.subheader("📈 Analyse détaillée")
                    
                    # Calculer des métriques supplémentaires
                    col1, col2 = st.columns(2)
                        
                    with col1:
                        st.write("**🏔️ Avalanche - Avantages:**")
                        st.write(f"• Économie d'intérêts: {abs(difference_cout):.2f}€" if difference_cout < 0 else f"• Coût supplémentaire: {difference_cout:.2f}€")
                        st.write(f"• Durée: {duree_avalanche} mois")
                        
                        # Premier crédit remboursé
                        premier_rembourse_av = None
                        for mois, h in enumerate(historique_avalanche):
                            for i, solde in enumerate(h['soldes']):
                                if solde == 0 and (mois == 0 or historique_avalanche[mois-1]['soldes'][i] > 0):
                                    premier_rembourse_av = (st.session_state.credits[i]['nom'], mois + 1)
                                    break
                            if premier_rembourse_av:
                                break
                        
                        if premier_rembourse_av:
                            st.write(f"• Premier crédit soldé: {premier_rembourse_av[0]} (mois {premier_rembourse_av[1]})")
                    
                    with col2:
                        st.write("**❄️ Snowball - Avantages:**")
                        st.write(f"• Coût supplémentaire: {difference_cout:.2f}€" if difference_cout > 0 else f"• Économie: {abs(difference_cout):.2f}€")
                        st.write(f"• Durée: {duree_snowball} mois")
                        
                        # Premier crédit remboursé
                        premier_rembourse_sb = None
                        for mois, h in enumerate(historique_snowball):
                            for i, solde in enumerate(h['soldes']):
                                if solde == 0 and (mois == 0 or historique_snowball[mois-1]['soldes'][i] > 0):
                                    premier_rembourse_sb = (st.session_state.credits[i]['nom'], mois + 1)
                                    break
                            if premier_rembourse_sb:
                                break
                        
                        if premier_rembourse_sb:
                            st.write(f"• Premier crédit soldé: {premier_rembourse_sb[0]} (mois {premier_rembourse_sb[1]})")
                            
                        # Avantage psychologique
                        nb_credits_soldes_12mois_sb = 0
                        if len(historique_snowball) >= 12:
                            for i in range(len(st.session_state.credits)):
                                if historique_snowball[11]['soldes'][i] == 0:
                                    nb_credits_soldes_12mois_sb += 1
                            st.write(f"• Crédits soldés en 12 mois: {nb_credits_soldes_12mois_sb}")
                        else:
                            st.warning(t("add_credits_info"))

# Footer
st.markdown("---")
st.markdown(t("footer_tip"))
