"""
Seed profession-specific specification questions for every category that
currently has NO active question of its own (only general questions exist).

Idempotent: a category that already has >=1 active question is skipped, and
re-running will not duplicate (it re-checks the count each time).

Run from projet_pfe2/ with:  python scripts/seed_missing_questions.py
"""
import sys, uuid, json
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.core import models
from sqlalchemy import func

# label, order, answer_type, options(optional)
QUESTIONS = {
    # ─────────────── DESIGN & CREATIVE ───────────────
    "Logo Designer": [
        ("Nom de marque a representer dans le logo",                       1, "text"),
        ("Style de logo souhaite",                                         2, "single_choice", ["Typographique (wordmark)", "Icone / Symbole", "Combinaison texte + icone", "Embleme / Badge"]),
        ("Nombre de propositions initiales souhaitees",                    3, "text"),
        ("Declinaisons requises (couleur, N&B, favicon, fond sombre) ?",   4, "single_choice", ["Oui - pack complet", "Couleur uniquement", "A definir"]),
        ("Fichiers sources vectoriels (AI/SVG) a livrer ?",                5, "single_choice", ["Oui", "Non"]),
    ],
    "Motion Graphics Designer": [
        ("Type d'animation graphique demandee",                           1, "text"),
        ("Duree approximative de l'animation",                            2, "text"),
        ("Style visuel de reference",                                      3, "text"),
        ("Audio a integrer ?",                                            4, "single_choice", ["Voix-off fournie", "Musique fournie", "Les deux", "A sourcer"]),
        ("Format et resolution de livraison",                            5, "single_choice", ["1080p 16:9", "4K 16:9", "Vertical 9:16", "Multi-format"]),
    ],

    # ─────────────── FINANCE ───────────────
    "Auditor": [
        ("Type d'audit requis",                                           1, "single_choice", ["Audit financier", "Audit interne", "Audit de conformite", "Audit operationnel"]),
        ("Periode / exercice a auditer",                                  2, "text"),
        ("Normes de reference (IFRS, normes locales...)",                3, "text"),
        ("Acces aux documents comptables disponible ?",                  4, "single_choice", ["Oui - acces complet", "Oui - acces partiel", "Non - a collecter"]),
        ("Rapport d'audit formel attendu ?",                             5, "single_choice", ["Oui", "Non"]),
    ],
    "Expert comptable": [
        ("Type de mission comptable",                                     1, "single_choice", ["Tenue de comptabilite", "Bilan annuel", "Conseil fiscal", "Mission complete"]),
        ("Forme juridique de l'entreprise",                              2, "text"),
        ("Volume de pieces comptables mensuelles estime",                3, "text"),
        ("Declarations fiscales et sociales incluses ?",                 4, "single_choice", ["Oui", "Non"]),
        ("Logiciel comptable utilise",                                    5, "text"),
    ],
    "Finance Manager": [
        ("Perimetre de la mission",                                       1, "single_choice", ["Gestion de tresorerie", "Budgetisation et previsionnel", "Controle de gestion", "Direction financiere complete"]),
        ("Taille de l'entreprise (effectif / CA)",                       2, "text"),
        ("Outils de gestion financiere en place",                        3, "text"),
        ("Reporting financier periodique requis ?",                      4, "single_choice", ["Mensuel", "Trimestriel", "Annuel", "Ponctuel"]),
        ("Objectifs financiers prioritaires",                            5, "text"),
    ],
    "Trader (Securities/Forex)": [
        ("Marche(s) cible(s)",                                           1, "single_choice", ["Actions / Securities", "Forex", "Crypto", "Matieres premieres"]),
        ("Strategie de trading souhaitee",                              2, "single_choice", ["Day trading", "Swing trading", "Long terme", "Algorithmique"]),
        ("Capital alloue (fourchette)",                                 3, "text"),
        ("Profil de risque",                                            4, "single_choice", ["Prudent", "Equilibre", "Agressif"]),
        ("Reporting de performance requis ?",                           5, "single_choice", ["Oui", "Non"]),
    ],

    # ─────────────── GAME DEVELOPMENT & 3D MODELING ───────────────
    "Environment Artist": [
        ("Type d'environnements a creer",                               1, "text"),
        ("Style artistique souhaite",                                   2, "single_choice", ["Realiste", "Stylise / Cartoon", "Low-poly", "Sci-fi / Fantasy"]),
        ("Moteur cible",                                                3, "single_choice", ["Unity", "Unreal Engine", "Godot", "Autre"]),
        ("Nombre approximatif de scenes / environnements",             4, "text"),
        ("Optimisation temps reel requise ?",                          5, "single_choice", ["Oui", "Non"]),
    ],
    "Game Tester / QA Specialist": [
        ("Type de tests requis",                                        1, "single_choice", ["Tests fonctionnels", "Tests de performance", "Tests de compatibilite", "Tout"]),
        ("Plateformes a tester",                                        2, "text"),
        ("Tests automatises souhaites ?",                              3, "single_choice", ["Oui", "Non - manuel uniquement"]),
        ("Rapport de bugs structure attendu ?",                       4, "single_choice", ["Oui", "Non"]),
        ("Phase du projet",                                            5, "single_choice", ["Alpha", "Beta", "Pre-lancement", "Post-lancement"]),
    ],
    "Level Designer": [
        ("Genre du jeu",                                               1, "text"),
        ("Nombre de niveaux / cartes a concevoir",                    2, "text"),
        ("Outils ou moteur a utiliser",                              3, "text"),
        ("Documentation de design des niveaux requise ?",             4, "single_choice", ["Oui", "Non"]),
        ("Difficulte progressive a integrer ?",                       5, "single_choice", ["Oui", "Non"]),
    ],
    "Sound Designer for Games": [
        ("Type d'audio a produire",                                   1, "single_choice", ["Effets sonores (SFX)", "Musique / Theme", "Ambiances", "Tout"]),
        ("Nombre approximatif d'assets audio",                       2, "text"),
        ("Middleware audio utilise (Wwise, FMOD) ?",                 3, "single_choice", ["Wwise", "FMOD", "Aucun", "A definir"]),
        ("Audio adaptatif / dynamique requis ?",                     4, "single_choice", ["Oui", "Non"]),
        ("Format de livraison des fichiers",                         5, "text"),
    ],
    "VFX Artist (Game Effects)": [
        ("Types d'effets requis (explosions, magie, particules...)", 1, "text"),
        ("Moteur cible",                                             2, "single_choice", ["Unity", "Unreal Engine", "Godot", "Autre"]),
        ("Style visuel des effets",                                  3, "single_choice", ["Realiste", "Stylise", "Retro / Pixel"]),
        ("Contraintes de performance (mobile, console) ?",          4, "text"),
        ("Nombre approximatif d'effets a produire",                 5, "text"),
    ],

    # ─────────────── INFORMATION TECHNOLOGY (IT) ───────────────
    "Cloud Engineer": [
        ("Fournisseur cloud cible",                                  1, "single_choice", ["AWS", "Azure", "GCP", "Multi-cloud"]),
        ("Type de mission",                                          2, "single_choice", ["Migration vers le cloud", "Nouvelle infrastructure", "Optimisation des couts", "Maintenance"]),
        ("Infrastructure as Code souhaitee (Terraform...) ?",       3, "single_choice", ["Terraform", "CloudFormation", "Pulumi", "Non"]),
        ("Haute disponibilite / multi-region requise ?",            4, "single_choice", ["Oui", "Non"]),
        ("Budget mensuel cloud estime",                             5, "text"),
    ],
    "Cybersecurity Analyst": [
        ("Type d'intervention requise",                             1, "single_choice", ["Audit de securite", "Test d'intrusion", "Surveillance (SOC)", "Mise en conformite"]),
        ("Norme de conformite visee (ISO 27001, RGPD...)",         2, "text"),
        ("Perimetre a securiser (web, reseau, applicatif...)",     3, "text"),
        ("Rapport de vulnerabilites attendu ?",                    4, "single_choice", ["Oui", "Non"]),
        ("Formation de sensibilisation incluse ?",                 5, "single_choice", ["Oui", "Non"]),
    ],
    "Data Analyst": [
        ("Objectif principal de l'analyse",                        1, "text"),
        ("Sources de donnees disponibles",                        2, "text"),
        ("Outil de visualisation prefere",                        3, "single_choice", ["Power BI", "Tableau", "Looker", "Excel / Sheets", "A definir"]),
        ("Tableau de bord interactif requis ?",                   4, "single_choice", ["Oui", "Non"]),
        ("Frequence de mise a jour des rapports",                 5, "single_choice", ["Temps reel", "Quotidien", "Hebdomadaire", "Mensuel"]),
    ],
    "Data Scientist": [
        ("Type de probleme a resoudre",                           1, "text"),
        ("Volume de donnees disponibles",                        2, "single_choice", ["Moins de 10k lignes", "10k a 1M lignes", "Plus de 1M lignes"]),
        ("Framework / langage prefere",                          3, "text"),
        ("Deploiement du modele requis ?",                       4, "single_choice", ["API REST", "Application web", "Edge device", "Non requis"]),
        ("Interpretabilite du modele requise ?",                 5, "single_choice", ["Oui", "Non"]),
    ],
    "Database Administrator (DBA)": [
        ("SGBD utilise ou prefere",                              1, "text"),
        ("Volume de donnees estime",                            2, "text"),
        ("Sauvegardes et plan de reprise requis ?",            3, "single_choice", ["Oui", "Non"]),
        ("Optimisation des performances requise ?",            4, "single_choice", ["Oui", "Non"]),
        ("Migration de donnees incluse ?",                     5, "single_choice", ["Oui", "Non"]),
    ],
    "DevOps Engineer": [
        ("Pipeline CI/CD requis ?",                            1, "single_choice", ["GitHub Actions", "GitLab CI", "Jenkins", "Non"]),
        ("Conteneurisation requise ?",                         2, "single_choice", ["Docker", "Kubernetes", "Docker + Kubernetes", "Non"]),
        ("Plateforme cloud cible",                             3, "single_choice", ["AWS", "Azure", "GCP", "On-premise"]),
        ("Outil de supervision (Grafana, Datadog) requis ?",  4, "single_choice", ["Oui", "Non"]),
        ("Automatisation de l'infrastructure souhaitee ?",    5, "single_choice", ["Oui", "Non"]),
    ],
    "Full-Stack Developer": [
        ("Langage backend prefere (Node.js, Django, Laravel...)", 1, "text"),
        ("Framework frontend prefere (React, Vue, Angular...)",   2, "text"),
        ("Base de donnees preferee",                              3, "text"),
        ("Type d'API requis",                                     4, "single_choice", ["REST", "GraphQL", "gRPC", "Les deux"]),
        ("Panneau d'administration requis ?",                     5, "single_choice", ["Oui", "Non"]),
    ],
    "IT Support Specialist": [
        ("Type de support requis",                               1, "single_choice", ["Support utilisateur (helpdesk)", "Support infrastructure", "Support applicatif", "Tout"]),
        ("Nombre d'utilisateurs / postes a supporter",          2, "text"),
        ("Support sur site ou a distance ?",                    3, "single_choice", ["Sur site", "A distance", "Hybride"]),
        ("Plage horaire de support requise",                    4, "single_choice", ["Heures de bureau", "Etendue (12h)", "24/7"]),
        ("Gestion d'un systeme de tickets requise ?",           5, "single_choice", ["Oui", "Non"]),
    ],
    "Machine Learning Engineer": [
        ("Type de modele ML a developper",                      1, "text"),
        ("Volume et nature des donnees d'entrainement",         2, "text"),
        ("Framework ML prefere (TensorFlow, PyTorch...)",       3, "text"),
        ("Mise en production (MLOps) requise ?",                4, "single_choice", ["Oui", "Non"]),
        ("Contraintes de latence / temps reel ?",              5, "text"),
    ],
    "Network Engineer": [
        ("Infrastructure reseau existante a maintenir ?",       1, "single_choice", ["Oui", "Non - nouvelle infrastructure"]),
        ("Nombre de sites / sites distants",                   2, "text"),
        ("VPN ou acces distant requis ?",                      3, "single_choice", ["Oui", "Non"]),
        ("Wifi manageable requis ?",                           4, "single_choice", ["Oui", "Non"]),
        ("Supervision reseau (NMS) souhaitee ?",               5, "single_choice", ["Oui", "Non"]),
    ],
    "QA Engineer (Quality Assurance)": [
        ("Type de tests requis",                               1, "single_choice", ["Tests manuels", "Tests automatises", "Les deux"]),
        ("Type d'application a tester",                        2, "text"),
        ("Framework de test automatise prefere",              3, "text"),
        ("Tests de performance / charge inclus ?",            4, "single_choice", ["Oui", "Non"]),
        ("Integration aux pipelines CI/CD requise ?",         5, "single_choice", ["Oui", "Non"]),
    ],
    "Systems Administrator": [
        ("Systemes a administrer",                             1, "single_choice", ["Linux", "Windows Server", "Les deux"]),
        ("Nombre de serveurs a gerer",                        2, "text"),
        ("Environnement virtualise ou physique ?",           3, "single_choice", ["Virtualise (VMware, Hyper-V)", "Physique", "Cloud", "Hybride"]),
        ("Sauvegardes et plan de reprise requis ?",          4, "single_choice", ["Oui", "Non"]),
        ("Supervision systeme (monitoring) souhaitee ?",     5, "single_choice", ["Oui", "Non"]),
    ],

    # ─────────────── MARKETING & ADVERTISING ───────────────
    "Google Ads / PPC Specialist": [
        ("Plateformes publicitaires cibles",                  1, "single_choice", ["Google Ads", "Meta Ads", "LinkedIn Ads", "Multi-plateforme"]),
        ("Budget publicitaire mensuel",                       2, "text"),
        ("Objectif principal des campagnes",                  3, "single_choice", ["Trafic site web", "Generation de leads", "Ventes / Conversions", "Notoriete"]),
        ("Compte publicitaire deja existant ?",              4, "single_choice", ["Oui", "Non - a creer"]),
        ("Suivi des conversions deja en place ?",            5, "single_choice", ["Oui", "Non"]),
    ],
    "Influencer Marketing Coordinator": [
        ("Plateformes prioritaires",                          1, "single_choice", ["Instagram", "TikTok", "YouTube", "Multi-plateforme"]),
        ("Type d'influenceurs vises",                        2, "single_choice", ["Nano (< 10k)", "Micro (10k-100k)", "Macro (100k-1M)", "Celebrites (> 1M)"]),
        ("Budget alloue aux collaborations",                 3, "text"),
        ("Objectif de la campagne",                          4, "text"),
        ("Suivi des performances (ROI) requis ?",            5, "single_choice", ["Oui", "Non"]),
    ],
    "Marketing Automation Expert (e.g., HubSpot, Mailchimp)": [
        ("Plateforme d'automatisation cible",                1, "single_choice", ["HubSpot", "Mailchimp", "ActiveCampaign", "A definir"]),
        ("Type de scenarios a automatiser",                  2, "text"),
        ("Taille de la base de contacts",                    3, "text"),
        ("Integration CRM requise ?",                        4, "single_choice", ["Oui", "Non"]),
        ("Lead scoring a mettre en place ?",                 5, "single_choice", ["Oui", "Non"]),
    ],

    # ─────────────── MEDIA & VIDEO PRODUCTION ───────────────
    "Animator (2D/3D)": [
        ("Type d'animation",                                 1, "single_choice", ["2D", "3D", "Motion design", "Stop motion"]),
        ("Duree approximative de l'animation",              2, "text"),
        ("Logiciel d'animation prefere",                   3, "text"),
        ("Storyboard ou script fourni ?",                  4, "single_choice", ["Oui", "Non"]),
        ("Format et resolution de livraison",              5, "text"),
    ],
    "Camera Operator": [
        ("Type de tournage",                                1, "text"),
        ("Duree de tournage prevue",                       2, "text"),
        ("Materiel camera fourni ou a apporter ?",         3, "single_choice", ["Fourni par le client", "A apporter par le prestataire"]),
        ("Prise de vue par drone requise ?",               4, "single_choice", ["Oui", "Non"]),
        ("Lieu(x) de tournage",                            5, "text"),
    ],
    "Post-Production Supervisor": [
        ("Perimetre de la post-production",                1, "single_choice", ["Montage", "Etalonnage", "Mixage audio", "Supervision complete"]),
        ("Duree du projet final",                          2, "text"),
        ("Nombre d'intervenants a coordonner",             3, "text"),
        ("Logiciels / workflow imposes ?",                 4, "text"),
        ("Delai de livraison final",                       5, "text"),
    ],
    "Sound Designer": [
        ("Type de projet audio",                           1, "single_choice", ["Film / Video", "Podcast", "Publicite", "Autre"]),
        ("Type de prestation requise",                    2, "single_choice", ["Design sonore (SFX)", "Mixage", "Voix-off", "Tout"]),
        ("Duree du contenu a sonoriser",                  3, "text"),
        ("Sources audio fournies ?",                      4, "single_choice", ["Oui", "Non - a creer"]),
        ("Format de livraison audio",                     5, "text"),
    ],

    # ─────────────── WRITING & CONTENT CREATION ───────────────
    "Creative Writer (Fiction/Non-fiction)": [
        ("Genre d'ecriture",                               1, "single_choice", ["Fiction", "Non-fiction", "Poesie", "Scenario"]),
        ("Volume estime (mots ou pages)",                 2, "text"),
        ("Ton et style souhaites",                        3, "text"),
        ("Brief ou trame fournie ?",                      4, "single_choice", ["Oui", "Non - liberte creative"]),
        ("Nombre de revisions incluses",                  5, "text"),
    ],
    "Newsletter Writer": [
        ("Frequence d'envoi de la newsletter",            1, "single_choice", ["Hebdomadaire", "Bi-mensuelle", "Mensuelle", "Ponctuelle"]),
        ("Thematique / secteur d'activite",               2, "text"),
        ("Longueur souhaitee par edition",                3, "text"),
        ("Ton editorial souhaite",                        4, "single_choice", ["Professionnel", "Decontracte", "Informatif", "Promotionnel"]),
        ("Integration dans un outil d'emailing requise ?", 5, "single_choice", ["Oui", "Non"]),
    ],
    "Product Description Writer": [
        ("Nombre de fiches produits a rediger",           1, "text"),
        ("Secteur / type de produits",                    2, "text"),
        ("Longueur souhaitee par description",            3, "single_choice", ["Courte (< 100 mots)", "Moyenne (100-300 mots)", "Longue (> 300 mots)"]),
        ("Optimisation SEO requise ?",                    4, "single_choice", ["Oui", "Non"]),
        ("Ton de marque a respecter ?",                   5, "text"),
    ],
    "Scriptwriter (YouTube, Podcasts, Video)": [
        ("Format du contenu",                             1, "single_choice", ["Video YouTube", "Podcast", "Publicite", "Court-metrage"]),
        ("Duree cible du contenu",                        2, "text"),
        ("Sujet / thematique",                            3, "text"),
        ("Ton souhaite",                                  4, "single_choice", ["Informatif", "Divertissant", "Persuasif", "Narratif"]),
        ("Nombre d'episodes / scripts a produire",        5, "text"),
    ],
}


def main():
    db = SessionLocal()
    try:
        # active, non-general categories grouped by stripped name
        cats = db.query(models.Category).filter(
            models.Category.status == 'active',
            models.Category.is_general == False
        ).all()

        added_total = 0
        touched = 0
        skipped_existing = 0
        for cat in cats:
            key = (cat.name or '').strip()
            spec = QUESTIONS.get(key)
            if not spec:
                continue
            existing = db.query(func.count(models.Question.id)).filter(
                models.Question.category_id == cat.id,
                models.Question.status == 'active'
            ).scalar() or 0
            if existing > 0:
                skipped_existing += 1
                continue
            for item in spec:
                label, order, atype = item[0], item[1], item[2]
                opts = item[3] if len(item) > 3 else None
                db.add(models.Question(
                    id=uuid.uuid4(), label=label, answer_type=atype,
                    options=json.dumps(opts) if opts else None,
                    is_required=True, display_order=order, status='active',
                    category_id=cat.id
                ))
                added_total += 1
            touched += 1

        db.commit()
        print(f"Categories seeded: {touched}")
        print(f"Questions added:   {added_total}")
        print(f"Skipped (already had questions): {skipped_existing}")

        # final coverage report
        all_cats = db.query(models.Category).filter(
            models.Category.status == 'active',
            models.Category.is_general == False
        ).all()
        missing = [c.name.strip() for c in all_cats if (db.query(func.count(models.Question.id)).filter(
            models.Question.category_id == c.id, models.Question.status == 'active').scalar() or 0) == 0]
        print(f"\nActive categories still WITHOUT questions: {len(missing)}")
        for m in missing:
            print("  - " + m)
    except Exception:
        db.rollback()
        import traceback; traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
