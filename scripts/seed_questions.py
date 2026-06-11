"""
Seed questionnaire questions based on Talent619 categories and subcategories.
Run from projet_pfe2/ with: venv\Scripts\python.exe scripts/seed_questions.py
"""
import sys, uuid, json
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.core import models
from sqlalchemy import func

db = SessionLocal()
try:
    cats = {c.name: c.id for c in db.query(models.Category).all()}
    print(f"Available categories: {len(cats)}")

    # ── General section (is_general=True, always shown) ─────────────────
    gen = models.Category(
        id=uuid.uuid4(),
        name="Informations Generales",
        is_general=True,
        status="active",
        description="Questions generales applicables a tous les projets"
    )
    db.add(gen)
    db.flush()

    general_questions = [
        ("Nom complet du projet",                                1, "text"),
        ("Description et objectif principal du projet",         2, "text"),
        ("Utilisateurs cibles (clients, equipes, public...)",   3, "text"),
        ("Budget estime pour ce projet (DT ou devise)",         4, "text"),
        ("Date limite souhaitee / delai de livraison",          5, "text"),
        ("Langue principale du livrable",                       6, "text"),
    ]
    for label, order, atype in general_questions:
        db.add(models.Question(
            id=uuid.uuid4(), label=label, answer_type=atype,
            is_required=True, display_order=order, status="active",
            category_id=gen.id
        ))

    def add_qs(cat_name, questions):
        """questions: list of (label, order, answer_type, options_list_or_None)"""
        cid = cats.get(cat_name)
        if not cid:
            return
        for item in questions:
            label, order, atype = item[0], item[1], item[2]
            opts = item[3] if len(item) > 3 else None
            db.add(models.Question(
                id=uuid.uuid4(), label=label, answer_type=atype,
                options=json.dumps(opts) if opts else None,
                is_required=True, display_order=order, status="active",
                category_id=cid
            ))

    # ─────────────────── INFORMATION TECHNOLOGY (IT) ────────────────────
    add_qs("Full Stack Developer", [
        ("Langage backend prefere (Node.js, Django, Laravel, FastAPI...)", 1, "text"),
        ("Framework frontend prefere (React, Vue, Angular...)",            2, "text"),
        ("Base de donnees preferee (PostgreSQL, MySQL, MongoDB...)",       3, "text"),
        ("Type d'API requis",                                              4, "single_choice", ["REST", "GraphQL", "gRPC", "Les deux"]),
        ("Nombre d'utilisateurs simultanees attendus",                     5, "text"),
        ("Panneau d'administration requis ?",                              6, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Front-End Developer", [
        ("Design system ou maquettes fournis ?",                           1, "single_choice", ["Oui - Figma", "Oui - Adobe XD", "Non - a creer"]),
        ("Framework frontend requis",                                      2, "text"),
        ("Support mobile requis",                                          3, "single_choice", ["Responsive web", "Application mobile native", "Les deux"]),
        ("Navigateurs cibles",                                             4, "text"),
        ("Animations ou microinteractions souhaitees ?",                   5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Back-End Developer", [
        ("Architecture applicative souhaitee",                             1, "single_choice", ["Monolithique", "Microservices", "Serverless"]),
        ("Hebergement prefere",                                            2, "single_choice", ["AWS", "Azure", "GCP", "VPS Linux", "On-premise"]),
        ("Methode d'authentification",                                     3, "single_choice", ["JWT", "OAuth2 / SSO", "Session classique", "API Key"]),
        ("Monitoring et logs requis ?",                                    4, "single_choice", ["Oui", "Non"]),
        ("Contraintes de performance ou SLA a respecter ?",               5, "text"),
    ])
    add_qs("Mobile App Developer (iOS/Android)", [
        ("Plateforme cible",                                               1, "single_choice", ["iOS uniquement", "Android uniquement", "iOS + Android natif", "Cross-platform (Flutter/RN)"]),
        ("Fonctionnement hors-ligne requis ?",                             2, "single_choice", ["Oui", "Non"]),
        ("Notifications push requises ?",                                  3, "single_choice", ["Oui", "Non"]),
        ("Paiement in-app requis ?",                                       4, "single_choice", ["Oui", "Non"]),
        ("Fonctionnalites hardware necessaires",                           5, "single_choice", ["GPS", "Camera / Scanner", "Les deux", "Aucune"]),
    ])
    add_qs("DevOps / Cloud Engineer", [
        ("Plateforme cloud cible",                                         1, "single_choice", ["AWS", "Azure", "GCP", "Multi-cloud", "On-premise"]),
        ("Pipeline CI/CD requis ?",                                        2, "single_choice", ["GitHub Actions", "GitLab CI", "Jenkins", "Non"]),
        ("Conteneurisation requise ?",                                     3, "single_choice", ["Docker", "Kubernetes", "Docker + Kubernetes", "Non"]),
        ("Haute disponibilite / load balancing requis ?",                  4, "single_choice", ["Oui", "Non"]),
        ("Outil de supervision (Grafana, Datadog) requis ?",              5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Data Scientist / ML Engineer", [
        ("Type de probleme ML a resoudre",                                 1, "text"),
        ("Volume de donnees disponibles",                                  2, "single_choice", ["Moins de 10k lignes", "10k a 1M lignes", "Plus de 1M lignes"]),
        ("Framework ML prefere",                                           3, "text"),
        ("Deploiement du modele requis ?",                                 4, "single_choice", ["API REST", "Application web", "Edge device", "Non requis"]),
        ("Interpretabilite du modele requise ?",                          5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Cybersecurity Specialist", [
        ("Type d'intervention requise",                                    1, "text"),
        ("Norme de conformite visee (ISO 27001, RGPD, SOC 2...)",        2, "text"),
        ("Tests d'intrusion (pentest) inclus ?",                          3, "single_choice", ["Oui - boite noire", "Oui - boite grise", "Oui - boite blanche", "Non"]),
        ("Rapport de vulnerabilites attendu ?",                           4, "single_choice", ["Oui", "Non"]),
        ("Formation de l'equipe incluse ?",                               5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("UI/UX Designer", [
        ("Livrable attendu",                                               1, "single_choice", ["Wireframes", "Maquettes HD", "Prototype cliquable Figma", "Tout"]),
        ("Outil de design prefere",                                        2, "text"),
        ("Charte graphique existante a respecter ?",                      3, "single_choice", ["Oui", "Non - a creer"]),
        ("Tests utilisateurs inclus dans la prestation ?",                4, "single_choice", ["Oui", "Non"]),
        ("Nombre d'ecrans / pages a concevoir",                           5, "text"),
    ])
    add_qs("Database Administrator", [
        ("SGBD utilise ou prefere",                                        1, "text"),
        ("Volume de donnees estime",                                       2, "text"),
        ("Sauvegardes et plan de reprise requis ?",                       3, "single_choice", ["Oui", "Non"]),
        ("Optimisation des performances requise ?",                       4, "single_choice", ["Oui", "Non"]),
        ("Migration de donnees incluse ?",                                5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Network Engineer", [
        ("Infrastructure reseau existante a maintenir ?",                 1, "single_choice", ["Oui", "Non - nouvelle infrastructure"]),
        ("Nombre de sites / sites distants",                              2, "text"),
        ("VPN ou acces distant requis ?",                                 3, "single_choice", ["Oui", "Non"]),
        ("Wifi manageable requis ?",                                      4, "single_choice", ["Oui", "Non"]),
        ("Supervision reseau (NMS) souhaitee ?",                         5, "single_choice", ["Oui", "Non"]),
    ])

    # ─────────────────── GAME DEVELOPMENT & 3D MODELING ─────────────────
    add_qs("Game Developer (Unity, Unreal)", [
        ("Moteur de jeu requis",                                           1, "single_choice", ["Unity", "Unreal Engine", "Godot", "Autre"]),
        ("Plateforme(s) cible(s)",                                        2, "single_choice", ["PC (Windows/Mac)", "Mobile (iOS/Android)", "Console", "Multi-plateforme"]),
        ("Dimension du jeu",                                              3, "single_choice", ["2D", "3D", "VR", "AR"]),
        ("Mode multijoueur requis ?",                                     4, "single_choice", ["Oui - en ligne", "Oui - local", "Non - solo"]),
        ("Duree de la partie / niveau moyen souhaitee",                   5, "text"),
    ])
    add_qs("Game Designer", [
        ("Genre du jeu (RPG, FPS, Puzzle, Platformer...)",                1, "text"),
        ("Mecaniques de jeu principales a concevoir",                     2, "text"),
        ("Game Design Document (GDD) requis ?",                          3, "single_choice", ["Oui", "Non"]),
        ("Systeme de progression requis (niveaux, XP, succès) ?",        4, "single_choice", ["Oui", "Non"]),
        ("Modele economique du jeu",                                      5, "single_choice", ["Achat unique", "Free-to-Play", "Abonnement", "Aucun"]),
    ])
    add_qs("3D Modeler", [
        ("Style artistique souhaite",                                     1, "single_choice", ["Realiste", "Cartoon / Stylise", "Low-poly", "Sci-fi / Futuriste"]),
        ("Logiciel 3D prefere",                                           2, "text"),
        ("Nombre approximatif d'assets a modeliser",                      3, "text"),
        ("Optimisation temps reel ou prerendu ?",                        4, "single_choice", ["Temps reel (jeu / AR)", "Pre-rendu (cinema / image)"]),
        ("Format de livraison des fichiers",                              5, "text"),
    ])
    add_qs("Concept Artist", [
        ("Nombre de concepts a produire",                                 1, "text"),
        ("Style artistique de reference",                                 2, "text"),
        ("Type de livrable (personnages, environnements, props)",        3, "text"),
        ("Format de livraison (PNG, PSD, PDF...)",                       4, "text"),
        ("Nombre de revisions incluses",                                  5, "text"),
    ])
    add_qs("Character Animator", [
        ("Logiciel d'animation (Maya, Blender, Motion Capture)",         1, "text"),
        ("Nombre de personnages a animer",                                2, "text"),
        ("Types d'animations requises (idle, marche, attaque...)",       3, "text"),
        ("Motion capture disponible ?",                                   4, "single_choice", ["Oui", "Non"]),
        ("Format d'export requis",                                        5, "text"),
    ])

    # ─────────────────── MEDIA & VIDEO PRODUCTION ────────────────────────
    add_qs("Video Editor", [
        ("Type de video (corporate, pub, evenement, YouTube...)",        1, "text"),
        ("Duree approximative de la video finale",                        2, "text"),
        ("Format de rendu requis",                                        3, "single_choice", ["1080p 16:9", "4K 16:9", "Vertical 9:16 (Stories/Reels)", "Multi-format"]),
        ("Les rushes (footage) sont-ils fournis ?",                      4, "single_choice", ["Oui - tous les rushes", "Non - a filmer", "Partiellement"]),
        ("Sous-titres ou traduction requise ?",                          5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Motion Graphics Artist", [
        ("Type d'animation (intro, explainer, infographie...)",          1, "text"),
        ("Duree de l'animation",                                          2, "text"),
        ("Style visuel de reference",                                     3, "text"),
        ("Voix-off ou musique a integrer ?",                              4, "single_choice", ["Voix-off fournie", "Musique fournie", "Les deux fournis", "A sourcer"]),
        ("Format de livraison",                                           5, "text"),
    ])
    add_qs("Videographer (Event/Corporate/Commercial)", [
        ("Type d'evenement ou de tournage",                               1, "text"),
        ("Duree de tournage prevue",                                      2, "text"),
        ("Nombre de cameras souhaitees",                                  3, "single_choice", ["1 camera", "2 cameras", "3+ cameras"]),
        ("Diffusion en direct (live streaming) requise ?",               4, "single_choice", ["Oui", "Non"]),
        ("Prise de vue par drone requise ?",                              5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Storyboard Artist", [
        ("Nombre de scenes / sequences a storyboarder",                  1, "text"),
        ("Format de livraison (numerique, papier, animatique)",          2, "text"),
        ("Niveau de detail souhaite (esquisse, semi-fini, fini)",       3, "single_choice", ["Esquisses rapides", "Semi-fini", "Fini et detaille"]),
        ("Brief creatif ou script fourni ?",                             4, "single_choice", ["Oui", "Non"]),
        ("Revisions incluses",                                            5, "text"),
    ])

    # ─────────────────── WRITING & CONTENT CREATION ─────────────────────
    add_qs("Copywriter", [
        ("Type de contenu (site web, pub, email, social media...)",      1, "text"),
        ("Ton souhaite",                                                  2, "single_choice", ["Formel / Professionnel", "Decontracte / Friendly", "Persuasif / Commercial", "Informatif / Editorial"]),
        ("Volume de mots ou nombre de pages estime",                     3, "text"),
        ("Public cible precis",                                           4, "text"),
        ("Optimisation SEO requise ?",                                   5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Technical Writer", [
        ("Type de document (manuel, API doc, guide utilisateur...)",     1, "text"),
        ("Format de livraison (Word, PDF, Confluence, Markdown)",        2, "text"),
        ("Niveau technique des lecteurs cibles",                         3, "single_choice", ["Debutant", "Intermediaire", "Expert"]),
        ("Captures d'ecran et diagrammes a inclure ?",                   4, "single_choice", ["Oui", "Non"]),
        ("Document a maintenir et mettre a jour regulierement ?",        5, "single_choice", ["Oui", "Non"]),
    ])

    # ─────────────────── MARKETING & ADVERTISING ─────────────────────────
    add_qs("Digital Marketing Specialist", [
        ("Canaux marketing prioritaires",                                  1, "text"),
        ("Objectif principal de la campagne",                             2, "single_choice", ["Notoriete de marque", "Generation de leads", "Ventes directes", "Fidelisation clients"]),
        ("Budget mensuel alloue au marketing digital",                   3, "text"),
        ("Outils analytics deja en place ?",                             4, "text"),
        ("KPIs prioritaires a atteindre",                                5, "text"),
    ])
    add_qs("Social Media Manager", [
        ("Reseaux sociaux prioritaires",                                  1, "text"),
        ("Frequence de publication souhaitee",                            2, "single_choice", ["1 a 3 posts par semaine", "4 a 7 posts par semaine", "1 post ou plus par jour"]),
        ("Creation visuelle (design, video) incluse ?",                  3, "single_choice", ["Oui", "Non - texte uniquement"]),
        ("Community management (reponses, moderation) inclus ?",         4, "single_choice", ["Oui", "Non"]),
        ("Publicites payantes (Ads) incluses ?",                         5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("SEO Specialist", [
        ("Site web existant a optimiser ou nouveau site ?",              1, "single_choice", ["Site existant", "Nouveau site"]),
        ("Mots-cles prioritaires ou secteur d'activite",                 2, "text"),
        ("Marche cible geographiquement",                                 3, "single_choice", ["Local", "National", "International"]),
        ("Audit SEO complet requis ?",                                   4, "single_choice", ["Oui", "Non"]),
        ("Creation de contenu optimise incluse ?",                       5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Content Strategist", [
        ("Objectif de la strategie de contenu",                          1, "text"),
        ("Canaux de distribution du contenu",                            2, "text"),
        ("Frequence de publication souhaitee",                            3, "text"),
        ("Calendrier editorial a livrer ?",                              4, "single_choice", ["Oui", "Non"]),
        ("Analyse des concurrents incluse ?",                            5, "single_choice", ["Oui", "Non"]),
    ])

    # ─────────────────── DESIGN & CREATIVE ───────────────────────────────
    add_qs("Graphic Designer", [
        ("Type de creation demandee",                                     1, "text"),
        ("Format(s) de livraison requis",                                2, "text"),
        ("Charte graphique existante a respecter ?",                     3, "single_choice", ["Oui", "Non - liberte creative"]),
        ("Nombre de revisions incluses",                                  4, "text"),
        ("Declinaisons de formats necessaires ?",                        5, "text"),
    ])
    add_qs("Brand Identity Designer", [
        ("Nom de marque deja defini ?",                                   1, "single_choice", ["Oui", "Non"]),
        ("Livrables attendus (logo, couleurs, typographies, charte)",    2, "text"),
        ("Secteur d'activite et concurrents de reference",               3, "text"),
        ("Valeurs et personnalite de la marque a exprimer",              4, "text"),
        ("Brand book (support de presentation) requis ?",                5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Illustrator", [
        ("Style d'illustration souhaite",                                 1, "text"),
        ("Nombre d'illustrations a realiser",                             2, "text"),
        ("Format de livraison (vectoriel, raster, impression)",          3, "text"),
        ("Brief ou references visuelles fournis ?",                      4, "single_choice", ["Oui", "Non"]),
        ("Droits d'utilisation requis (commercial, editorial...)",       5, "text"),
    ])

    # ─────────────────── FINANCE ─────────────────────────────────────────
    add_qs("Financial Analyst", [
        ("Type d'analyse requise",                                        1, "text"),
        ("Secteur ou entreprise a analyser",                              2, "text"),
        ("Format de livraison du rapport",                                3, "text"),
        ("Donnees financieres disponibles ?",                             4, "single_choice", ["Oui - acces complet", "Oui - acces partiel", "Non - a collecter"]),
        ("Frequence du reporting souhaite",                               5, "single_choice", ["Ponctuel", "Mensuel", "Trimestriel", "Annuel"]),
    ])
    add_qs("Accountant / Bookkeeper", [
        ("Logiciel comptable utilise",                                    1, "text"),
        ("Volume de transactions mensuelles estime",                      2, "text"),
        ("Declarations fiscales incluses ?",                              3, "single_choice", ["Oui", "Non"]),
        ("Cloture annuelle requise ?",                                    4, "single_choice", ["Oui", "Non"]),
        ("Gestion de la paie incluse ?",                                  5, "single_choice", ["Oui", "Non"]),
    ])
    add_qs("Investment Advisor", [
        ("Profil de risque du client",                                    1, "single_choice", ["Prudent", "Equilibre", "Dynamique", "Agressif"]),
        ("Montant a investir (fourchette)",                               2, "text"),
        ("Horizon d'investissement",                                      3, "single_choice", ["Court terme (< 1 an)", "Moyen terme (1-5 ans)", "Long terme (> 5 ans)"]),
        ("Classes d'actifs preferees",                                    4, "text"),
        ("Rapport de performance regulier requis ?",                     5, "single_choice", ["Oui", "Non"]),
    ])

    db.commit()

    total_q = db.query(models.Question).count()
    print(f"\nTotal questions seeded: {total_q}")
    print("\nQuestions per category:")
    summary = db.query(models.Category.name, func.count(models.Question.id)).join(
        models.Question, models.Question.category_id == models.Category.id
    ).group_by(models.Category.name).order_by(func.count(models.Question.id).desc()).all()
    for name, count in summary:
        print(f"  {count:2d}  {name}")

except Exception as e:
    db.rollback()
    import traceback; traceback.print_exc()
finally:
    db.close()
